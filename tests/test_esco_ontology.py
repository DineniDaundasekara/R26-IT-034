import os
import sys
import unittest

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(workspace_root, "backend", "python")
for p in [workspace_root, backend_dir, os.path.join(workspace_root, "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from ml.esco_ontology import get_esco_ontology
except ImportError:
    from esco_ontology import get_esco_ontology



class TestESCOOntology(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.esco = get_esco_ontology()

    def test_lookup_skill_canonical(self):
        skill = self.esco.lookup_skill("Python")
        self.assertIsNotNone(skill)
        self.assertIn("python", skill["preferredLabel"].lower())

    def test_resolve_skill_aliases(self):
        self.assertEqual(self.esco.resolve_canonical_skill_name("React.js"), "React")
        self.assertEqual(self.esco.resolve_canonical_skill_name("JS"), "JavaScript")

    def test_search_occupations(self):
        results = self.esco.search_occupations("developer", limit=3)
        self.assertGreater(len(results), 0)
        self.assertIn("developer", results[0]["preferredLabel"].lower())

    def test_default_role_config(self):
        config = self.esco.get_default_role_config("Full Stack MERN Developer")
        self.assertEqual(config["roleId"], "full_stack_mern")
        req_names = [s["name"] for s in config["requiredSkills"]]
        self.assertIn("React", req_names)
        self.assertIn("Node.js", req_names)
        self.assertIn("MongoDB", req_names)


if __name__ == "__main__":
    unittest.main()
