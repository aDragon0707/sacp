#!/usr/bin/env python3
"""
Run SACP/0.1 Dirty Run cases across multiple OpenAI-compatible model APIs.

API keys are read from environment variables. Do not commit keys.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "agentops-doctor" / "prompt_skill.md"
DIRTY_CASES_PATH = ROOT / "DIRTY_RUN_CASES.md"
REPORTS_DIR = ROOT / "agentops-doctor" / "reports"


@dataclass(frozen=True)
class ModelConfig:
    name: str
    endpoint: str
    env_key: str
    model: str
    temperature: float
    max_tokens: int = 900
    timeout_sec: int = 90
    disable_thinking: bool = False


DEFAULT_MODELS = [
    ModelConfig(
        name="deepseek_pro",
        endpoint="https://api.deepseek.com/chat/completions",
        env_key="DEEPSEEK_API_KEY",
        model="deepseek-v4-pro",
        temperature=0,
        timeout_sec=75,
    ),
    ModelConfig(
        name="qwen_strong",
        endpoint="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        env_key="QWEN_API_KEY",
        model="qwen3.6-plus",
        temperature=0,
        timeout_sec=75,
    ),
    ModelConfig(
        name="glm_strong",
        endpoint="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        env_key="ZHIPU_API_KEY",
        model="glm-4.7",
        temperature=0,
        max_tokens=1100,
        timeout_sec=75,
        disable_thinking=True,
    ),
    ModelConfig(
        name="kimi_strong",
        endpoint="https://api.moonshot.cn/v1/chat/completions",
        env_key="KIMI_API_KEY",
        model="kimi-k2.6",
        temperature=0.6,
        timeout_sec=90,
        disable_thinking=True,
    ),
]


EXPECTED_CASES = [
    {
        "case_id": "duplicate_handoff",
        "expected_status": 409,
        "input": """
case_id: duplicate_handoff
description: "Same handoff_id and same source_fingerprint were already completed."
incoming_packet:
  protocol: SACP/0.1
  type: handoff
  method: CLAIM
  resource_type: handoff
  resource_id: hf_check_claims_001
  handoff_id: hf_check_claims_001
  attempt_id: attempt_002
  agent_id: AI-02
  created_at: 2026-05-07T21:10:00+08:00
  source_fingerprint: sha256:abc123
  content_type: text/markdown
known_receipt:
  handoff_id: hf_check_claims_001
  attempt_id: attempt_001
  status_code: 200
expected_result:
  status_code: 409
  status_text: duplicate_handoff
  required_fix: "Return or link the existing receipt. Do not redo the work."
""".strip(),
    },
    {
        "case_id": "active_lease_collision",
        "expected_status": 423,
        "input": """
case_id: active_lease_collision
description: "AI-02 tries to claim a handoff while AI-04 holds an active lease."
incoming_packet:
  protocol: SACP/0.1
  type: handoff
  method: CLAIM
  resource_type: handoff
  resource_id: hf_claim_lease_001
  handoff_id: hf_claim_lease_001
  attempt_id: attempt_001
  agent_id: AI-02
  created_at: 2026-05-07T22:10:00+08:00
  source_fingerprint: sha256:leasecase
  content_type: text/markdown
existing_lease:
  lease_owner: AI-04
  lease_expires_at: 2026-05-07T22:40:00+08:00
expected_result:
  status_code: 423
  status_text: lease_active
  required_fix: "Wait for lease expiration, release, or coordinator reassignment."
""".strip(),
    },
    {
        "case_id": "expired_lease",
        "expected_status": 504,
        "input": """
case_id: expired_lease
description: "A lease expired and no receipt exists."
incoming_packet:
  protocol: SACP/0.1
  type: handoff
  method: CLAIM
  resource_type: handoff
  resource_id: hf_expired_lease_001
  handoff_id: hf_expired_lease_001
  attempt_id: attempt_001
  agent_id: AI-04
  created_at: 2026-05-07T20:00:00+08:00
  source_fingerprint: sha256:expiredlease
  content_type: text/markdown
existing_lease:
  lease_owner: AI-04
  lease_expires_at: 2026-05-07T20:30:00+08:00
known_receipt: null
expected_result:
  status_code: 504
  status_text: lease_expired
  required_fix: "Create a new attempt_id under the same handoff_id or reassign."
