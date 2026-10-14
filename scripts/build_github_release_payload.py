"""Build a GitHub REST-shaped release payload from CI outputs and reviews."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--action-id", required=True)
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--checkpoint-id", required=True)
    parser.add_argument("--input-digest", required=True)
    parser.add_argument("--action-scope", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--check-run-id", required=True)
    parser.add_argument("--test-output-digest", required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--observed-at", default=None)
    args = parser.parse_args()
    observed_at = datetime.fromisoformat(args.observed_at) if args.observed_at else datetime.now(timezone.utc)
    reviews = json.loads(Path(args.reviews).read_text(encoding="utf-8"))
    payload = {
        "action_id": args.action_id,
        "thread_id": args.thread_id,
        "run_id": args.run_id,
        "checkpoint_id": args.checkpoint_id,
        "input_digest": args.input_digest,
        "action_scope": args.action_scope,
        "observed_at": observed_at.isoformat(),
        "approval_expires_at": (observed_at + timedelta(hours=1)).isoformat(),
        "workflow_run": {
            "id": args.run_id,
            "name": "SACP release gate CI",
            "head_sha": args.commit,
            "conclusion": "success",
            "check_suite_id": args.check_run_id,
            "output_digest": args.test_output_digest,
        },
        "artifact": {
            "id": args.artifact_name,
            "name": args.artifact_name,
            "digest": args.artifact_digest,
            "workflow_run": {"head_sha": args.commit},
        },
        "reviews": reviews,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
