"""HR Candidate Selection — evidence-based candidate assessment service.

Wraps the SkillVerify Python AI engine (ESCO v1.1 ontology, multi-format PDF claim
parsing, multi-language GitHub evidence miner, temporal tenure calibrator, 4-way
epistemic NLI claim verifier, supervised ML model inference, direct LinkedIn &
resume career profile extractor, and recruiter HITL decision panel) into an
importable service for the unified Career Intelligence Platform FastAPI app.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class HRCandidateService:
    def __init__(self, backend_dir: Path):
        self.backend_dir = Path(backend_dir)
        self.model_path = self.backend_dir / "models" / "best_ml_model.joblib"
        self.db_file = self.backend_dir / "data_store.json"

        self._loaded = False
        self._load_error: Optional[str] = None

        self.esco = None
        self.resume_extractor = None
        self.github_miner = None
        self.temporal_calibrator = None
        self.verifier = None
        self.ml_service = None
        self.linkedin_retriever = None
        self.guidance_engine = None

    def exists(self) -> bool:
        return self.model_path.exists()

    def load(self):
        if self._loaded:
            return
        self._loaded = True
        try:
            import sys
            p_str = str(self.backend_dir)
            if p_str not in sys.path:
                sys.path.insert(0, p_str)

            from hr_ml.esco_ontology import get_esco_ontology
            from hr_ml.resume_parser import ResumeDocumentParser, ResumeClaimExtractor
            from hr_ml.github_miner import GitHubEvidenceMiner
            from hr_ml.temporal_calibrator import TemporalCalibrator
            from hr_ml.claim_verifier import CrossSourceClaimVerifier
            from hr_ml.model_service import get_ml_model_service
            from hr_ml.guidance import RecruiterGuidanceEngine
            from hr_ml.linkedin_retriever import get_linkedin_retriever

            self._ResumeDocumentParser = ResumeDocumentParser
            self._GitHubEvidenceMiner = GitHubEvidenceMiner
            self._RecruiterGuidanceEngine = RecruiterGuidanceEngine

            self.esco = get_esco_ontology()
            self.resume_extractor = ResumeClaimExtractor(self.esco)
            self.github_miner = GitHubEvidenceMiner()
            self.temporal_calibrator = TemporalCalibrator()
            self.verifier = CrossSourceClaimVerifier(
                esco=self.esco,
                resume_extractor=self.resume_extractor,
                github_miner=self.github_miner,
                temporal_calibrator=self.temporal_calibrator,
            )
            self.ml_service = get_ml_model_service()
            self.linkedin_retriever = get_linkedin_retriever()
        except Exception as exc:
            self._load_error = str(exc)
            print(f"[HRCandidateService Load Error] {exc}")

    def health(self) -> Dict[str, Any]:
        self.load()
        return {
            "status": "healthy" if not self._load_error else "error",
            "service": "HR Candidate Selection AI Engine",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "esco_skills_loaded": len(getattr(self.esco, "skills_by_uri", getattr(self.esco, "skills", []))) if self.esco else 0,
            "ml_model_loaded": bool(self.ml_service and self.ml_service.is_loaded),
            "ml_model_name": self.ml_service.model_name if self.ml_service else None,
            "error": self._load_error,
        }

    # ------------------------------------------------------------------
    # Local JSON data store (candidates + custom job role profiles)
    # ------------------------------------------------------------------

    def _load_db(self) -> Dict[str, Any]:
        if self.db_file.exists():
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"candidates": {}, "custom_roles": {}}

    def _save_db(self, data: Dict[str, Any]):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            print(f"[HRCandidateService] Failed to save data store: {exc}")

    # ------------------------------------------------------------------
    # Role Profiles & ESCO Taxonomy
    # ------------------------------------------------------------------

    def get_roles(self) -> Dict[str, Any]:
        self.load()
        db = self._load_db()
        standard_roles = []
        if self.esco:
            try:
                standard_roles = [
                    self.esco.get_default_role_config("full stack mern developer"),
                    self.esco.get_default_role_config("backend python engineer"),
                    self.esco.get_default_role_config("frontend react developer"),
                    self.esco.get_default_role_config("devops engineer"),
                    self.esco.get_default_role_config("data scientist"),
                ]
            except Exception as exc:
                print(f"[HRCandidateService] Error fetching standard roles: {exc}")
        custom_roles = list(db.get("custom_roles", {}).values())
        return {
            "standardRoles": standard_roles,
            "customRoles": custom_roles,
            "roles": standard_roles + custom_roles,
        }

    def create_custom_role(self, role_dict: Dict[str, Any]) -> Dict[str, Any]:
        db = self._load_db()
        role_id = role_dict.get("roleId") or str(uuid.uuid4())
        role_dict["roleId"] = role_id
        if "custom_roles" not in db:
            db["custom_roles"] = {}
        db["custom_roles"][role_id] = role_dict
        self._save_db(db)
        return role_dict

    def search_skills(self, query: str) -> Dict[str, Any]:
        self.load()
        canonical = self.esco.resolve_canonical_skill_name(query) if self.esco else query
        metadata = self.esco.lookup_skill(query) if self.esco else None
        return {
            "query": query,
            "canonical": canonical,
            "metadata": metadata,
        }

    # ------------------------------------------------------------------
    # Candidate Assessment Pipeline
    # ------------------------------------------------------------------

    def assess_candidate(
        self,
        filename: str,
        file_bytes: Optional[bytes] = None,
        resume_text: Optional[str] = None,
        candidate_name: Optional[str] = None,
        email: Optional[str] = None,
        github_username: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        apify_token: Optional[str] = None,
        target_role_id: Optional[str] = "full_stack_mern",
    ) -> Dict[str, Any]:
        self.load()

        extracted_text = ""
        if file_bytes:
            extracted_text = self._ResumeDocumentParser.extract_text(file_bytes, filename)
        elif resume_text:
            extracted_text = resume_text
        else:
            raise ValueError("Either a resume document upload or resume text must be provided.")

        if not extracted_text.strip():
            raise ValueError("No readable text could be extracted from the uploaded document.")

        db = self._load_db()
        resolved_role_key = target_role_id or "full_stack_mern"
        if resolved_role_key in db.get("custom_roles", {}):
            role_config = db["custom_roles"][resolved_role_key]
        else:
            role_config = self.esco.get_default_role_config(resolved_role_key) if self.esco else {
                "roleName": "Software Engineer",
                "requiredSkills": [],
                "preferredSkills": [],
            }

        clean_github = self._GitHubEvidenceMiner.clean_username(github_username) if github_username else None

        assessment_result = self.verifier.verify_candidate(
            resume_text=extracted_text,
            target_role_config=role_config,
            github_username=clean_github or None,
            candidate_name=candidate_name,
        )

        active_token = (
            apify_token.strip() if apify_token and apify_token.strip() else None
        ) or os.getenv("APIFY_API_TOKEN")

        linkedin_data = self.linkedin_retriever.get_profile_data(
            linkedin_url=linkedin_url,
            candidate_name=candidate_name or assessment_result.get("candidateName"),
            github_username=assessment_result.get("githubUsername") or clean_github,
            resume_text=extracted_text,
            api_token=active_token,
        )
        assessment_result["linkedinData"] = linkedin_data

        interview_probes = self._RecruiterGuidanceEngine.generate_interview_probes(
            assessment_result.get("skillVerifications", [])
        )
        assessment_result["interviewProbes"] = interview_probes

        assessment_id = str(uuid.uuid4())
        assessment_record = {
            "assessmentId": assessment_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "candidateName": candidate_name or assessment_result.get("candidateName", "Candidate"),
            "email": email or assessment_result.get("contact", {}).get("email"),
            "githubUsername": assessment_result.get("githubUsername") or clean_github,
            "linkedinUrl": linkedin_url or linkedin_data.get("linkedin_url"),
            "linkedinProfile": linkedin_data,
            "linkedinData": linkedin_data,
            "targetRole": role_config.get("roleName", "Full Stack MERN Developer"),
            "targetRoleId": resolved_role_key,
            "assessment": assessment_result,
            "hrDecision": None,
        }

        db.setdefault("candidates", {})[assessment_id] = assessment_record
        self._save_db(db)

        return assessment_record

    # ------------------------------------------------------------------
    # Candidate Records & Recruiter HITL Decision
    # ------------------------------------------------------------------

    def get_candidates(self) -> List[Dict[str, Any]]:
        db = self._load_db()
        items = list(db.get("candidates", {}).values())
        items.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        return items

    def get_candidate_detail(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        db = self._load_db()
        candidates = db.get("candidates", {})
        if assessment_id in candidates:
            return candidates[assessment_id]
        for k, v in candidates.items():
            if str(v.get("assessmentId")) == assessment_id or str(v.get("_id")) == assessment_id or str(k) == assessment_id:
                return v
        return None

    def record_hr_decision(
        self,
        assessment_id: str,
        decision: str,
        notes: str = "",
        reviewer_name: str = "Hiring Manager",
    ) -> Optional[Dict[str, Any]]:
        db = self._load_db()
        candidates = db.get("candidates", {})
        target_key = None
        if assessment_id in candidates:
            target_key = assessment_id
        else:
            for k, v in candidates.items():
                if str(v.get("assessmentId")) == assessment_id or str(v.get("_id")) == assessment_id or str(k) == assessment_id:
                    target_key = k
                    break

        if not target_key:
            return None

        candidates[target_key]["hrDecision"] = {
            "decision": decision,
            "notes": notes,
            "reviewerName": reviewer_name,
            "decidedAt": datetime.now(timezone.utc).isoformat(),
        }
        self._save_db(db)
        return candidates[target_key]

    def delete_candidate(self, assessment_id: str) -> bool:
        db = self._load_db()
        candidates = db.get("candidates", {})
        if assessment_id in candidates:
            del candidates[assessment_id]
            self._save_db(db)
            return True
        for k, v in list(candidates.items()):
            if str(v.get("assessmentId")) == assessment_id or str(v.get("_id")) == assessment_id or str(k) == assessment_id:
                del candidates[k]
                self._save_db(db)
                return True
        return False

    def get_ablation_results(self) -> Dict[str, Any]:
        results_path = self.backend_dir / "models" / "ablation_study_results.json"
        if results_path.exists():
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as exc:
                raise RuntimeError(f"Failed to read ablation results: {exc}")
        return {"status": "NOT_FOUND", "message": "Run ablation experiments first."}
