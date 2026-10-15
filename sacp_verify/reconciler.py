"""Bounded absence checks, including accepted executions without a terminal result."""
from __future__ import annotations

from datetime import datetime, timezone

from .lifecycle import terminal_attested
from .model import ReconciliationEvent, RetryPolicy
from .store import EventStore
from .verifier import Verifier


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class Reconciler:
    def __init__(self, store: EventStore, verifier: Verifier, policy: RetryPolicy | None = None) -> None:
        self.store = store
        self.verifier = verifier
        self.policy = policy or RetryPolicy()

    def reconcile(self, now: datetime | None = None) -> list[str]:
        """Append due routes once per claim/attempt; never execute side effects.

        Callers supply a scheduler. A configured deadline and owner are required.
        SQLite serializes concurrent check-and-append decisions, including restarts.
        """
        current = now or datetime.now(timezone.utc)
        created = []
        for action_id in sorted({row["action_id"] for row in self.store.events()}):
            with self.store.transaction():
                event_id = self._reconcile_action(action_id, current)
                if event_id:
                    created.append(event_id)
        return created

    def _reconcile_action(self, action_id: str, current: datetime) -> str | None:
        rows = self.store.events(action_id)
        claims = [row for row in rows if row["event_type"] == "claim"]
        if not claims:
            return None
        latest = claims[-1]
        claim = self.store.decode(latest)["payload"]
        deadline, owner = claim.get("attestation_deadline"), claim.get("reconciliation_owner")
        if not deadline or not owner or current < _time(deadline):
            return None
        observations = [self.store.decode(row)["payload"] for row in rows if row["event_type"] == "provider_observation"]
        if terminal_attested(observations):
            return None
        previous = [self.store.decode(row)["payload"] for row in rows if row["event_type"] == "reconciliation" and row["sequence"] > latest["sequence"]]
        absent = [item for item in previous if item.get("result") == "absent"]
        attempt = 1
        if absent:
            last = absent[-1]
            due = last.get("next_check_at")
            if not due or current < _time(due):
                return None
            attempt = int(last["attempt"]) + 1
        if attempt < self.policy.max_attempts:
            route, next_check = "retry", current + self.policy.retry_delay
        else:
            route, next_check = ("compensation" if self.policy.compensation_owner else "human_review"), None
            owner = self.policy.compensation_owner or owner
        event = ReconciliationEvent(action_id, "absent", current, owner, next_check, attempt, self.policy.max_attempts, route, latest["event_id"])
        return self.store.record_reconciliation(event)
