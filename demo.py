"""Run the MVP's core evidence-boundary scenarios by hand."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sacp_verify import Claim, EventStore, HostObservation, MockProvider, Reconciler, Verifier


BASE = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)


def add_claim(store: EventStore, action_id: str, claim_type: str, **kwargs: object) -> None:
    store.append_claim(
        Claim(
            action_id=action_id,
            claim_type=claim_type,
            text=claim_type,
            thread_id="demo-thread",
            run_id="demo-run",
            checkpoint_id="demo-checkpoint",
            created_at=BASE,
            **kwargs,
        )
    )


def show(verifier: Verifier, action_id: str, label: str) -> None:
    receipt = verifier.project_receipt(action_id, BASE + timedelta(minutes=10))
    print(f"{label}: {receipt.status} (next owner={receipt.next_action_owner!r}, retry={receipt.retry_allowed})")


def main() -> None:
    store = EventStore()
    verifier = Verifier(store)
    provider = MockProvider(store)
    try:
        add_claim(store, "demo-1", "tests_passed")
        show(verifier, "demo-1", "1) claim without evidence")

        host_event = store.record_host_observation(
            HostObservation(
                action_id="demo-2",
                kind="test_run",
                source="demo-test-runner",
                thread_id="demo-thread",
                run_id="demo-run",
                checkpoint_id="demo-checkpoint",
                payload={"exit_code": 0, "output_digest": "sha256:demo"},
                observed_at=BASE,
            )
        )
        add_claim(store, "demo-2", "tests_passed", evidence_refs=(host_event,))
        show(verifier, "demo-2", "2) host test evidence")

        add_claim(store, "demo-3", "notification_sent")
        provider.emit("demo-3", "accepted", "provider-demo-3", BASE)
        show(verifier, "demo-3", "3) provider accepted only")

        add_claim(store, "demo-4", "notification_sent")
        provider.emit("demo-4", "accepted", "provider-demo-4", BASE)
        provider.emit("demo-4", "delivered", "provider-demo-4", BASE + timedelta(minutes=1))
        provider.emit("demo-4", "bounced", "provider-demo-4", BASE + timedelta(minutes=2))
        show(verifier, "demo-4", "4) delivered then bounced")

        add_claim(
            store,
            "demo-5",
            "notification_sent",
            attestation_deadline=BASE + timedelta(minutes=5),
            reconciliation_owner="demo-reconciliation-queue",
        )
        Reconciler(store, verifier).reconcile(BASE + timedelta(minutes=6))
        show(verifier, "demo-5", "5) deadline without provider evidence")
    finally:
        store.close()


if __name__ == "__main__":
    main()
