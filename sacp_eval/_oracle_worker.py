"""Trusted unittest inventory/summary worker, invoked with Python -I -B.

Product code may still behave maliciously in this process. Run the entire outer
evaluator within an OS isolation boundary before accepting real-agent patches.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1])
    sys.path.insert(0, str(root / "source"))

    class Result(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.executed_ids = []

        def startTest(self, test):
            self.executed_ids.append(test.id())
            super().startTest(test)

    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
    summary = {"total": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses), "executed_test_ids": result.executed_ids}
    (root / "result.json").write_text(json.dumps(summary), encoding="utf-8")
    return 0 if result.wasSuccessful() and not result.skipped and not result.expectedFailures else 1


if __name__ == "__main__":
    raise SystemExit(main())
