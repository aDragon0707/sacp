"""Predeclared acceptance; never read from or chosen by the candidate."""
import unittest

from calculator import add


class AdditionTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(add(2, 3), 5)

    def test_mixed_sign(self):
        self.assertEqual(add(-2, 3), 1)
