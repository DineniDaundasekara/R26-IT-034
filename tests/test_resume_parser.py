"""
Unit tests for Resume Claim Extractor module.
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
    from ml.resume_parser import ResumeClaimExtractor
except ImportError:
    from resume_parser import ResumeClaimExtractor



class TestResumeClaimExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = ResumeClaimExtractor()

    def test_extract_skills_and_durations(self):
        sample_resume = """
        John Doe
        Email: john.doe@example.com | GitHub: github.com/johndoe
        
        Summary:
        Full-Stack Engineer with 4 years of experience building modern web applications with React and Node.js.
        
        Technical Skills:
        - Languages: JavaScript, TypeScript, Python
        - Frameworks: React, Express.js, FastAPI
        - Databases: MongoDB, PostgreSQL
        - Tools: Docker, Git, AWS
        
        Experience:
        Senior Software Engineer - Tech Solutions (2020 - Present)
        - Developed an e-commerce platform using MERN stack (MongoDB, Express, React, Node.js).
        - Architected REST APIs with FastAPI and Docker.
        """
        parsed = self.extractor.parse(sample_resume)
        
        # Test Contact Info
        self.assertEqual(parsed["contact"]["email"], "john.doe@example.com")
        self.assertEqual(parsed["contact"]["github"], "johndoe")
        
        # Test Skills
        skill_names = [s["name"] for s in parsed["skills"]]
        self.assertIn("React", skill_names)
        self.assertIn("Node.js", skill_names)
        self.assertIn("MongoDB", skill_names)
        self.assertIn("Python", skill_names)
        self.assertIn("Docker", skill_names)

        # Test Temporal Claims
        self.assertGreater(len(parsed["temporalClaims"]), 0)
        found_4yr = any(tc.get("claimedYears") == 4.0 for tc in parsed["temporalClaims"])
        self.assertTrue(found_4yr)

        # Test Project Claims
        self.assertGreater(len(parsed["projectClaims"]), 0)


if __name__ == "__main__":
    unittest.main()
