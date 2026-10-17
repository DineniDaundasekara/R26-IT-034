"""
SkillVerify Evidence-Based Recruiter Guidance & Decision Support
================================================================
Generates deterministic, explainable recruiter recommendations,
interview question probes, and skill gap remediation advice based
on verified public code, private experience, and ESCO requirements.
"""

from typing import Dict, List, Any, Optional


class RecruiterGuidanceEngine:
    """
    Synthesizes actionable HR guidance and tailored technical interview probes.
    """

    @staticmethod
    def generate_interview_probes(verified_skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates targeted interview questions based on the epistemic verification state of each skill.
        """
        probes = []
        for s in verified_skills:
            skill_name = s.get("skillName", "")
            status = s.get("status", "")
            claimed_years = s.get("claimedYears")
            
            if status == "INSUFFICIENT_EVIDENCE":
                probes.append({
                    "skill": skill_name,
                    "category": "Private Enterprise Experience Validation",
                    "question": f"Can you walk us through a production project at your previous employer where you architected with {skill_name}?",
                    "goal": "Verify commercial application depth for proprietary skills not visible on public GitHub."
                })
            elif status == "PARTIALLY_SUPPORTED":
                probes.append({
                    "skill": skill_name,
                    "category": "Experience Depth Probe",
                    "question": f"Your public code shows recent work with {skill_name}. Can you explain how you handled state management or performance optimization in that context?",
                    "goal": "Assess technical mastery beyond the observed public commit span."
                })
            elif status == "POTENTIAL_CONTRADICTION":
                probes.append({
                    "skill": skill_name,
                    "category": "Timeline Clarification Probe",
                    "question": f"Could you clarify your timeline regarding {skill_name} and how your role evolved from early adoption to production use?",
                    "goal": "Resolve chronological discrepancy identified between resume claim and technology launch date."
                })
            elif status == "SUPPORTED":
                probes.append({
                    "skill": skill_name,
                    "category": "Deep Technical Architecture",
                    "question": f"Given your verified {claimed_years or 'solid'} years of public {skill_name} repositories, what design patterns do you prefer for large-scale codebases?",
                    "goal": "Validate senior-level architectural design capabilities."
                })

        return probes

    @staticmethod
    def synthesize_recruiter_summary(
        candidate_name: str,
        target_role_name: str,
        match_score: int,
        verified_skills: List[Dict[str, Any]],
        counts: Dict[str, int]
    ) -> str:
        """
        Produces a concise, high-impact executive summary paragraph for hiring managers.
        """
        supported_skills = [s["skillName"] for s in verified_skills if s.get("status") == "SUPPORTED"]
        private_skills = [s["skillName"] for s in verified_skills if s.get("status") == "INSUFFICIENT_EVIDENCE"]
        contradiction_skills = [s["skillName"] for s in verified_skills if s.get("status") == "POTENTIAL_CONTRADICTION"]

        parts = []
        if supported_skills:
            parts.append(
                f"Candidate {candidate_name} exhibits verified public open-source corroboration for {', '.join(supported_skills[:4])}"
            )
        
        if private_skills:
            parts.append(
                f"Core enterprise skills ({', '.join(private_skills[:4])}) reflect consistent private career history with zero penalty assigned"
            )

        if contradiction_skills:
            parts.append(
                f"Attention: Chronological timeline discrepancies were identified on {', '.join(contradiction_skills)}"
            )

        if match_score >= 80 and not contradiction_skills:
            parts.append("Recommendation: Proceed directly to Senior Technical Architecture Interview.")
        elif match_score >= 60 and not contradiction_skills:
            parts.append("Recommendation: Schedule Technical Interview with focused probes on secondary stack requirements.")
        else:
            parts.append("Recommendation: Clarify candidate background in preliminary screening before advancing.")

        return ". ".join(parts) + "."
