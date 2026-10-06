import os
import sys
import unittest

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(workspace_root, "backend", "python")
for p in [workspace_root, backend_dir, os.path.join(workspace_root, "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from ml.github_miner import GitHubEvidenceMiner
except ImportError:
    from github_miner import GitHubEvidenceMiner



class TestGitHubEvidenceMiner(unittest.TestCase):

    def setUp(self):
        self.miner = GitHubEvidenceMiner()

    def test_extract_skill_evidence_from_mock_profile(self):
        mock_profile = {
            "exists": True,
            "username": "candidate_alex",
            "name": "Alex Developer",
            "publicReposCount": 5,
            "repositories": [
                {
                    "name": "mern-ecommerce",
                    "description": "Full-stack ecommerce platform built with React, Node, Express, and MongoDB",
                    "primaryLanguage": "JavaScript",
                    "languages": {"JavaScript": 50000, "HTML": 2000, "CSS": 3000},
                    "topics": ["react", "nodejs", "mongodb", "express"],
                    "dependencies": ["react", "express", "mongoose", "jsonwebtoken"],
                    "createdAt": "2021-03-15T10:00:00Z",
                    "pushedAt": "2024-05-10T14:00:00Z",
                    "stars": 12,
                    "isFork": False,
                    "htmlUrl": "https://github.com/candidate_alex/mern-ecommerce"
                },
                {
                    "name": "fastapi-microservice",
                    "description": "Async REST backend with FastAPI and Docker",
                    "primaryLanguage": "Python",
                    "languages": {"Python": 25000, "Dockerfile": 500},
                    "topics": ["fastapi", "docker", "python"],
                    "dependencies": ["fastapi", "uvicorn", "pydantic", "sqlalchemy"],
                    "createdAt": "2023-01-10T08:00:00Z",
                    "pushedAt": "2024-08-01T12:00:00Z",
                    "stars": 5,
                    "isFork": False,
                    "htmlUrl": "https://github.com/candidate_alex/fastapi-microservice"
                }
            ]
        }

        # Test React Evidence
        react_ev = self.miner.extract_skill_evidence(mock_profile, "React")
        self.assertTrue(react_ev["hasEvidence"])
        self.assertEqual(react_ev["relevantProjectsCount"], 1)
        self.assertGreater(react_ev["temporalMetrics"]["observedPublicYears"], 3.0)

        # Test Unknown Skill
        ruby_ev = self.miner.extract_skill_evidence(mock_profile, "Ruby on Rails")
        self.assertFalse(ruby_ev["hasEvidence"])
        self.assertEqual(ruby_ev["relevantProjectsCount"], 0)


if __name__ == "__main__":
    unittest.main()
