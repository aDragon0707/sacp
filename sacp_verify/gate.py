"""Execution gate that turns a derived receipt into an allow/block decision."""

from __future__ import annotations

from datetime import datetime

from .model import GateDecision
from .store import EventStore
from .verifier import Verifier


class ReleaseGate:
    """Allow release only when evidence and current authority are both ready."""

    def __init__(self, store: EventStore, verifier: Verifier) -> None:
        self.store = store
        self.verifier = verifier

    def can_proceed(self, action_id: str, now: datetime | None = None) -> GateDecision:
        receipt = self.verifier.project_receipt(action_id, now=now)
        claims = [
            self.store.decode(row)["payload"]
            for row in self.store.events(action_id)
            if row["event_type"] == "claim"
        ]
        if not any(claim.get("claim_type") == "ready_to_publish" for claim in claims):
            return GateDecision(action_id, False, "ready_to_publish_claim_missing", receipt)
        if receipt.overall_status == "ready_for_external_action":
            return GateDecision(action_id, True, "release_evidence_and_authority_verified", receipt)
        reasons = {
            "needs_approval": "release_approval_missing_or_stale",
            "unverified": "release_evidence_missing_or_invalid",
            "authority_violation": "external_action_observed_without_approval",
            "host_failed": "release_host_evidence_failed",
            "provider_error": "release_provider_error",
        }
        return GateDecision(action_id, False, reasons.get(receipt.overall_status, receipt.overall_status), receipt)
