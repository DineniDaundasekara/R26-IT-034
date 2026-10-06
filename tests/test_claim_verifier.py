"""
Unit tests for Cross-Source Claim Verifier module.
"""

import os
import sys
import unittest

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(workspace_root, "backend", "python")
for p in [workspace_root, backend_dir, os.path.join(workspace_root, "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from ml.claim_verifier import CrossSourceClaimVerifier
    from ml.esco_ontology import get_esco_ontology
except ImportError:
    from claim_verifier import CrossSourceClaimVerifier
    from esco_ontology import get_esco_ontology



class TestClaimVerifier(unittest.TestCase):

    def setUp(self):
        self.verifier = CrossSourceClaimVerifier()
        self.esco = get_esco_ontology()
        self.role_config = self.esco.get_default_role_config("Full Stack MERN Developer")

    def test_verify_candidate_end_to_end(self):
        sample_resume = """
        Alex Smith
        Email: alex.smith@example.com | GitHub: candidate_alex
        
        Summary:
        Full Stack Developer with 3 years of experience in MERN stack.
        
        Skills:
        React, Node.js, Express.js, MongoDB, JavaScript, Docker
        
        Experience:
        Full Stack Developer (2021 - Present)
        - Developed an e-commerce platform using React, Node.js, Express, and MongoDB.
        """
        # Test candidate verification
        result = self.verifier.verify_candidate(
            resume_text=sample_resume,
            target_role_config=self.role_config,
            github_username="candidate_alex",
            candidate_name="Alex Smith"
        )

        self.assertEqual(result["candidateName"], "Alex Smith")
        self.assertEqual(result["targetRole"], "Full Stack MERN Developer")
        self.assertIn("skillVerifications", result)
        self.assertGreater(len(result["skillVerifications"]), 0)
        self.assertIn("overallAssessment", result)
        self.assertIn("hrDecisionSupport", result)


if __name__ == "__main__":
    unittest.main()
