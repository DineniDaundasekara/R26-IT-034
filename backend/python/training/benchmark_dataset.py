"""
Domain-Specific Cross-Source Candidate Verification Benchmark
Constructs a standardized, balanced test suite across 4 major technical roles and 4 archetypes:
- SUPPORTED
- PARTIALLY_SUPPORTED
- INSUFFICIENT_EVIDENCE
- POTENTIAL_CONTRADICTION
"""

import json
import random
from typing import List, Dict, Any


def generate_benchmark_dataset(num_samples: int = 300, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates a balanced benchmark suite of candidate evaluations with full cross-source ground truth.
    """
    random.seed(seed)
    benchmark = []

    roles = [
        "Full Stack MERN Developer",
        "Backend Python Engineer",
        "Frontend React Developer",
        "DevOps Engineer"
    ]

    archetypes = [
        "strong_verifiable",       # Public GitHub strongly supports resume claims (>=70% tenure, matching repos/deps)
        "partial_tenure",          # Public GitHub shows recent activity but shorter tenure than claimed
        "enterprise_private_repo", # Genuine skills on resume, but no public GitHub repositories (INSUFFICIENT_EVIDENCE)
        "anachronistic_claim"      # Chronologically impossible claims (e.g. 16 yrs React in 2026 -> CONTRADICTION)
    ]

    for i in range(num_samples):
        role_idx = i % len(roles)
        arch_idx = (i // len(roles)) % len(archetypes)
        
        role = roles[role_idx]
        archetype = archetypes[arch_idx]
        candidate_id = f"cand_{i+1:03d}"

        if role == "Full Stack MERN Developer":
            skills_claimed = ["React", "Node.js", "Express.js", "MongoDB", "JavaScript"]
            
            if archetype == "strong_verifiable":
                resume_text = f"Alex Doe ({candidate_id})\nEmail: alex{i}@example.com\nGitHub: github.com/alex_{candidate_id}\n\nSummary:\nFull Stack MERN Developer with 3 years of experience in React and Node.js.\nSkills: React, Node.js, Express.js, MongoDB, JavaScript, Docker\nExperience:\nFull Stack Developer (2022-Present):\n- Built e-commerce platform using MERN stack."
                github_profile = {
                    "exists": True,
                    "username": f"alex_{candidate_id}",
                    "publicReposCount": 4,
                    "repositories": [
                        {
                            "name": "mern-ecommerce",
                            "description": "Full stack store with React, Express, and MongoDB",
                            "primaryLanguage": "JavaScript",
                            "languages": {"JavaScript": 60000},
                            "topics": ["react", "nodejs", "mongodb"],
                            "dependencies": ["react", "express", "mongoose", "node"],
                            "createdAt": "2022-02-01T10:00:00Z",
                            "pushedAt": "2025-11-15T10:00:00Z",
                            "stars": 8,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/alex_{candidate_id}/mern-ecommerce"
                        }
                    ]
                }
                ground_truth = {
                    "React": "SUPPORTED",
                    "Node.js": "SUPPORTED",
                    "Express.js": "SUPPORTED",
                    "MongoDB": "SUPPORTED",
                    "JavaScript": "SUPPORTED"
                }

            elif archetype == "partial_tenure":
                resume_text = f"Jordan Smith ({candidate_id})\nEmail: jordan{i}@example.com\nGitHub: github.com/jordan_{candidate_id}\n\nSummary:\nSenior MERN Developer with 5 years of experience in React.\nSkills: React, Node.js, Express.js, MongoDB, JavaScript\nExperience:\nDeveloper (2020-Present):\n- Web applications in React."
                github_profile = {
                    "exists": True,
                    "username": f"jordan_{candidate_id}",
                    "publicReposCount": 2,
                    "repositories": [
                        {
                            "name": "react-notes-app",
                            "description": "Small React app",
                            "primaryLanguage": "JavaScript",
                            "languages": {"JavaScript": 15000},
                            "topics": ["react"],
                            "dependencies": ["react"],
                            "createdAt": "2024-06-01T10:00:00Z",
                            "pushedAt": "2025-08-10T10:00:00Z",
                            "stars": 1,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/jordan_{candidate_id}/react-notes-app"
                        }
                    ]
                }
                ground_truth = {
                    "React": "PARTIALLY_SUPPORTED",
                    "Node.js": "INSUFFICIENT_EVIDENCE",
                    "Express.js": "INSUFFICIENT_EVIDENCE",
                    "MongoDB": "INSUFFICIENT_EVIDENCE",
                    "JavaScript": "PARTIALLY_SUPPORTED"
                }

            elif archetype == "enterprise_private_repo":
                resume_text = f"Sam Taylor ({candidate_id})\nEmail: sam{i}@example.com\n\nSummary:\nFull Stack Engineer with 4 years of experience building private banking portals in Node.js and React.\nSkills: React, Node.js, Express.js, MongoDB, JavaScript\nExperience:\nFinTech Corp (2021-Present):\n- Enterprise internal portals."
                github_profile = {"exists": False, "username": None, "repositories": []}
                ground_truth = {
                    "React": "INSUFFICIENT_EVIDENCE",
                    "Node.js": "INSUFFICIENT_EVIDENCE",
                    "Express.js": "INSUFFICIENT_EVIDENCE",
                    "MongoDB": "INSUFFICIENT_EVIDENCE",
                    "JavaScript": "INSUFFICIENT_EVIDENCE"
                }

            else:  # anachronistic_claim
                resume_text = f"Morgan Lee ({candidate_id})\nEmail: morgan{i}@example.com\nGitHub: github.com/morgan_{candidate_id}\n\nSummary:\nVeteran engineer with 16 years of experience in React.\nSkills: React, Node.js, Express.js, MongoDB, JavaScript\nExperience:\nTech Lead (2010-Present):\n- 16 years of React experience."
                github_profile = {
                    "exists": True,
                    "username": f"morgan_{candidate_id}",
                    "publicReposCount": 1,
                    "repositories": [
                        {
                            "name": "sample-repo",
                            "description": "Repo",
                            "primaryLanguage": "JavaScript",
                            "languages": {"JavaScript": 5000},
                            "dependencies": ["react"],
                            "createdAt": "2024-01-01T10:00:00Z",
                            "pushedAt": "2024-02-01T10:00:00Z",
                            "stars": 0,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/morgan_{candidate_id}/sample-repo"
                        }
                    ]
                }
                ground_truth = {
                    "React": "POTENTIAL_CONTRADICTION",
                    "Node.js": "INSUFFICIENT_EVIDENCE",
                    "Express.js": "INSUFFICIENT_EVIDENCE",
                    "MongoDB": "INSUFFICIENT_EVIDENCE",
                    "JavaScript": "PARTIALLY_SUPPORTED"
                }

        elif role == "Backend Python Engineer":
            skills_claimed = ["Python", "FastAPI", "REST API", "PostgreSQL"]
            
            if archetype == "strong_verifiable":
                resume_text = f"Chris Brown ({candidate_id})\nEmail: chris{i}@example.com\nGitHub: github.com/chris_{candidate_id}\n\nSummary:\nBackend Python Engineer with 3 years of experience.\nSkills: Python, FastAPI, REST API, PostgreSQL, Docker\nExperience:\nBackend Engineer (2022-Present):\n- High-throughput REST microservices in FastAPI and PostgreSQL."
                github_profile = {
                    "exists": True,
                    "username": f"chris_{candidate_id}",
                    "publicReposCount": 3,
                    "repositories": [
                        {
                            "name": "fastapi-service",
                            "description": "Async microservice with PostgreSQL and FastAPI",
                            "primaryLanguage": "Python",
                            "languages": {"Python": 45000},
                            "topics": ["fastapi", "python", "postgresql"],
                            "dependencies": ["fastapi", "asyncpg", "sqlalchemy"],
                            "createdAt": "2022-05-10T10:00:00Z",
                            "pushedAt": "2025-10-01T10:00:00Z",
                            "stars": 15,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/chris_{candidate_id}/fastapi-service"
                        }
                    ]
                }
                ground_truth = {
                    "Python": "SUPPORTED",
                    "FastAPI": "SUPPORTED",
                    "REST API": "SUPPORTED",
                    "PostgreSQL": "SUPPORTED"
                }

            elif archetype == "partial_tenure":
                resume_text = f"Dana White ({candidate_id})\nEmail: dana{i}@example.com\nGitHub: github.com/dana_{candidate_id}\n\nSummary:\nBackend Developer with 4 years of experience in Python.\nSkills: Python, FastAPI, REST API, PostgreSQL\nExperience:\nBackend Dev (2021-Present):\n- Python services."
                github_profile = {
                    "exists": True,
                    "username": f"dana_{candidate_id}",
                    "publicReposCount": 1,
                    "repositories": [
                        {
                            "name": "python-script",
                            "description": "Utility script",
                            "primaryLanguage": "Python",
                            "languages": {"Python": 8000},
                            "dependencies": [],
                            "createdAt": "2025-01-15T10:00:00Z",
                            "pushedAt": "2025-02-01T10:00:00Z",
                            "stars": 0,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/dana_{candidate_id}/python-script"
                        }
                    ]
                }
                ground_truth = {
                    "Python": "PARTIALLY_SUPPORTED",
                    "FastAPI": "INSUFFICIENT_EVIDENCE",
                    "REST API": "INSUFFICIENT_EVIDENCE",
                    "PostgreSQL": "INSUFFICIENT_EVIDENCE"
                }

            elif archetype == "enterprise_private_repo":
                resume_text = f"Robin Hood ({candidate_id})\nEmail: robin{i}@example.com\n\nSummary:\nPython backend engineer with 5 years enterprise database experience.\nSkills: Python, FastAPI, REST API, PostgreSQL\nExperience:\nEnterprise Systems (2020-Present):\n- Private internal systems."
                github_profile = {"exists": False, "username": None, "repositories": []}
                ground_truth = {
                    "Python": "INSUFFICIENT_EVIDENCE",
                    "FastAPI": "INSUFFICIENT_EVIDENCE",
                    "REST API": "INSUFFICIENT_EVIDENCE",
                    "PostgreSQL": "INSUFFICIENT_EVIDENCE"
                }

            else:  # anachronistic_claim
                resume_text = f"Terry Fox ({candidate_id})\nEmail: terry{i}@example.com\nGitHub: github.com/terry_{candidate_id}\n\nSummary:\n12 years of experience in FastAPI.\nSkills: Python, FastAPI, REST API, PostgreSQL\nExperience:\nLead Engineer (2014-Present):\n- 12 years of FastAPI microservices."
                github_profile = {
                    "exists": True,
                    "username": f"terry_{candidate_id}",
                    "publicReposCount": 1,
                    "repositories": [
                        {
                            "name": "fastapi-demo",
                            "description": "Demo",
                            "primaryLanguage": "Python",
                            "languages": {"Python": 12000},
                            "dependencies": ["fastapi"],
                            "createdAt": "2023-01-01T10:00:00Z",
                            "pushedAt": "2023-05-01T10:00:00Z",
                            "stars": 1,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/terry_{candidate_id}/fastapi-demo"
                        }
                    ]
                }
                ground_truth = {
                    "Python": "PARTIALLY_SUPPORTED",
                    "FastAPI": "POTENTIAL_CONTRADICTION",
                    "REST API": "INSUFFICIENT_EVIDENCE",
                    "PostgreSQL": "INSUFFICIENT_EVIDENCE"
                }

        elif role == "Frontend React Developer":
            skills_claimed = ["React", "JavaScript", "HTML5", "CSS3"]
            if archetype == "strong_verifiable":
                resume_text = f"Pat Casey ({candidate_id})\nEmail: pat{i}@example.com\nGitHub: github.com/pat_{candidate_id}\n\nSummary:\nFrontend Developer with 3 years of experience in React and JavaScript.\nSkills: React, JavaScript, HTML5, CSS3, TypeScript\nExperience:\nFrontend Engineer (2022-Present):\n- Built responsive UIs."
                github_profile = {
                    "exists": True,
                    "username": f"pat_{candidate_id}",
                    "publicReposCount": 2,
                    "repositories": [
                        {
                            "name": "react-component-lib",
                            "description": "React UI components with HTML5 and CSS3",
                            "primaryLanguage": "JavaScript",
                            "languages": {"JavaScript": 35000, "HTML": 10000, "CSS": 8000},
                            "topics": ["react", "javascript", "css3"],
                            "dependencies": ["react"],
                            "createdAt": "2022-03-01T10:00:00Z",
                            "pushedAt": "2025-09-01T10:00:00Z",
                            "stars": 6,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/pat_{candidate_id}/react-component-lib"
                        }
                    ]
                }
                ground_truth = {
                    "React": "SUPPORTED",
                    "JavaScript": "SUPPORTED",
                    "HTML5": "SUPPORTED",
                    "CSS3": "SUPPORTED"
                }
            elif archetype == "partial_tenure":
                resume_text = f"Kelly Ray ({candidate_id})\nEmail: kelly{i}@example.com\nGitHub: github.com/kelly_{candidate_id}\n\nSummary:\nFrontend specialist with 4 years of React.\nSkills: React, JavaScript, HTML5, CSS3\nExperience:\nDeveloper (2021-Present)."
                github_profile = {
                    "exists": True,
                    "username": f"kelly_{candidate_id}",
                    "publicReposCount": 1,
                    "repositories": [
                        {
                            "name": "portfolio-site",
                            "description": "Personal website in JavaScript and HTML5",
                            "primaryLanguage": "JavaScript",
                            "languages": {"JavaScript": 12000, "HTML": 4000},
                            "dependencies": [],
                            "createdAt": "2024-08-01T10:00:00Z",
                            "pushedAt": "2025-01-01T10:00:00Z",
                            "stars": 0,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/kelly_{candidate_id}/portfolio-site"
                        }
                    ]
                }
                ground_truth = {
                    "React": "INSUFFICIENT_EVIDENCE",
                    "JavaScript": "PARTIALLY_SUPPORTED",
                    "HTML5": "PARTIALLY_SUPPORTED",
                    "CSS3": "INSUFFICIENT_EVIDENCE"
                }
            elif archetype == "enterprise_private_repo":
                resume_text = f"Taylor Swiftly ({candidate_id})\nEmail: ts{i}@example.com\n\nSummary:\nFrontend engineer with 5 years enterprise UI experience.\nSkills: React, JavaScript, HTML5, CSS3\nExperience:\nEnterprise Apps (2020-Present)."
                github_profile = {"exists": False, "username": None, "repositories": []}
                ground_truth = {
                    "React": "INSUFFICIENT_EVIDENCE",
                    "JavaScript": "INSUFFICIENT_EVIDENCE",
                    "HTML5": "INSUFFICIENT_EVIDENCE",
                    "CSS3": "INSUFFICIENT_EVIDENCE"
                }
            else: # anachronistic
                resume_text = f"Avery Brooks ({candidate_id})\nEmail: ab{i}@example.com\nGitHub: github.com/ab_{candidate_id}\n\nSummary:\n16 years of experience in React web development.\nSkills: React, JavaScript, HTML5, CSS3\nExperience:\nLead Engineer (2010-Present)."
                github_profile = {
                    "exists": True,
                    "username": f"ab_{candidate_id}",
                    "publicReposCount": 1,
                    "repositories": [
                        {
                            "name": "react-demo",
                            "description": "Demo",
                            "primaryLanguage": "JavaScript",
                            "languages": {"JavaScript": 5000},
                            "dependencies": ["react"],
                            "createdAt": "2024-01-01T10:00:00Z",
                            "pushedAt": "2024-02-01T10:00:00Z",
                            "stars": 0,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/ab_{candidate_id}/react-demo"
                        }
                    ]
                }
                ground_truth = {
                    "React": "POTENTIAL_CONTRADICTION",
                    "JavaScript": "PARTIALLY_SUPPORTED",
                    "HTML5": "INSUFFICIENT_EVIDENCE",
                    "CSS3": "INSUFFICIENT_EVIDENCE"
                }

        else:  # DevOps Engineer
            skills_claimed = ["Docker", "Kubernetes", "CI/CD", "Linux"]
            if archetype == "strong_verifiable":
                resume_text = f"Jamie Oliver ({candidate_id})\nEmail: jo{i}@example.com\nGitHub: github.com/jo_{candidate_id}\n\nSummary:\nDevOps Engineer with 3 years of experience in Docker and Kubernetes.\nSkills: Docker, Kubernetes, CI/CD, Linux, AWS\nExperience:\nDevOps (2022-Present):\n- Kubernetes clusters and CI/CD pipelines."
                github_profile = {
                    "exists": True,
                    "username": f"jo_{candidate_id}",
                    "publicReposCount": 2,
                    "repositories": [
                        {
                            "name": "k8s-infra",
                            "description": "Kubernetes manifest repository with Docker and CI/CD",
                            "primaryLanguage": "Go",
                            "languages": {"Go": 20000, "Dockerfile": 2000},
                            "topics": ["kubernetes", "docker", "ci-cd"],
                            "dependencies": ["docker", "kubernetes"],
                            "createdAt": "2022-04-01T10:00:00Z",
                            "pushedAt": "2025-10-15T10:00:00Z",
                            "stars": 10,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/jo_{candidate_id}/k8s-infra"
                        }
                    ]
                }
                ground_truth = {
                    "Docker": "SUPPORTED",
                    "Kubernetes": "SUPPORTED",
                    "CI/CD": "SUPPORTED",
                    "Linux": "PARTIALLY_SUPPORTED"
                }
            elif archetype == "partial_tenure":
                resume_text = f"Casey Stone ({candidate_id})\nEmail: cs{i}@example.com\nGitHub: github.com/cs_{candidate_id}\n\nSummary:\nDevOps specialist with 4 years in Docker.\nSkills: Docker, Kubernetes, CI/CD, Linux\nExperience:\nSysAdmin (2021-Present)."
                github_profile = {
                    "exists": True,
                    "username": f"cs_{candidate_id}",
                    "publicReposCount": 1,
                    "repositories": [
                        {
                            "name": "docker-compose-utils",
                            "description": "Docker utility compose files",
                            "primaryLanguage": "Shell",
                            "languages": {"Shell": 4000, "Dockerfile": 1000},
                            "topics": ["docker"],
                            "dependencies": ["docker"],
                            "createdAt": "2024-09-01T10:00:00Z",
                            "pushedAt": "2025-01-10T10:00:00Z",
                            "stars": 1,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/cs_{candidate_id}/docker-compose-utils"
                        }
                    ]
                }
                ground_truth = {
                    "Docker": "PARTIALLY_SUPPORTED",
                    "Kubernetes": "INSUFFICIENT_EVIDENCE",
                    "CI/CD": "INSUFFICIENT_EVIDENCE",
                    "Linux": "INSUFFICIENT_EVIDENCE"
                }
            elif archetype == "enterprise_private_repo":
                resume_text = f"Drew Barry ({candidate_id})\nEmail: db{i}@example.com\n\nSummary:\nInfrastructure engineer with 5 years enterprise DevOps experience.\nSkills: Docker, Kubernetes, CI/CD, Linux\nExperience:\nEnterprise Cloud (2020-Present)."
                github_profile = {"exists": False, "username": None, "repositories": []}
                ground_truth = {
                    "Docker": "INSUFFICIENT_EVIDENCE",
                    "Kubernetes": "INSUFFICIENT_EVIDENCE",
                    "CI/CD": "INSUFFICIENT_EVIDENCE",
                    "Linux": "INSUFFICIENT_EVIDENCE"
                }
            else: # anachronistic
                resume_text = f"Reese Witherspoon ({candidate_id})\nEmail: rw{i}@example.com\nGitHub: github.com/rw_{candidate_id}\n\nSummary:\n16 years of experience in Docker containerization.\nSkills: Docker, Kubernetes, CI/CD, Linux\nExperience:\nInfrastructure Architect (2010-Present)."
                github_profile = {
                    "exists": True,
                    "username": f"rw_{candidate_id}",
                    "publicReposCount": 1,
                    "repositories": [
                        {
                            "name": "docker-test",
                            "description": "Test",
                            "primaryLanguage": "Shell",
                            "languages": {"Shell": 2000},
                            "dependencies": ["docker"],
                            "createdAt": "2024-01-01T10:00:00Z",
                            "pushedAt": "2024-02-01T10:00:00Z",
                            "stars": 0,
                            "isFork": False,
                            "htmlUrl": f"https://github.com/rw_{candidate_id}/docker-test"
                        }
                    ]
                }
                ground_truth = {
                    "Docker": "POTENTIAL_CONTRADICTION",
                    "Kubernetes": "INSUFFICIENT_EVIDENCE",
                    "CI/CD": "INSUFFICIENT_EVIDENCE",
                    "Linux": "INSUFFICIENT_EVIDENCE"
                }

        benchmark.append({
            "candidateId": candidate_id,
            "targetRole": role,
            "archetype": archetype,
            "resumeText": resume_text,
            "githubProfile": github_profile,
            "groundTruthSkills": ground_truth
        })

    return benchmark
