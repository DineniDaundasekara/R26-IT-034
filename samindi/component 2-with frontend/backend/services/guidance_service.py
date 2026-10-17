import json
import os
from typing import Dict, List

try:
    from groq import Groq
except ImportError:  # Backend can still use deterministic fallback guidance.
    Groq = None


DEFAULT_GUIDANCE = {
    "strengths": [],
    "priority_improvements": [],
    "cv_maintenance": [],
    "career_paths": [],
    "interview_preparation": [],
    "next_actions": [],
}


class GuidanceService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    def configured(self) -> bool:
        return bool(self.api_key and Groq is not None)

    @staticmethod
    def _fallback(predicted_career_path: str, cv_evidence: Dict, readiness: Dict, jobs: List[Dict], target_role: str = "") -> Dict:
        skills = cv_evidence.get("skills") or []
        missing_sections = readiness.get("missing_core_sections") or []
        missing_skills = readiness.get("recurring_missing_skills") or []
        role_alignment = readiness.get("role_alignment") or {}
        is_transition = role_alignment.get("is_career_transition", False)

        strengths = []
        if skills:
            strengths.append("Your CV clearly presents evidence of " + ", ".join(skills[:8]) + ".")
        if any(job.get("fit") in {"Strong Match", "Potential Match"} for job in jobs[:5]):
            strengths.append("Your CV already aligns with skills requested in at least one current vacancy.")
        if is_transition:
            strengths.append(f"Strong foundation in {predicted_career_path} with transferable technical capabilities.")

        improvements = []
        if is_transition and target_role:
            improvements.append(
                f"Career Transition Priority: Your profile aligns with {predicted_career_path}. "
                f"To transition into {target_role}, develop domain-specific projects and certifications."
            )
        if missing_sections:
            improvements.append("Strengthen these CV sections: " + ", ".join(missing_sections) + ".")
        if missing_skills:
            improvements.append("Build demonstrable evidence for recurring market requirements such as " + ", ".join(missing_skills[:6]) + ".")
        if not improvements:
            improvements.append("Tailor project and experience bullet points to the requirements of each vacancy you apply for.")

        career_paths = []
        if target_role and target_role not in career_paths:
            career_paths.append(target_role)
        if predicted_career_path and predicted_career_path not in career_paths:
            career_paths.append(predicted_career_path)
        for job in jobs[:6]:
            title = str(job.get("title") or "").strip()
            if title and title not in career_paths:
                career_paths.append(title)
            if len(career_paths) >= 4:
                break

        result = dict(DEFAULT_GUIDANCE)
        result.update({
            "strengths": strengths,
            "priority_improvements": improvements,
            "cv_maintenance": [
                "Keep contact details, professional links, technical skills and recent experience up to date.",
                "Use achievement-focused bullet points that explain what you built, how you contributed and the result.",
                "Tailor the professional summary and most relevant skills to each role instead of sending one unchanged CV.",
                "Keep formatting consistent, use clear section headings and remove unnecessary personal information.",
            ],
            "career_paths": career_paths,
            "interview_preparation": [
                "Prepare a concise explanation for every major project and experience item included in the CV.",
                "Prepare examples that demonstrate the skills matched to the selected vacancy.",
                "Review recurring missing skills before interviewing for similar roles.",
            ],
            "next_actions": [
                "Open the recommended vacancies and verify the employer's latest requirements before applying.",
                "Update the CV only with skills and experience you can genuinely demonstrate.",
                "Prioritize vacancies where your existing evidence is strongest, then plan upskilling for recurring gaps.",
            ],
        })
        return result

    def generate(
        self,
        target_role: str,
        predicted_career_path: str,
        cv_evidence: Dict,
        readiness: Dict,
        jobs: List[Dict],
    ) -> Dict:
        if not self.api_key or Groq is None:
            return self._fallback(predicted_career_path, cv_evidence, readiness, jobs, target_role=target_role)

        client = Groq(api_key=self.api_key, timeout=20.0)
        compact_jobs = [
            {
                "title": job.get("title"),
                "company": job.get("company"),
                "source": job.get("source_name"),
                "fit": job.get("fit"),
                "matched_skills": job.get("matched_skills"),
                "missing_skills": job.get("missing_skills"),
            }
            for job in jobs[:6]
        ]

        evidence = {
            "target_role": target_role,
            "ml_career_path_prediction": predicted_career_path,
            "qualitative_cv_level": readiness.get("level"),
            "readiness_reasons": readiness.get("reasons"),
            "document_quality": readiness.get("document_quality"),
            "role_alignment": readiness.get("role_alignment"),
            "cv_skills": cv_evidence.get("skills"),
            "cv_sections": cv_evidence.get("sections"),
            "missing_core_sections": readiness.get("missing_core_sections"),
            "recurring_missing_market_skills": readiness.get("recurring_missing_skills"),
            "retrieved_job_evidence": compact_jobs,
        }

        system_prompt = """
You are the career-guidance wording layer of a CV analysis application.

STRICT RULES:
1. Use only the supplied evidence for claims about the candidate and vacancies.
2. Never invent employers, vacancies, education, experience, projects, certifications or candidate skills.
3. New skills may be suggested only as upskilling recommendations.
4. Do not output numeric CV scores, hiring probabilities, interview-pass probabilities or ATS percentages.
5. Do not override the machine-learning career-path prediction.
6. Do not claim the qualitative CV level came from the career-path classifier.
7. Give professional, concise, practical CV-maintenance and career guidance.
8. Return JSON only with exactly these keys:
   strengths,
   priority_improvements,
   cv_maintenance,
   career_paths,
   interview_preparation,
   next_actions
Each value must be an array of short strings.
""".strip()

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate guidance from this evidence:\n" + json.dumps(evidence, ensure_ascii=False)},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(response.choices[0].message.content or "{}")
            result = dict(DEFAULT_GUIDANCE)
            for key in result:
                value = parsed.get(key)
                if isinstance(value, list):
                    result[key] = [str(item).strip() for item in value if str(item).strip()][:8]
            return result
        except Exception:
            return self._fallback(predicted_career_path, cv_evidence, readiness, jobs)
