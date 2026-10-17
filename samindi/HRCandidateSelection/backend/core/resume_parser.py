"""
Resume Processing and Claim Extraction Pipeline
Extracts candidate metadata, contact handles (GitHub, Email), section boundaries,
standardized technical skills, temporal claims, and project descriptions from resumes.
"""

import io
import re
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

try:
    from ml.esco_ontology import get_esco_ontology, ESCOOntology
except ImportError:
    from core.esco_ontology import get_esco_ontology, ESCOOntology



class ResumeDocumentParser:
    """Extracts raw text from multiple document formats (PDF, DOCX, TXT, HTML)."""

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        ext = filename.lower().split(".")[-1]
        
        if ext == "pdf":
            if PdfReader is None:
                return file_bytes.decode("utf-8", errors="ignore")
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_text = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages_text)
        
        elif ext in ["docx", "doc"]:
            if docx is None:
                return file_bytes.decode("utf-8", errors="ignore")
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([p.text for p in doc.paragraphs])
        
        elif ext in ["html", "htm"]:
            soup = BeautifulSoup(file_bytes.decode("utf-8", errors="ignore"), "html.parser")
            return soup.get_text(separator="\n")
        
        else:
            # Plain text / fallback
            return file_bytes.decode("utf-8", errors="ignore")


