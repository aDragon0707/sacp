"""Deterministic refund provider and finalize gate for a payment test scenario."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .model import GateDecision, ProviderObservation
from .store import EventStore
from .verifier import Verifier


class MockRefundProvider:
    """Simulate a payment provider without moving real money."""

    def __init__(self, store: EventStore, provider: str = "mock-refund-provider") -> None:
        self.store = store
        self.provider = provider
        self._refund_ids: dict[str, str] = {}

    def request(
        self,
        action_id: str,
        order_id: str,
        amount: int,
        currency: str,
        idempotency_key: str,
        observed_at: datetime,
    ) -> str:
        if amount <= 0:
            raise ValueError("refund amount must be positive")
        if idempotency_key in self._refund_ids:
            return self._refund_ids[idempotency_key]
        refund_id = f"refund-{len(self._refund_ids) + 1}"
        self._refund_ids[idempotency_key] = refund_id
        self.store.record_provider_observation(
            ProviderObservation(
                action_id=action_id,
                provider=self.provider,
                receipt_id=refund_id,
                provider_event="accepted",
                observed_at=observed_at,
                raw_digest=f"refund-request:{refund_id}",
                metadata={
                    "order_id": order_id,
                    "amount": amount,
                    "currency": currency,
                    "idempotency_key": idempotency_key,
                },
            )
        )
        return refund_id

    def webhook(
        self,
        action_id: str,
        event: str,
        refund_id: str,
        order_id: str,
        amount: int,
        currency: str,
        observed_at: datetime,
    ) -> str:
        if event not in {"succeeded", "failed"}:
            raise ValueError(f"Unsupported refund event: {event}")
        return self.store.record_provider_observation(
            ProviderObservation(
                action_id=action_id,
                provider=self.provider,
                receipt_id=refund_id,
                provider_event=event,
                observed_at=observed_at,
                raw_digest=f"refund-webhook:{refund_id}:{event}",
                metadata={"order_id": order_id, "amount": amount, "currency": currency},
            )
        )


class RefundGate:
    """Allow finalization only for an approved, scope-matching succeeded refund."""

    def __init__(self, store: EventStore, verifier: Verifier) -> None:
        self.store = store
        self.verifier = verifier

    def can_finalize(self, action_id: str, expected: dict[str, Any]) -> GateDecision:
        rows = self.store.events(action_id)
        observed_times = [row["created_at"] for row in rows]
        now = datetime.fromisoformat(max(observed_times)) if observed_times else None
        receipt = self.verifier.project_receipt(action_id, now=now)
        observations = [
            self.store.decode(row)["payload"]
            for row in rows
            if row["event_type"] == "provider_observation"
        ]
        matching_succeeded = any(
            item.get("provider_event") == "succeeded"
            and item.get("metadata", {}) == {
                "order_id": expected.get("order_id"),
                "amount": expected.get("amount"),
                "currency": expected.get("currency"),
            }
            for item in observations
        )
        if receipt.authority_status != "approved":
            return GateDecision(action_id, False, "refund_authority_missing", receipt)
        if not matching_succeeded:
            return GateDecision(action_id, False, "refund_scope_mismatch", receipt)
        return GateDecision(action_id, True, "refund_succeeded", receipt)
