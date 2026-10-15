"""Collect GitHub facts and inspect Git objects without executing PR code.

The receipt workflow must run this file from the default branch. Artifacts are
only candidates: the API, commit parents and Git tree independently bind them.
This attests execution and coverage, not the honesty of arbitrary Python tests.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SHA = re.compile(r"^[0-9a-f]{40}$")
DISPLAY = {"core-ubuntu-3.11": "core-ubuntu-311", "core-ubuntu-3.12": "core-ubuntu-312", "core-windows-3.12": "core-windows-312", "integration-langgraph-ubuntu-3.12": "integration-langgraph-ubuntu-312"}
EXECUTION_FILES = (".github/workflows/pr-ci.yml", "scripts/run_tests.py", "requirements-ci.txt", "requirements-integration.txt", "tests/__init__.py", "sitecustomize.py", "usercustomize.py")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout


def blob(ref: str, path: str) -> str:
    result = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return result.stdout if result.returncode == 0 else ""


def api(path: str):
    token = os.environ.get("GH_TOKEN", "")
    request = Request(f"https://api.github.com/{path}", headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def inventory(ref: str) -> dict[str, int]:
    paths = git("ls-tree", "-r", "--name-only", ref).splitlines()
    counts = {"core": 0, "langgraph": 0, "protocol": 0, "harness": 8}
    for path in paths:
        if path.startswith("tests/test_") and path.endswith(".py") and path != "tests/test_harness.py":
            tree = ast.parse(blob(ref, path))
            count = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_") for node in ast.walk(tree))
            counts["langgraph" if path == "tests/test_langgraph_adapter.py" else "core"] += count
        if (path.startswith("examples/") and path.count("/") == 1 or path.startswith("sample-corpus/translated-receipts/")) and path.endswith(".yaml"):
            counts["protocol"] += 1
    return counts


def validate_execution(base: str, merge: str, *, mode: str) -> list[str]:
    if mode == "main":
        return []  # main is the explicitly reviewed policy baseline.
    return [f"execution definition changed: {path}; maintainer bootstrap review required" for path in EXECUTION_FILES if blob(base, path) != blob(merge, path)]


def collect(event: dict, mode: str, evidence_dir: Path, repository: str) -> tuple[dict, dict]:
    from scripts.build_ci_receipt import load_evidence
    run_id = event.get("workflow_run", {}).get("id") if mode == "pr" else os.environ.get("GITHUB_RUN_ID")
    if not str(run_id).isdigit() or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid run or repository identity")
    run = api(f"repos/{repository}/actions/runs/{run_id}")
    errors = []
    jobs = {}
    page = 1
    while True:
        batch = api(f"repos/{repository}/actions/runs/{run_id}/attempts/{run['run_attempt']}/jobs?per_page=100&page={page}")["jobs"]
        for job in batch:
            name = DISPLAY.get(job["name"], job["name"])
            if name in jobs:
                errors.append(f"duplicate GitHub job: {name}")
            jobs[name] = job.get("conclusion") if job.get("status") == "completed" else job.get("status")
        if len(batch) < 100:
            break
        page += 1
    if run.get("repository", {}).get("full_name") != repository or run.get("event") != ("pull_request" if mode == "pr" else "push"):
        errors.append("run repository or event mismatch")
    expected_path = f".github/workflows/{'pr-ci' if mode == 'pr' else 'main-verify'}.yml"
    if run.get("path") != expected_path:
        errors.append("unexpected workflow path")

    if mode == "pr":
        candidates = api(f"repos/{repository}/commits/{run['head_sha']}/pulls?per_page=100")
        candidates = [pr for pr in candidates if pr.get("head", {}).get("sha") == run["head_sha"] and pr.get("base", {}).get("repo", {}).get("full_name") == repository and pr.get("state") == "open"]
        if len(candidates) != 1:
            raise ValueError("run does not resolve to one open PR at its current head (possibly superseded)")
        pr = api(f"repos/{repository}/pulls/{candidates[0]['number']}")
        base, head = pr["base"]["sha"], pr["head"]["sha"]
        if head != run["head_sha"] or pr["state"] != "open":
            errors.append("PR head is superseded or PR is closed")
        items, _ = load_evidence(evidence_dir)
        merges = {item.get("merge_sha") for item in items.values() if SHA.fullmatch(str(item.get("merge_sha", "")))}
        if len(merges) != 1:
            raise ValueError("evidence has no unique tested merge candidate")
        merge = merges.pop()
        if pr.get("merge_commit_sha") != merge:
            errors.append("tested merge is no longer the current GitHub PR merge")
        normalized = {"workflow_run": {**run, "pull_requests": [{"number": pr["number"], "base": {"sha": base}, "head": {"sha": head}}]}}
    else:
        base, head, merge = event["before"], event["after"], event["after"]
        normalized = {**event, "run_id": run_id}
        if run["head_sha"] != head:
            errors.append("main run SHA mismatch")
    if not all(SHA.fullmatch(value) for value in (base, head, merge)):
        raise ValueError("expected full commit SHAs")
    subprocess.run(["git", "fetch", "--no-tags", "origin", base, head, merge], cwd=ROOT, check=True, capture_output=True)
    if mode == "pr":
        parents = git("show", "-s", "--format=%P", merge).strip().split()
        if parents != [base, head]:
            errors.append("tested merge parents do not match current base and head")
        # Compare against the trusted checkout too: old base policy cannot replace current policy.
        errors += validate_execution("HEAD", merge, mode=mode)
    minimum = inventory(base if mode == "pr" else head)
    current_inventory = inventory(merge)
    for suite in minimum:
        if current_inventory[suite] < minimum[suite]:
            errors.append(f"{suite}: test inventory decreased; explicit maintainer review required")
        minimum[suite] = max(minimum[suite], current_inventory[suite])
    tree = subprocess.run(["git", "ls-tree", "-r", "--full-tree", merge], cwd=ROOT, capture_output=True, check=True).stdout
    attestation = {"run_id": str(run_id), "run_attempt": run["run_attempt"], "base_sha": base, "head_sha": head, "merge_sha": merge, "source_fingerprint": "sha256:" + hashlib.sha256(tree).hexdigest(), "jobs": jobs, "minimum_tests": minimum, "errors": errors}
    return attestation, normalized


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("pr", "main"), required=True)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--normalized-event", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    event = json.loads(args.event.read_text(encoding="utf-8"))
    try:
        result, normalized = collect(event, args.mode, args.evidence_dir, os.environ["GITHUB_REPOSITORY"])
    except Exception as exc:
        # Always emit an auditable blocked receipt; do not print HTTP bodies or credentials.
        result, normalized = {"errors": [f"independent attestation unavailable: {type(exc).__name__}"], "jobs": {}}, event
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    args.normalized_event.write_text(json.dumps(normalized), encoding="utf-8")
    if args.github_output and "merge_sha" in result:
        with args.github_output.open("a", encoding="utf-8") as output:
            for key in ("base_sha", "head_sha", "merge_sha"):
                output.write(f"{key}={result[key]}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Direct invocation must resolve only trusted sibling scripts.
    import sys
    sys.path.insert(0, str(ROOT))
    main()
