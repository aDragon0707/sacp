"""Run a stable SACP test suite and emit machine-readable CI evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
OPTIONAL_TEST_MODULES = {"tests.test_langgraph_adapter", "tests.test_harness"}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def source_fingerprint() -> str:
    tree = subprocess.run(
        ["git", "ls-tree", "-r", "--full-tree", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return f"sha256:{hashlib.sha256(tree).hexdigest()}"


def environment() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "runner_os": os.environ.get("RUNNER_OS", platform.system()),
    }


def _test_modules() -> list[str]:
    return [
        f"tests.{path.stem}"
        for path in sorted(TESTS.glob("test_*.py"))
    ]


def suite_modules(suite: str) -> list[str]:
    if suite == "core":
        return [module for module in _test_modules() if module not in OPTIONAL_TEST_MODULES]
    if suite == "langgraph":
        return ["tests.test_langgraph_adapter"]
    raise ValueError(f"unittest modules are not defined for suite: {suite}")


def _run_unittest_suite(suite: str) -> dict[str, Any]:
    modules = suite_modules(suite)
    tests = unittest.defaultTestLoader.loadTestsFromNames(modules)
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    return {
        "total": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "successful": result.wasSuccessful(),
        "modules": modules,
    }


def _run_protocol_suite() -> dict[str, Any]:
    import validator

    targets = validator.example_paths(ROOT)
    targets += sorted((ROOT / "sample-corpus" / "translated-receipts").glob("*.yaml"))
    results = [validator.validate_document(path) for path in targets]
    failed = [item for item in results if not item["valid"] or item["warnings"]]
    return {
        "total": len(results),
        "failures": len(failed),
        "errors": 0,
        "skipped": 0,
        "successful": not failed and bool(results),
        "results": results,
    }


def _run_harness_suite() -> dict[str, Any]:
    from sacp_harness import build_report, report_passed

    report = build_report()
    engine = report["engine"]
    protocol = report["protocol"]
    return {
        "total": engine["total"],
        "failures": engine["false_success_allowed"] + protocol["fail"],
        "errors": 1 if protocol["error"] else 0,
        "skipped": 0,
        "successful": report_passed(report),
        "report": report,
    }


def run_suite(suite: str) -> dict[str, Any]:
    if suite in {"core", "langgraph"}:
        return _run_unittest_suite(suite)
    if suite == "protocol":
        return _run_protocol_suite()
    if suite == "harness":
        return _run_harness_suite()
    raise ValueError(f"unknown suite: {suite}")


def build_evidence(
    *,
    suite: str,
    job: str,
    result: dict[str, Any],
    fail_on_skip: bool,
    command: str,
) -> dict[str, Any]:
    skipped = int(result["skipped"])
    passed = bool(result["successful"]) and (not fail_on_skip or skipped == 0)
    return {
        "schema": "sacp-ci-evidence/1",
        "job": job,
        "suite": suite,
        "status": "passed" if passed else "failed",
        "exit_code": 0 if passed else 1,
        "command": command,
        "source_fingerprint": source_fingerprint(),
        "base_sha": os.environ.get("SACP_BASE_SHA", ""),
        "head_sha": os.environ.get("SACP_HEAD_SHA", os.environ.get("GITHUB_SHA", "")),
        "merge_sha": os.environ.get("SACP_MERGE_SHA", os.environ.get("GITHUB_SHA", "")),
        "environment": environment(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("core", "langgraph", "protocol", "harness"), required=True)
    parser.add_argument("--job", help="Stable CI job name; defaults to the suite name")
    parser.add_argument("--fail-on-skip", action="store_true")
    parser.add_argument("--json", type=Path, required=True, help="Evidence JSON output path")
    args = parser.parse_args(argv)

    command = " ".join(["python", "scripts/run_tests.py", *(argv or sys.argv[1:])])
    result = run_suite(args.suite)
    evidence = build_evidence(
        suite=args.suite,
        job=args.job or args.suite,
        result=result,
        fail_on_skip=args.fail_on_skip,
        command=command,
    )
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"{args.suite}: status={evidence['status']} total={result['total']} "
        f"failures={result['failures']} errors={result['errors']} skipped={result['skipped']}"
    )
    return int(evidence["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
