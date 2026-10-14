"""Run GitHub REST-shaped payloads through the release gate."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sacp_verify import EventStore, GitHubActionsPayloadAdapter, ReleaseGate, Verifier


BASE = datetime(2026, 8, 31, 17, 0, tzinfo=timezone.utc)


def payload(approval: bool = True, artifact_commit: str = "abc123") -> dict:
    data = {
        "action_id": "github-api-release-v1.4.0",
        "thread_id": "github-api-thread",
        "run_id": "github-api-run-1",
        "checkpoint_id": "github-api-checkpoint-1",
        "input_digest": "sha256:release-v1.4.0",
        "action_scope": "publish-v1.4.0",
        "observed_at": BASE.isoformat(),
        "approval_expires_at": (BASE + timedelta(hours=1)).isoformat(),
        "workflow_run": {
            "id": 1001,
            "name": "CI",
            "head_sha": "abc123",
            "conclusion": "success",
            "output_digest": "sha256:ci-run-1001",
        },
        "artifact": {
            "id": 2001,
            "name": "release-v1.4.0.tgz",
            "digest": "sha256:artifact-2001",
            "workflow_run": {"head_sha": artifact_commit},
        },
        "reviews": [],
    }
    if approval:
        data["reviews"].append(
            {
                "id": 3001,
                "state": "APPROVED",
                "commit_id": "abc123",
                "submitted_at": BASE.isoformat(),
                "user": {"login": "release-manager"},
            }
        )
    return data


def run(label: str, data: dict) -> None:
    store = EventStore()
    try:
        GitHubActionsPayloadAdapter(store).ingest_release(data)
        decision = ReleaseGate(store, Verifier(store)).can_proceed(data["action_id"], now=BASE)
        print(f"{label}: allowed={decision.allowed}, reason={decision.reason}, overall={decision.receipt.overall_status}")
    finally:
        store.close()


def main() -> None:
    run("1) REST-shaped payload without approval", payload(approval=False))
    run("2) REST-shaped payload with matching review", payload())
    run("3) REST-shaped payload with mismatched artifact", payload(artifact_commit="other-commit"))


if __name__ == "__main__":
    main()
