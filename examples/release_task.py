"""Simulate a release-announcement task without sending a real message."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sacp_verify import AuthorityDecision, Claim, EventStore, HostObservation, MockProvider, Verifier


BASE = datetime(2026, 8, 31, 14, 0, tzinfo=timezone.utc)
ACTION_ID = "release-v1.4.0"


def claim(*, claim_type: str, evidence_refs: tuple[str, ...] = (), requires_authority: bool = False) -> Claim:
    return Claim(
        action_id=ACTION_ID,
        claim_type=claim_type,
        text=f"{claim_type}: v1.4.0",
        thread_id="release-thread",
        run_id="release-run-1",
        checkpoint_id="release-checkpoint-1",
        input_digest="sha256:release-v1.4.0",
        action_scope="publish-release-announcement",
        evidence_refs=evidence_refs,
        requires_authority=requires_authority,
        created_at=BASE,
    )


def show(verifier: Verifier, label: str, at: datetime) -> None:
    receipt = verifier.project_receipt(ACTION_ID, at)
    print(
        f"{label}: overall={receipt.overall_status}, "
        f"host={receipt.host_status}, authority={receipt.authority_status}, "
        f"external={receipt.external_status}, "
        f"retry_allowed={receipt.retry_allowed}"
    )


def main() -> None:
    store = EventStore()
    verifier = Verifier(store)
    provider = MockProvider(store, provider="release-announcement-provider")
    try:
        # The deterministic runner records the fact before the agent can cite it.
        test_event = store.record_host_observation(
            HostObservation(
                action_id=ACTION_ID,
                kind="test_run",
                source="deterministic-ci",
                thread_id="release-thread",
                run_id="release-run-1",
                checkpoint_id="release-checkpoint-1",
                payload={
                    "command": "python -m unittest discover -s tests -v",
                    "exit_code": 0,
                    "output_digest": "sha256:tests-v1.4.0",
                },
                observed_at=BASE,
                idempotency_key="release-v1.4.0:test-run",
            )
        )
        store.append_claim(claim(claim_type="tests_passed", evidence_refs=(test_event,)))
        artifact_event = store.record_host_observation(
            HostObservation(
                action_id=ACTION_ID,
                kind="artifact",
                source="deterministic-build",
                thread_id="release-thread",
                run_id="release-run-1",
                checkpoint_id="release-checkpoint-1",
                payload={"artifact_name": "release-v1.4.0.tgz", "digest": "sha256:artifact-v1.4.0", "commit": "release-v1.4.0"},
                observed_at=BASE,
                idempotency_key="release-v1.4.0:artifact",
            )
        )
        store.append_claim(claim(claim_type="artifact_built", evidence_refs=(artifact_event,)))
        store.append_claim(
            claim(
                claim_type="ready_to_publish",
                evidence_refs=(test_event, artifact_event),
                requires_authority=True,
            )
        )
        show(verifier, "1) tests passed, before human approval", BASE)

        approval_event = store.record_authority_decision(
            AuthorityDecision(
                action_id=ACTION_ID,
                decision="approved",
                owner="release-manager",
                thread_id="release-thread",
                run_id="release-run-1",
                checkpoint_id="release-checkpoint-1",
                input_digest="sha256:release-v1.4.0",
                action_scope="publish-release-announcement",
                expires_at=BASE + timedelta(hours=1),
                decided_at=BASE + timedelta(minutes=1),
                rationale="Approved the exact v1.4.0 release scope.",
            )
        )
        assert approval_event
        show(verifier, "2) matching human approval", BASE + timedelta(minutes=1))

        provider.emit(ACTION_ID, "accepted", "provider-release-1", BASE + timedelta(minutes=2))
        show(verifier, "3) provider accepted", BASE + timedelta(minutes=2))

        provider.emit(ACTION_ID, "delivered", "provider-release-1", BASE + timedelta(minutes=3))
        show(verifier, "4) provider reported delivered", BASE + timedelta(minutes=3))

        # A later provider event changes the current projection without rewriting history.
        provider.emit(ACTION_ID, "bounced", "provider-release-1", BASE + timedelta(minutes=4))
        show(verifier, "5) later bounce", BASE + timedelta(minutes=4))
        print(f"history_events={store.event_count(ACTION_ID)}")
    finally:
        store.close()


if __name__ == "__main__":
    main()
