"""Passing revision of the controlled, unmerged governance smoke fixture."""
import unittest


class GovernanceSmoke(unittest.TestCase):
    def test_deliberate_failure(self):
        self.assertEqual(2 + 2, 4)
