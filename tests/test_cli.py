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
    def run_payload(self, data: dict, *, reviewers=("release-manager",), at=BASE.isoformat()) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payload.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                args = ["--payload", str(path)]
                for reviewer in reviewers:
                    args.extend(["--authorized-reviewer", reviewer])
                if at:
                    args.extend(["--now", at])
                code = main(args)
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

    def test_cli_requires_explicit_trusted_reviewer(self):
        self.assertEqual(self.run_payload(payload(), reviewers=())[0], 1)

    def test_cli_uses_wall_time_instead_of_payload_timestamp(self):
        self.assertEqual(self.run_payload(payload(), at=None)[0], 1)


if __name__ == "__main__":
    unittest.main()
