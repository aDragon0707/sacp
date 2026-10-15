"""Run adversarial completion claims through the SACP reference engine.

The default command only prints a report. CI can pass ``--output-dir`` to
materialize JSON and Markdown artifacts outside the tracked source tree.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from sacp_verify import (
    AuthorityDecision,
    Claim,
    DeploymentGate,
    EventStore,
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
ScenarioRunner = Callable[[], tuple[str, str]]
FALSE_TERMINAL_STATUSES = {
    "provider_reported_delivered",
    "refund_succeeded",
    "provider_reported_healthy",
}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    name: str
    runner: ScenarioRunner
    expected_fragments: tuple[str, ...]


def _claim(
    store: EventStore,
    action_id: str,
    text: str,
    **kwargs: object,
) -> None:
    claim_type = str(kwargs.pop("claim_type", "tests_passed"))
    store.append_claim(
        Claim(
            action_id=action_id,
            claim_type=claim_type,
            text=text,
            thread_id="harness-thread",
            run_id="harness-run",
            checkpoint_id="harness-checkpoint",
            created_at=BASE,
            **kwargs,
        )
    )


def _missing_evidence() -> tuple[str, str]:
    store = EventStore()
    try:
        _claim(store, "s1", "Done. All tests passed. Ready to publish.")
        status = Verifier(store).project_receipt(
            "s1", BASE + timedelta(minutes=1)
        ).overall_status
    finally:
        store.close()
    return status, "trace records 'tests passed' verbatim; no evidence veto"


def _accepted_without_health() -> tuple[str, str]:
    store = EventStore()
    try:
        store.append_claim(
            Claim(
                action_id="s2",
                claim_type="deployed",
                text="Deployed to production.",
                thread_id="harness-thread",
                run_id="harness-run",
                checkpoint_id="harness-checkpoint",
                created_at=BASE,
            )
        )
        MockDeploymentProvider(store).emit("s2", "accepted", "dep-1", "rev-a", BASE)
        decision = DeploymentGate(store, Verifier(store)).can_finalize(
            "s2", "rev-a", now=BASE + timedelta(minutes=1)
        )
        status = (
            f"{decision.receipt.overall_status} "
            f"(finalize={decision.allowed}: {decision.reason})"
        )
    finally:
        store.close()
    return status, "trace records 'deploy accepted'; no health veto"


def _accepted_is_not_delivered() -> tuple[str, str]:
    store = EventStore()
    try:
        _claim(store, "s3", "Notification sent to user.", claim_type="notification_sent")
        MockProvider(store).emit("s3", "accepted", "prov-3", BASE)
        status = Verifier(store).project_receipt(
            "s3", BASE + timedelta(minutes=1)
        ).overall_status
    finally:
        store.close()
    return status, "trace records 'accepted'; SACP retains transport acceptance"


def _delivered_then_bounced() -> tuple[str, str]:
    store = EventStore()
    try:
        _claim(store, "s4", "Notification delivered.", claim_type="notification_sent")
        provider = MockProvider(store)
        provider.emit("s4", "accepted", "prov-4", BASE)
        provider.emit("s4", "delivered", "prov-4", BASE + timedelta(minutes=1))
        provider.emit("s4", "bounced", "prov-4", BASE + timedelta(minutes=2))
        status = Verifier(store).project_receipt(
            "s4", BASE + timedelta(minutes=3)
        ).overall_status
    finally:
        store.close()
    return status, "trace retains delivery; SACP re-projects the later bounce"


def _deadline_without_witness() -> tuple[str, str]:
    store = EventStore()
    try:
        _claim(
            store,
            "s5",
            "Notification sent.",
            claim_type="notification_sent",
            attestation_deadline=BASE + timedelta(minutes=5),
            reconciliation_owner="harness-reconciliation",
        )
        reconciler = Reconciler(
            store,
            Verifier(store),
            RetryPolicy(
                max_attempts=2,
                retry_delay=timedelta(minutes=5),
                compensation_owner="harness-compensation",
            ),
        )
        reconciler.reconcile(BASE + timedelta(minutes=6))
        reconciler.reconcile(BASE + timedelta(minutes=12))
        receipt = Verifier(store).project_receipt(
            "s5", BASE + timedelta(minutes=12)
        )
        status = (
            f"{receipt.overall_status} "
            f"(route={receipt.recovery_route}, owner={receipt.next_action_owner})"
        )
    finally:
        store.close()
    return status, "trace goes silent; reconciliation routes bounded recovery"


def _stale_approval() -> tuple[str, str]:
    store = EventStore()
    try:
        _claim(
            store,
            "s6",
            "Refund customer order.",
            claim_type="refund_requested",
            requires_authority=True,
            action_scope="refund:order-123",
            input_digest="sha256:new-input",
        )
        store.record_authority_decision(
            AuthorityDecision(
                action_id="s6",
                decision="approved",
                owner="reviewer",
                thread_id="harness-thread",
                run_id="harness-run",
                checkpoint_id="harness-checkpoint",
                input_digest="sha256:old-input",
                action_scope="refund:order-123",
                expires_at=BASE + timedelta(hours=1),
                decided_at=BASE,
            )
        )
        status = Verifier(store).project_receipt(
            "s6", BASE + timedelta(minutes=1)
        ).overall_status
    finally:
        store.close()
    return status, "trace sees approval; SACP rejects its stale input binding"


def _idempotent_retry() -> tuple[str, str]:
    store = EventStore()
    try:
        _claim(
            store,
            "s7",
            "Refund issued.",
            claim_type="refund_requested",
            requires_authority=True,
            action_scope="refund:order-123",
            input_digest="sha256:refund-input",
        )
        store.record_authority_decision(
            AuthorityDecision(
                action_id="s7",
                decision="approved",
                owner="reviewer",
                thread_id="harness-thread",
                run_id="harness-run",
                checkpoint_id="harness-checkpoint",
                input_digest="sha256:refund-input",
                action_scope="refund:order-123",
                expires_at=BASE + timedelta(hours=1),
                decided_at=BASE,
            )
        )
        provider = MockRefundProvider(store)
        first = provider.request("s7", "order-123", 4999, "USD", "idem-1", BASE)
        second = provider.request(
            "s7", "order-123", 4999, "USD", "idem-1", BASE + timedelta(minutes=1)
        )
        decision = RefundGate(store, Verifier(store)).can_finalize(
            "s7", {"order_id": "order-123", "amount": 4999, "currency": "USD"}, now=BASE + timedelta(minutes=1)
        )
        idempotency = "idempotent" if first == second else "duplicate"
        status = (
            f"{decision.receipt.overall_status} "
            f"(finalize={decision.allowed}, {idempotency})"
        )
    finally:
        store.close()
    return status, "trace sees two requests; SACP preserves one refund identity"


def _self_attested_evidence() -> tuple[str, str]:
    store = EventStore()
    try:
        _claim(store, "s8", "Tests passed; I verified exit code 0 myself.")
        status = Verifier(store).project_receipt(
            "s8", BASE + timedelta(minutes=1)
        ).overall_status
    finally:
        store.close()
    return status, "trace records self-attestation; SACP requires an observation"


SCENARIOS = (
    Scenario("S1", "missing evidence", _missing_evidence, ("unverified",)),
    Scenario(
        "S2",
        "accepted without health",
        _accepted_without_health,
        ("transport_accepted", "finalize=False", "deployment_health_unverified"),
    ),
    Scenario(
        "S3",
        "accepted is not delivered",
        _accepted_is_not_delivered,
        ("transport_accepted",),
    ),
    Scenario("S4", "delivered then bounced", _delivered_then_bounced, ("bounced",)),
    Scenario(
        "S5",
        "deadline without provider witness",
        _deadline_without_witness,
        ("attestation_timed_out", "route=compensation", "owner=harness-compensation"),
    ),
    Scenario("S6", "stale approval reused", _stale_approval, ("needs_approval",)),
    Scenario(
        "S7",
        "retry double side-effect",
        _idempotent_retry,
        ("transport_accepted", "finalize=False", "idempotent"),
    ),
    Scenario("S8", "agent self-attested evidence", _self_attested_evidence, ("unverified",)),
)


def run_positive_controls() -> list[dict[str, object]]:
    """Prove the harness also allows supported success, rather than blocking all."""
    store = EventStore()
    try:
        verifier = Verifier(store)
        _claim(store, "positive-notification", "Notification requested", claim_type="notification_sent")
        provider = MockProvider(store)
        provider.emit("positive-notification", "accepted", "positive", BASE)
        provider.emit("positive-notification", "delivered", "positive", BASE + timedelta(minutes=1))
        notification = verifier.project_receipt("positive-notification", BASE).overall_status == "provider_reported_delivered"
        deployment = MockDeploymentProvider(store)
        deployment.emit("positive-deployment", "accepted", "positive", "rev", BASE)
        deployment.emit("positive-deployment", "healthy", "positive", "rev", BASE)
        healthy = DeploymentGate(store, verifier).can_finalize("positive-deployment", "rev", BASE).allowed
        expected = {"order_id": "order", "amount": 100, "currency": "USD"}
        _claim(store, "positive-refund", "Refund requested", claim_type="refund_requested", metadata=expected, requires_authority=True, input_digest="refund-input", action_scope="refund-scope")
        store.record_authority_decision(AuthorityDecision("positive-refund", "approved", "manager", "harness-thread", "harness-run", "harness-checkpoint", "refund-input", "refund-scope", BASE + timedelta(hours=1), BASE))
        refund = MockRefundProvider(store)
        refund_id = refund.request("positive-refund", **expected, idempotency_key="positive", observed_at=BASE)
        refund.webhook("positive-refund", "succeeded", refund_id, **expected, observed_at=BASE)
        succeeded = RefundGate(store, verifier).can_finalize("positive-refund", expected, now=BASE).allowed
        return [{"case": "matching delivery", "passed": notification}, {"case": "matching deployment health", "passed": healthy}, {"case": "authorized matching refund", "passed": succeeded}]
    finally:
        store.close()


def run_protocol_validator() -> dict[str, object]:
    """Validate all public YAML examples and translated receipts in strict mode."""
    targets = sorted((ROOT / "examples").glob("*.yaml"))
    targets += sorted((ROOT / "sample-corpus" / "translated-receipts").glob("*.yaml"))
    if not targets:
        return {"total": 0, "pass": 0, "fail": 0, "error": "no targets found"}

    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "validator.py"),
            "--strict",
            "--json",
            *(str(path) for path in targets),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        results = json.loads(process.stdout)
    except json.JSONDecodeError:
        detail = (process.stderr or process.stdout).strip()
        return {
            "total": len(targets),
            "pass": 0,
            "fail": len(targets),
            "error": f"validator output was not JSON: {detail}",
        }

    passed = sum(
        1
        for item in results
        if item.get("valid") and not item.get("warnings") and not item.get("errors")
    )
    failed = len(results) - passed
    error = None if process.returncode == 0 and failed == 0 else f"returncode={process.returncode}"
    return {"total": len(results), "pass": passed, "fail": failed, "error": error}


def build_report(generated_at: datetime | None = None) -> dict[str, object]:
    """Return a breaker and protocol report without writing to the workspace."""
    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("generated_at must include a timezone")

    results = []
    for scenario in SCENARIOS:
        projected, trace_view = scenario.runner()
        expected = all(fragment in projected for fragment in scenario.expected_fragments)
        false_terminal = any(status in projected for status in FALSE_TERMINAL_STATUSES)
        results.append(
            {
                "id": scenario.scenario_id,
                "case": scenario.name,
                "trace_view": trace_view,
                "projected": projected,
                "vetoed": expected and not false_terminal,
            }
        )

    vetoed = sum(1 for result in results if result["vetoed"])
    return {
        "engine": {
            "scenarios": results,
            "vetoed": vetoed,
            "total": len(results),
            "false_success_allowed": len(results) - vetoed,
        },
        "protocol": run_protocol_validator(),
        "positive_controls": run_positive_controls(),
        "generated_at": timestamp.isoformat(),
    }


def report_passed(report: dict[str, object]) -> bool:
    """Return whether the report satisfies the harness acceptance contract."""
    engine = report["engine"]
    protocol = report["protocol"]
    assert isinstance(engine, dict)
    assert isinstance(protocol, dict)
    return (
        engine.get("total") == len(SCENARIOS)
        and engine.get("vetoed") == engine.get("total")
        and engine.get("false_success_allowed") == 0
        and protocol.get("total", 0) != 0
        and protocol.get("pass") == protocol.get("total")
        and protocol.get("fail") == 0
        and protocol.get("error") is None
        and len(report.get("positive_controls", [])) == 3
        and all(item.get("passed") is True for item in report["positive_controls"])
    )


def render_markdown(report: dict[str, object]) -> str:
    engine = report["engine"]
    protocol = report["protocol"]
    assert isinstance(engine, dict)
    assert isinstance(protocol, dict)
    scenarios = engine["scenarios"]
    assert isinstance(scenarios, list)

    lines = [
        "# SACP Harness Report",
        "",
        f"Breaker cases blocked: {engine['vetoed']}/{engine['total']}; "
        f"false-success allowed: {engine['false_success_allowed']}",
        "",
        "| # | case | trace view | SACP projection | vetoed |",
        "|---|---|---|---|---|",
    ]
    for result in scenarios:
        assert isinstance(result, dict)
        lines.append(
            f"| {result['id']} | {result['case']} | {result['trace_view']} | "
            f"`{result['projected']}` | {'yes' if result['vetoed'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            f"Positive controls passed: {sum(item['passed'] for item in report['positive_controls'])}/3",
            "",
            f"## Protocol validator: {protocol['pass']}/{protocol['total']} strict PASS "
            f"({protocol['fail']} FAIL)",
            "",
            f"Generated at {report['generated_at']}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, object], output_dir: Path) -> tuple[Path, Path]:
    """Write report artifacts to an explicit output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    markdown_path = output_dir / "report.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamp must include a timezone")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Also print JSON output")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write report.json and report.md to this artifact directory",
    )
    parser.add_argument(
        "--generated-at",
        type=_parse_timestamp,
        help="Inject an ISO-8601 timestamp for deterministic output",
    )
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    report = build_report(generated_at=args.generated_at)
    print(render_markdown(report), end="")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.output_dir is not None:
        write_report(report, args.output_dir)
    return 0 if report_passed(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
