"""Contract tests are static checks, NOT agent-behavior evaluation."""
import pathlib
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]

class SkillContractTests(unittest.TestCase):
    def test_skill_entry_exists(self):
        self.assertTrue((ROOT / 'SKILL.md').is_file(), 'Installable SKILL.md is required')

    def test_required_documents_exist(self):
        paths = ['README.md','agents/openai.yaml','references/swiftui-lookup.md',
                 'references/sources.json','references/coverage.md','references/verification.md',
                 'tests/scenarios.md','scripts/sync_docs.py','scripts/validate_skill.py',
                 'scripts/probe_environment.py']
        self.assertEqual([p for p in paths if not (ROOT / p).is_file()], [])

if __name__ == '__main__':
    unittest.main()
