"""Evidence validation and conservative receipt projection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .model import DerivedReceipt
from .policy import claim_evidence_satisfied as policy_satisfies_evidence
from .store import EventStore


def _dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class Verifier:
    """Derives status from stored observations; status is never caller-supplied."""

    def __init__(self, store: EventStore) -> None:
        self.store = store

    def project_receipt(self, action_id: str, now: datetime | None = None) -> DerivedReceipt:
        derived_at = now or datetime.now(timezone.utc)
        rows = self.store.events(action_id)
        claims: list[tuple[str, dict[str, Any]]] = []
        hosts: list[tuple[str, dict[str, Any]]] = []
        providers: list[tuple[str, dict[str, Any]]] = []
        authorities: list[tuple[str, dict[str, Any]]] = []
        reconciliations: list[dict[str, Any]] = []
        for row in rows:
            decoded = self.store.decode(row)
            if decoded["event_type"] == "claim":
                claims.append((decoded["event_id"], decoded["payload"]))
            elif decoded["event_type"] == "host_observation":
                hosts.append((decoded["event_id"], decoded["payload"]))
            elif decoded["event_type"] == "provider_observation":
                providers.append((decoded["event_id"], decoded["payload"]))
            elif decoded["event_type"] == "authority_decision":
                authorities.append((decoded["event_id"], decoded["payload"]))
            elif decoded["event_type"] == "reconciliation":
                reconciliations.append(decoded["payload"])

        events_by_id = {row["event_id"]: self.store.decode(row) for row in rows}
        evidence_refs_valid = all(
            evidence_ref in events_by_id
            for _, payload in claims
            for evidence_ref in payload.get("evidence_refs", [])
        )
        claim_evidence_satisfied = all(
            policy_satisfies_evidence(payload, events_by_id)
            for _, payload in claims
        )
        required = any(bool(payload.get("requires_authority")) for _, payload in claims)
        matching_authority, authority_status = self._authority_state(
            authorities, claims, now=derived_at, required=required
        )
        authority_ref = matching_authority[0] if matching_authority else None
        owner = self._owner(claims, matching_authority)

        host_status = self._host_status(hosts, claims, events_by_id)
        external_status = self._provider_status(providers)
        if external_status is None and any(item.get("result") == "absent" for item in reconciliations):
            external_status = "attestation_timed_out"
        if external_status is None:
            external_status = "not_attempted"
        latest_reconciliation = reconciliations[-1] if reconciliations else None
        recovery_route = (latest_reconciliation or {}).get("route", "none")
        next_check_at = _dt((latest_reconciliation or {}).get("next_check_at"))
        if providers:
            recovery_route = "none"
            next_check_at = None
        if latest_reconciliation and recovery_route in {"retry", "compensation", "human_review"}:
            owner = latest_reconciliation.get("owner") or owner
        overall_status = self._overall_status(
            claims=claims,
            host_status=host_status,
            authority_status=authority_status,
            external_status=external_status,
            evidence_refs_valid=evidence_refs_valid,
            claim_evidence_satisfied=claim_evidence_satisfied,
        )
        if not evidence_refs_valid or not claim_evidence_satisfied:
            overall_status = "unverified"

        retry_allowed = (
            external_status in {"undelivered", "provider_error", "attestation_timed_out"}
            and recovery_route in {"none", "retry"}
        )
        return DerivedReceipt(
            action_id=action_id,
            host_status=host_status,
            authority_status=authority_status,
            external_status=external_status,
            overall_status=overall_status,
            claim_refs=tuple(event_id for event_id, _ in claims),
            host_evidence_refs=tuple(event_id for event_id, _ in hosts),
            provider_evidence_refs=tuple(event_id for event_id, _ in providers),
            authority_ref=authority_ref,
            authority_required=required,
            next_action_owner=owner,
            retry_allowed=retry_allowed,
            recovery_route=recovery_route,
            next_check_at=next_check_at,
            derived_at=derived_at,
        )

    @staticmethod
    def _overall_status(
        *,
        claims: list[tuple[str, dict[str, Any]]],
        host_status: str,
        authority_status: str,
        external_status: str,
        evidence_refs_valid: bool,
        claim_evidence_satisfied: bool,
    ) -> str:
        if not claims:
            return "unknown"
        if not evidence_refs_valid or not claim_evidence_satisfied:
            return "unverified"
        if (
            any(bool(payload.get("requires_authority")) for _, payload in claims)
            and authority_status != "approved"
            and external_status != "not_attempted"
        ):
            return "authority_violation"
        if external_status != "not_attempted":
            return external_status
        if host_status == "failed":
            return "host_failed"
        if authority_status in {"pending", "mismatched", "expired"}:
            return "needs_approval"
        if authority_status == "denied":
            return "authority_denied"
        if authority_status == "approved":
            return "ready_for_external_action"
        if host_status == "completed":
            return "host_completed"
        return "unverified"

    @staticmethod
    def _provider_status(providers: list[tuple[str, dict[str, Any]]]) -> str | None:
        if not providers:
            return None
        events = [payload.get("provider_event") for _, payload in providers]
        if "rolled_back" in events:
            return "deployment_rolled_back"
        if "failed" in events:
            if any(payload.get("provider", "").startswith("mock-refund") for _, payload in providers):
                return "refund_failed"
            return "deployment_failed"
        if "healthy" in events:
            return "provider_reported_healthy"
        if "succeeded" in events:
            return "refund_succeeded"
        if "bounced" in events:
            return "bounced"
        if "unauthorized" in events or "bad_request" in events or "provider_error" in events:
            return "provider_error"
        if "counterparty_declined" in events:
            return "counterparty_declined"
        if "delivered" in events:
            return "provider_reported_delivered"
        if "accepted" in events:
            return "transport_accepted"
        return "undelivered"

    @staticmethod
    def _host_status(
        hosts: list[tuple[str, dict[str, Any]]],
        claims: list[tuple[str, dict[str, Any]]],
        events_by_id: dict[str, dict[str, Any]],
    ) -> str:
        if not hosts:
            return "not_observed"
        referenced_ids = {
            reference
            for _, claim in claims
            for reference in claim.get("evidence_refs", [])
        }
        for event_id in referenced_ids:
            event = events_by_id.get(event_id)
            if not event or event["event_type"] != "host_observation":
                continue
            payload = event["payload"]
            details = payload.get("payload", {})
            if payload.get("kind") == "test_run" and details.get("exit_code") == 0 and details.get("output_digest"):
                return "completed"
            if (
                payload.get("kind") == "ci_check"
                and details.get("conclusion") == "success"
                and details.get("check_run_id")
                and details.get("output_digest")
            ):
                return "completed"
        if any(
            payload.get("kind") in {"test_run", "ci_check"}
            and (
                payload.get("payload", {}).get("exit_code", 0) != 0
                or payload.get("payload", {}).get("conclusion") not in {None, "success"}
            )
            for _, payload in hosts
        ):
            return "failed"
        return "unverified"

    @staticmethod
    def _owner(
        claims: list[tuple[str, dict[str, Any]]], authority: tuple[str, dict[str, Any]] | None
    ) -> str | None:
        if authority:
            return authority[1].get("owner")
        for _, payload in claims:
            if payload.get("reconciliation_owner"):
                return payload["reconciliation_owner"]
        return None

    @staticmethod
    def _authority_state(
        authorities: list[tuple[str, dict[str, Any]]],
        claims: list[tuple[str, dict[str, Any]]],
        now: datetime,
        required: bool,
    ) -> tuple[tuple[str, dict[str, Any]] | None, str]:
        if not required:
            return None, "not_required"
        if not authorities:
            return None, "pending"
        claim = claims[-1][1] if claims else {}
        for event_id, decision in reversed(authorities):
            same_scope = (
                decision.get("thread_id") == claim.get("thread_id")
                and decision.get("run_id") == claim.get("run_id")
                and decision.get("checkpoint_id") == claim.get("checkpoint_id")
                and decision.get("action_scope") == claim.get("action_scope")
                and decision.get("input_digest") == claim.get("input_digest")
            )
            if not same_scope:
                continue
            decision_type = decision.get("decision")
            if decision_type in {"denied", "revoked"}:
                return (event_id, decision), "denied"
            if decision_type == "approved":
                if _dt(decision.get("expires_at")) and _dt(decision["expires_at"]) <= now:
                    return None, "expired"
                return (event_id, decision), "approved"
            return None, "pending"
        return None, "mismatched"

    # Kept as a narrow compatibility seam for callers that used the old private helper.
    _matching_authority = _authority_state
