"""Extract validated base, head, and tested merge SHAs from CI evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")


def extract_refs(event: dict, evidence_dir: Path) -> dict[str, str]:
    workflow_run = event.get("workflow_run", {})
    pull_requests = workflow_run.get("pull_requests", [])
    if not pull_requests:
        raise ValueError("workflow_run does not identify a pull request")
    pull_request = pull_requests[0]
    expected = {
        "base_sha": pull_request.get("base", {}).get("sha", ""),
        "head_sha": pull_request.get("head", {}).get("sha", ""),
    }
    for name, value in expected.items():
        if not SHA.fullmatch(value):
            raise ValueError(f"event {name} is not a full commit SHA")

    candidates: set[str] = set()
    for path in sorted(evidence_dir.rglob("*.json")) if evidence_dir.exists() else []:
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if item.get("base_sha") != expected["base_sha"] or item.get("head_sha") != expected["head_sha"]:
            continue
        merge_sha = item.get("merge_sha")
        if isinstance(merge_sha, str) and SHA.fullmatch(merge_sha):
            candidates.add(merge_sha)
    if len(candidates) != 1:
        raise ValueError("CI evidence does not identify exactly one tested merge SHA")
    return {**expected, "merge_sha": candidates.pop()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)
    refs = extract_refs(
        json.loads(args.event.read_text(encoding="utf-8")), args.evidence_dir
    )
    output = args.github_output
    if output is None:
        raw_output = os.environ.get("GITHUB_OUTPUT")
        if not raw_output:
            parser.error("provide --github-output or GITHUB_OUTPUT")
        output = Path(raw_output)
    with output.open("a", encoding="utf-8") as handle:
        for name, value in refs.items():
            handle.write(f"{name}={value}\n")
    print(json.dumps(refs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
