"""Fail unless every required PR CI dependency completed successfully."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

REQUIRED_JOBS = (
    "protocol-validation",
    "core-ubuntu-311",
    "core-ubuntu-312",
    "core-windows-312",
    "integration-langgraph-ubuntu-312",
    "harness",
    "pr-policy",
)


def evaluate_gate(needs: dict[str, Any], required: tuple[str, ...] = REQUIRED_JOBS) -> dict[str, object]:
    missing = [job for job in required if job not in needs]
    unexpected = {
        job: needs[job].get("result")
        for job in required
        if job in needs and needs[job].get("result") != "success"
    }
    return {
        "passed": not missing and not unexpected,
        "missing": missing,
        "non_success": unexpected,
        "required": list(required),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--needs-json", type=Path, help="Read the GitHub needs object from a file")
    args = parser.parse_args(argv)
    if args.needs_json:
        needs = json.loads(args.needs_json.read_text(encoding="utf-8"))
    else:
        raw = os.environ.get("NEEDS_JSON")
        if not raw:
            parser.error("provide --needs-json or NEEDS_JSON")
        needs = json.loads(raw)
    result = evaluate_gate(needs)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
