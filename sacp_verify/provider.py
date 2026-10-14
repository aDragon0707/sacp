"""Deterministic mock provider for failure-injection tests."""

from __future__ import annotations

from datetime import datetime

from .model import ProviderObservation
from .store import EventStore


class MockProvider:
    def __init__(self, store: EventStore, provider: str = "mock-provider") -> None:
        self.store = store
        self.provider = provider

    def emit(
        self,
        action_id: str,
        event: str,
        receipt_id: str,
        observed_at: datetime,
        raw_digest: str = "mock-digest",
    ) -> str:
        if event not in {
            "accepted",
            "delivered",
            "bounced",
            "unauthorized",
            "bad_request",
            "provider_error",
            "counterparty_declined",
        }:
            raise ValueError(f"Unsupported provider event: {event}")
        return self.store.record_provider_observation(
            ProviderObservation(
                action_id=action_id,
                provider=self.provider,
                receipt_id=receipt_id,
                provider_event=event,
                observed_at=observed_at,
                raw_digest=raw_digest,
            )
        )
