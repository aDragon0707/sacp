"""Run the GitHub Actions fixture through the SACP release gate."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sacp_verify import EventStore, GitHubActionsFixtureAdapter, ReleaseGate, Verifier


BASE = datetime(2026, 8, 31, 16, 0, tzinfo=timezone.utc)


def fixture(approval: dict | None = None, artifact_commit: str = "abc123") -> dict:
    return {
        "action_id": "github-release-v1.4.0",
        "thread_id": "github-release-thread",
        "run_id": "github-run-1",
        "checkpoint_id": "github-checkpoint-1",
        "input_digest": "sha256:release-v1.4.0",
        "action_scope": "publish-v1.4.0",
        "observed_at": BASE.isoformat(),
        "commit": "abc123",
        "check_run": {"check_run_id": "check-100", "name": "tests", "conclusion": "success", "output_digest": "sha256:ci"},
        "artifact": {"artifact_name": "release-v1.4.0.tgz", "digest": "sha256:artifact", "commit": artifact_commit},
        "approval": approval,
    }


def run(label: str, data: dict) -> None:
    store = EventStore()
    try:
        GitHubActionsFixtureAdapter(store).ingest(data)
        decision = ReleaseGate(store, Verifier(store)).can_proceed(data["action_id"])
        print(f"{label}: allowed={decision.allowed}, reason={decision.reason}, overall={decision.receipt.overall_status}")
    finally:
        store.close()


def main() -> None:
    approval = {
        "decision": "approved",
        "owner": "release-manager",
        "input_digest": "sha256:release-v1.4.0",
        "action_scope": "publish-v1.4.0",
        "expires_at": (BASE + timedelta(hours=1)).isoformat(),
    }
    run("1) missing approval", fixture())
    run("2) matching approval", fixture(approval=approval))
    run("3) artifact belongs to another commit", fixture(approval=approval, artifact_commit="other-commit"))


if __name__ == "__main__":
    main()
