"""SACP harness — run the 8 breaker cases through the reference engine.

Usage:
    python -m sacp_harness.run            # print + write report
    python -m sacp_harness.run --json     # also print machine-readable JSON

Each case answers one question: an agent claims "done"; a trace/observability
tool records that claim verbatim and never vetoes it; what does SACP project?
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from glob import glob
from pathlib import Path

from sacp_verify import (
    AuthorityDecision,
    Claim,
    DeploymentGate,
    EventStore,
    HostObservation,
    MockDeploymentProvider,
    MockProvider,
    MockRefundProvider,
    Reconciler,
    RefundGate,
    RetryPolicy,
    Verifier,
)

BASE = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# Scenario builders. Each runs against a fresh EventStore and returns the
# projected overall_status plus a short "what a trace records" note.
# --------------------------------------------------------------------------- #

def _claim(store, action_id, text, **kw):
    claim_type = kw.pop("claim_type", "tests_passed")
    store.append_claim(
        Claim(
            action_id=action_id,
            claim_type=claim_type,
            text=text,
            thread_id="harness-thread",
            run_id="harness-run",
            checkpoint_id="harness-checkpoint",
            created_at=BASE,
            **kw,
        )
    )


def s1_missing_evidence():
    """Case 05 / breaker 1: 'tests passed' with no evidence at all."""
    store = EventStore()
    try:
        _claim(store, "s1", "Done. All tests passed. Ready to publish.")
        status = Verifier(store).project_receipt("s1", BASE + timedelta(minutes=1)).overall_status
    finally:
        store.close()
    return status, "trace records 'tests passed' verbatim; no veto"


def s2_deploy_exit0_no_health():
    """breaker 2: deploy accepted, but no provider health evidence."""
    store = EventStore()
    try:
        store.append_claim(
            Claim(
                action_id="s2", claim_type="deployed", text="Deployed to production.",
                thread_id="harness-thread", run_id="harness-run", checkpoint_id="harness-checkpoint",
                created_at=BASE,
            )
        )
        MockDeploymentProvider(store).emit("s2", "accepted", "dep-1", "rev-a", BASE)
        gate = DeploymentGate(store, Verifier(store)).can_finalize("s2", "rev-a", now=BASE + timedelta(minutes=1))
        status = f"{gate.receipt.overall_status} (finalize={gate.allowed}: {gate.reason})"
    finally:
        store.close()
    return status, "trace records 'deploy accepted'; no health veto"


def s3_accepted_not_delivered():
    """breaker 3: provider accepted is not delivery."""
    store = EventStore()
    try:
        _claim(store, "s3", "Notification sent to user.", claim_type="notification_sent")
        MockProvider(store).emit("s3", "accepted", "prov-3", BASE)
        status = Verifier(store).project_receipt("s3", BASE + timedelta(minutes=1)).overall_status
    finally:
        store.close()
    return status, "trace records 'accepted'; observability calls it done, SACP calls it transport_accepted"


def s4_delivered_then_bounced():
    """breaker 3b: a later bounce must degrade the final state."""
    store = EventStore()
    try:
        _claim(store, "s4", "Notification delivered.", claim_type="notification_sent")
        p = MockProvider(store)
        p.emit("s4", "accepted", "prov-4", BASE)
        p.emit("s4", "delivered", "prov-4", BASE + timedelta(minutes=1))
        p.emit("s4", "bounced", "prov-4", BASE + timedelta(minutes=2))
        status = Verifier(store).project_receipt("s4", BASE + timedelta(minutes=3)).overall_status
    finally:
        store.close()
    return status, "trace keeps all three records; SACP re-projects to 'bounced', never freezes at 'delivered'"


def s5_deadline_no_witness():
    """breaker 5: workflow dies; an independent reconciler must keep converging."""
    store = EventStore()
    try:
        _claim(
            store, "s5", "Notification sent.",
            claim_type="notification_sent",
            attestation_deadline=BASE + timedelta(minutes=5),
            reconciliation_owner="harness-recon-queue",
        )
        reconciler = Reconciler(
            store,
            Verifier(store),
            RetryPolicy(max_attempts=2, retry_delay=timedelta(minutes=5), compensation_owner="harness-compensation"),
        )
        reconciler.reconcile(BASE + timedelta(minutes=6))   # attempt 1 -> retry
        reconciler.reconcile(BASE + timedelta(minutes=12))  # attempt 2 -> compensation
        r = Verifier(store).project_receipt("s5", BASE + timedelta(minutes=12))
        status = f"{r.overall_status} (route={r.recovery_route}, owner={r.next_action_owner})"
    finally:
        store.close()
    return status, "trace goes silent after the crash; SACP's reconciler mints deadline/owner, then retry -> compensation"


def s6_stale_approval():
    """breaker 6: an approval bound to the old input must not authorize new input."""
    store = EventStore()
    try:
        _claim(
            store, "s6", "Refund customer order.",
            claim_type="refund_requested",
            requires_authority=True,
            action_scope="refund:order-123",
            input_digest="sha256:new-input",
        )
        store.record_authority_decision(
            AuthorityDecision(
                action_id="s6", decision="approved", owner="reviewer",
                thread_id="harness-thread", run_id="harness-run", checkpoint_id="harness-checkpoint",
                input_digest="sha256:old-input", action_scope="refund:order-123",
                expires_at=BASE + timedelta(hours=1), decided_at=BASE,
            )
        )
        status = Verifier(store).project_receipt("s6", BASE + timedelta(minutes=1)).overall_status
    finally:
        store.close()
    return status, "trace records an approval exists; SACP sees input_digest mismatch and withholds approval"


def s7_retry_double_side_effect():
    """breaker 7: retry must not double-execute a refund."""
    store = EventStore()
    try:
        _claim(
            store, "s7", "Refund issued.",
            claim_type="refund_requested", requires_authority=True,
            action_scope="refund:order-123", input_digest="sha256:in",
        )
        store.record_authority_decision(
            AuthorityDecision(
                action_id="s7", decision="approved", owner="reviewer",
                thread_id="harness-thread", run_id="harness-run", checkpoint_id="harness-checkpoint",
                input_digest="sha256:in", action_scope="refund:order-123",
                expires_at=BASE + timedelta(hours=1), decided_at=BASE,
            )
        )
        provider = MockRefundProvider(store)
        r1 = provider.request("s7", "order-123", 4999, "USD", "idem-1", BASE)
        r2 = provider.request("s7", "order-123", 4999, "USD", "idem-1", BASE + timedelta(minutes=1))
        gate = RefundGate(store, Verifier(store)).can_finalize(
            "s7", {"order_id": "order-123", "amount": 4999, "currency": "USD"}
        )
        idem = "idempotent" if r1 == r2 else "double-spent"
        status = f"{gate.receipt.overall_status} (finalize={gate.allowed}, {idem})"
    finally:
        store.close()
    return status, "trace records two requests; SACP returns the same refund id and refuses finalize without 'succeeded'"


def s8_agent_self_attested():
    """breaker 8: the agent cannot manufacture its own evidence."""
    store = EventStore()
    try:
        _claim(store, "s8", "Tests passed — I verified exit code 0 myself.")
        status = Verifier(store).project_receipt("s8", BASE + timedelta(minutes=1)).overall_status
    finally:
        store.close()
    return status, "trace records the claim (self-declared evidence); SACP requires a host/provider observation, so stays unverified"


SCENARIOS = [
    ("S1", "missing evidence", s1_missing_evidence),
    ("S2", "accepted without health", s2_deploy_exit0_no_health),
    ("S3", "accepted is not delivered", s3_accepted_not_delivered),
    ("S4", "delivered then bounced", s4_delivered_then_bounced),
    ("S5", "deadline without provider witness", s5_deadline_no_witness),
    ("S6", "stale approval reused", s6_stale_approval),
    ("S7", "retry double side-effect", s7_retry_double_side_effect),
    ("S8", "agent self-attested evidence", s8_agent_self_attested),
]

# A case is "vetoed" when SACP does NOT project the false terminal success the
# agent claimed. None of these 8 may project a false success.
FALSE_SUCCESS = {"provider_reported_delivered", "refund_succeeded", "provider_reported_healthy"}


def _vetoed(projected: str) -> bool:
    return not any(fs in projected for fs in FALSE_SUCCESS)


def run_protocol_validator() -> dict:
    """Count PASS/FAIL across spec examples and the 33-receipt corpus."""
    targets = sorted(glob(str(ROOT / "examples" / "*.yaml"))) + sorted(
        glob(str(ROOT / "sample-corpus" / "translated-receipts" / "*.yaml"))
    )
    if not targets:
        return {"total": 0, "pass": 0, "fail": 0, "error": "no targets found"}
    out = subprocess.run(
        [sys.executable, str(ROOT / "validator.py"), *targets],
        capture_output=True, text=True,
    )
    text = out.stdout + out.stderr
    return {
        "total": len(targets),
        "pass": text.count("PASS"),
        "fail": text.count("FAIL") + text.count("ERROR"),
        "error": None if out.returncode == 0 else f"returncode={out.returncode}",
    }


def build_report() -> dict:
    results = []
    for sid, name, fn in SCENARIOS:
        projected, trace_view = fn()
        results.append(
            {
                "id": sid,
                "case": name,
                "trace_view": trace_view,
                "projected": projected,
                "vetoed": _vetoed(projected),
            }
        )
    vetoed = sum(1 for r in results if r["vetoed"])
    proof = run_protocol_validator()
    return {
        "engine": {
            "scenarios": results,
            "vetoed": vetoed,
            "total": len(results),
            "false_success_allowed": len(results) - vetoed,
        },
        "protocol": proof,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _render_md(report: dict) -> str:
    lines = ["# SACP Harness Report", ""]
    engine = report["engine"]
    lines.append(f"**Breaker cases blocked: {engine['vetoed']}/{engine['total']}** · false-success allowed: {engine['false_success_allowed']}")
    lines.append("")
    lines.append("| # | case | what a trace records | what SACP projects | vetoed |")
    lines.append("|---|---|---|---|---|")
    for r in engine["scenarios"]:
        v = "✅" if r["vetoed"] else "❌"
        lines.append(f"| {r['id']} | {r['case']} | {r['trace_view']} | `{r['projected']}` | {v} |")
    lines.append("")
    p = report["protocol"]
    lines.append(f"## Protocol validator · {p['pass']}/{p['total']} receipts PASS ({p['fail']} FAIL)")
    if p.get("error"):
        lines.append(f"  (warning: {p['error']})")
    lines.append("")
    lines.append(f"_generated {report['generated_at']}_")
    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    report = build_report()
    md = _render_md(report)
    (ROOT / "sacp_harness" / "report.md").write_text(md, encoding="utf-8")
    (ROOT / "sacp_harness" / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(md)
    if "--json" in sys.argv:
        print("\n" + json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()