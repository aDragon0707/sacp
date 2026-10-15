"""No-model Pi probe, trace inspection and explicitly opted-in fixture acceptance."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .acceptance import verify_source
from .evaluate import evaluate_trace
from .pi import digest, parse_trace, probe_pi, read_bounded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("probe", help="get installed Pi version and RPC state; no prompt/model calls")
    probe.add_argument("--node", type=Path, required=True)
    probe.add_argument("--pi-cli", type=Path, required=True)
    inspect = commands.add_parser("inspect", help="inspect a saved JSON-mode trace without executing code")
    inspect.add_argument("--trace", type=Path, required=True)
    inspect.add_argument("--process-exit-code", type=int, required=True)
    verify = commands.add_parser("verify-local", help="run a trusted local fixture oracle, then evaluate an explicitly selected test claim")
    verify.add_argument("--trace", type=Path, required=True)
    verify.add_argument("--process-exit-code", type=int, required=True)
    verify.add_argument("--contract", type=Path, required=True)
    verify.add_argument("--source", type=Path, required=True)
    verify.add_argument("--delivery-digest", required=True, help="source snapshot digest recorded at delivery by the trusted caller")
    verify.add_argument("--claim-text", required=True, help="exact substring selected by caller as a tests_passed claim")
    verify.add_argument("--allow-local-execution", action="store_true", help="execute trusted fixture code locally; this is not a sandbox")
    verify.add_argument("--timeout", type=float, default=15)
    for command in (probe, inspect, verify):
        command.add_argument("--output", type=Path, help="new report path; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        if args.output and args.output.exists():
            raise ValueError("output already exists")
        if args.command == "probe":
            result = probe_pi(args.node, args.pi_cli)
            passed = result["rpc_get_state"] == "passed"
        else:
            raw = read_bounded(args.trace)
            if args.command == "inspect":
                result = parse_trace(raw)
                result["process_exit_code"] = args.process_exit_code
                passed = result["status"] == "complete" and args.process_exit_code == 0
            else:
                acceptance = verify_source(args.contract, args.source, allow_local_execution=args.allow_local_execution, timeout=args.timeout, trace_digest=digest(raw))
                result = evaluate_trace(raw, acceptance, process_exit_code=args.process_exit_code, delivery_digest=args.delivery_digest, claim_text=args.claim_text)
                passed = result["allowed"]
        encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(encoded)
        print(encoded, end="")
        return 0 if passed else 1
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "error", "error_type": type(error).__name__, "message": "input, execution or transport validation failed; no successful evaluation was produced"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
