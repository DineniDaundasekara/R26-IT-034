from collections import Counter
from typing import Dict, List, Optional


ROLE_DOMAINS = {
    "Software Engineer": "Software Engineering",
    "Frontend Developer": "Software Engineering",
    "Backend Developer": "Software Engineering",
    "Full Stack Developer": "Software Engineering",
    "QA Engineer": "Quality Assurance",
    "DevOps Engineer": "Cloud & Infrastructure",
    "Data Analyst": "Data & Analytics",
    "Business Analyst": "Business & Process Analytics",
    "UI/UX Designer": "Product & Design",
}


class ReadinessService:
    """Explainable qualitative CV quality and role readiness rubric (Decoupled 2D Framework)."""

    CORE_SECTIONS = ["profile", "skills", "experience", "projects", "education"]

    LEVEL_DESCRIPTIONS = {
        "Weak": "Important CV evidence or core sections are missing and should be strengthened before applying.",
        "Average": "The CV has a usable foundation, but key core sections and market alignment can be improved.",
        "Developing (Career Transition)": "Your CV document is structurally complete, but your current evidence reflects a different career domain. Additional domain-specific projects and skills are needed for this role.",
        "Developing Match": "The CV has a solid structure, but key technical qualifications for this target role are still developing.",
        "Good": "The CV presents solid evidence and shows useful alignment with current target vacancies.",
        "Excellent": "The CV is structurally complete and exhibits strong evidence alignment with target vacancies.",
    }

    def _get_domain(self, role: str) -> str:
        role_clean = (role or "").strip()
        for key, domain in ROLE_DOMAINS.items():
            if key.lower() in role_clean.lower() or role_clean.lower() in key.lower():
                return domain
        return "General Technology"

    def assess(
        self,
        cv_evidence: Dict[str, object],
        matched_jobs: List[Dict],
        target_role: Optional[str] = None,
        predicted_career_path: Optional[str] = None,
    ) -> Dict[str, object]:
        sections = cv_evidence.get("sections") or {}
        cv_skills = cv_evidence.get("skills") or []
        links = cv_evidence.get("links") or {}

        # -----------------------------------------------------
        # 1. Intrinsic Evaluation: Document Structural Quality
        # -----------------------------------------------------
        present_sections = [s for s in self.CORE_SECTIONS if sections.get(s)]
        missing_sections = [s for s in self.CORE_SECTIONS if not sections.get(s)]
        has_links = bool(
            (links.get("github") and len(links["github"]) > 0)
            or (links.get("linkedin") and len(links["linkedin"]) > 0)
            or (links.get("portfolio_or_other") and len(links["portfolio_or_other"]) > 0)
        )

        if len(present_sections) == 5 and len(cv_skills) >= 4:
            document_quality_level = "Complete"
            document_quality_desc = "All 5 core CV sections are present and technical skills are well documented."
        elif len(present_sections) >= 3 and len(cv_skills) >= 2:
            document_quality_level = "Moderate"
            document_quality_desc = f"Contains {len(present_sections)} of 5 core sections. Strengthening missing sections will improve presentation."
        else:
            document_quality_level = "Incomplete"
            document_quality_desc = "Multiple essential CV sections (e.g. projects, experience, or skills) are missing."

        # -----------------------------------------------------
        # 2. Extrinsic Evaluation: Target Role Alignment
        # -----------------------------------------------------
        target_domain = self._get_domain(target_role or "")
        predicted_domain = self._get_domain(predicted_career_path or "")
        is_career_transition = bool(
            target_role
            and predicted_career_path
            and target_domain != predicted_domain
        )

        top_jobs = matched_jobs[:5] if matched_jobs else []
        recurring_missing = Counter()
        for job in top_jobs:
            recurring_missing.update(job.get("missing_skills") or [])

        recurring_missing_skills = [
            skill
            for skill, count in recurring_missing.most_common(8)
            if count >= 2 or len(top_jobs) <= 2
        ]

        role_aligned_jobs = [j for j in top_jobs if j.get("role_aligned")]
        has_strong_match = any(job.get("fit") == "Strong Match" for job in top_jobs)
        has_potential_match = any(
            job.get("fit") in {"Strong Match", "Potential Match"} for job in (role_aligned_jobs or top_jobs)
        )
        has_any_match = any(
            job.get("fit") in {"Strong Match", "Potential Match", "Developing Match"} for job in top_jobs
        )

        if has_strong_match and not is_career_transition:
            role_alignment_status = "High Alignment"
            role_alignment_desc = f"Strong evidence match for {target_role} vacancies."
        elif has_potential_match and not is_career_transition:
            role_alignment_status = "Potential Alignment"
            role_alignment_desc = f"Relevant skill foundation for {target_role} with minor skill gaps."
        elif is_career_transition:
            role_alignment_status = "Career Transition"
            role_alignment_desc = (
                f"CV primary profile is {predicted_career_path or predicted_domain}, "
                f"applying for {target_role or target_domain}. Requires domain-specific portfolio & skills."
            )
        elif has_any_match:
            role_alignment_status = "Developing Alignment"
            role_alignment_desc = f"Some transferable skills detected, but essential {target_role} requirements are missing."
        else:
            role_alignment_status = "Low Alignment"
            role_alignment_desc = f"Very few matching requirements found for {target_role}."

        # -----------------------------------------------------
        # 3. Decoupled Combined Readiness Rubric
        # -----------------------------------------------------
        if document_quality_level == "Incomplete" or len(cv_skills) < 2:
            level = "Weak"
        elif is_career_transition:
            # Structurally solid, but cross-domain application
            level = "Developing (Career Transition)"
        elif document_quality_level == "Complete" and has_strong_match and not missing_sections:
            level = "Excellent"
        elif document_quality_level in {"Complete", "Moderate"} and has_potential_match:
            level = "Good"
        elif has_any_match or document_quality_level == "Moderate":
            level = "Average"
        else:
            level = "Developing Match"

        # -----------------------------------------------------
        # 4. Explainable Reasons
        # -----------------------------------------------------
        reasons: List[str] = []
        if present_sections:
            reasons.append(f"CV Document Structure: {len(present_sections)}/5 core sections detected ({', '.join(present_sections)}).")
        if missing_sections:
            reasons.append(f"Missing core sections to add: {', '.join(missing_sections)}.")

        if is_career_transition:
            reasons.append(
                f"Career Transition: Your background aligns with '{predicted_career_path}', whereas your selected target is '{target_role}'. "
                f"Document quality is {document_quality_level.lower()}, but target domain alignment requires role-specific evidence."
            )
        elif has_strong_match:
            reasons.append(f"Market Evidence: Strong alignment detected with active {target_role} vacancies.")
        elif has_potential_match:
            reasons.append(f"Market Evidence: Useful skill alignment detected with active {target_role} vacancies.")
        elif top_jobs:
            reasons.append(f"Market Evidence: Vacancy comparisons indicate key skills to strengthen for {target_role}.")
        else:
            reasons.append("Market Evidence: Qualitative level is evaluated based on CV structure and detected skills.")

        return {
            "level": level,
            "description": self.LEVEL_DESCRIPTIONS.get(level, self.LEVEL_DESCRIPTIONS["Average"]),
            "method": "explainable_decoupled_rubric",
            "reasons": reasons,
            "document_quality": {
                "level": document_quality_level,
                "description": document_quality_desc,
                "present_core_sections": present_sections,
                "missing_core_sections": missing_sections,
                "has_professional_links": has_links,
            },
            "role_alignment": {
                "status": role_alignment_status,
                "description": role_alignment_desc,
                "is_career_transition": is_career_transition,
                "predicted_career_path": predicted_career_path,
                "target_role": target_role,
                "target_domain": target_domain,
                "predicted_domain": predicted_domain,
            },
            "present_core_sections": present_sections,
            "missing_core_sections": missing_sections,
            "recurring_missing_skills": recurring_missing_skills,
            "note": "Decoupled evaluation separating document structural quality from target domain fit.",
        }
