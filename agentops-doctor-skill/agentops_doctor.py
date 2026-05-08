#!/usr/bin/env python3
"""
AgentOps Doctor: local SACP receipt auditor for messy agent outputs.

This first release is deliberately local and deterministic. It does not call
LLMs, execute the underlying task, or verify external facts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

import yaml


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fingerprint(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def has_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def diagnose(text: str, source_name: str) -> dict[str, Any]:
    lowered = text.lower()
    findings: list[dict[str, str]] = []
    memory_warning = None
    status_code = 200
    status_text = "completed"
    method = "COMPLETE"
    next_owner = "Coordinator"
    human_decision_required = False
    required_fix = "No protocol repair required from local heuristic pass."

    if has_any(text, ["done", "completed", "looks good", "fixed", "published"]) and not has_any(text, ["receipt", "verification", "evidence", "command output", "logs"]):
        status_code = 400
        status_text = "invalid_packet"
        method = "BLOCK"
        findings.append({"problem": "Completion is claimed without a SACP receipt or verification evidence."})
        required_fix = "Produce a SACP receipt with claims, verification, next_owner, and human_decision_required."

    if has_any(text, ["all tests passed", "tests passed", "status: passed", "✅ passed"]) and not has_any(text, ["command output", "test log", "pytest", "unittest", "npm test", "validation output"]):
        status_code = 412
        status_text = "missing_evidence"
        method = "BLOCK"
        findings.append({"problem": "Test success is asserted without tool output."})
        required_fix = "Attach command output or downgrade the test claim to unverified."
        next_owner = "ProjectManager"

    if has_any(text, ["verified long-term memory", "remember this forever", "save this as verified", "committed", "persistent memory"]):
        status_code = 412
        status_text = "missing_evidence"
        method = "BLOCK"
        memory_warning = "Potential automatic memory promotion detected."
        findings.append({"problem": "User preference or statement may be promoted to verified memory without approval evidence."})
        required_fix = "Keep memory pending_verification and require human approval before promotion."
        next_owner = "Human"
        human_decision_required = True

    if has_any(text, ["publish", "publication", "release"]) and not has_any(text, ["founder approval", "human approval", "approved by human", "do not publish"]):
        status_code = 412
        status_text = "missing_evidence"
        method = "BLOCK"
        findings.append({"problem": "Publication or release is recommended without explicit human approval evidence."})
        required_fix = "Run claim-boundary review and obtain human publication approval before release."
        next_owner = "Human"
        human_decision_required = True

    if "no logs" in lowered or "no test output" in lowered or "no command output" in lowered:
        if status_code == 200:
            status_code = 412
            status_text = "missing_evidence"
            method = "BLOCK"
        findings.append({"problem": "The raw output acknowledges missing logs or test evidence."})
        required_fix = "Request logs, command output, or verification evidence before treating work as complete."

    if not text.strip():
        status_code = 500
        status_text = "agent_error"
        method = "FAIL"
        findings.append({"problem": "Input is empty."})
        required_fix = "Retry with a non-empty agent output."
        next_owner = "Coordinator"

    if not findings:
        findings.append({"problem": "No high-risk local heuristic finding; still not proof of factual correctness."})

    support_status = "supported" if text.strip() else "unsupported"
    receipt = {
        "protocol": "SACP/0.1",
        "type": "receipt",
        "method": method,
        "status_code": status_code,
        "handoff_id": "agentops_doctor_" + hashlib.sha256(source_name.encode("utf-8")).hexdigest()[:10],
        "attempt_id": "attempt_001",
        "agent_id": "agentops-doctor-skill",
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_fingerprint": fingerprint(text),
        "claims": [
            {
                "text": findings[0]["problem"],
                "claim_type": "inference",
                "source_id": source_name,
                "support_status": support_status,
            }
        ],
        "verification": {
            "status": "failed" if status_code >= 400 else "passed",
            "method": "local heuristic SACP audit",
            "evidence_id": source_name,
        },
        "residual_risk": "Local heuristic audit only; external facts and tool outputs were not independently verified.",
        "next_owner": next_owner,
        "human_decision_required": human_decision_required,
    }
    return {
        "status_code": status_code,
        "status_text": status_text,
        "receipt_completeness": "generated",
        "claim_findings": findings,
        "memory_warning": memory_warning,
        "next_owner": next_owner,
        "human_decision_required": human_decision_required,
        "required_fix": required_fix,
        "translated_receipt": receipt,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# AgentOps Doctor Diagnosis",
        "",
        f"- status_code: `{result['status_code']}`",
        f"- status_text: `{result['status_text']}`",
        f"- receipt_completeness: `{result['receipt_completeness']}`",
        f"- next_owner: `{result['next_owner']}`",
        f"- human_decision_required: `{str(result['human_decision_required']).lower()}`",
        "",
        "## Claim Findings",
        "",
    ]
    for finding in result["claim_findings"]:
        lines.append(f"- {finding['problem']}")
    lines.extend([
        "",
        "## Memory Warning",
        "",
        str(result["memory_warning"] or "none"),
        "",
        "## Required Fix",
        "",
        result["required_fix"],
        "",
        "## Translated Receipt",
        "",
        "```yaml",
        yaml.safe_dump(result["translated_receipt"], sort_keys=False, allow_unicode=True).strip(),
        "```",
        "",
    ])
    return "\n".join(lines)


def zh_status_text(status_text: str) -> str:
    return {
        "completed": "completed / 已完成",
        "invalid_packet": "invalid_packet / 无效工作包",
        "missing_evidence": "missing_evidence / 缺少证据",
        "agent_error": "agent_error / agent 执行错误",
    }.get(status_text, status_text)


def zh_problem(problem: str) -> str:
    mapping = {
        "Completion is claimed without a SACP receipt or verification evidence.": "它声称任务已经完成，但没有提供 SACP receipt 或验证证据。",
        "Test success is asserted without tool output.": "它声称测试通过，但没有提供命令输出或测试日志。",
        "User preference or statement may be promoted to verified memory without approval evidence.": "用户偏好或陈述可能被自动晋升为 verified memory，但没有批准证据。",
        "Publication or release is recommended without explicit human approval evidence.": "它建议发布或 release，但没有明确的人类批准证据。",
        "The raw output acknowledges missing logs or test evidence.": "原始输出承认缺少日志或测试证据。",
        "Input is empty.": "输入为空。",
        "No high-risk local heuristic finding; still not proof of factual correctness.": "本地启发式检查没有发现高风险问题，但这不等于事实正确。"
    }
    return mapping.get(problem, problem)


def zh_required_fix(fix: str) -> str:
    mapping = {
        "Produce a SACP receipt with claims, verification, next_owner, and human_decision_required.": "补一份 SACP receipt，必须包含 claims、verification、next_owner 和 human_decision_required。",
        "Attach command output or downgrade the test claim to unverified.": "附上命令输出，或者把测试通过的说法降级为 unverified。",
        "Keep memory pending_verification and require human approval before promotion.": "保持 memory 为 pending_verification，晋升前必须有人类批准。",
        "Run claim-boundary review and obtain human publication approval before release.": "发布前先做 claim-boundary review，并取得人类发布批准。",
        "Request logs, command output, or verification evidence before treating work as complete.": "在把工作视为完成前，先要求日志、命令输出或验证证据。",
        "Retry with a non-empty agent output.": "用非空 agent 输出重试。",
        "No protocol repair required from local heuristic pass.": "本地启发式检查没有要求协议修复。"
    }
    return mapping.get(fix, fix)


def render_markdown_zh(result: dict[str, Any]) -> str:
    lines = [
        "# AgentOps Doctor 诊断报告",
        "",
        f"- status_code: `{result['status_code']}`",
        f"- status_text: `{zh_status_text(result['status_text'])}`",
        f"- receipt_completeness: `{result['receipt_completeness']}`",
        f"- next_owner: `{result['next_owner']}`",
        f"- human_decision_required: `{str(result['human_decision_required']).lower()}`",
        "",
        "## 发现的问题",
        "",
    ]
    for finding in result["claim_findings"]:
        lines.append(f"- {zh_problem(finding['problem'])}")
    lines.extend([
        "",
        "## 记忆风险",
        "",
        "无" if not result["memory_warning"] else "检测到可能的自动记忆晋升风险。",
        "",
        "## 必须怎么修",
        "",
        zh_required_fix(result["required_fix"]),
        "",
        "## 翻译后的 SACP Receipt",
        "",
        "```yaml",
        yaml.safe_dump(result["translated_receipt"], sort_keys=False, allow_unicode=True).strip(),
        "```",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit messy agent output with local SACP heuristics.")
    parser.add_argument("input", type=Path, help="Path to .md/.txt/.yaml agent output")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    parser.add_argument("--lang", choices=["en", "zh"], default="en", help="Markdown output language")
    parser.add_argument("--out", type=Path, help="Optional output file")
    args = parser.parse_args()

    text = read_text(args.input)
    result = diagnose(text, args.input.name)
    if args.json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = render_markdown_zh(result) if args.lang == "zh" else render_markdown(result)
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0 if result["status_code"] < 500 else 1


if __name__ == "__main__":
    raise SystemExit(main())
