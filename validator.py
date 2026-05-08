#!/usr/bin/env python3
"""
Minimal SACP/0.1 validator.

This script intentionally validates only the text-first MVP rules. It is not a
runtime, security boundary, or factual verifier.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PROTOCOL = "SACP/0.1"

METHODS = {
    "READ",
    "CLAIM",
    "COMPLETE",
    "FAIL",
    "BLOCK",
    "RETRY",
    "PROPOSE",
    "PROMOTE",
}

RESOURCE_TYPES = {
    "task",
    "handoff",
    "attempt",
    "receipt",
    "claim",
    "memory_item",
    "skill_candidate",
    "human_decision",
}

STATUS_CODES = {
    200: "completed",
    202: "accepted_processing",
    204: "no_action_needed",
    301: "superseded_by_human_decision",
    400: "invalid_packet",
    409: "duplicate_handoff",
    412: "missing_evidence",
    423: "lease_active",
    500: "agent_error",
    504: "lease_expired",
}

CLAIM_TYPES = {
    "user_statement",
    "retrieved_fact",
    "tool_result",
    "inference",
}

SUPPORT_STATUS = {
    "supported",
    "unsupported",
    "unverified",
    "not_applicable",
}

VERIFICATION_STATUS = {
    "passed",
    "failed",
    "not_run",
    "blocked",
}

ENVELOPE_REQUIRED = {
    "protocol",
    "type",
    "method",
    "resource_type",
    "resource_id",
    "handoff_id",
    "attempt_id",
    "agent_id",
    "created_at",
    "source_fingerprint",
    "content_type",
}

RECEIPT_REQUIRED = {
    "protocol",
    "type",
    "method",
    "status_code",
    "handoff_id",
    "attempt_id",
    "agent_id",
    "claims",
    "verification",
    "next_owner",
    "human_decision_required",
}

CORE_FIELDS = ENVELOPE_REQUIRED | RECEIPT_REQUIRED


def load_yaml(path: Path) -> tuple[Any, list[str]]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")), []
    except Exception as exc:  # pragma: no cover - useful for CLI diagnostics
        return None, [f"YAML parse error: {exc}"]


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def check_extension_overrides(packet: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    extensions = packet.get("extensions")
    if extensions is None:
        return
    if not isinstance(extensions, dict):
        errors.append("extensions must be a map when present")
        return
    for key in extensions:
        last_segment = str(key).split(".")[-1]
        if last_segment in CORE_FIELDS or str(key).startswith("sacp.core."):
            errors.append(f"extension must not override or hide core field: {key}")
        elif "." not in str(key):
            warnings.append(f"extension key should be namespaced: {key}")


def check_common_packet(packet: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    if packet.get("protocol") != PROTOCOL:
        errors.append(f"protocol must be {PROTOCOL}")

    method = packet.get("method")
    if method is not None and method not in METHODS:
        errors.append(f"unknown method: {method}")

    resource_type = packet.get("resource_type")
    if resource_type is not None and resource_type not in RESOURCE_TYPES:
        errors.append(f"unknown resource_type: {resource_type}")

    check_extension_overrides(packet, errors, warnings)


def check_envelope(packet: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    missing = sorted(field for field in ENVELOPE_REQUIRED if field not in packet)
    for field in missing:
        errors.append(f"missing envelope field: {field}")

    if packet.get("type") != "handoff":
        errors.append("envelope type must be handoff")

    if packet.get("lease_owner") and not packet.get("lease_expires_at"):
        warnings.append("lease_owner exists without lease_expires_at")

    check_common_packet(packet, errors, warnings)


def check_claims(packet: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    claims = packet.get("claims")
    if not isinstance(claims, list):
        errors.append("claims must be a list")
        return
    if not claims:
        warnings.append("claims list is empty; ensure this is intentional")
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"claim[{index}] must be a map")
            continue
        for field in ("text", "claim_type", "source_id", "support_status"):
            if field not in claim:
                errors.append(f"claim[{index}] missing field: {field}")
        claim_type = claim.get("claim_type")
        support_status = claim.get("support_status")
        source_id = claim.get("source_id")
        if claim_type is not None and claim_type not in CLAIM_TYPES:
            errors.append(f"claim[{index}] unknown claim_type: {claim_type}")
        if support_status is not None and support_status not in SUPPORT_STATUS:
            errors.append(f"claim[{index}] unknown support_status: {support_status}")
        if support_status == "supported" and source_id in (None, "", "none", "null"):
            errors.append(f"claim[{index}] is supported but has no source_id")
        if claim_type == "retrieved_fact" and source_id in (None, "", "none", "null"):
            errors.append(f"claim[{index}] retrieved_fact requires source_id")


def check_verification(packet: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    verification = packet.get("verification")
    if not isinstance(verification, dict):
        errors.append("verification must be a map")
        return

    status = verification.get("status")
    if status not in VERIFICATION_STATUS:
        errors.append(f"unknown verification.status: {status}")
    if "method" not in verification:
        errors.append("verification missing field: method")
    if status == "not_run" and "reason" not in verification:
        warnings.append("verification.status is not_run but reason is missing")


def check_next_owner(packet: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    next_owner = packet.get("next_owner")
    if not isinstance(next_owner, str) or not next_owner.strip():
        errors.append("next_owner must be a non-empty string")
        return
    if next_owner.strip().lower() in {"someone", "later", "unknown", "tbd"}:
        errors.append(f"next_owner is ambiguous: {next_owner}")


def check_receipt(packet: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    missing = sorted(field for field in RECEIPT_REQUIRED if field not in packet)
    for field in missing:
        errors.append(f"missing receipt field: {field}")

    if packet.get("type") != "receipt":
        errors.append("receipt type must be receipt")

    status_code = packet.get("status_code")
    if status_code not in STATUS_CODES:
        errors.append(f"unknown status_code: {status_code}")

    if not isinstance(packet.get("human_decision_required"), bool):
        errors.append("human_decision_required must be boolean")

    check_common_packet(packet, errors, warnings)
    check_claims(packet, errors, warnings)
    check_verification(packet, errors, warnings)
    check_next_owner(packet, errors, warnings)


def check_dirty_case(packet: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    if "expected_result" not in packet:
        errors.append("dirty case missing expected_result")
        return
    expected = packet["expected_result"]
    if not isinstance(expected, dict):
        errors.append("expected_result must be a map")
        return
    if expected.get("status_code") not in STATUS_CODES:
        errors.append(f"dirty case has unknown expected status_code: {expected.get('status_code')}")
    if not expected.get("required_fix"):
        errors.append("dirty case expected_result missing required_fix")


def validate_document(path: Path) -> dict[str, Any]:
    data, load_errors = load_yaml(path)
    errors = list(load_errors)
    warnings: list[str] = []

    if load_errors:
        return result(path, errors, warnings)
    if not isinstance(data, dict):
        errors.append("top-level YAML value must be a map")
        return result(path, errors, warnings)

    if "case_id" in data:
        check_dirty_case(data, errors, warnings)
    elif data.get("type") == "receipt":
        check_receipt(data, errors, warnings)
    elif data.get("type") == "handoff":
        check_envelope(data, errors, warnings)
    else:
        errors.append("document must be a handoff, receipt, or dirty case")

    return result(path, errors, warnings)


def result(path: Path, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "file": str(path),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def example_paths(root: Path) -> list[Path]:
    return sorted((root / "examples").glob("*.yaml"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SACP/0.1 YAML files.")
    parser.add_argument("paths", nargs="*", type=Path, help="YAML files to validate")
    parser.add_argument("--examples", action="store_true", help="Validate all examples/*.yaml")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Print JSON results")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    paths = list(args.paths)
    if args.examples:
        paths.extend(example_paths(root))
    if not paths:
        parser.error("provide at least one YAML path or --examples")

    results = [validate_document(path if path.is_absolute() else root / path) for path in paths]

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for item in results:
            status = "PASS" if item["valid"] and (not args.strict or not item["warnings"]) else "FAIL"
            print(f"{status} {item['file']}")
            for error in item["errors"]:
                print(f"  error: {error}")
            for warning in item["warnings"]:
                print(f"  warning: {warning}")

    failed = any(not item["valid"] or (args.strict and item["warnings"]) for item in results)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
