"""Deliberate failing PR fixture. Never merge this smoke-test branch."""
import unittest


class GovernanceSmoke(unittest.TestCase):
    def test_deliberate_failure(self):
        self.fail("Expected smoke failure: pr-gate and receipt must block this SHA")