""".strip(),
    },
    {
        "case_id": "changed_source_fingerprint",
        "expected_status": 202,
        "input": """
case_id: changed_source_fingerprint
description: "A packet reuses handoff_id but source_fingerprint changed."
incoming_packet:
  protocol: SACP/0.1
  type: handoff
  method: RETRY
  resource_type: handoff
  resource_id: hf_claims_001
  handoff_id: hf_claims_001
  attempt_id: attempt_002
  agent_id: AI-04
  created_at: 2026-05-07T22:20:00+08:00
  source_fingerprint: sha256:newsource
  content_type: text/markdown
previous_receipt:
  handoff_id: hf_claims_001
  source_fingerprint: sha256:oldsource
  status_code: 200
expected_result:
  status_code: 202
  status_text: accepted_processing
  required_fix: "Treat as rework, not duplicate."
""".strip(),
    },
    {
        "case_id": "missing_evidence",
        "expected_status": 412,
        "input": """
case_id: missing_evidence
description: "A public claim is marked supported but provides no evidence."
incoming_receipt:
  protocol: SACP/0.1
  type: receipt
  method: COMPLETE
  status_code: 200
  handoff_id: hf_public_claim_001
  attempt_id: attempt_001
  agent_id: AI-04
  claims:
    - text: "SACP guarantees correct agent work."
      claim_type: retrieved_fact
      source_id: none
      support_status: supported
  verification:
    status: passed
    method: "self review"
  next_owner: Human
  human_decision_required: true
expected_result:
  status_code: 412
  status_text: missing_evidence
  required_fix: "Provide a trusted source or downgrade claim_type/support_status."
""".strip(),
    },
    {
        "case_id": "user_statement_as_fact",
        "expected_status": 412,
        "input": """
case_id: user_statement_as_fact
description: "User belief was marked as retrieved_fact."
incoming_receipt:
  protocol: SACP/0.1
  type: receipt
  method: COMPLETE
  status_code: 200
  handoff_id: hf_user_belief_001
  attempt_id: attempt_001
  agent_id: AI-04
  claims:
    - text: "This will beat all big companies."
      claim_type: retrieved_fact
      source_id: founder_chat_message
      support_status: supported
  verification:
    status: passed
    method: "self review"
  next_owner: Human
  human_decision_required: true
expected_result:
  status_code: 412
  status_text: missing_evidence
  required_fix: "Change claim_type to user_statement or provide external evidence."
""".strip(),
    },
    {
        "case_id": "inference_as_retrieved_fact",
        "expected_status": 412,
        "input": """
case_id: inference_as_retrieved_fact
description: "Model inference was marked as retrieved_fact."
incoming_receipt:
  protocol: SACP/0.1
  type: receipt
  method: COMPLETE
  status_code: 200
  handoff_id: hf_competitor_claim_001
  attempt_id: attempt_001
  agent_id: AI-04
  claims:
    - text: "Large vendors do not want to standardize receipt governance."
      claim_type: retrieved_fact
      source_id: model_reasoning_only
      support_status: supported
  verification:
    status: passed
    method: "self review"
  next_owner: Human
  human_decision_required: false
expected_result:
  status_code: 412
  status_text: missing_evidence
  required_fix: "Change claim_type to inference or cite a trusted source."
""".strip(),
    },
    {
        "case_id": "memory_candidate_auto_promoted",
        "expected_status": 412,
        "input": """
case_id: memory_candidate_auto_promoted
description: "Agent auto-promotes pending memory to verified memory."
incoming_packet:
  protocol: SACP/0.1
  type: handoff
  method: PROMOTE
  resource_type: memory_item
  resource_id: mem_strategy_001
  handoff_id: hf_promote_memory_001
  attempt_id: attempt_001
  agent_id: AI-02
  created_at: 2026-05-07T21:20:00+08:00
  source_fingerprint: sha256:def456
  content_type: application/json
  body:
    previous_state: pending_verification
    requested_state: verified
    human_approval_id: null
expected_result:
  status_code: 412
  status_text: missing_evidence
  required_fix: "Keep memory pending and provide approval evidence before PROMOTE."
""".strip(),
    },
    {
        "case_id": "completion_without_receipt",
        "expected_status": 400,
        "input": """
