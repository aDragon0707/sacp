"""Deployment provider observations and post-deploy finalization gate."""

from __future__ import annotations

from datetime import datetime

from .model import GateDecision, ProviderObservation
from .store import EventStore
from .verifier import Verifier


class MockDeploymentProvider:
    """Emit deployment lifecycle observations without touching a real environment."""

    def __init__(self, store: EventStore, provider: str = "mock-deployment") -> None:
        self.store = store
        self.provider = provider

    def emit(
        self,
        action_id: str,
        event: str,
        deployment_id: str,
        revision: str,
        observed_at: datetime,
        raw_digest: str = "mock-deployment-digest",
    ) -> str:
        if event not in {"accepted", "healthy", "failed", "rolled_back"}:
            raise ValueError(f"Unsupported deployment event: {event}")
        return self.store.record_provider_observation(
            ProviderObservation(
                action_id=action_id,
                provider=self.provider,
                receipt_id=deployment_id,
                provider_event=event,
                observed_at=observed_at,
                raw_digest=raw_digest,
                metadata={"revision": revision},
            )
        )


class DeploymentGate:
    """Finalize deployment only after provider acceptance and matching health evidence."""

    def __init__(self, store: EventStore, verifier: Verifier) -> None:
        self.store = store
        self.verifier = verifier

    def can_finalize(self, action_id: str, revision: str, now: datetime | None = None) -> GateDecision:
        receipt = self.verifier.project_receipt(action_id, now=now)
        rows = self.store.events(action_id)
        observations = [
            self.store.decode(row)["payload"]
            for row in rows
            if row["event_type"] == "provider_observation"
            and self.store.decode(row)["payload"].get("metadata", {}).get("revision") == revision
        ]
        events = [item.get("provider_event") for item in observations]
        if "rolled_back" in events:
            reason = "deployment_rolled_back"
            allowed = False
        elif "failed" in events:
            reason = "deployment_health_failed"
            allowed = False
        elif "healthy" in events and "accepted" in events:
            reason = "deployment_health_verified"
            allowed = True
        elif "accepted" in events:
            reason = "deployment_health_unverified"
            allowed = False
        else:
            reason = "deployment_acceptance_missing"
            allowed = False
        return GateDecision(action_id, allowed, reason, receipt)
