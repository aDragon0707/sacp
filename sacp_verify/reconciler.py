"""Independent deadline and absence checks."""

from __future__ import annotations

from datetime import datetime, timezone

from .model import ReconciliationEvent, RetryPolicy
from .store import EventStore
from .verifier import Verifier


class Reconciler:
    def __init__(
        self,
        store: EventStore,
        verifier: Verifier,
        policy: RetryPolicy | None = None,
    ) -> None:
        self.store = store
        self.verifier = verifier
        self.policy = policy or RetryPolicy()

    def reconcile(self, now: datetime | None = None) -> list[str]:
        current = now or datetime.now(timezone.utc)
        action_ids = {row["action_id"] for row in self.store.events()}
        created: list[str] = []
        for action_id in sorted(action_ids):
            rows = self.store.events(action_id)
            claims = [
                self.store.decode(row)["payload"]
                for row in rows
                if row["event_type"] == "claim"
            ]
            if not claims:
                continue
            claim = claims[-1]
            deadline_text = claim.get("attestation_deadline")
            owner = claim.get("reconciliation_owner")
            if not deadline_text or not owner:
                continue
            last_claim_sequence = max(
                row["sequence"] for row in rows if row["event_type"] == "claim"
            )
            absent_rows = [
                row
                for row in rows
                if row["event_type"] == "reconciliation"
                and self.store.decode(row)["payload"].get("result") == "absent"
            ]
            last_absent = absent_rows[-1] if absent_rows else None
            deadline = datetime.fromisoformat(deadline_text)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            receipt = self.verifier.project_receipt(action_id, current)
            has_provider = bool(receipt.provider_evidence_refs)
            if has_provider:
                continue

            if last_absent is not None and last_absent["sequence"] > last_claim_sequence:
                previous = self.store.decode(last_absent)["payload"]
                next_check_text = previous.get("next_check_at")
                if next_check_text is None:
                    continue
                next_check = datetime.fromisoformat(next_check_text)
                if next_check.tzinfo is None:
                    next_check = next_check.replace(tzinfo=timezone.utc)
                if current < next_check:
                    continue
                attempt = int(previous.get("attempt", 1)) + 1
            elif current > deadline:
                attempt = 1
            else:
                continue

            route = "none"
            owner_for_event = owner
            next_check_at = None
            if attempt < self.policy.max_attempts:
                route = "retry"
                next_check_at = current + self.policy.retry_delay
            elif attempt >= self.policy.max_attempts and self.policy.compensation_owner:
                route = "compensation"
                owner_for_event = self.policy.compensation_owner

            if current > deadline or last_absent is not None:
                event = ReconciliationEvent(
                    action_id=action_id,
                    result="absent",
                    checked_at=current,
                    owner=owner_for_event,
                    next_check_at=next_check_at,
                    attempt=attempt,
                    max_attempts=self.policy.max_attempts,
                    route=route,
                )
                created.append(self.store.record_reconciliation(event))
        return created
