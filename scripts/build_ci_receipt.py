"""Build a trusted SACP/0.1 receipt from untrusted CI evidence artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PR_REQUIRED_JOBS = (
    "protocol-validation",
    "core-ubuntu-311",
    "core-ubuntu-312",
    "core-windows-312",
    "integration-langgraph-ubuntu-312",
    "harness",
    "pr-policy",
)
MAIN_REQUIRED_JOBS = PR_REQUIRED_JOBS[:-1]
FINGERPRINT = re.compile(r"^sha256:[0-9a-f]{64}$")
CHECK_DISPLAY_NAMES = {
    "core-ubuntu-311": "core-ubuntu-3.11",
    "core-ubuntu-312": "core-ubuntu-3.12",
    "core-windows-312": "core-windows-3.12",
    "integration-langgraph-ubuntu-312": "integration-langgraph-ubuntu-3.12",
}


def load_evidence(directory: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    evidence: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    if not directory.exists():
        return evidence, [f"evidence directory is missing: {directory}"]
    for path in sorted(directory.rglob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: invalid JSON: {exc}")
            continue
        job = item.get("job")
        if not isinstance(job, str) or not job:
            errors.append(f"{path.name}: missing job identity")
            continue
        if job in evidence:
            errors.append(f"{path.name}: duplicate evidence for {job}")
            continue
        evidence[job] = item
    return evidence, errors


def event_identity(event: dict[str, Any], mode: str) -> dict[str, Any]:
    if mode == "pr":
        workflow_run = event.get("workflow_run", {})
        pull_requests = workflow_run.get("pull_requests", [])
        pull_request = pull_requests[0] if pull_requests else {}
        return {
            "pr_number": pull_request.get("number"),
            "base_sha": pull_request.get("base", {}).get("sha", ""),
            "head_sha": pull_request.get("head", {}).get("sha", workflow_run.get("head_sha", "")),
            "merge_sha": workflow_run.get("head_sha", ""),
            "run_id": str(workflow_run.get("id", "unknown")),
            "conclusion": workflow_run.get("conclusion", "failure"),
            "processed_at": workflow_run.get("updated_at"),
        }
    return {
        "pr_number": None,
        "base_sha": event.get("before", ""),
        "head_sha": event.get("after", event.get("head_commit", {}).get("id", "")),
        "merge_sha": event.get("after", ""),
        "run_id": str(event.get("run_id", "unknown")),
        "conclusion": "success",
        "processed_at": event.get("head_commit", {}).get("timestamp"),
    }


def validate_evidence(
    evidence: dict[str, dict[str, Any]],
    required_jobs: Iterable[str],
    identity: dict[str, Any],
) -> tuple[list[str], list[str], list[str], str | None]:
    required = tuple(required_jobs)
    missing = [job for job in required if job not in evidence]
    blocked: list[str] = []
    invalid: list[str] = []
    fingerprints: set[str] = set()
    merge_shas: set[str] = set()

    for job in required:
        item = evidence.get(job)
        if item is None:
            continue
        if item.get("schema") != "sacp-ci-evidence/1":
            invalid.append(f"{job}: unsupported evidence schema")
        if item.get("status") != "passed" or item.get("exit_code") != 0:
            blocked.append(f"{job}: check did not pass")
        if not item.get("command"):
            invalid.append(f"{job}: command is missing")
        if item.get("head_sha") != identity["head_sha"]:
            invalid.append(f"{job}: head SHA does not match current event")
        if item.get("base_sha") != identity["base_sha"]:
            invalid.append(f"{job}: base SHA does not match current event")
        merge_sha = item.get("merge_sha")
        if not merge_sha:
            invalid.append(f"{job}: merge SHA is missing")
        else:
            merge_shas.add(str(merge_sha))
        fingerprint = item.get("source_fingerprint")
        if not isinstance(fingerprint, str) or not FINGERPRINT.fullmatch(fingerprint):
            invalid.append(f"{job}: source fingerprint is missing or invalid")
        else:
            fingerprints.add(fingerprint)
        environment = item.get("environment")
        if not isinstance(environment, dict) or not all(
            environment.get(field) for field in ("platform", "python", "runner_os")
        ):
            invalid.append(f"{job}: execution environment is incomplete")
        results = item.get("results", {})
        if item.get("suite") != "pr-policy" and results.get("skipped") != 0:
            blocked.append(f"{job}: skipped tests are not allowed")

    if len(fingerprints) > 1:
        invalid.append("required jobs disagree on the source fingerprint")
    if len(merge_shas) > 1:
        invalid.append("required jobs disagree on the tested merge SHA")
    fingerprint = next(iter(fingerprints), None)
    return missing, blocked, invalid, fingerprint


def _fallback_fingerprint(identity: dict[str, Any]) -> str:
    material = f"{identity['base_sha']}...{identity['head_sha']}".encode("utf-8")
    return f"sha256:{hashlib.sha256(material).hexdigest()}"


def build_receipt(
    *,
    event: dict[str, Any],
    mode: str,
    evidence: dict[str, dict[str, Any]],
    required_jobs: Iterable[str],
    load_errors: Iterable[str] = (),
) -> dict[str, Any]:
    required = tuple(required_jobs)
    identity = event_identity(event, mode)
    missing, blocked, invalid, fingerprint = validate_evidence(evidence, required, identity)
    invalid = [*load_errors, *invalid]
    workflow_failed = mode == "pr" and identity["conclusion"] != "success"

    if invalid:
        method, status_code, verification_status = "FAIL", 500, "failed"
        next_owner = "contributor"
    elif missing or blocked or workflow_failed:
        method, status_code, verification_status = "BLOCK", 412, "blocked"
        next_owner = "contributor"
    else:
        method, status_code, verification_status = "COMPLETE", 200, "passed"
        next_owner = "maintainer"

    policy = evidence.get("pr-policy", {}).get("results", {})
    change_classes = policy.get("change_classes", []) if isinstance(policy, dict) else []
    all_errors = [
        *invalid,
        *blocked,
        *(f"missing evidence: {job}" for job in missing),
    ]
    if workflow_failed:
        all_errors.append(f"PR CI workflow conclusion: {identity['conclusion']}")
    check_names = [CHECK_DISPLAY_NAMES.get(job, job) for job in required]
    if mode == "pr":
        check_names.append("pr-gate")
    target = f"PR #{identity['pr_number']}" if identity["pr_number"] else "main"
    claim_text = (
        f"Automated preflight completed for {target} at {identity['head_sha']}."
        if method == "COMPLETE"
        else f"Automated preflight did not complete for {target} at {identity['head_sha']}."
    )
    processed_at = identity["processed_at"] or datetime.now(timezone.utc).isoformat()

    return {
        "protocol": "SACP/0.1",
        "type": "receipt",
        "method": method,
        "status_code": status_code,
        "handoff_id": f"github-{mode}-{identity['pr_number'] or identity['head_sha']}",
        "attempt_id": f"github-run-{identity['run_id']}",
        "agent_id": "github-actions",
        "processed_at": processed_at,
        "source_fingerprint": fingerprint or _fallback_fingerprint(identity),
        "claims": [
            {
                "text": claim_text,
                "claim_type": "tool_result",
                "source_id": f"github-actions-run-{identity['run_id']}",
                "support_status": "supported" if method == "COMPLETE" else "unverified",
            }
        ],
        "verification": {
            "status": verification_status,
            "method": "trusted receipt builder over CI evidence artifacts",
            "evidence_id": f"github-actions-run-{identity['run_id']}",
        },
        "residual_risk": (
            "Automated preflight is not approval, merge authorization, or release authorization."
            if method == "COMPLETE"
            else "; ".join(all_errors) or "Automated evidence is incomplete."
        ),
        "next_owner": next_owner,
        "human_decision_required": True,
        "extensions": {
            "github.pr_number": identity["pr_number"],
            "github.base_sha": identity["base_sha"],
            "github.head_sha": identity["head_sha"],
            "github.merge_sha": next(
                (item.get("merge_sha") for item in evidence.values() if item.get("merge_sha")),
                identity["merge_sha"],
            ),
            "sacp.change_classes": change_classes,
            "sacp.risk": policy.get("risk", "unknown") if isinstance(policy, dict) else "unknown",
            "sacp.policy_warnings": policy.get("warnings", []) if isinstance(policy, dict) else [],
            "sacp.required_checks": check_names,
            "sacp.evidence_errors": all_errors,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("pr", "main"), required=True)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--required-job", action="append", dest="required_jobs")
    args = parser.parse_args(argv)

    event = json.loads(args.event.read_text(encoding="utf-8"))
    evidence, load_errors = load_evidence(args.evidence_dir)
    defaults = PR_REQUIRED_JOBS if args.mode == "pr" else MAIN_REQUIRED_JOBS
    receipt = build_receipt(
        event=event,
        mode=args.mode,
        evidence=evidence,
        required_jobs=args.required_jobs or defaults,
        load_errors=load_errors,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        yaml.safe_dump(receipt, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    import validator

    result = validator.validate_document(args.output)
    if not result["valid"] or result["warnings"]:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1
    print(
        f"receipt: method={receipt['method']} status_code={receipt['status_code']} "
        f"head_sha={receipt['extensions']['github.head_sha']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
