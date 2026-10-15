"""Deployment provider observations and post-deploy finalization gate."""

from __future__ import annotations

from datetime import datetime

from .model import GateDecision, ProviderObservation
from .store import EventStore
from .verifier import Verifier
from .lifecycle import active_observations


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

    def can_dispatch(self, action_id: str, now: datetime | None = None) -> GateDecision:
        """Check authorization before dispatch; health finalization is separate."""
        receipt = self.verifier.project_receipt(action_id, now=now)
        allowed = receipt.authority_required and receipt.authority_status == "approved" and receipt.overall_status not in {"unverified", "host_failed"}
        return GateDecision(action_id, allowed, "deployment_authorized" if allowed else "deployment_authority_missing", receipt)

    def can_finalize(self, action_id: str, revision: str, now: datetime | None = None, *, require_authority: bool = False) -> GateDecision:
        """Check one active deployment's health; optionally require dispatch authority.

        Existing observation-only callers remain supported. Claims declaring
        authority always enforce it; consumers that dispatch must use can_dispatch.
        """
        receipt = self.verifier.project_receipt(action_id, now=now)
        rows = self.store.events(action_id)
        observations = active_observations([
            self.store.decode(row)["payload"]
            for row in rows
            if row["event_type"] == "provider_observation"
        ])
        observations = [item for item in observations if item.get("metadata", {}).get("revision") == revision]
        if (require_authority or receipt.authority_required) and receipt.authority_status != "approved":
            return GateDecision(action_id, False, "deployment_authority_missing", receipt)
        events = [item.get("provider_event") for item in observations]
        if "rolled_back" in events:
            reason = "deployment_rolled_back"
            allowed = False
        elif "failed" in events:
            reason = "deployment_health_failed"
            allowed = False
        elif "healthy" in events and "accepted" in events and receipt.external_status == "provider_reported_healthy" and receipt.overall_status not in {"unverified", "authority_violation", "provider_conflict", "host_failed"}:
            reason = "deployment_health_verified"
            allowed = True
        elif "accepted" in events:
            reason = "deployment_health_unverified"
            allowed = False
        else:
            reason = "deployment_acceptance_missing"
            allowed = False
        return GateDecision(action_id, allowed, reason, receipt)
