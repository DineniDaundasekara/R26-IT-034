from io import BytesIO
from pathlib import Path
import re
from typing import Dict, List

import pymupdf
from docx import Document

from .skill_catalog import extract_skills


SECTION_PATTERNS = {
    "profile": [
        r"\bprofile\b",
        r"\bprofessional summary\b",
        r"\bsummary\b",
        r"\bcareer objective\b",
        r"\bobjective\b",
    ],
    "skills": [
        r"\bskills\b",
        r"\btechnical skills\b",
        r"\bcore competencies\b",
        r"\btechnologies\b",
    ],
    "experience": [
        r"\bexperience\b",
        r"\bwork experience\b",
        r"\bprofessional experience\b",
        r"\bemployment\b",
    ],
    "projects": [
        r"\bprojects\b",
        r"\bacademic projects\b",
        r"\bpersonal projects\b",
        r"\bproject experience\b",
    ],
    "education": [
        r"\beducation\b",
        r"\bacademic qualifications\b",
        r"\bacademic background\b",
    ],
    "certifications": [
        r"\bcertifications\b",
        r"\bcertificates\b",
        r"\bprofessional certifications\b",
    ],
}


# --------------------------------------------------
# Professional profile URL validation
# --------------------------------------------------

def validate_profile_url(url: str, platform: str) -> bool:

    if not url:
        return False

    url = url.strip().rstrip(".,;)")


    if platform == "linkedin":

        if "linkedin.com/in/" not in url.lower():
            return False

        username = url.lower().split("linkedin.com/in/")[-1]

        invalid = [
            "",
            "404",
            "profile",
            "user",
            "linkedin"
        ]

        return (
            len(username) > 3
            and username not in invalid
        )


    if platform == "github":

        if "github.com/" not in url.lower():
            return False

        username = url.lower().split("github.com/")[-1]

        invalid = [
            "",
            "features",
            "topics",
            "login",
            "signup"
        ]

        return (
            len(username) > 1
            and username not in invalid
        )


    return True



# --------------------------------------------------
# Text cleaning
# --------------------------------------------------

def _clean_text(text: str) -> str:

    text = text.replace("\x00", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()



# --------------------------------------------------
# CV Text extraction
# --------------------------------------------------

def extract_cv_text(filename: str, data: bytes) -> str:

    suffix = Path(filename or "").suffix.lower()


    if suffix == ".pdf":

        document = pymupdf.open(
            stream=data,
            filetype="pdf"
        )

        pages = [
            page.get_text("text")
            for page in document
        ]

        document.close()

        return _clean_text(
            "\n".join(pages)
        )


    if suffix == ".docx":

        document = Document(
            BytesIO(data)
        )

        return _clean_text(
            "\n".join(
                p.text
                for p in document.paragraphs
            )
        )


    if suffix in {
        ".txt",
        ".text"
    }:

        return _clean_text(
            data.decode(
                "utf-8",
                errors="ignore"
            )
        )


    raise ValueError(
        "Unsupported CV type. Please upload PDF, DOCX, or TXT."
    )



# --------------------------------------------------
# Detect CV sections
# --------------------------------------------------

def detect_sections(text: str) -> Dict[str, bool]:

    lowered = text.lower()

    return {

        section:
        any(
            re.search(
                pattern,
                lowered,
                flags=re.IGNORECASE
            )
            for pattern in patterns
        )

        for section, patterns in SECTION_PATTERNS.items()
    }



# --------------------------------------------------
# Extract and validate professional links
# --------------------------------------------------

def find_links(text: str) -> Dict[str, List[str]]:


    urls = re.findall(
        r"https?://[^\s<>()]+",
        text or "",
        flags=re.IGNORECASE
    )


    linkedin_links = []
    github_links = []
    portfolio_links = []


    for url in urls:

        clean_url = url.rstrip(
            ".,;)"
        )


        if "linkedin.com" in clean_url.lower():

            if validate_profile_url(
                clean_url,
                "linkedin"
            ):
                linkedin_links.append(clean_url)


        elif "github.com" in clean_url.lower():

            if validate_profile_url(
                clean_url,
                "github"
            ):
                github_links.append(clean_url)


        else:

            portfolio_links.append(
                clean_url
            )



    return {

        # only one real profile shown
        "linkedin": list(
            dict.fromkeys(
                linkedin_links
            )
        )[:1],


        "github": list(
            dict.fromkeys(
                github_links
            )
        )[:1],


        "portfolio_or_other": list(
            dict.fromkeys(
                portfolio_links
            )
        )[:3],
    }



# --------------------------------------------------
# Experience evidence
# --------------------------------------------------

def estimate_experience_evidence(text: str) -> Dict[str, object]:

    lowered = (
        text or ""
    ).lower()


    cues = [

        "intern",
        "internship",
        "trainee",
        "engineer",
        "developer",
        "analyst",
        "assistant",
        "executive",
        "employment",
        "work experience",

    ]


    matched = sorted(
        {
            cue
            for cue in cues
            if cue in lowered
        }
    )


    return {

        "has_experience_evidence":
            bool(matched),

        "detected_cues":
            matched,

    }



# --------------------------------------------------
# Final CV evidence builder
# --------------------------------------------------

def build_cv_evidence(text: str) -> Dict[str, object]:


    sections = detect_sections(text)

    links = find_links(text)

    skills = extract_skills(text)

    experience = estimate_experience_evidence(text)



    missing_core_sections = [

        name

        for name in [
            "profile",
            "skills",
            "experience",
            "projects",
            "education"
        ]

        if not sections.get(
            name,
            False
        )

    ]


    return {


        "skills":
            skills,


        "sections":
            sections,


        "missing_core_sections":
            missing_core_sections,


        "links":
            links,


        "experience_evidence":
            experience,


        "text_length":
            len(text),

    }