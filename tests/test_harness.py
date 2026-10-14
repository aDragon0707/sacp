from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sacp_harness import build_report, report_passed, write_report


class HarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generated_at = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
        cls.report = build_report(generated_at=cls.generated_at)

    def test_all_breakers_are_vetoed_and_protocol_is_strictly_valid(self) -> None:
        engine = self.report["engine"]
        protocol = self.report["protocol"]
        self.assertEqual(engine["vetoed"], 8)
        self.assertEqual(engine["total"], 8)
        self.assertEqual(engine["false_success_allowed"], 0)
        self.assertEqual(protocol["pass"], protocol["total"])
        self.assertEqual(protocol["fail"], 0)
        self.assertIsNone(protocol["error"])
        self.assertTrue(report_passed(self.report))

    def test_explicit_output_directory_writes_deterministic_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            json_path, markdown_path = write_report(self.report, Path(directory))
            saved = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(saved, self.report)
            self.assertEqual(saved["generated_at"], self.generated_at.isoformat())
            self.assertIn("Breaker cases blocked: 8/8", markdown_path.read_text(encoding="utf-8"))

    def test_naive_generated_at_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone"):
            build_report(generated_at=datetime(2026, 10, 14, 12, 0))


if __name__ == "__main__":
    unittest.main()
