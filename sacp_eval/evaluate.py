"""Bind an explicitly selected Pi claim to independently rerun host evidence."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sacp_verify import Claim, EventStore, HostObservation, Verifier

from .pi import digest, parse_trace


def evaluate_trace(raw: bytes, acceptance: dict[str, Any], *, process_exit_code: int | None, delivery_digest: str, claim_text: str | None = None) -> dict[str, Any]:
    """Evaluate only a caller-selected tests_passed claim, never infer NLP truth.

    Acceptance is a trusted-caller input from verify_source, not a Pi artifact.
    Loaded reports are unauthenticated replay data. This is an experimental result,
    not an official SACP/0.1 or GitHub receipt, approval, or release authorization.
    """
    trace = parse_trace(raw)
    errors = list(trace["errors"])
    if type(process_exit_code) is not int or process_exit_code != 0:
        errors.append("pi_process_did_not_exit_successfully")
    if acceptance.get("trace_digest") != trace["events_digest"]:
        errors.append("acceptance_trace_mismatch")
    if not delivery_digest or acceptance.get("snapshot_digest") != delivery_digest:
        errors.append("acceptance_delivery_mismatch")
    selected = bool(claim_text) and claim_text in trace["final_text"]
    if not selected:
        errors.append("explicit_claim_selection_required")
    result = acceptance.get("results", {})
    if not isinstance(result, dict):
        result = {}
    host_passed = (
        acceptance.get("schema") == "sacp-task-acceptance/1"
        and acceptance.get("status") == "passed"
        and type(acceptance.get("exit_code")) is int and acceptance["exit_code"] == 0
        and acceptance.get("timed_out") is False and acceptance.get("output_oversized") is False
        and isinstance(acceptance.get("snapshot_digest"), str)
        and acceptance["snapshot_digest"].startswith("sha256:")
        and bool(acceptance.get("contract_digest")) and bool(acceptance.get("output_digest"))
        and type(result.get("total")) is int and result["total"] > 0
        and all(type(result.get(key)) is int and result[key] == 0 for key in ("failures", "errors", "skipped", "expected_failures", "unexpected_successes"))
    )
    if not host_passed:
        errors.append("independent_acceptance_not_passed")
    now = datetime.now(timezone.utc)
    identity = digest(raw + str(acceptance.get("snapshot_digest")).encode("utf-8"))
    context = dict(action_id=identity, thread_id=str(trace["session_id"] or "unknown"), run_id=identity, checkpoint_id=str(acceptance.get("snapshot_digest", "unknown")))
    store = EventStore()
    try:
        evidence = ()
        if not errors:
            event_id = store.record_host_observation(HostObservation(**context, kind="test_run", source="sacp-eval-independent-acceptance", payload={"exit_code": 0, "output_digest": acceptance["output_digest"], "commit": acceptance["snapshot_digest"], "contract_digest": acceptance["contract_digest"]}, observed_at=now))
            evidence = (event_id,)
        store.append_claim(Claim(**context, claim_type="tests_passed", text=claim_text or "Unclassified final response", actor="pi", evidence_refs=evidence, metadata={"commit": acceptance.get("snapshot_digest"), "claim_selection": "explicit caller classification; not automatic extraction"}, created_at=now))
        receipt = Verifier(store).project_receipt(identity, now).as_dict()
    finally:
        store.close()
    return {
        "schema": "sacp-agent-evaluation/1", "mode": "caller-supplied trace replay",
        "trace": trace, "pi_exit_code": process_exit_code,
        "acceptance": acceptance, "delivery_digest": delivery_digest, "selected_claim": claim_text,
        "claim_type": "tests_passed" if selected else "unclassified",
        "allowed": not errors and receipt["overall_status"] == "host_completed",
        "errors": sorted(set(errors)), "derived_receipt": receipt,
        "human_decision_required": True,
        "scope": "selected test claim for copied source files; not general task correctness or release authorization",
    }
