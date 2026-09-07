"""Public domain models for evidence-bounded completion receipts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Literal


def _as_tuple(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    return tuple(values or ())


@dataclass(frozen=True)
class Claim:
    action_id: str
    claim_type: str
    text: str
    thread_id: str
    run_id: str
    checkpoint_id: str
    input_digest: str | None = None
    actor: str = "agent"
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
    requires_authority: bool = False
    action_scope: str | None = None
    attestation_deadline: datetime | None = None
    reconciliation_owner: str | None = None
    next_check_at: datetime | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_refs", _as_tuple(self.evidence_refs))


@dataclass(frozen=True)
class HostObservation:
    action_id: str
    kind: str
    source: str
    thread_id: str
    run_id: str
    checkpoint_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    observed_at: datetime | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True)
class ProviderObservation:
    action_id: str
    provider: str
    receipt_id: str
    provider_event: str
    observed_at: datetime
    raw_digest: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthorityDecision:
    action_id: str
    decision: Literal["approved", "denied", "pending", "revoked"]
    owner: str
    thread_id: str
    run_id: str
    checkpoint_id: str
    input_digest: str
    action_scope: str
    expires_at: datetime
    decided_at: datetime | None = None
    rationale: str | None = None


@dataclass(frozen=True)
class ReconciliationEvent:
    action_id: str
    result: Literal["attested", "absent", "provider_error"]
    checked_at: datetime
    owner: str
    next_check_at: datetime | None = None
    attempt: int = 1
    max_attempts: int = 1
    route: Literal["none", "retry", "compensation", "human_review"] = "none"


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    retry_delay: timedelta = timedelta(minutes=5)
    compensation_owner: str | None = None

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.retry_delay.total_seconds() <= 0:
            raise ValueError("retry_delay must be positive")


@dataclass(frozen=True)
class DerivedReceipt:
    action_id: str
    host_status: str
    authority_status: str
    external_status: str
    overall_status: str
    claim_refs: tuple[str, ...]
    host_evidence_refs: tuple[str, ...]
    provider_evidence_refs: tuple[str, ...]
    authority_ref: str | None
    authority_required: bool
    next_action_owner: str | None
    retry_allowed: bool
    recovery_route: str
    next_check_at: datetime | None
    derived_at: datetime

    @property
    def status(self) -> str:
        """Compatibility alias for callers migrating to overall_status."""
        return self.overall_status

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "status": self.overall_status,
            "host_status": self.host_status,
            "authority_status": self.authority_status,
            "external_status": self.external_status,
            "overall_status": self.overall_status,
            "claim_refs": list(self.claim_refs),
            "host_evidence_refs": list(self.host_evidence_refs),
            "provider_evidence_refs": list(self.provider_evidence_refs),
            "authority_ref": self.authority_ref,
            "authority_required": self.authority_required,
            "next_action_owner": self.next_action_owner,
            "retry_allowed": self.retry_allowed,
            "recovery_route": self.recovery_route,
            "next_check_at": self.next_check_at.isoformat() if self.next_check_at else None,
            "derived_at": self.derived_at.isoformat(),
        }


@dataclass(frozen=True)
class GateDecision:
    action_id: str
    allowed: bool
    reason: str
    receipt: DerivedReceipt

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "allowed": self.allowed,
            "reason": self.reason,
            "receipt": self.receipt.as_dict(),
        }
