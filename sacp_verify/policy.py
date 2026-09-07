"""Claim-specific evidence rules for the release-gate MVP."""

from __future__ import annotations

from typing import Any


def claim_evidence_satisfied(claim: dict[str, Any], events_by_id: dict[str, dict[str, Any]]) -> bool:
    """Return true only when the claim references matching, sufficient evidence."""
    claim_type = claim.get("claim_type")
    if claim_type == "tests_passed":
        return _has_host_event(claim, events_by_id, _valid_ci_check, claim.get("metadata", {}).get("commit"))
    if claim_type == "artifact_built":
        return _has_host_event(claim, events_by_id, _valid_artifact, claim.get("metadata", {}).get("commit"))
    if claim_type == "ready_to_publish":
        return (
            _has_host_event(claim, events_by_id, _valid_ci_check, claim.get("metadata", {}).get("commit"))
            and _has_host_event(claim, events_by_id, _valid_artifact, claim.get("metadata", {}).get("commit"))
        )
    return True


def _has_host_event(
    claim: dict[str, Any],
    events_by_id: dict[str, dict[str, Any]],
    predicate: object,
    commit: str | None,
) -> bool:
    for reference in claim.get("evidence_refs", []):
        event = events_by_id.get(reference)
        if not event or event["event_type"] != "host_observation":
            continue
        if callable(predicate) and predicate(event["payload"], commit):
            return True
    return False


def _valid_ci_check(payload: dict[str, Any], commit: str | None) -> bool:
    details = payload.get("payload", {})
    if payload.get("kind") == "test_run":
        return details.get("exit_code") == 0 and bool(details.get("output_digest"))
    return (
        payload.get("kind") == "ci_check"
        and details.get("conclusion") == "success"
        and bool(details.get("check_run_id"))
        and bool(details.get("output_digest"))
        and (commit is None or details.get("head_sha") == commit)
    )


def _valid_artifact(payload: dict[str, Any], commit: str | None) -> bool:
    details = payload.get("payload", {})
    return (
        payload.get("kind") == "artifact"
        and bool(details.get("artifact_name"))
        and bool(details.get("digest"))
        and (commit is None or details.get("commit") == commit)
    )
