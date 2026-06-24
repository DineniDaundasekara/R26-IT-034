"""
ESCO Skill and Role Ontology Module
Provides standardized occupational profiling, skill synonym resolution,
and hierarchical skill-to-role mappings based on the European Commission's ESCO v1.1 taxonomy,
augmented with IT domain framework and dependency catalogs.
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from collections import defaultdict


class ESCOOntology:
    """
    Manages the ESCO knowledge graph for IT occupations, essential/optional skills,
    augmented with tech stack synonyms, aliases, and configurable role profiles.
    """

    # Comprehensive canonical tech dictionary mapping aliases to canonical names
    TECH_CANONICAL_MAP = {
        "react": "React",
        "react.js": "React",
        "reactjs": "React",
        "react native": "React Native",
        "node": "Node.js",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "express": "Express.js",
        "express.js": "Express.js",
        "expressjs": "Express.js",
        "mongodb": "MongoDB",
        "mongo": "MongoDB",
        "mongoose": "MongoDB",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "ecmascript": "JavaScript",
        "es6": "JavaScript",
        "typescript": "TypeScript",
        "ts": "TypeScript",
        "python": "Python",
        "python3": "Python",
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "rest api": "REST API",
        "restful api": "REST API",
        "rest": "REST API",
        "restful": "REST API",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "psql": "PostgreSQL",
        "mysql": "MySQL",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "aws": "AWS",
        "amazon web services": "AWS",
        "gcp": "GCP",
        "google cloud platform": "GCP",
        "azure": "Azure",
        "microsoft azure": "Azure",
        "git": "Git",
        "github": "Git",
        "gitlab": "Git",
        "ci/cd": "CI/CD",
        "continuous integration": "CI/CD",
        "linux": "Linux",
        "unix": "Linux",
        "redis": "Redis",
        "graphql": "GraphQL",
        "html": "HTML5",
        "html5": "HTML5",
        "css": "CSS3",
        "css3": "CSS3",
        "tailwind": "Tailwind CSS",
        "tailwindcss": "Tailwind CSS",
        "next.js": "Next.js",
        "nextjs": "Next.js",
        "vue": "Vue.js",
        "vue.js": "Vue.js",
        "vuejs": "Vue.js",
        "angular": "Angular",
        "angularjs": "Angular",
        "machine learning": "Machine Learning",
        "ml": "Machine Learning",
        "deep learning": "Deep Learning",
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "scikit-learn": "scikit-learn",
        "sklearn": "scikit-learn",
        "sql": "SQL",
        "nosql": "NoSQL"
    }

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Dynamically locate data/raw/04_esco or datasets/04_esco
            curr = os.path.abspath(__file__)
            resolved_dir = None
            while curr and curr != os.path.dirname(curr):
                candidate_paths = [
                    os.path.join(curr, "backend", "data", "raw", "04_esco"),
                    os.path.join(curr, "data", "raw", "04_esco"),
                    os.path.join(curr, "datasets", "04_esco"),
                ]
                for cp in candidate_paths:
                    if os.path.exists(cp) and os.path.exists(os.path.join(cp, "skills_en.csv")):
                        resolved_dir = cp
                        break
                if resolved_dir:
                    break
                curr = os.path.dirname(curr)

            if not resolved_dir:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                resolved_dir = os.path.join(base_dir, "data", "raw", "04_esco")

            data_dir = resolved_dir

        self.data_dir = data_dir

        self.occupations_df: Optional[pd.DataFrame] = None
        self.skills_df: Optional[pd.DataFrame] = None
        self.relations_df: Optional[pd.DataFrame] = None

        # Lookup indexes
        self.skills_by_uri: Dict[str, Dict[str, Any]] = {}
        self.skills_by_label: Dict[str, str] = {}  # lower(preferred_label) -> uri
        self.alias_to_uri: Dict[str, str] = {}     # lower(alias) -> uri
        self.occupations_by_uri: Dict[str, Dict[str, Any]] = {}
        self.occupations_by_label: Dict[str, str] = {}

        # Relations
        self.occ_essential_skills: Dict[str, List[str]] = defaultdict(list)
        self.occ_optional_skills: Dict[str, List[str]] = defaultdict(list)

        self._load_and_index()

    def _load_and_index(self):
        """Loads ESCO CSVs and builds in-memory indexes."""
        occ_path = os.path.join(self.data_dir, "occupations_en.csv")
        sk_path = os.path.join(self.data_dir, "skills_en.csv")
        rel_path = os.path.join(self.data_dir, "occupationSkillRelations_en.csv")

        if not (os.path.exists(occ_path) and os.path.exists(sk_path) and os.path.exists(rel_path)):
            raise FileNotFoundError(f"ESCO datasets not found in {self.data_dir}")

        self.occupations_df = pd.read_csv(occ_path)
        self.skills_df = pd.read_csv(sk_path)
        self.relations_df = pd.read_csv(rel_path)

        # 1. Index ESCO Skills
        for _, row in self.skills_df.iterrows():
            uri = str(row["conceptUri"])
            pref_label = str(row["preferredLabel"]).strip()
            skill_type = str(row.get("skillType", ""))
            reuse_level = str(row.get("reuseLevel", ""))
            
            alt_labels_raw = str(row.get("altLabels", ""))
            alt_labels = [s.strip() for s in alt_labels_raw.split("\n") if s.strip() and s.strip() != "nan"] if pd.notna(row.get("altLabels")) else []

            self.skills_by_uri[uri] = {
                "uri": uri,
                "preferredLabel": pref_label,
                "skillType": skill_type,
                "reuseLevel": reuse_level,
                "altLabels": alt_labels,
                "description": str(row.get("description", "")) if pd.notna(row.get("description")) else ""
            }

            self.skills_by_label[pref_label.lower()] = uri
            self.alias_to_uri[pref_label.lower()] = uri
            for alt in alt_labels:
                self.alias_to_uri[alt.lower()] = uri

        # 2. Index ESCO Occupations
        for _, row in self.occupations_df.iterrows():
            uri = str(row["conceptUri"])
            pref_label = str(row["preferredLabel"]).strip()
            isco = str(row.get("iscoGroup", ""))
            
            alt_labels_raw = str(row.get("altLabels", ""))
            alt_labels = [s.strip() for s in alt_labels_raw.split("\n") if s.strip() and s.strip() != "nan"] if pd.notna(row.get("altLabels")) else []

            self.occupations_by_uri[uri] = {
                "uri": uri,
                "preferredLabel": pref_label,
                "iscoGroup": isco,
                "altLabels": alt_labels,
                "description": str(row.get("description", "")) if pd.notna(row.get("description")) else ""
            }

            self.occupations_by_label[pref_label.lower()] = uri
            for alt in alt_labels:
                self.occupations_by_label[alt.lower()] = uri

        # 3. Index Relations
        for _, row in self.relations_df.iterrows():
            occ_uri = str(row["occupationUri"])
            sk_uri = str(row["skillUri"])
            rel_type = str(row.get("relationType", "essential")).lower()

            if sk_uri in self.skills_by_uri:
                sk_name = self.skills_by_uri[sk_uri]["preferredLabel"]
                if rel_type == "essential":
                    self.occ_essential_skills[occ_uri].append(sk_name)
                else:
                    self.occ_optional_skills[occ_uri].append(sk_name)

    def lookup_skill(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Resolves a skill term or alias to its standardized canonical skill entity.
        First checks domain tech dictionary, then ESCO knowledge graph.
        """
        cleaned = query.strip().lower()
        
        # Check canonical tech map first
        if cleaned in self.TECH_CANONICAL_MAP:
            canonical_name = self.TECH_CANONICAL_MAP[cleaned]
            # Check if canonical name is in ESCO
            if canonical_name.lower() in self.alias_to_uri:
                uri = self.alias_to_uri[canonical_name.lower()]
                return self.skills_by_uri[uri]
            return {
                "uri": f"custom:tech:{cleaned}",
                "preferredLabel": canonical_name,
                "skillType": "knowledge",
                "reuseLevel": "sector-specific",
                "altLabels": [cleaned],
                "description": f"Domain software engineering competency: {canonical_name}"
            }

        if cleaned in self.alias_to_uri:
            uri = self.alias_to_uri[cleaned]
            return self.skills_by_uri[uri]
        
        # Substring / fuzzy heuristic fallback
        for alias, uri in self.alias_to_uri.items():
            if cleaned == alias or f"{cleaned} (" in alias or alias == f"{cleaned} (computer programming)":
                return self.skills_by_uri[uri]

        return None

    def resolve_canonical_skill_name(self, query: str) -> str:
        """
        Returns the standardized canonical name for any recognized skill/synonym.
        """
        cleaned = query.strip().lower()
        if cleaned in self.TECH_CANONICAL_MAP:
            return self.TECH_CANONICAL_MAP[cleaned]
        
        skill_meta = self.lookup_skill(query)
        if skill_meta:
            pref = skill_meta["preferredLabel"]
            if "(computer programming)" in pref:
                return pref.replace("(computer programming)", "").strip()
            return pref
        return query.strip()

    def search_occupations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches occupations by keyword or role title, prioritizing exact and whole-word matches.
        """
        q = query.lower().strip()
        exact_results = []
        partial_results = []

        for uri, occ in self.occupations_by_uri.items():
            pref = occ["preferredLabel"].lower()
            alts = [a.lower() for a in occ["altLabels"]]
            
            # Prioritize ICT / technical ISCO groups (25xx for ICT professionals)
            is_ict = str(occ["iscoGroup"]).startswith("25") or str(occ["iscoGroup"]).startswith("21")
            
            item = {
                "uri": uri,
                "preferredLabel": occ["preferredLabel"],
                "iscoGroup": occ["iscoGroup"],
                "essentialSkillsCount": len(self.occ_essential_skills[uri]),
                "optionalSkillsCount": len(self.occ_optional_skills[uri]),
                "description": occ["description"][:200] + "..." if len(occ["description"]) > 200 else occ["description"]
            }

            if q == pref:
                exact_results.insert(0, item)
            elif re.search(r'\b' + re.escape(q) + r'\b', pref):
                if is_ict:
                    exact_results.append(item)
                else:
                    partial_results.append(item)
            elif any(q in a for a in alts):
                partial_results.append(item)

        combined = exact_results + partial_results
        return combined[:limit]

    def get_role_profile_by_uri(self, occ_uri: str) -> Dict[str, Any]:
        """
        Returns structured requirement profile for a given ESCO occupation URI.
        """
        occ = self.occupations_by_uri.get(occ_uri)
        if not occ:
            return {}
        
        return {
            "uri": occ_uri,
            "roleName": occ["preferredLabel"],
            "iscoGroup": occ["iscoGroup"],
            "essentialSkills": sorted(list(set(self.occ_essential_skills[occ_uri]))),
            "optionalSkills": sorted(list(set(self.occ_optional_skills[occ_uri])))
        }

    def get_default_role_config(self, role_key: str) -> Dict[str, Any]:
        """
        Provides standardized, configurable Job Role Profiles grounded in ESCO and industry standards.
        """
        key = role_key.lower().replace("_", " ").strip()
        
        defaults = {
            "full stack mern developer": {
                "roleId": "full_stack_mern",
                "roleName": "Full Stack MERN Developer",
                "category": "Software Engineering",
                "escoReferenceUri": "http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-a7b2-be9f30c6e0ff",
                "requiredSkills": [
                    {"name": "React", "canonical": "React", "category": "Frontend", "importance": 1.0, "aliases": ["React.js", "ReactJS", "React native"]},
                    {"name": "Node.js", "canonical": "Node.js", "category": "Backend", "importance": 1.0, "aliases": ["NodeJS", "Node"]},
                    {"name": "Express.js", "canonical": "Express.js", "category": "Backend", "importance": 0.9, "aliases": ["Express", "ExpressJS"]},
                    {"name": "MongoDB", "canonical": "MongoDB", "category": "Database", "importance": 0.9, "aliases": ["Mongo", "Mongoose"]},
                    {"name": "JavaScript", "canonical": "JavaScript", "category": "Language", "importance": 1.0, "aliases": ["JS", "ECMAScript", "ES6"]}
                ],
                "preferredSkills": [
                    {"name": "TypeScript", "canonical": "TypeScript", "category": "Language", "importance": 0.8, "aliases": ["TS"]},
                    {"name": "REST API", "canonical": "REST API", "category": "Architecture", "importance": 0.8, "aliases": ["REST", "RESTful web services", "RESTful API"]},
                    {"name": "Docker", "canonical": "Docker", "category": "DevOps", "importance": 0.7, "aliases": ["Docker container"]},
                    {"name": "Git", "canonical": "Git", "category": "Tools", "importance": 0.7, "aliases": ["GitHub", "Git version control"]},
                    {"name": "AWS", "canonical": "AWS", "category": "Cloud", "importance": 0.6, "aliases": ["Amazon Web Services", "Amazon EC2", "AWS S3"]}
                ]
            },
            "backend python engineer": {
                "roleId": "backend_python",
                "roleName": "Backend Python Engineer",
                "category": "Software Engineering",
                "escoReferenceUri": "http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-a7b2-be9f30c6e0ff",
                "requiredSkills": [
                    {"name": "Python", "canonical": "Python", "category": "Language", "importance": 1.0, "aliases": ["Python", "Python 3"]},
                    {"name": "FastAPI", "canonical": "FastAPI", "category": "Backend", "importance": 0.9, "aliases": ["FastAPI framework", "Flask", "Django"]},
                    {"name": "REST API", "canonical": "REST API", "category": "Architecture", "importance": 0.9, "aliases": ["RESTful", "REST API design"]},
                    {"name": "PostgreSQL", "canonical": "PostgreSQL", "category": "Database", "importance": 0.9, "aliases": ["Postgres", "SQL", "Relational Database"]}
                ],
                "preferredSkills": [
                    {"name": "Docker", "canonical": "Docker", "category": "DevOps", "importance": 0.8, "aliases": ["Docker containerization"]},
                    {"name": "Redis", "canonical": "Redis", "category": "Database/Cache", "importance": 0.7, "aliases": ["Redis cache"]},
                    {"name": "AWS", "canonical": "AWS", "category": "Cloud", "importance": 0.7, "aliases": ["AWS Cloud", "Amazon Web Services"]},
                    {"name": "Linux", "canonical": "Linux", "category": "OS", "importance": 0.7, "aliases": ["Unix", "Ubuntu", "Debian"]}
                ]
            },
            "frontend react developer": {
                "roleId": "frontend_react",
                "roleName": "Frontend React Developer",
                "category": "Frontend Engineering",
                "escoReferenceUri": "http://data.europa.eu/esco/occupation/c40a2919-48a9-4d1a-8e6d-47fb1f1f1d1e",
                "requiredSkills": [
                    {"name": "React", "canonical": "React", "category": "Frontend", "importance": 1.0, "aliases": ["React.js", "ReactJS"]},
                    {"name": "JavaScript", "canonical": "JavaScript", "category": "Language", "importance": 1.0, "aliases": ["JS", "ES6+"]},
                    {"name": "HTML5", "canonical": "HTML5", "category": "Frontend", "importance": 0.9, "aliases": ["HTML", "Semantic HTML"]},
                    {"name": "CSS3", "canonical": "CSS3", "category": "Frontend", "importance": 0.9, "aliases": ["CSS", "SCSS", "SASS", "Tailwind CSS"]}
                ],
                "preferredSkills": [
                    {"name": "TypeScript", "canonical": "TypeScript", "category": "Language", "importance": 0.85, "aliases": ["TS"]},
                    {"name": "Next.js", "canonical": "Next.js", "category": "Frontend", "importance": 0.8, "aliases": ["NextJS"]},
                    {"name": "Git", "canonical": "Git", "category": "Tools", "importance": 0.7, "aliases": ["Git workflow"]}
                ]
            },
            "devops engineer": {
                "roleId": "devops_engineer",
                "roleName": "DevOps Engineer",
                "category": "Infrastructure & Operations",
                "escoReferenceUri": "http://data.europa.eu/esco/occupation/cc867bee-6234-4b5b-b9f1-3ecfcf8d0c24",
                "requiredSkills": [
                    {"name": "Docker", "canonical": "Docker", "category": "Containerization", "importance": 1.0, "aliases": ["Docker container"]},
                    {"name": "Kubernetes", "canonical": "Kubernetes", "category": "Orchestration", "importance": 1.0, "aliases": ["K8s"]},
                    {"name": "CI/CD", "canonical": "CI/CD", "category": "DevOps", "importance": 0.95, "aliases": ["GitHub Actions", "Jenkins", "GitLab CI"]},
                    {"name": "Linux", "canonical": "Linux", "category": "OS", "importance": 0.9, "aliases": ["Linux Administration", "Bash"]}
                ],
                "preferredSkills": [
                    {"name": "AWS", "canonical": "AWS", "category": "Cloud", "importance": 0.85, "aliases": ["AWS", "GCP", "Azure"]},
                    {"name": "Git", "canonical": "Git", "category": "Tools", "importance": 0.8, "aliases": ["Git repository"]}
                ]
            },
            "data scientist": {
                "roleId": "data_scientist",
                "roleName": "Data Scientist",
                "category": "Data & AI",
                "escoReferenceUri": "http://data.europa.eu/esco/occupation/258e46f9-7e44-4861-bc9a-b44c01d4a04d",
                "requiredSkills": [
                    {"name": "Python", "canonical": "Python", "category": "Language", "importance": 1.0, "aliases": ["Python"]},
                    {"name": "Machine Learning", "canonical": "Machine Learning", "category": "Data Science", "importance": 1.0, "aliases": ["ML", "scikit-learn"]},
                    {"name": "SQL", "canonical": "SQL", "category": "Database", "importance": 0.9, "aliases": ["PostgreSQL", "MySQL"]},
                    {"name": "Pandas", "canonical": "Pandas", "category": "Data Processing", "importance": 0.9, "aliases": ["Pandas", "NumPy"]}
                ],
                "preferredSkills": [
                    {"name": "PyTorch", "canonical": "PyTorch", "category": "Deep Learning", "importance": 0.85, "aliases": ["TensorFlow", "Deep Learning"]},
                    {"name": "Git", "canonical": "Git", "category": "Tools", "importance": 0.75, "aliases": ["Version Control"]}
                ]
            }
        }

        for match_key, conf in defaults.items():
            if match_key in key or key in match_key:
                return conf

        return defaults["full stack mern developer"]


# Global cached instance
_ontology_instance: Optional[ESCOOntology] = None


def get_esco_ontology() -> ESCOOntology:
    """Returns a singleton cached instance of ESCOOntology."""
    global _ontology_instance
    if _ontology_instance is None:
        _ontology_instance = ESCOOntology()
    return _ontology_instance
