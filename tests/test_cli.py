from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from examples.github_api_payload_gate import BASE, payload
from sacp_verify.cli import main


class CliTests(unittest.TestCase):
    def run_payload(self, data: dict) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payload.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--payload", str(path)])
            return code, json.loads(output.getvalue())

    def test_cli_returns_zero_for_allowed_release(self) -> None:
        data = payload()
        code, result = self.run_payload(data)
        self.assertEqual(code, 0)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["receipt"]["overall_status"], "ready_for_external_action")

    def test_cli_returns_nonzero_for_missing_review(self) -> None:
        data = payload(approval=False)
        code, result = self.run_payload(data)
        self.assertEqual(code, 1)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "release_approval_missing_or_stale")

    def test_cli_returns_nonzero_for_expired_review(self) -> None:
        data = payload()
        data["approval_expires_at"] = (BASE - timedelta(seconds=1)).isoformat()
        code, result = self.run_payload(data)
        self.assertEqual(code, 1)
        self.assertEqual(result["receipt"]["authority_status"], "expired")


if __name__ == "__main__":
    unittest.main()
