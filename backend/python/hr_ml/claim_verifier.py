"""
Cross-Source Claim Verification and Assessment Engine
Performs multi-dimensional verification (Skills, Temporal Consistency, Project Alignment)
and generates explainable decision-support findings for HR professionals.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
try:
    from hr_ml.esco_ontology import get_esco_ontology, ESCOOntology
    from hr_ml.resume_parser import ResumeClaimExtractor
    from hr_ml.github_miner import GitHubEvidenceMiner
    from hr_ml.temporal_calibrator import TemporalCalibrator
    from hr_ml.repository_engineering_evidence import RepositoryEngineeringEvidenceEngine, get_ree_engine
except ImportError:
    from core.esco_ontology import get_esco_ontology, ESCOOntology
    from core.resume_parser import ResumeClaimExtractor
    from core.github_miner import GitHubEvidenceMiner
    from core.temporal_calibrator import TemporalCalibrator
    try:
        from core.repository_engineering_evidence import RepositoryEngineeringEvidenceEngine, get_ree_engine
    except ImportError:
        from repository_engineering_evidence import RepositoryEngineeringEvidenceEngine, get_ree_engine



class CrossSourceClaimVerifier:
    """
    Core verification engine orchestrating claim extraction, GitHub artifact mining,
    temporal calibration, repository engineering evidence (REE), and explainable decision synthesis.
    """

    def __init__(
        self,
        esco: Optional[ESCOOntology] = None,
        resume_extractor: Optional[ResumeClaimExtractor] = None,
        github_miner: Optional[GitHubEvidenceMiner] = None,
        temporal_calibrator: Optional[TemporalCalibrator] = None,
        ree_engine: Optional[RepositoryEngineeringEvidenceEngine] = None
    ):
        self.esco = esco or get_esco_ontology()
        self.resume_extractor = resume_extractor or ResumeClaimExtractor(self.esco)
        self.github_miner = github_miner or GitHubEvidenceMiner()
        self.calibrator = temporal_calibrator or TemporalCalibrator()
        self.ree_engine = ree_engine or get_ree_engine()
        
        # Load trained ML model artifact if available
        self.ml_model_bundle = None
        try:
            import joblib
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate_paths = [
                os.path.join(base_dir, "models", "best_ml_model.joblib"),
                os.path.join(base_dir, "..", "results", "best_ml_model.joblib")
            ]
            for p in candidate_paths:
                if os.path.exists(p):
                    self.ml_model_bundle = joblib.load(p)
                    break
        except Exception:
            self.ml_model_bundle = None


    def verify_candidate(
        self,
        resume_text: str,
        target_role_config: Dict[str, Any],
        github_username: Optional[str] = None,
        candidate_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full end-to-end evaluation pipeline for a candidate against a target job role.
        """
        # 1. Parse Resume Claims
        parsed_resume = self.resume_extractor.parse(resume_text)
        
        # Resolve GitHub handle from resume if not explicitly passed
        resolved_github = self.github_miner.clean_username(github_username or parsed_resume["contact"].get("github"))
        
        # 2. Fetch GitHub Evidence
        github_profile = {}
        if resolved_github:
            github_profile = self.github_miner.fetch_user_data(resolved_github)
        else:
            github_profile = {"exists": False, "username": None}

        # 3. Perform Skill-by-Skill Cross-Source Verification
        verified_skills = []
        role_reqs = target_role_config.get("requiredSkills", [])
        role_prefs = target_role_config.get("preferredSkills", [])
        all_target_skills = [(s, True) for s in role_reqs] + [(s, False) for s in role_prefs]

        resume_skills_map = {s["canonical"]: s for s in parsed_resume["skills"]}

        supported_count = 0
        partial_count = 0
        insufficient_count = 0
        contradiction_count = 0

        for skill_def, is_required in all_target_skills:
            skill_name = skill_def["name"]
            canonical = skill_def.get("canonical", skill_name)
            
            # Check Resume
            in_resume = canonical in resume_skills_map
            resume_claim_data = resume_skills_map.get(canonical, {})
            claimed_years = resume_claim_data.get("claimedYears")
            
            # If claimed_years not on skill directly, check temporal claims
            if claimed_years is None:
                for tc in parsed_resume["temporalClaims"]:
                    if canonical in tc.get("associatedSkills", []):
                        claimed_years = tc.get("claimedYears")
                        break

            # Check GitHub
            gh_evidence = self.github_miner.extract_skill_evidence(github_profile, canonical)
            
            # Evaluate Consistency
            if not in_resume and not gh_evidence["hasEvidence"]:
                status = "NOT_DETECTED"
                confidence = 0.90
                justification = f"'{skill_name}' was not detected in the resume text or in public GitHub repositories."
            elif not in_resume and gh_evidence["hasEvidence"]:
                status = "UNCLAIMED_PUBLIC_EVIDENCE"
                confidence = 0.85
                justification = f"'{skill_name}' was not claimed in the resume, but public GitHub evidence was found across {gh_evidence['relevantProjectsCount']} repository(ies)."
            else:
                # Skill is in resume -> Evaluate cross-source
                t_eval = self.calibrator.evaluate_temporal_consistency(
                    skill_name=canonical,
                    claimed_years=claimed_years,
                    observed_years=gh_evidence["temporalMetrics"].get("observedPublicYears", 0.0),
                    days_since_last_activity=gh_evidence["temporalMetrics"].get("daysSinceLastActivity", 9999),
                    projects_count=gh_evidence["relevantProjectsCount"]
                )
                status = t_eval["verdict"]
                confidence = t_eval["confidence"]
                justification = t_eval["reason"]

            if status == "SUPPORTED":
                supported_count += 1
            elif status == "PARTIALLY_SUPPORTED":
                partial_count += 1
            elif status == "INSUFFICIENT_EVIDENCE":
                insufficient_count += 1
            elif status == "POTENTIAL_CONTRADICTION":
                contradiction_count += 1

            verified_skills.append({
                "skillName": skill_name,
                "canonical": canonical,
                "category": skill_def.get("category", "General"),
                "isRequired": is_required,
                "importance": skill_def.get("importance", 1.0),
                "inResume": in_resume,
                "claimedYears": claimed_years,
                "resumeContexts": resume_claim_data.get("contexts", []),
                "githubEvidence": {
                    "hasEvidence": gh_evidence["hasEvidence"],
                    "relevantProjectsCount": gh_evidence["relevantProjectsCount"],
                    "relevantRepos": gh_evidence["relevantRepos"],
                    "temporalMetrics": gh_evidence["temporalMetrics"]
                },
                "status": status,
                "confidence": confidence,
                "justification": justification
            })

        # 4. Project-Level Consistency Verification
        verified_projects = self._verify_projects(parsed_resume["projectClaims"], github_profile)

        # 5. Extract Repository Engineering Evidence (REE)
        c_name = candidate_name or parsed_resume["contact"].get("email", "Candidate")
        role_name = target_role_config.get("roleName", "Software Developer")
        extracted_skills_list = [s["skillName"] for s in verified_skills]
        ree_evidence = self.ree_engine.analyze_candidate_repositories(
            repositories=github_profile.get("repositories", []),
            candidate_skills=extracted_skills_list,
            candidate_name=c_name
        )

        # 6. Synthesize Explainable HR Assessment
        summary_verdict, hr_recommendations = self._generate_hr_decision_support(
            verified_skills, verified_projects, github_profile
        )

        # 7. Generate Actionable Final Verdict & Recommendation
        final_verdict = self.generate_final_verdict(
            candidate_name=c_name,
            target_role_name=role_name,
            verified_skills=verified_skills,
            verified_projects=verified_projects,
            github_profile=github_profile
        )


        return {
            "candidateName": c_name,
            "targetRole": role_name,
            "contact": parsed_resume.get("contact", {}),
            "githubUsername": resolved_github,
            "githubProfileExists": github_profile.get("exists", False),
            "githubProfile": github_profile,
            "finalVerdict": final_verdict,
            "verificationCounts": {
                "supported": supported_count,
                "partiallySupported": partial_count,
                "insufficientEvidence": insufficient_count,
                "potentialContradiction": contradiction_count,
                "totalAuditedSkills": len(verified_skills)
            },
            "skillVerifications": verified_skills,
            "projectVerifications": verified_projects,
            "repositoryEngineeringEvidence": ree_evidence,
            "overallAssessment": summary_verdict,
            "hrDecisionSupport": hr_recommendations
        }


    def _verify_projects(
        self,
        resume_projects: List[Dict[str, Any]],
        github_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Matches resume projects with GitHub repositories via token and tech overlap."""
        verified = []
        repos = github_profile.get("repositories", [])

        for proj in resume_projects:
            desc = proj["description"].lower()
            name = proj["projectName"].lower()
            techs = [t.lower() for t in proj.get("technologies", [])]

            best_match = None
            best_score = 0.0
            matched_repo = None

            for repo in repos:
                r_name = repo.get("name", "").lower()
                r_desc = repo.get("description", "").lower()
                r_deps = [d.lower() for d in repo.get("dependencies", [])]
                r_topics = [t.lower() for t in repo.get("topics", [])]

                score = 0.0
                reasons = []

                # Name overlap
                name_tokens = set(re.findall(r"\w+", name))
                repo_tokens = set(re.findall(r"\w+", r_name))
                overlap = name_tokens.intersection(repo_tokens)
                if overlap:
                    score += 0.4
                    reasons.append(f"Name match on '{', '.join(overlap)}'")

                # Technology overlap
                tech_overlap = [t for t in techs if t in r_deps or t in r_topics or t in r_desc]
                if tech_overlap:
                    score += 0.4 * (len(tech_overlap) / max(1, len(techs)))
                    reasons.append(f"Matching tech: {', '.join(tech_overlap)}")

                if score > best_score:
                    best_score = score
                    matched_repo = repo
                    best_match = reasons

            if best_score >= 0.4 and matched_repo:
                status = "SUPPORTED" if best_score >= 0.7 else "PARTIALLY_SUPPORTED"
                justification = f"Matched to public repository '{matched_repo['name']}'. {'; '.join(best_match)}."
            elif not github_profile.get("exists", False):
                status = "INSUFFICIENT_EVIDENCE"
                justification = "No public GitHub profile provided to verify project repository."
            else:
                status = "INSUFFICIENT_EVIDENCE"
                justification = "Project claimed on resume, but no matching public repository found on GitHub (may be private or enterprise)."

            verified.append({
                "projectName": proj["projectName"],
                "description": proj["description"],
                "technologies": proj["technologies"],
                "status": status,
                "matchedRepository": matched_repo.get("name") if matched_repo else None,
                "repositoryUrl": matched_repo.get("htmlUrl") if matched_repo else None,
                "justification": justification
            })

        return verified

    def _generate_hr_decision_support(
        self,
        skills: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
        github_profile: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Synthesizes human-in-the-loop decision options and transparent justification."""
        req_skills = [s for s in skills if s["isRequired"]]
        
        req_supported = sum(1 for s in req_skills if s["status"] == "SUPPORTED")
        req_partial = sum(1 for s in req_skills if s["status"] == "PARTIALLY_SUPPORTED")
        req_insufficient = sum(1 for s in req_skills if s["status"] == "INSUFFICIENT_EVIDENCE")
        contradictions = sum(1 for s in skills if s["status"] == "POTENTIAL_CONTRADICTION")

        # Explainable summary
        if contradictions > 0:
            summary = "POTENTIAL_TIMELINE_DISCREPANCIES_DETECTED"
            summary_desc = "One or more technical claims contain chronological discrepancies that require clarification during interview."
            recommended_action = "REQUEST_CLARIFICATION"
        elif req_supported >= len(req_skills) * 0.7:
            summary = "STRONGLY_SUPPORTED_TECHNICAL_PROFILE"
            summary_desc = "Majority of core required technical skills are independently corroborated by public GitHub evidence."
            recommended_action = "PROCEED_TO_INTERVIEW"
        elif (req_supported + req_partial) >= len(req_skills) * 0.5:
            summary = "PARTIALLY_CORROBORATED_PROFILE"
            summary_desc = "Key technical skills are demonstrated in public repositories, with additional claims requiring commercial verification."
            recommended_action = "PROCEED_TO_INTERVIEW"
        else:
            summary = "LIMITED_PUBLIC_EVIDENCE"
            summary_desc = "Resume claims lack observable public corroboration on GitHub. Recommend requesting code samples or technical work portfolio."
            recommended_action = "REQUEST_ADDITIONAL_EVIDENCE"

        actions = [
            {
                "action": "Proceed to Technical Interview",
                "recommended": recommended_action == "PROCEED_TO_INTERVIEW",
                "rationale": "Sufficient technical evidence exists to proceed with competency-focused interviewing."
            },
            {
                "action": "Request Additional Portfolio / Code Samples",
                "recommended": recommended_action == "REQUEST_ADDITIONAL_EVIDENCE",
                "rationale": "Key skills lack public repositories (common for enterprise developers with private repos)."
            },
            {
                "action": "Request Clarification on Experience Timeline",
                "recommended": recommended_action == "REQUEST_CLARIFICATION",
                "rationale": "Investigate identified timeline boundaries or unsupported tenure assertions."
            },
            {
                "action": "Shortlist Candidate",
                "recommended": False,
                "rationale": "Advance candidate directly to hiring manager review."
            },
            {
                "action": "Reject Candidate",
                "recommended": False,
                "rationale": "Candidate does not meet core role requirements."
            }
        ]

        verdict = {
            "profileStatus": summary,
            "explanation": summary_desc,
            "recommendedHRAction": recommended_action,
            "coreRequirementsCoverage": {
                "totalRequired": len(req_skills),
                "supported": req_supported,
                "partiallySupported": req_partial,
                "insufficientPublicEvidence": req_insufficient,
                "potentialContradictions": contradictions
            }
        }

        return verdict, actions

    def generate_final_verdict(
        self,
        candidate_name: str,
        target_role_name: str,
        verified_skills: List[Dict[str, Any]],
        verified_projects: List[Dict[str, Any]],
        github_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes the Final Assessment & Recommendation Verdict according to decision rules:
        1. Suitable: Mandatory core skills present, score >= 80%, contradictions == 0.
        2. Partially Suitable: Score 60%-79% or partial skills needing upskilling, contradictions == 0.
        3. Not Suitable: Score < 60%, mandatory skills missing, or potential contradictions present.
        """
        required_skills = [s for s in verified_skills if s.get("isRequired", False)]
        preferred_skills = [s for s in verified_skills if not s.get("isRequired", False)]

        supported_skills = []
        partially_supported = []
        private_skills = []
        missing_req_skills = []
        missing_pref_skills = []
        contradictory_skills = []

        total_req_points = 0.0

        for s in required_skills:
            name = s["skillName"]
            st = s["status"]
            if st == "SUPPORTED":
                supported_skills.append(name)
                total_req_points += 100.0
            elif st == "PARTIALLY_SUPPORTED":
                partially_supported.append(name)
                total_req_points += 75.0
            elif st == "INSUFFICIENT_EVIDENCE":
                private_skills.append(name)
                total_req_points += 70.0
            elif st == "UNCLAIMED_PUBLIC_EVIDENCE":
                supported_skills.append(name)
                total_req_points += 80.0
            elif st == "POTENTIAL_CONTRADICTION":
                contradictory_skills.append(name)
                total_req_points += 0.0
            else:
                missing_req_skills.append(name)
                total_req_points += 0.0

        # Preferred skills bonus
        bonus_points = 0.0
        for s in preferred_skills:
            name = s["skillName"]
            st = s["status"]
            if st in ["SUPPORTED", "UNCLAIMED_PUBLIC_EVIDENCE"]:
                supported_skills.append(name)
                bonus_points += 5.0
            elif st == "PARTIALLY_SUPPORTED":
                partially_supported.append(name)
                bonus_points += 3.0
            elif st == "INSUFFICIENT_EVIDENCE":
                private_skills.append(name)
                bonus_points += 2.0
            elif st == "POTENTIAL_CONTRADICTION":
                contradictory_skills.append(name)
            else:
                missing_pref_skills.append(name)

        req_count = len(required_skills) if len(required_skills) > 0 else 1
        base_match_score = (total_req_points / (req_count * 100.0)) * 100.0
        final_match_score = min(100.0, base_match_score + bonus_points)

        # Matched Skills (Only skills verified by public code or partial corroboration)
        matched_public_skills = list(dict.fromkeys(supported_skills + partially_supported))
        matched_private_skills = list(dict.fromkeys(private_skills))

        # Overall matched skills list: verified public skills first, then private confirmed skills
        matched_skills = matched_public_skills + [f"{s} (Private Experience)" for s in matched_private_skills if s not in matched_public_skills]
        
        # Missing core skills
        missing_core_skills = [s for s in missing_req_skills if s not in matched_public_skills and s not in matched_private_skills]

        skills_to_improve = []
        # Missing core required skills
        for s in missing_core_skills:
            skills_to_improve.append(f"{s} (Missing / Core Requirement)")
        
        # Contradictions
        for s in contradictory_skills:
            skills_to_improve.append(f"{s} (Timeline Discrepancy)")
        
        # Skills with shorter public history needing upskilling
        for s in partially_supported:
            skills_to_improve.append(f"{s} (Requires Timeline Upskilling)")

        # Optional preferred skills that could be learned
        for s in missing_pref_skills:
            if s not in matched_public_skills and s not in matched_private_skills:
                skills_to_improve.append(f"{s} (Recommended Secondary Skill)")

        if not skills_to_improve:
            skills_to_improve = ["CI/CD Pipeline Automation", "Cloud Deployment Architecture (AWS/GCP)"]

        # Decision Rules:
        # 1. NOT_SUITABLE: Contradictions present, or score < 60%, or >=2 mandatory core skills missing
        # 2. SUITABLE: Score >= 80% and zero core mandatory skills missing
        # 3. PARTIALLY_SUITABLE: Score 60-79% or exactly 1 core gap needing upskilling
        if len(contradictory_skills) > 0:
            status = "This employee is not suitable for our job."
            verdict_type = "NOT_SUITABLE"
            final_match_score = min(final_match_score, 45.0)
        elif final_match_score >= 80.0 and len(missing_core_skills) == 0:
            status = "This employee is suitable for our job."
            verdict_type = "SUITABLE"
        elif final_match_score >= 60.0:
            status = "This employee is partially suitable for our job (Skill upskilling recommended)."
            verdict_type = "PARTIALLY_SUITABLE"
        else:
            status = "This employee is not suitable for our job."
            verdict_type = "NOT_SUITABLE"

        # Evidence-backed Executive Summary Comment
        name_label = candidate_name if candidate_name else "The candidate"
        repos_count = len(github_profile.get("repositories", []))
        
        summary_sentences = []
        if verdict_type == "SUITABLE":
            summary_sentences.append(
                f"{name_label} demonstrates strong practical competency for the {target_role_name} position."
            )
            if repos_count > 0 and matched_public_skills:
                summary_sentences.append(
                    f"Independent cross-source verification confirmed active public GitHub code across {repos_count} repositories, corroborating core technologies ({', '.join(matched_public_skills[:4])})."
                )
            if matched_private_skills:
                summary_sentences.append(
                    f"Additional technologies ({', '.join(matched_private_skills[:3])}) align with private enterprise development patterns with zero timeline contradictions."
                )
            summary_sentences.append("Recommended to advance directly to technical competency interviewing.")
        
        elif verdict_type == "PARTIALLY_SUITABLE":
            summary_sentences.append(
                f"{name_label} meets foundational requirements for {target_role_name}, with targeted areas identified for upskilling."
            )
            if matched_public_skills:
                summary_sentences.append(
                    f"Verified capabilities exist in {', '.join(matched_public_skills[:4])}."
                )
            if skills_to_improve:
                clean_gaps = [g.split(' (')[0] for g in skills_to_improve]
                summary_sentences.append(
                    f"Upskilling is recommended in {', '.join(clean_gaps[:3])} to meet production standards."
                )
            summary_sentences.append("Recommended for interview with targeted technical assessment on identified growth areas.")
        
        else: # NOT_SUITABLE
            if contradictory_skills:
                summary_sentences.append(
                    f"Evaluation identified significant chronological timeline discrepancies in {', '.join(contradictory_skills)}."
                )
            else:
                summary_sentences.append(
                    f"{name_label} does not currently meet the mandatory technical criteria for {target_role_name}."
                )
            summary_sentences.append("Core mandatory skills lack sufficient verification. Candidate is not recommended for this specific position at this time.")

        summary_comment = " ".join(summary_sentences)

        return {
            "status": status,
            "verdictType": verdict_type,
            "matchScore": int(round(final_match_score)),
            "summaryComment": summary_comment,
            "matchedSkills": matched_skills,
            "skillsToImprove": skills_to_improve
        }
