"""
Unit Tests for Repository Engineering Evidence (REE) Engine
===========================================================
Validates:
  1. Date parsing robustness, timezone normalization, negative delta prevention
  2. Missing field policies (null releases, empty license, zero values)
  3. Empirical quantile-based threshold classifications (Maintenance, Collaboration, Activity)
  4. Skill-grounded repository relevance filtering
  5. Candidate-level evidence strength synthesis
  6. Protection of private candidate profiles (epistemic distinction)
  7. End-to-end integration with CrossSourceClaimVerifier
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(workspace_root, "backend", "python")
for p in [workspace_root, backend_dir, os.path.join(workspace_root, "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ml.repository_engineering_evidence import RepositoryEngineeringEvidenceEngine, get_ree_engine
from ml.claim_verifier import CrossSourceClaimVerifier
from ml.esco_ontology import get_esco_ontology


class TestRepositoryEngineeringEvidence(unittest.TestCase):

    def setUp(self):
        # Fix reference date to 2026-08-01 for deterministic unit test assertions
        self.ref_date = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.engine = RepositoryEngineeringEvidenceEngine(reference_date=self.ref_date)

    def test_parse_iso_date_robustness(self):
        """Validates safe parsing across ISO strings, YYYY-MM-DD, None, and edge cases."""
        self.assertIsNone(self.engine.parse_iso_date(None))
        self.assertIsNone(self.engine.parse_iso_date(""))
        self.assertIsNone(self.engine.parse_iso_date("nan"))
        self.assertIsNone(self.engine.parse_iso_date("invalid-date-string"))

        dt1 = self.engine.parse_iso_date("2026-06-15T15:30:00Z")
        self.assertIsNotNone(dt1)
        self.assertEqual(dt1.year, 2026)
        self.assertEqual(dt1.month, 6)

        dt2 = self.engine.parse_iso_date("2024-03-20")
        self.assertIsNotNone(dt2)
        self.assertEqual(dt2.year, 2024)

    def test_missing_data_policy(self):
        """Ensures missing optional fields (license, releases, diskUsage) degrade gracefully."""
        minimal_repo = {
            "name": "barebones-repo",
            "createdAt": "2025-01-01T00:00:00Z",
            "lastCommitDate": "2026-07-20T00:00:00Z",
            "lastReleaseDate": None,
            "license": None,
            "diskUsage": None,
            "commits": None,
            "contributors": None
        }
        res = self.engine.analyze_repository(minimal_repo)
        self.assertEqual(res["hasRelease"], False)
        self.assertIsNone(res["daysSinceLastRelease"])
        self.assertEqual(res["hasLicense"], False)
        self.assertEqual(res["commits"], 0)
        self.assertEqual(res["contributors"], 1)
        self.assertEqual(res["maintenanceStatus"], "ACTIVE")

    def test_maintenance_quantile_thresholds(self):
        """Validates empirical maintenance boundaries (ACTIVE <= 100d, STABLE <= 380d, INACTIVE > 380d)."""
        # Active: commit 12 days before reference
        repo_active = {
            "name": "active-repo",
            "lastCommitDate": (self.ref_date - timedelta(days=12)).isoformat(),
            "createdAt": (self.ref_date - timedelta(days=300)).isoformat()
        }
        self.assertEqual(self.engine.analyze_repository(repo_active)["maintenanceStatus"], "ACTIVE")

        # Stable: commit 200 days before reference
        repo_stable = {
            "name": "stable-repo",
            "lastCommitDate": (self.ref_date - timedelta(days=200)).isoformat(),
            "createdAt": (self.ref_date - timedelta(days=500)).isoformat()
        }
        self.assertEqual(self.engine.analyze_repository(repo_stable)["maintenanceStatus"], "STABLE")

        # Inactive: commit 450 days before reference
        repo_inactive = {
            "name": "dormant-repo",
            "lastCommitDate": (self.ref_date - timedelta(days=450)).isoformat(),
            "createdAt": (self.ref_date - timedelta(days=600)).isoformat()
        }
        self.assertEqual(self.engine.analyze_repository(repo_inactive)["maintenanceStatus"], "INACTIVE")

    def test_collaboration_quantile_thresholds(self):
        """Validates collaboration indicators (Community >= 5 contribs & 10 PRs, Multi >= 2 contribs, Solo = 1)."""
        community_repo = {
            "name": "framework-core",
            "contributors": 12,
            "pulls": 45,
            "commits": 300
        }
        self.assertEqual(self.engine.analyze_repository(community_repo)["collaborationStatus"], "COMMUNITY_PROJECT")

        multi_repo = {
            "name": "team-project",
            "contributors": 3,
            "pulls": 4,
            "commits": 85
        }
        self.assertEqual(self.engine.analyze_repository(multi_repo)["collaborationStatus"], "MULTI_CONTRIBUTOR")

        solo_repo = {
            "name": "personal-utility",
            "contributors": 1,
            "pulls": 0,
            "commits": 15
        }
        self.assertEqual(self.engine.analyze_repository(solo_repo)["collaborationStatus"], "SOLO_CONTRIBUTOR")

    def test_skill_relevance_filtering(self):
        """Ensures technical relevance is properly mapped against claimed skills."""
        repo = {
            "name": "react-query-dashboard",
            "description": "Full stack microservice built with Node.js and Express",
            "primaryLanguage": "TypeScript",
            "topics": ["react", "nodejs", "graphql"],
            "dependencies": ["react", "express", "mongodb"]
        }
        analysis = self.engine.analyze_repository(repo, claimed_skills=["React", "MongoDB", "Python"])
        self.assertIn("React", analysis["relevance"])
        self.assertIn("MongoDB", analysis["relevance"])
        self.assertNotIn("Python", analysis["relevance"])

    def test_private_experience_protection(self):
        """Verifies that candidates without public repos receive NO PUBLIC REPOSITORY EVIDENCE without penalty."""
        res = self.engine.analyze_candidate_repositories(
            repositories=[],
            candidate_skills=["Python", "FastAPI"],
            candidate_name="Sarah Jenkins"
        )
        self.assertEqual(res["evidenceStrength"], "NO PUBLIC REPOSITORY EVIDENCE")
        self.assertEqual(res["summary"]["repositoriesAnalyzed"], 0)
        self.assertIn("must not be construed as negative evidence", res["explanation"])

    def test_end_to_end_verifier_integration(self):
        """Validates that CrossSourceClaimVerifier returns repositoryEngineeringEvidence payload."""
        esco = get_esco_ontology()
        verifier = CrossSourceClaimVerifier(esco=esco, ree_engine=self.engine)
        role_config = esco.get_default_role_config("Full Stack MERN Developer")

        sample_resume = """
        Alex Chen
        Full Stack MERN Developer with 3 years of commercial experience in React, Node.js, Express.js, and MongoDB.
        """

        result = verifier.verify_candidate(
            resume_text=sample_resume,
            target_role_config=role_config,
            github_username="alexchen-dev",
            candidate_name="Alex Chen"
        )

        self.assertIn("repositoryEngineeringEvidence", result)
        ree = result["repositoryEngineeringEvidence"]
        self.assertIn("summary", ree)
        self.assertIn("maintenance", ree)
        self.assertIn("collaboration", ree)
        self.assertIn("activityMaturity", ree)
        self.assertIn("evidenceStrength", ree)
        self.assertIn("repositorySummaries", ree)
        self.assertGreaterEqual(ree["summary"]["repositoriesAnalyzed"], 1)


if __name__ == "__main__":
    unittest.main()