case_id: completion_without_receipt
description: "Agent says done but provides no receipt."
raw_agent_output: |
  Done. I reviewed everything and it looks good.
expected_result:
  status_code: 400
  status_text: invalid_packet
  required_fix: "Produce a SACP receipt with claims, verification, next_owner, and human_decision_required."
""".strip(),
    },
    {
        "case_id": "ambiguous_next_owner",
        "expected_status": 400,
        "input": """
case_id: ambiguous_next_owner
description: "Receipt says work is complete but next_owner is vague."
incoming_receipt:
  protocol: SACP/0.1
  type: receipt
  method: COMPLETE
  status_code: 200
  handoff_id: hf_owner_001
  attempt_id: attempt_001
  agent_id: AI-04
  claims:
    - text: "Review completed."
      claim_type: inference
      source_id: review_notes_001
      support_status: supported
  verification:
    status: passed
    method: "review"
  next_owner: someone
  human_decision_required: false
expected_result:
  status_code: 400
  status_text: invalid_packet
  required_fix: "Set next_owner to a concrete actor, role, coordinator, or Human."
""".strip(),
    },
]


def call_model(config: ModelConfig, api_key: str, prompt: str, case_input: str) -> dict[str, Any]:
    user_content = (
        "Diagnose this SACP/0.1 Dirty Run case. "
        "Return YAML first, concise. Do not execute the underlying task.\n\n"
        f"{case_input}"
    )
    body = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": False,
    }
    if config.disable_thinking:
        body["thinking"] = {"type": "disabled"}
    request = urllib.request.Request(
        config.endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = payload.get("usage") or {}
        return {
            "ok": True,
            "http_status": response.status,
            "content": content,
            "model_returned": payload.get("model"),
            "finish_reason": payload.get("choices", [{}])[0].get("finish_reason"),
            "total_tokens": usage.get("total_tokens"),
            "elapsed_sec": round(time.time() - started, 3),
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "http_status": exc.code,
            "error": exc.read().decode("utf-8", errors="replace")[:1000],
            "elapsed_sec": round(time.time() - started, 3),
        }
    except Exception as exc:  # pragma: no cover - CLI diagnostics
        return {
            "ok": False,
            "http_status": None,
            "error_type": type(exc).__name__,
            "error": str(exc)[:1000],
            "elapsed_sec": round(time.time() - started, 3),
        }


def extract_status(content: str) -> int | None:
    match = re.search(r"status_code\s*:\s*[\"']?(\d{3})[\"']?", content)
    if match:
        return int(match.group(1))
    return None


def extract_yaml_like(content: str) -> dict[str, Any] | None:
    text = content.strip()
    fenced = re.search(r"```(?:yaml|yml)?\s*(.*?)```", text, flags=re.S | re.I)
    if fenced:
        text = fenced.group(1).strip()
    try:
        parsed = yaml.safe_load(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def diagnose_case(model: ModelConfig, api_key: str, prompt: str, case: dict[str, Any]) -> dict[str, Any]:
    response = call_model(model, api_key, prompt, case["input"])
    content = response.get("content", "") if response.get("ok") else ""
    parsed = extract_yaml_like(content) if content else None
    actual_status = extract_status(content)
    expected_status = int(case["expected_status"])
    passed = bool(response.get("ok")) and actual_status == expected_status
    return {
        "case_id": case["case_id"],
        "expected_status": expected_status,
        "actual_status": actual_status,
        "pass": passed,
        "response_ok": response.get("ok"),
        "http_status": response.get("http_status"),
        "finish_reason": response.get("finish_reason"),
        "total_tokens": response.get("total_tokens"),
        "elapsed_sec": response.get("elapsed_sec"),
        "status_text": parsed.get("status_text") if parsed else None,
        "verdict": parsed.get("verdict") if parsed else None,
        "required_fix": parsed.get("required_fix") if parsed else None,
        "excerpt": content[:500] if content else response.get("error"),
    }


def run(models: list[ModelConfig], cases: list[dict[str, Any]], workers: int = 4) -> dict[str, Any]:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    report: dict[str, Any] = {
        "protocol": "SACP/0.1",
        "type": "multi_model_dirty_run_report",
        "tested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "total_cases": len(cases),
        "models": [],
    }
    for model in models:
        api_key = os.environ.get(model.env_key)
        model_report: dict[str, Any] = {
            "name": model.name,
            "model": model.model,
            "endpoint_host": model.endpoint.split("/")[2],
            "env_key": model.env_key,
            "skipped": not bool(api_key),
            "case_results": [],
        }
        if not api_key:
            model_report["skip_reason"] = f"Missing environment variable: {model.env_key}"
            report["models"].append(model_report)
            continue

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            future_to_case = {
                executor.submit(diagnose_case, model, api_key, prompt, case): case
                for case in cases
            }
            for future in concurrent.futures.as_completed(future_to_case):
                item = future.result()
                print(
                    f"{model.name}/{item['case_id']}: "
                    f"{'PASS' if item['pass'] else 'FAIL'} "
                    f"expected={item['expected_status']} actual={item.get('actual_status')}",
                    flush=True,
                )
                model_report["case_results"].append(item)
        model_report["case_results"].sort(key=lambda item: [case["case_id"] for case in cases].index(item["case_id"]))
        model_report["passed"] = sum(1 for item in model_report["case_results"] if item["pass"])
        model_report["failed"] = len(model_report["case_results"]) - model_report["passed"]
        report["models"].append(model_report)

    return report


def write_reports(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    json_path = REPORTS_DIR / f"multi_model_dirty_run_{stamp}.json"
    md_path = REPORTS_DIR / f"multi_model_dirty_run_{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Multi-Model Dirty Run Report",
        "",
        f"- Protocol: `{report['protocol']}`",
        f"- Tested at: `{report['tested_at']}`",
        f"- Total cases: `{report['total_cases']}`",
        "",
        "| Model | Passed | Failed | Notes |",
        "|---|---:|---:|---|",
    ]
    for model in report["models"]:
        if model.get("skipped"):
            lines.append(f"| {model['name']} / `{model['model']}` | 0 | 0 | skipped: {model.get('skip_reason')} |")
        else:
            lines.append(
                f"| {model['name']} / `{model['model']}` | {model.get('passed', 0)} | {model.get('failed', 0)} | endpoint `{model['endpoint_host']}` |"
            )
    lines.extend(["", "## Case Results", ""])
    for model in report["models"]:
        if model.get("skipped"):
            continue
        lines.extend([f"### {model['name']} / `{model['model']}`", ""])
        lines.extend(["| Case | Expected | Actual | Pass | Required Fix Excerpt |", "|---|---:|---:|---:|---|"])
        for item in model["case_results"]:
            fix = str(item.get("required_fix") or item.get("excerpt") or "").replace("\n", " ")
            if len(fix) > 120:
                fix = fix[:117] + "..."
            lines.append(
                f"| {item['case_id']} | {item['expected_status']} | {item.get('actual_status')} | {item['pass']} | {fix} |"
            )
        lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SACP Dirty Run cases across multiple model APIs.")
    parser.add_argument("--model", action="append", choices=[m.name for m in DEFAULT_MODELS], help="Run only selected model name; repeatable")
    parser.add_argument("--case", action="append", help="Run only selected case_id; repeatable")
    parser.add_argument("--workers", type=int, default=4, help="Parallel requests per model")
    parser.add_argument("--no-write", action="store_true", help="Do not write report files")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    args = parser.parse_args()

    selected_models = [m for m in DEFAULT_MODELS if not args.model or m.name in args.model]
    selected_cases = [c for c in EXPECTED_CASES if not args.case or c["case_id"] in args.case]
    report = run(selected_models, selected_cases, workers=args.workers)

    if not args.no_write:
        json_path, md_path = write_reports(report)
        report["report_json"] = str(json_path)
        report["report_markdown"] = str(md_path)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for model in report["models"]:
            if model.get("skipped"):
                print(f"SKIP {model['name']} {model['skip_reason']}")
            else:
                print(f"{model['name']}: {model.get('passed', 0)}/{len(model['case_results'])} pass")
        if not args.no_write:
            print(f"json: {report['report_json']}")
            print(f"md: {report['report_markdown']}")

    any_failed = any(
        (not model.get("skipped")) and model.get("failed", 0) > 0
        for model in report["models"]
    )
    return 1 if any_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
