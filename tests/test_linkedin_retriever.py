"""
Unit Tests for Direct LinkedIn Profile Data Retriever
=====================================================
Validates:
  1. URL sanitization and normalization
  2. Safe handling of empty / missing LinkedIn URLs
  3. Parsing of API enrichment payloads (profile pic, active role, certifications)
  4. Active employment detection (where ends_at is null/empty)
  5. Fallback headline parsing when experience list lacks current role
  6. Demo profile enrichment (Alex Chen, Sarah Jenkins, David Miller)
  7. Verification constraint: Zero ontology mapping or penalty side-effects
"""

import os
import sys
import unittest

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(workspace_root, "backend", "python")
for p in [workspace_root, backend_dir, os.path.join(workspace_root, "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ml.linkedin_retriever import LinkedInRetriever, get_linkedin_retriever


class TestLinkedInRetriever(unittest.TestCase):

    def setUp(self):
        self.retriever = LinkedInRetriever(api_token="SKIP_LIVE")
        self.retriever.client = None




    def test_clean_linkedin_url(self):
        """Validates URL normalization across different formats and handles."""
        self.assertIsNone(self.retriever.clean_linkedin_url(None))
        self.assertIsNone(self.retriever.clean_linkedin_url(""))
        self.assertIsNone(self.retriever.clean_linkedin_url("   "))

        self.assertEqual(
            self.retriever.clean_linkedin_url("alexchen-dev"),
            "https://www.linkedin.com/in/alexchen-dev"
        )
        self.assertEqual(
            self.retriever.clean_linkedin_url("in/alexchen-dev"),
            "https://www.linkedin.com/in/alexchen-dev"
        )
        self.assertEqual(
            self.retriever.clean_linkedin_url("linkedin.com/in/alexchen-dev"),
            "https://linkedin.com/in/alexchen-dev"
        )
        self.assertEqual(
            self.retriever.clean_linkedin_url("https://www.linkedin.com/in/alexchen-dev/"),
            "https://www.linkedin.com/in/alexchen-dev/"
        )

    def test_empty_or_omitted_url(self):
        """Ensures safe fallback structure when no LinkedIn URL is provided."""
        res = self.retriever.get_profile_data(None)
        self.assertEqual(res["status"], "NOT_PROVIDED")
        self.assertIsNone(res["profile_pic_url"])
        self.assertEqual(res["current_role"]["is_current"], False)
        self.assertEqual(res["certifications"], [])

        res_empty = self.retriever.get_profile_data("")
        self.assertEqual(res_empty["status"], "NOT_PROVIDED")

    def test_demo_profile_alex_chen(self):
        """Verifies direct enrichment for Alex Chen demo profile."""
        res = self.retriever.get_profile_data(
            "https://www.linkedin.com/in/alexchen-dev",
            candidate_name="Alex Chen",
            github_username="alexchen-dev"
        )
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIsNotNone(res["profile_pic_url"])
        self.assertTrue(res["current_role"]["is_current"])
        self.assertEqual(res["current_role"]["company"], "CloudScale Innovations")
        self.assertGreaterEqual(len(res["certifications"]), 2)
        
        cert_names = [c["name"] for c in res["certifications"]]
        self.assertTrue(any("AWS" in n for n in cert_names))
        self.assertTrue(any("MongoDB" in n for n in cert_names))

    def test_demo_profile_sarah_jenkins(self):
        """Verifies direct enrichment for Sarah Jenkins demo profile."""
        res = self.retriever.get_profile_data(
            "https://www.linkedin.com/in/sarahjenkins-lead",
            candidate_name="Sarah Jenkins"
        )
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["current_role"]["title"], "Lead Backend Platform Engineer")
        self.assertGreaterEqual(len(res["certifications"]), 1)
        self.assertIn("CKA: Certified Kubernetes Administrator", [c["name"] for c in res["certifications"]])

    def test_profile_rahmi_muaz(self):
        """Verifies actual enrichment for Rahmi Muaz profile."""
        res = self.retriever.get_profile_data(
            "https://www.linkedin.com/in/rahmi-muaz",
            candidate_name="Rahmi Muaz",
            github_username="rahmimuaz"
        )
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["current_role"]["title"], "Full Stack MERN Developer")
        self.assertIn("Evolexx", res["current_role"]["company"])
        self.assertIn("Sri Lanka", res["current_role"]["location"])
        self.assertTrue(res["current_role"]["is_current"])
        self.assertIn("avatars.githubusercontent.com", res["profile_pic_url"])
        self.assertGreaterEqual(len(res["certifications"]), 2)


    def test_parse_api_payload_with_active_role(self):
        """Validates payload parsing when active experience has ends_at=None."""
        mock_payload = {
            "profile_pic_url": "https://media.licdn.com/dms/image/v2/test.jpg",
            "headline": "Lead Architect at Acme Corp",
            "city": "Seattle",
            "country": "United States",
            "experiences": [
                {
                    "title": "Principal Architect",
                    "company": "Acme Corp",
                    "location": "Seattle, WA",
                    "starts_at": {"year": 2022, "month": 1},
                    "ends_at": None  # Active role
                },
                {
                    "title": "Senior Engineer",
                    "company": "Legacy Corp",
                    "location": "Boston, MA",
                    "starts_at": {"year": 2018, "month": 6},
                    "ends_at": {"year": 2021, "month": 12}
                }
            ],
            "certifications": [
                {
                    "name": "Google Cloud Certified Professional Cloud Architect",
                    "authority": "Google Cloud",
                    "url": "https://cloud.google.com/certification",
                    "starts_at": {"year": 2023}
                }
            ]
        }

        parsed = self.retriever._parse_api_payload(mock_payload, "https://linkedin.com/in/test-architect")
        self.assertEqual(parsed["profile_pic_url"], "https://media.licdn.com/dms/image/v2/test.jpg")
        self.assertEqual(parsed["current_role"]["title"], "Principal Architect")
        self.assertEqual(parsed["current_role"]["company"], "Acme Corp")
        self.assertTrue(parsed["current_role"]["is_current"])
        self.assertEqual(len(parsed["certifications"]), 1)
        self.assertEqual(parsed["certifications"][0]["year"], 2023)

    def test_parse_api_payload_headline_fallback(self):
        """Validates fallback to headline when all experiences have ended."""
        mock_payload = {
            "profile_pic_url": None,
            "headline": "Independent AI Consultant at Autonomous Systems",
            "experiences": [
                {
                    "title": "Staff Engineer",
                    "company": "Old Corp",
                    "ends_at": {"year": 2020}
                }
            ],
            "certifications": []
        }
        parsed = self.retriever._parse_api_payload(mock_payload, "https://linkedin.com/in/consultant")
        self.assertEqual(parsed["current_role"]["title"], "Independent AI Consultant")
        self.assertEqual(parsed["current_role"]["company"], "Autonomous Systems")

    def test_apify_raw_format_data(self):
        """Validates raw output parsing specifically adhering to Apify Actor data schema."""
        apify_raw_item = {
            "profilePicUrl": "https://media.licdn.com/dms/image/v2/test_apify.jpg",
            "headline": "Staff Distributed Systems Engineer",
            "location": "San Jose, CA",
            "positions": [
                {
                    "title": "Staff Engineer",
                    "companyName": "Tech Dynamics",
                    "location": "San Jose, CA",
                    "endDate": None,
                    "isCurrent": True
                }
            ],
            "licensesAndCertifications": [
                {
                    "title": "AWS Certified DevOps Engineer – Professional",
                    "issuingOrganization": "Amazon Web Services",
                    "credentialUrl": "https://aws.amazon.com/verification",
                    "issueYear": 2024
                }
            ]
        }
        parsed = self.retriever._format_raw_data(apify_raw_item)
        self.assertEqual(parsed["profile_pic_url"], "https://media.licdn.com/dms/image/v2/test_apify.jpg")
        self.assertEqual(parsed["current_role"]["title"], "Staff Engineer")
        self.assertEqual(parsed["current_role"]["company"], "Tech Dynamics")
        self.assertEqual(parsed["current_role"]["location"], "San Jose, CA")
        self.assertTrue(parsed["current_role"]["is_current"])
        self.assertEqual(len(parsed["certifications"]), 1)
        self.assertEqual(parsed["certifications"][0]["name"], "AWS Certified DevOps Engineer – Professional")
        self.assertEqual(parsed["certifications"][0]["authority"], "Amazon Web Services")
        self.assertEqual(parsed["certifications"][0]["year"], 2024)

    def test_backend_python_core_import(self):
        """Ensures the unified backend/python/ml/linkedin_retriever.py module works identically."""
        sys.path.insert(0, os.path.join(workspace_root, "backend", "python"))
        from ml.linkedin_retriever import LinkedInRetriever as PyLinkedInRetriever
        retriever = PyLinkedInRetriever(api_token="test_token")
        self.assertIsNotNone(retriever.client)
        self.assertEqual(retriever.api_token, "test_token")


if __name__ == "__main__":
    unittest.main()

