"""Demonstrate reconciliation recovery across SQLite store reopenings."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

from sacp_verify import Claim, EventStore, Reconciler, Verifier


BASE = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)


def main() -> None:
    with TemporaryDirectory() as directory:
        database = f"{directory}/reconciliation.sqlite3"
        first_store = EventStore(database)
        first_store.append_claim(
            Claim(
                action_id="restart-demo",
                claim_type="notification_sent",
                text="notification_sent",
                thread_id="thread-restart",
                run_id="run-restart",
                checkpoint_id="checkpoint-1",
                attestation_deadline=BASE + timedelta(minutes=5),
                reconciliation_owner="reconciliation-queue",
                created_at=BASE,
            )
        )
        first_store.close()

        resumed_store = EventStore(database)
        resumed_reconciler = Reconciler(resumed_store, Verifier(resumed_store))
        timeout_at = BASE + timedelta(minutes=6)
        first_timeout = resumed_reconciler.reconcile(timeout_at)
        first_receipt = Verifier(resumed_store).project_receipt("restart-demo", timeout_at)
        print(
            "1) after restart: "
            f"created={len(first_timeout)}, status={first_receipt.status}, "
            f"events={resumed_store.event_count('restart-demo')}"
        )
        resumed_store.close()

        restarted_store = EventStore(database)
        restarted_reconciler = Reconciler(restarted_store, Verifier(restarted_store))
        second_timeout = restarted_reconciler.reconcile(BASE + timedelta(minutes=7))
        second_receipt = Verifier(restarted_store).project_receipt(
            "restart-demo", BASE + timedelta(minutes=7)
        )
        print(
            "2) second reconciliation: "
            f"created={len(second_timeout)}, status={second_receipt.status}, "
            f"events={restarted_store.event_count('restart-demo')}"
        )
        restarted_store.close()


if __name__ == "__main__":
    main()