class ResumeClaimExtractor:
    """
    Extracts structured technical claims, skills, temporal assertions,
    and project descriptions from resume text.
    """

    # Section header indicators
    SECTION_PATTERNS = {
        "summary": re.compile(r"^(?:professional\s+)?summary|profile|about\s+me|objective", re.IGNORECASE | re.MULTILINE),
        "skills": re.compile(r"^(?:technical\s+|core\s+)?skills|technologies|proficiencies|competencies|tech\s+stack", re.IGNORECASE | re.MULTILINE),
        "experience": re.compile(r"^(?:work\s+|professional\s+)?experience|employment\s+history|career\s+history", re.IGNORECASE | re.MULTILINE),
        "projects": re.compile(r"^(?:personal\s+|key\s+|academic\s+)?projects|technical\s+projects|portfolio", re.IGNORECASE | re.MULTILINE),
        "education": re.compile(r"^education|academic\s+background|qualifications", re.IGNORECASE | re.MULTILINE),
        "certifications": re.compile(r"^certifications|licenses|courses", re.IGNORECASE | re.MULTILINE)
    }

    # Temporal patterns: e.g. "4 years of experience", "3+ years developing in React"
    YEAR_PATTERN = re.compile(
        r"(?:(?:over|more than|approximately|about|\+)?\s*(\d+(?:\.\d+)?)\s*\+?\s*years?(?:\s+of\s+experience)?(?:\s+(?:in|with|developing|using|building)\s+([A-Za-z0-9\s,\.\/+#-]+))?)",
        re.IGNORECASE
    )

    # Date range patterns: e.g. "Jan 2020 - Present", "2018 to 2022"
    DATE_RANGE_PATTERN = re.compile(
        r"(?:(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+)?(\d{4})\s*(?:to|-|–|—)\s*(?:(Present|Current|Now)|(?:(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+)?(\d{4}))",
        re.IGNORECASE
    )

    def __init__(self, esco: Optional[ESCOOntology] = None):
        self.esco = esco or get_esco_ontology()

    def clean_text(self, text: str) -> str:
        """Removes HTML tags and normalizes excessive whitespace."""
        cleaned = re.sub(r"<[^>]+>", " ", text)
        cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        return cleaned.strip()

    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extracts candidate emails, GitHub usernames, and links."""
        email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        email = email_match.group(0) if email_match else None

        # GitHub patterns: github.com/username or @username or github: username
        github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)", text, re.IGNORECASE)
        if not github_match:
            github_match = re.search(r"(?:github(?:\.com)?|git)\s*[:\-\s]\s*@?([A-Za-z0-9_-]{2,38})", text, re.IGNORECASE)
        github_handle = github_match.group(1) if github_match else None

        # LinkedIn patterns: linkedin.com/in/username
        linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_%\-]+)", text, re.IGNORECASE)
        linkedin_url = f"https://www.linkedin.com/in/{linkedin_match.group(1)}" if linkedin_match else None

        # Phone pattern
        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        phone = phone_match.group(0) if phone_match else None

        return {
            "email": email,
            "github": github_handle,
            "linkedin": linkedin_url,
            "phone": phone
        }

    def segment_sections(self, text: str) -> Dict[str, str]:
        """Segments raw resume text into semantic sections."""
        lines = text.split("\n")
        sections = {"summary": "", "skills": "", "experience": "", "projects": "", "education": "", "certifications": "", "other": ""}
        current_sec = "summary"
        
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue
            
            matched_sec = None
            for sec_name, pat in self.SECTION_PATTERNS.items():
                if pat.match(trimmed) and len(trimmed) < 40:
                    matched_sec = sec_name
                    break
            
            if matched_sec:
                current_sec = matched_sec
            else:
                sections[current_sec] += trimmed + "\n"

        return {k: v.strip() for k, v in sections.items() if v.strip()}

    def extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts technical skills with canonical ESCO mapping, mention counts,
        and localized context.
        """
        found_skills = {}
        # 1. Search known canonical map and aliases
        for term, canonical in self.esco.TECH_CANONICAL_MAP.items():
            pattern = r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])"
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                contexts = []
                for m in matches[:3]:
                    start = max(0, m.start() - 50)
                    end = min(len(text), m.end() + 50)
                    ctx = text[start:end].replace("\n", " ").strip()
                    contexts.append(ctx)

                found_skills[canonical] = {
                    "name": canonical,
                    "canonical": canonical,
                    "count": len(matches),
                    "contexts": contexts
                }

        # 2. Check for explicit duration annotations like "React (4 years)" or "Python - 3 yrs"
        duration_pattern = re.compile(
            r"([A-Za-z0-9\.\+#]+)\s*(?:\((?:over\s+)?(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\)|-\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?))",
            re.IGNORECASE
        )
        for m in duration_pattern.finditer(text):
            raw_skill = m.group(1).strip()
            years = float(m.group(2) or m.group(3))
            canonical = self.esco.resolve_canonical_skill_name(raw_skill)
            if canonical in found_skills:
                found_skills[canonical]["claimedYears"] = years
            elif len(raw_skill) > 1 and self.esco.lookup_skill(raw_skill):
                found_skills[canonical] = {
                    "name": canonical,
                    "canonical": canonical,
                    "count": 1,
                    "claimedYears": years,
                    "contexts": [m.group(0)]
                }

        return list(found_skills.values())

    def extract_temporal_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extracts explicit experience timeline statements from resume sentences."""
        claims = []
        sentences = re.split(r"(?<=[.!?\n])\s+", text)
        
        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean or len(sent_clean) < 15:
                continue

            # Check year duration matches
            m_year = self.YEAR_PATTERN.search(sent_clean)
            if m_year:
                years = float(m_year.group(1))
                # Detect associated skills in the sentence
                associated_skills = []
                for term, canonical in self.esco.TECH_CANONICAL_MAP.items():
                    if re.search(r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])", sent_clean, re.IGNORECASE):
                        if canonical not in associated_skills:
                            associated_skills.append(canonical)

                claims.append({
                    "claimType": "TEMPORAL_DURATION",
                    "statement": sent_clean,
                    "claimedYears": years,
                    "associatedSkills": associated_skills,
                    "isVerifiable": len(associated_skills) > 0
                })

            # Check date range matches
            m_range = self.DATE_RANGE_PATTERN.search(sent_clean)
            if m_range and not m_year:
                start_year = int(m_range.group(2))
                end_str = m_range.group(3) or m_range.group(5)
                end_year = 2026 if (end_str and end_str.lower() in ["present", "current", "now"]) else (int(end_str) if end_str else None)
                
                span_years = (end_year - start_year) if end_year else None

                associated_skills = []
                for term, canonical in self.esco.TECH_CANONICAL_MAP.items():
                    if re.search(r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])", sent_clean, re.IGNORECASE):
                        if canonical not in associated_skills:
                            associated_skills.append(canonical)

                if associated_skills and span_years and span_years > 0:
                    claims.append({
                        "claimType": "TEMPORAL_RANGE",
                        "statement": sent_clean,
                        "startYear": start_year,
                        "endYear": end_year,
                        "claimedYears": span_years,
                        "associatedSkills": associated_skills,
                        "isVerifiable": True
                    })

        return claims

    def extract_project_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extracts claimed software projects and related tech stacks."""
        projects = []
        sections = self.segment_sections(text)
        project_text = sections.get("projects", "") or sections.get("experience", "")
        
        paragraphs = [p.strip() for p in project_text.split("\n\n") if len(p.strip()) > 30]
        if not paragraphs:
            paragraphs = [line.strip() for line in project_text.split("\n") if len(line.strip()) > 40]

        for p in paragraphs:
            # Check if paragraph discusses developing/building software
            if re.search(r"\b(developed|built|architected|designed|implemented|created|engineered|launched)\b", p, re.IGNORECASE):
                associated_skills = []
                for term, canonical in self.esco.TECH_CANONICAL_MAP.items():
                    if re.search(r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])", p, re.IGNORECASE):
                        if canonical not in associated_skills:
                            associated_skills.append(canonical)

                # Extract potential project name (first 6 words or leading phrase)
                first_line = p.split("\n")[0]
                name_candidate = first_line[:60].strip()

                projects.append({
                    "claimType": "PROJECT_CONTRIBUTION",
                    "projectName": name_candidate,
                    "description": p,
                    "technologies": associated_skills,
                    "isVerifiable": len(associated_skills) > 0
                })

        return projects

    def parse(self, raw_content: str, filename: str = "resume.txt") -> Dict[str, Any]:
        """Full pipeline parsing a resume into structured claims and entities."""
        cleaned = self.clean_text(raw_content)
        contact = self.extract_contact_info(cleaned)
        sections = self.segment_sections(cleaned)
        skills = self.extract_skills(cleaned)
        temporal_claims = self.extract_temporal_claims(cleaned)
        project_claims = self.extract_project_claims(cleaned)

        return {
            "filename": filename,
            "contact": contact,
            "sections": sections,
            "skills": skills,
            "skillsCount": len(skills),
            "temporalClaims": temporal_claims,
            "projectClaims": project_claims,
            "rawTextLength": len(cleaned)
        }
