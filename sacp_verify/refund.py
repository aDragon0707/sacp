"""Deterministic refund provider and finalize gate for a payment test scenario."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from typing import Any

from .model import GateDecision, ProviderObservation
from .store import EventStore
from .verifier import Verifier
from .lifecycle import active_observations


class MockRefundProvider:
    """Simulate a payment provider without moving real money."""

    def __init__(self, store: EventStore, provider: str = "mock-refund-provider") -> None:
        self.store = store
        self.provider = provider

    def request(
        self,
        action_id: str,
        order_id: str,
        amount: int,
        currency: str,
        idempotency_key: str,
        observed_at: datetime,
    ) -> str:
        if type(amount) is not int or amount <= 0:
            raise ValueError("refund amount must be positive")
        if not all((action_id, order_id, currency, idempotency_key)):
            raise ValueError("refund identity, currency and idempotency key must be nonempty")
        refund_id = f"refund-{uuid4()}"
        return self.store.record_mock_refund_request(
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
            ), idempotency_key,
        )

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

    def can_finalize(self, action_id: str, expected: dict[str, Any], now: datetime | None = None) -> GateDecision:
        rows = self.store.events(action_id)
        receipt = self.verifier.project_receipt(action_id, now=now)
        observations = active_observations([
            self.store.decode(row)["payload"]
            for row in rows
            if row["event_type"] == "provider_observation"
        ])
        accepted = [item for item in observations if item.get("provider_event") == "accepted"]
        matching_succeeded = any(
            item.get("provider_event") == "succeeded"
            and item.get("metadata", {}) == {
                "order_id": expected.get("order_id"),
                "amount": expected.get("amount"),
                "currency": expected.get("currency"),
            }
            and any((start.get("provider"), start.get("receipt_id")) == (item.get("provider"), item.get("receipt_id")) and all(start.get("metadata", {}).get(key) == expected.get(key) for key in ("order_id", "amount", "currency")) for start in accepted)
            for item in observations
        )
        if receipt.authority_status != "approved":
            return GateDecision(action_id, False, "refund_authority_missing", receipt)
        claims = [self.store.decode(row)["payload"] for row in rows if row["event_type"] == "claim"]
        if not claims or any(claims[-1].get("metadata", {}).get(key) != expected.get(key) for key in ("order_id", "amount", "currency")):
            return GateDecision(action_id, False, "refund_scope_mismatch", receipt)
        if not matching_succeeded:
            return GateDecision(action_id, False, "refund_scope_mismatch", receipt)
        if receipt.external_status != "refund_succeeded" or receipt.overall_status != "refund_succeeded":
            return GateDecision(action_id, False, "refund_terminal_conflict", receipt)
        return GateDecision(action_id, True, "refund_succeeded", receipt)
