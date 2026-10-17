\
import re
from typing import Dict, Iterable, List, Set

# Canonical skill -> aliases that may appear in CVs / vacancies.
# Add new domain skills here as your research expands.
SKILL_ALIASES: Dict[str, List[str]] = {
    "Python": ["python"],
    "Java": ["java"],
    "C#": ["c#", "c sharp"],
    "C++": ["c++"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript"],
    "PHP": ["php"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],

    "React": ["react", "react.js", "reactjs"],
    "Angular": ["angular"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Node.js": ["node", "node.js", "nodejs"],
    "Express.js": ["express", "express.js", "expressjs"],
    "Spring Boot": ["spring boot", "springboot"],
    ".NET": [".net", "dotnet", "asp.net", "asp.net core"],
    "Laravel": ["laravel"],
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],

    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "Tailwind CSS": ["tailwind", "tailwind css"],
    "Bootstrap": ["bootstrap"],

    "REST API": ["rest api", "restful api", "restful services", "rest"],
    "GraphQL": ["graphql"],
    "Microservices": ["microservices", "microservice architecture"],

    "MySQL": ["mysql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MongoDB": ["mongodb", "mongo db"],
    "SQL Server": ["sql server", "mssql"],
    "Oracle": ["oracle database", "oracle db"],
    "Redis": ["redis"],
    "SQL": ["sql"],

    "Git": ["git"],
    "GitHub": ["github"],
    "GitLab": ["gitlab"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Jenkins": ["jenkins"],
    "CI/CD": ["ci/cd", "continuous integration", "continuous delivery", "continuous deployment"],
    "Linux": ["linux"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure", "microsoft azure"],
    "Google Cloud": ["google cloud", "gcp"],
    "Terraform": ["terraform"],
    "Ansible": ["ansible"],

    "Postman": ["postman"],
    "Selenium": ["selenium"],
    "Cypress": ["cypress"],
    "JUnit": ["junit"],
    "PyTest": ["pytest"],
    "Unit Testing": ["unit testing", "unit tests"],
    "Integration Testing": ["integration testing", "integration tests"],

    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Excel": ["microsoft excel", "excel"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Data Visualization": ["data visualization", "data visualisation"],
    "NLP": ["natural language processing", "nlp"],

    "Figma": ["figma"],
    "UI/UX": ["ui/ux", "ux design", "ui design"],
    "Agile": ["agile"],
    "Scrum": ["scrum"],
    "Jira": ["jira"],

    "Communication": ["communication skills", "communication"],
    "Teamwork": ["teamwork", "team work", "team player"],
    "Problem Solving": ["problem solving", "problem-solving"],
    "Leadership": ["leadership"],
    "Time Management": ["time management"],
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _contains_alias(text: str, alias: str) -> bool:
    """Boundary-aware matching that still supports aliases containing punctuation."""
    text = _normalize(text)
    alias = _normalize(alias)
    if not alias:
        return False

    # For simple alphanumeric aliases use word boundaries.
    if re.fullmatch(r"[a-z0-9 ]+", alias):
        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None

    return alias in text


def extract_skills(text: str) -> List[str]:
    found: Set[str] = set()

    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            if _contains_alias(text, alias):
                found.add(canonical)
                break

    return sorted(found, key=str.lower)


def canonicalize_skill_names(skills: Iterable[str]) -> List[str]:
    """Convert a list of user/gold-label skills to catalog canonical names where possible."""
    canonicalized: Set[str] = set()

    for raw in skills:
        raw = (raw or "").strip()
        if not raw:
            continue

        matched = False
        for canonical, aliases in SKILL_ALIASES.items():
            candidates = [canonical] + aliases
            if any(_normalize(raw) == _normalize(c) for c in candidates):
                canonicalized.add(canonical)
                matched = True
                break

        if not matched:
            canonicalized.add(raw)

    return sorted(canonicalized, key=str.lower)
