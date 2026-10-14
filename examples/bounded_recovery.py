"""Demonstrate bounded retry scheduling and compensation routing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sacp_verify import Claim, EventStore, Reconciler, RetryPolicy, Verifier


BASE = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)


def main() -> None:
    store = EventStore()
    try:
        store.append_claim(
            Claim(
                action_id="bounded-demo",
                claim_type="notification_sent",
                text="notification_sent",
                thread_id="thread-bounded",
                run_id="run-bounded",
                checkpoint_id="checkpoint-1",
                attestation_deadline=BASE + timedelta(minutes=5),
                reconciliation_owner="reconciliation-queue",
                created_at=BASE,
            )
        )
        verifier = Verifier(store)
        reconciler = Reconciler(
            store,
            verifier,
            policy=RetryPolicy(
                max_attempts=2,
                retry_delay=timedelta(minutes=5),
                compensation_owner="compensation-queue",
            ),
        )
        first_at = BASE + timedelta(minutes=6)
        reconciler.reconcile(first_at)
        first = verifier.project_receipt("bounded-demo", first_at)
        print(
            f"1) timeout: route={first.recovery_route}, "
            f"retry_allowed={first.retry_allowed}, next_check_at={first.next_check_at.isoformat()}"
        )

        second_at = BASE + timedelta(minutes=12)
        reconciler.reconcile(second_at)
        second = verifier.project_receipt("bounded-demo", second_at)
        print(
            f"2) max attempts reached: route={second.recovery_route}, "
            f"retry_allowed={second.retry_allowed}, owner={second.next_action_owner}"
        )
    finally:
        store.close()


if __name__ == "__main__":
    main()
