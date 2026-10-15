"""Parse Pi JSON-mode records without treating agent/tool messages as host proof.

The supported event contract is Pi coding-agent 1.0/1.2 JSON mode. RPC responses
are deliberately separate. A session settling is a transport fact, not task truth.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


MAX_BYTES = 8 * 1024 * 1024
MAX_RECORD_BYTES = 1024 * 1024
PASSIVE_EVENTS = {
    "turn_start", "turn_end", "message_start", "message_update",
    "tool_execution_update", "queue_update", "entry_appended",
    "session_info_changed", "thinking_level_changed", "compaction_start",
    "compaction_end", "summarization_retry_scheduled",
    "summarization_retry_attempt_start", "summarization_retry_finished",
    "auto_retry_start", "auto_retry_end",
}


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def json_object(raw: bytes) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError("non-finite JSON number")

    result = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=reject_constant)
    if not isinstance(result, dict):
        raise ValueError("JSON record must be an object")
    return result


def read_bounded(path: Path) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input exceeds 8 MiB")
    return raw


def parse_trace(raw: bytes) -> dict[str, Any]:
    """Summarize one JSON-mode invocation; malformed input fails closed.

    Only LF separates records. U+2028/U+2029 inside a JSON string are content.
    A final unterminated record is incomplete even when its JSON happens to parse.
    """
    errors: list[str] = []
    tool_errors: list[str] = []
    active_tools: dict[str, str] = {}
    seen_tools: set[str] = set()
    final: dict[str, Any] | None = None
    started = False
    active = False
    ended = False
    settled = False
    aborted = False
    retry_pending = False
    session_id = None
    tools = 0
    records = 0
    stream_digest = digest(raw)
    if len(raw) > MAX_BYTES:
        errors.append("trace_too_large")
        raw = b""
    if not raw or not raw.endswith(b"\n"):
        errors.append("incomplete_jsonl")
    lines = raw.split(b"\n")
    if len(lines) > 100_001:
        raise ValueError("too many JSONL records")
    for number, line in enumerate(lines, 1):
        if number == len(lines) and not line:
            break
        if len(line) > MAX_RECORD_BYTES:
            errors.append(f"record_too_large:{number}")
            continue
        try:
            event = json_object(line.rstrip(b"\r"))
        except (ValueError, UnicodeError, RecursionError):
            errors.append(f"invalid_record:{number}")
            continue
        records += 1
        kind = event.get("type")
        if not isinstance(kind, str):
            errors.append(f"invalid_event_type:{number}")
            continue
        if settled:
            errors.append("event_after_settled")
        if kind == "session":
            if records != 1 or session_id is not None or event.get("version") != 3 or not isinstance(event.get("id"), str) or not event["id"]:
                errors.append("invalid_session")
            else:
                session_id = event["id"]
        elif session_id is None:
            errors.append("session_header_missing")
        if kind == "agent_start":
            if active:
                errors.append("overlapping_agent_runs")
            active = started = True
            ended = False
            final = None
            retry_pending = False
        elif kind == "agent_end":
            if not active:
                errors.append("agent_end_without_start")
            if active_tools:
                errors.append("agent_ended_with_active_tools")
            active = False
            ended = True
            if "willRetry" in event and type(event["willRetry"]) is not bool:
                errors.append("invalid_retry_flag")
            retry_pending = event.get("willRetry", False) is not False
        elif kind == "agent_settled":
            if active or not started or not ended:
                errors.append("settled_without_ended_run")
            if retry_pending:
                errors.append("settled_with_retry_pending")
            if "aborted" in event and type(event["aborted"]) is not bool:
                errors.append("invalid_aborted_flag")
            aborted = event.get("aborted", False) is not False
            settled = True
        elif kind == "tool_execution_start":
            identity, name = event.get("toolCallId"), event.get("toolName")
            if not active or not isinstance(identity, str) or not identity or identity in seen_tools or not isinstance(name, str):
                errors.append("invalid_tool_start")
            else:
                seen_tools.add(identity)
                active_tools[identity] = name
                tools += 1
        elif kind == "tool_execution_end":
            identity = event.get("toolCallId")
            if not active or not isinstance(identity, str) or identity not in active_tools or active_tools.get(identity) != event.get("toolName") or type(event.get("isError")) is not bool or not isinstance(event.get("result"), dict):
                errors.append("invalid_tool_end")
            else:
                active_tools.pop(identity)
                if event["isError"]:
                    tool_errors.append(identity)
        elif kind == "message_end":
            message = event.get("message")
            if not isinstance(message, dict):
                errors.append("invalid_message")
            elif message.get("role") == "assistant":
                if not active or not isinstance(message.get("content"), list):
                    errors.append("invalid_assistant_message")
                else:
                    final = message
        elif kind not in PASSIVE_EVENTS and kind != "session":
            errors.append("unsupported_event")
    if active_tools:
        errors.append("unfinished_tools")
    if aborted:
        errors.append("agent_aborted")
    if not settled:
        errors.append("agent_not_settled")
    if final is None or final.get("stopReason") != "stop":
        errors.append("final_assistant_success_missing")
    text_parts = []
    if final:
        for part in final.get("content", []):
            if not isinstance(part, dict):
                errors.append("invalid_content_block")
            elif part.get("type") == "text":
                if not isinstance(part.get("text"), str):
                    errors.append("invalid_text_block")
                else:
                    text_parts.append(part["text"])
    return {
        "events_digest": stream_digest, "session_id": session_id,
        "records": records, "settled": settled,
        "final_text": "\n".join(text_parts), "tool_calls": tools,
        "tool_errors": tool_errors, "errors": sorted(set(errors)),
        "status": "complete" if not errors else "incomplete",
    }


def probe_pi(node: Path, cli: Path, timeout: float = 15) -> dict[str, Any]:
    """Ask an installed Pi only for version and RPC state; never send a prompt.

    Use a fresh config/work directory, omit credentials, disable resources/tools
    and startup network operations. This is a compatibility probe, not a sandbox.
    """
    if not node.is_file() or not cli.is_file():
        raise ValueError("node and Pi CLI must be explicit existing files")
    node, cli = node.resolve(), cli.resolve()
    with tempfile.TemporaryDirectory(prefix="sacp-pi-probe-") as directory:
        env = {key: value for key, value in os.environ.items() if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATHEXT"}}
        env.update(PI_CODING_AGENT_DIR=directory, PI_OFFLINE="1", PI_SKIP_VERSION_CHECK="1", PI_TELEMETRY="0")
        version = subprocess.run([str(node), str(cli), "--version"], cwd=directory, env=env, capture_output=True, timeout=timeout, check=True).stdout.decode("utf-8").strip()
        flags = ["--mode", "rpc", "--no-session", "--no-tools", "--no-extensions", "--no-skills", "--no-prompt-templates", "--no-themes", "--no-context-files", "--no-approve", "--offline"]
        process = subprocess.run([str(node), str(cli), *flags], input=b'{"id":"sacp-probe","type":"get_state"}\n', cwd=directory, env=env, capture_output=True, timeout=timeout)
        records = [json_object(line.rstrip(b"\r")) for line in process.stdout.split(b"\n") if line]
        responses = [record for record in records if record.get("id") == "sacp-probe" and record.get("type") == "response"]
        passed = process.returncode == 0 and len(responses) == 1 and responses[0].get("command") == "get_state" and responses[0].get("success") is True
        return {"schema": "sacp-pi-probe/1", "pi_version": version, "cli_digest": digest(cli.read_bytes()), "rpc_get_state": "passed" if passed else "failed", "exit_code": process.returncode, "prompts_sent": 0, "model_calls_requested": 0, "credentials_inherited": False, "stderr_digest": digest(process.stderr)}
