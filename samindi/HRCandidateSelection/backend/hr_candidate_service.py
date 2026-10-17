"""HR Candidate Selection — evidence-based candidate assessment service.

Ported from the standalone SkillVerify MERN/Python prototype (Node/Express +
MongoDB gateway dropped in favor of the unified app's own auth/session layer,
matching the pattern used for the other components) into an importable
service used by the unified Career Intelligence Platform FastAPI app.

This is an admin-only (HR) tool: cross-references a candidate resume against
independent public GitHub evidence and a direct LinkedIn profile lookup, and
produces an explainable, evidence-grounded assessment with a human-in-the-loop
recruiter decision panel.
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
            from core.esco_ontology import get_esco_ontology
            from core.resume_parser import ResumeDocumentParser, ResumeClaimExtractor
            from core.github_miner import GitHubEvidenceMiner
            from core.temporal_calibrator import TemporalCalibrator
            from core.claim_verifier import CrossSourceClaimVerifier
            from core.model_service import get_ml_model_service
            from core.guidance import RecruiterGuidanceEngine
            from core.linkedin_retriever import get_linkedin_retriever

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

    def health(self) -> Dict[str, Any]:
        self.load()
        return {
            "status": "healthy" if not self._load_error else "error",
            "service": "HR Candidate Selection AI Engine",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "esco_skills_loaded": len(getattr(self.esco, "skills_by_uri", getattr(self.esco, "skills", []) if self.esco else [])) if self.esco else 0,
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

    def _save_db(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            print(f"[HRCandidateService] Failed to save data store: {exc}")

    # ------------------------------------------------------------------
    # Job role profiles
    # ------------------------------------------------------------------

    def get_roles(self) -> Dict[str, Any]:
        self.load()
        db = self._load_db()
        standard_roles = [
            self.esco.get_default_role_config("full stack mern developer"),
            self.esco.get_default_role_config("backend python engineer"),
            self.esco.get_default_role_config("frontend react developer"),
            self.esco.get_default_role_config("devops engineer"),
            self.esco.get_default_role_config("data scientist"),
        ]
        custom_roles = list(db.get("custom_roles", {}).values())
        return {
            "standardRoles": standard_roles,
            "customRoles": custom_roles,
            "roles": standard_roles + custom_roles,
        }

    def create_custom_role(self, role: Dict[str, Any]) -> Dict[str, Any]:
        db = self._load_db()
        db.setdefault("custom_roles", {})[role["roleId"]] = role
        self._save_db(db)
        return role

    def search_skills(self, q: str) -> Dict[str, Any]:
        self.load()
        return {
            "query": q,
            "canonical": self.esco.resolve_canonical_skill_name(q),
            "metadata": self.esco.lookup_skill(q),
        }

    # ------------------------------------------------------------------
    # Candidate assessment
    # ------------------------------------------------------------------

    def assess_candidate(
        self,
        filename: str,
        file_bytes: Optional[bytes],
        resume_text: Optional[str],
        candidate_name: Optional[str],
        email: Optional[str],
        github_username: Optional[str],
        linkedin_url: Optional[str],
        apify_token: Optional[str],
        target_role_id: Optional[str],
    ) -> Dict[str, Any]:
        self.load()
        if self._load_error:
            raise RuntimeError(self._load_error)

        if file_bytes:
            extracted_text = self._ResumeDocumentParser.extract_text(file_bytes, filename)
        elif resume_text:
            extracted_text = resume_text
        else:
            raise ValueError("Either a resume file upload or resume text must be provided.")

        if not extracted_text.strip():
            raise ValueError("No readable text could be extracted from the uploaded document.")

        db = self._load_db()
        resolved_role_key = target_role_id or "full_stack_mern"
        if resolved_role_key in db.get("custom_roles", {}):
            role_config = db["custom_roles"][resolved_role_key]
        else:
            role_config = self.esco.get_default_role_config(resolved_role_key)

        clean_github = self._GitHubEvidenceMiner.clean_username(github_username)

        assessment_result = self.verifier.verify_candidate(
            resume_text=extracted_text,
            target_role_config=role_config,
            github_username=clean_github or None,
            candidate_name=candidate_name,
        )

        active_token = (apify_token.strip() if apify_token and apify_token.strip() else None) or os.getenv(
            "APIFY_API_TOKEN"
        )
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

    def get_candidates(self) -> List[Dict[str, Any]]:
        db = self._load_db()
        items = list(db.get("candidates", {}).values())
        items.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        return items

    def get_candidate_detail(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        db = self._load_db()
        return db.get("candidates", {}).get(assessment_id)

    def record_hr_decision(
        self, assessment_id: str, decision: str, notes: str, reviewer_name: str
    ) -> Optional[Dict[str, Any]]:
        db = self._load_db()
        candidates = db.get("candidates", {})
        if assessment_id not in candidates:
            return None
        candidates[assessment_id]["hrDecision"] = {
            "decision": decision,
            "notes": notes,
            "reviewerName": reviewer_name,
            "decidedAt": datetime.now(timezone.utc).isoformat(),
        }
        self._save_db(db)
        return candidates[assessment_id]

    def delete_candidate(self, assessment_id: str) -> bool:
        db = self._load_db()
        candidates = db.get("candidates", {})
        if assessment_id in candidates:
            del candidates[assessment_id]
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
