"""Run explicit Pi-format fixtures through independent acceptance; no model calls."""
from __future__ import annotations

from pathlib import Path

from sacp_eval.acceptance import snapshot_digest, verify_source
from sacp_eval.evaluate import evaluate_trace
from sacp_eval.pi import digest


def main() -> int:
    fixtures = Path(__file__).with_name("pi_eval")
    raw = (fixtures / "scripted-events.jsonl").read_bytes()
    print("Scripted Pi-format replay, not a real agent run; zero model calls.")
    checks = []
    for name, expected in (("candidate_good", True), ("candidate_bad", False)):
        source = fixtures / name
        # The trusted outer caller records delivery before running acceptance.
        delivery = snapshot_digest({"calculator.py": (source / "calculator.py").read_bytes()})
        acceptance = verify_source(fixtures / "task.json", source, allow_local_execution=True, trace_digest=digest(raw))
        result = evaluate_trace(raw, acceptance, process_exit_code=0, delivery_digest=delivery, claim_text="All tests passed.")
        checks.append(result["allowed"] == expected)
        print(f"{name}: acceptance={acceptance['status']}, allowed={result['allowed']}, overall={result['derived_receipt']['overall_status']}")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
