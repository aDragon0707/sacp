"""Classify a PR diff and enforce repository-level contribution policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _source_fingerprint(ref: str) -> str:
    tree = subprocess.run(
        ["git", "ls-tree", "-r", "--full-tree", ref],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return f"sha256:{hashlib.sha256(tree).hexdigest()}"


def changed_files(base: str, head: str) -> list[str]:
    process = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return [line.strip().replace("\\", "/") for line in process.stdout.splitlines() if line.strip()]


def file_at_ref(ref: str, path: str) -> str | None:
    process = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return process.stdout if process.returncode == 0 else None


def classify_files(paths: Iterable[str]) -> list[str]:
    classes: set[str] = set()
    for raw_path in paths:
        path = raw_path.replace("\\", "/")
        name = Path(path).name
        if path.startswith(".github/") or path.startswith("scripts/") or name in {"requirements-ci.txt", "validator.py"}:
            classes.add("automation")
        if path.startswith("sample-corpus/"):
            classes.add("corpus")
        if path.startswith("sacp_verify/"):
            if name in {"github_actions.py", "langgraph_adapter.py", "cli.py"}:
                classes.add("adapter")
            else:
                classes.add("engine")
        if path == "requirements-integration.txt" or path.startswith("examples/langgraph_") or path.startswith("examples/github_"):
            classes.add("adapter")
        if path.startswith("sacp_harness/"):
            classes.add("engine")
        if path.startswith("sacp_eval/") or path.startswith("examples/pi_eval/") or path == "examples/pi_evaluation.py":
            classes.add("adapter")
        if name in {
            "SPEC.md",
            "ENVELOPE.md",
            "RECEIPT.md",
            "STATUS_CODES.md",
            "CONFORMANCE.md",
            "PROTOCOL_EVOLUTION.md",
            "DIRTY_RUN_CASES.md",
        } or name == "validator.py" or path.startswith("examples/") and path.endswith(".yaml"):
            classes.add("protocol")
        if path.startswith("docs/") or path.endswith(".md"):
            classes.add("docs")
    return sorted(classes)


def inspect_workflows(workflows: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for path, content in workflows.items():
        try:
            document = yaml.safe_load(content)
        except yaml.YAMLError:
            errors.append(f"{path}: invalid workflow YAML")
            continue
        if not isinstance(document, dict):
            errors.append(f"{path}: workflow must be a mapping")
            continue
        triggers = document.get("on", document.get(True, {}))
        if "pull_request_target" in document or triggers == "pull_request_target" or isinstance(triggers, (dict, list)) and "pull_request_target" in triggers:
            errors.append(f"{path}: pull_request_target is forbidden")

        visited: set[int] = set()

        def inspect(node):
            if isinstance(node, (list, dict)):
                if id(node) in visited:
                    errors.append(f"{path}: YAML aliases require separate review")
                    return
                visited.add(id(node))
            if isinstance(node, list):
                for child in node:
                    inspect(child)
            elif isinstance(node, dict):
                permissions = node.get("permissions")
                if permissions == "write-all" or isinstance(permissions, dict) and any(value == "write" for value in permissions.values()):
                    errors.append(f"{path}: write permission is forbidden")
                action = node.get("uses")
                if action is not None and (not isinstance(action, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40}", action)):
                    errors.append(f"{path}: action must use a full commit SHA; local and container actions require separate review")
                for child in node.values():
                    inspect(child)

        inspect(document)
    return errors


def evaluate_policy(paths: list[str], workflows: dict[str, str]) -> dict[str, object]:
    normalized = [path.replace("\\", "/") for path in paths]
    path_set = set(normalized)
    errors = inspect_workflows(workflows)
    warnings: list[str] = []
    classes = classify_files(normalized)

    readme_changed = "README.md" in path_set
    chinese_readme_changed = "README.zh-CN.md" in path_set
    if readme_changed != chinese_readme_changed:
        errors.append("README.md and README.zh-CN.md must be changed together")

    if "protocol" in classes:
        companion_checks = {
            "dirty case": any(path.startswith("examples/dirty_") for path in normalized) or "DIRTY_RUN_CASES.md" in path_set,
            "compatibility note": "PROTOCOL_EVOLUTION.md" in path_set,
            "reference example": any(path.startswith("examples/") and path.endswith(".yaml") for path in normalized),
            "changelog": "CHANGELOG.md" in path_set,
        }
        missing = [name for name, present in companion_checks.items() if not present]
        if missing:
            warnings.append("protocol change needs maintainer review for: " + ", ".join(missing))

    automation_critical = any(
        path.startswith(".github/workflows/")
        or path in {
            "scripts/run_tests.py",
            "scripts/check_pr_policy.py",
            "scripts/check_pr_gate.py",
            "scripts/build_ci_receipt.py",
            "scripts/extract_ci_refs.py",
            "scripts/ci_attestation.py",
            "validator.py",
        }
        for path in normalized
    )
    return {
        "change_classes": classes,
        "risk": "automation-critical" if automation_critical else "normal",
        "errors": errors,
        "warnings": warnings,
        "changed_files": normalized,
        "passed": not errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--job", default="pr-policy")
    parser.add_argument("--source-ref", default="HEAD")
    args = parser.parse_args(argv)

    paths = changed_files(args.base, args.head)
    workflows = {}
    for path in paths:
        if not path.startswith(".github/workflows/"):
            continue
        content = file_at_ref(args.head, path)
        if content is not None:
            workflows[path] = content
    result = evaluate_policy(paths, workflows)
    evidence = {
        "schema": "sacp-ci-evidence/1",
        "job": args.job,
        "suite": "pr-policy",
        "status": "passed" if result["passed"] else "failed",
        "exit_code": 0 if result["passed"] else 1,
        "command": f"python scripts/check_pr_policy.py --base {args.base} --head {args.head}",
        "source_fingerprint": _source_fingerprint(args.source_ref),
        "base_sha": args.base,
        "head_sha": args.head,
        "merge_sha": os.environ.get("SACP_MERGE_SHA", os.environ.get("GITHUB_SHA", args.head)),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "runner_os": os.environ.get("RUNNER_OS", platform.system()),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": result,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return int(evidence["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
