\
import re
from typing import Dict, List, Set, Tuple

from .skill_catalog import extract_skills


FIT_ORDER = {
    "Strong Match": 4,
    "Potential Match": 3,
    "Developing Match": 2,
    "Low Evidence Match": 1,
    "Requirements Not Detected": 0,
}


def _role_tokens(role: str) -> Set[str]:
    stop = {"and", "or", "the", "a", "an", "junior", "senior", "associate"}
    return {
        token
        for token in re.findall(r"[a-z0-9+#.]+", (role or "").lower())
        if len(token) > 1 and token not in stop
    }


def _role_alignment(target_role: str, job_title: str) -> bool:
    target = _role_tokens(target_role)
    title = _role_tokens(job_title)
    return bool(target and title and target.intersection(title))


def _fit_label(matched: int, total_required: int, role_aligned: bool) -> str:
    """
    No numeric score is returned to the user.
    A ratio is used internally only to map evidence into a qualitative label.
    """
    if total_required <= 0:
        return "Requirements Not Detected"

    ratio = matched / total_required

    if role_aligned:
        if ratio >= 0.65:
            return "Strong Match"
        if ratio >= 0.40:
            return "Potential Match"
        if ratio >= 0.20:
            return "Developing Match"
        return "Low Evidence Match"
    else:
        if ratio >= 0.70:
            return "Potential Match"
        if ratio >= 0.35:
            return "Developing Match"
        return "Low Evidence Match"


def compare_one_job(cv_skills: List[str], target_role: str, job: Dict) -> Dict:
    cv_set = set(cv_skills)

    requirement_text = "\n".join([
        str(job.get("description") or ""),
        "\n".join(job.get("qualifications") or []),
        "\n".join(job.get("responsibilities") or []),
    ])

    required_skills = extract_skills(requirement_text)
    req_set = set(required_skills)

    matched = sorted(cv_set.intersection(req_set), key=str.lower)
    missing = sorted(req_set.difference(cv_set), key=str.lower)

    role_aligned = _role_alignment(target_role, job.get("title") or "")
    label = _fit_label(len(matched), len(required_skills), role_aligned)

    result = dict(job)
    result.update({
        "role_aligned": role_aligned,
        "required_skills_detected": required_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "fit": label,
    })
    return result


def compare_cv_to_jobs(
    cv_skills: List[str],
    target_role: str,
    jobs: List[Dict],
) -> List[Dict]:
    compared = [compare_one_job(cv_skills, target_role, job) for job in jobs]

    # Ranking uses qualitative evidence; no numeric score is exposed.
    compared.sort(
        key=lambda j: (
            FIT_ORDER.get(j.get("fit", ""), 0),
            len(j.get("matched_skills") or []),
            -len(j.get("missing_skills") or []),
        ),
        reverse=True,
    )
    return compared
