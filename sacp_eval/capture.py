"""Explicit opt-in Pi JSON subprocess capture for a caller-owned isolation boundary.

This module provides a launcher seam, not a sandbox. A real caller must enforce
the launcher, credential scope, model budget and filesystem/network isolation.
There is deliberately no live-model CLI command in the initial integration.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from .pi import MAX_BYTES, digest, parse_trace


def pi_json_command(node: str, cli: str, *, provider: str, model: str, prompt: str) -> list[str]:
    """Construct an explicit model selection; '--' keeps prompt text out of flags."""
    if not all(isinstance(item, str) and item and "\0" not in item for item in (node, cli, provider, model, prompt)):
        raise ValueError("node, CLI, provider, model and prompt must be nonempty strings")
    return [node, cli, "--mode", "json", "--no-session", "--no-extensions", "--no-skills", "--no-prompt-templates", "--no-themes", "--no-context-files", "--no-approve", "--offline", "--tools", "read,bash,edit,write", "--provider", provider, "--model", model, "--", prompt]


def _kill_tree(process: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def capture_pi_json(
    command: list[str],
    *,
    launcher: list[str],
    cwd: Path,
    output_dir: Path,
    env: dict[str, str],
    timeout: float = 60,
    max_output_bytes: int = MAX_BYTES,
    permit_model_calls: bool = False,
) -> dict[str, Any]:
    """Capture a JSON-mode invocation after explicit external authorization.

    command and launcher are trusted-caller inputs, never read from Pi records.
    The caller provides an already reviewed isolation launcher and an explicit
    environment. A nonempty launcher is a declaration, not isolation attestation.
    Raw logs may contain sensitive data; the returned summary excludes prompt/env.
    """
    if not permit_model_calls:
        raise ValueError("model execution is disabled without explicit caller permission")
    if not launcher or not command or not all(isinstance(item, str) and item for item in (*launcher, *command)):
        raise ValueError("an explicit isolation launcher and command are required")
    if not 0 < timeout <= 3600 or not 0 < max_output_bytes <= MAX_BYTES:
        raise ValueError("invalid time or accepted-output limit")
    output_dir.mkdir(parents=True, exist_ok=False)
    stdout_path, stderr_path = output_dir / "events.jsonl", output_dir / "stderr.log"
    status = "exited"
    started = time.monotonic()
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen([*launcher, *command], cwd=cwd, env=dict(env), stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=os.name != "nt", creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
        try:
            while process.poll() is None:
                if time.monotonic() - started > timeout:
                    status = "timeout"
                    _kill_tree(process)
                    break
                if stdout_path.stat().st_size + stderr_path.stat().st_size > max_output_bytes:
                    status = "output_limit"
                    _kill_tree(process)
                    break
                time.sleep(0.02)
        finally:
            if process.poll() is None:
                _kill_tree(process)
    sizes = stdout_path.stat().st_size + stderr_path.stat().st_size
    if sizes > max_output_bytes:
        status = "output_limit"
    with stdout_path.open("rb") as stream:
        raw = stream.read(max_output_bytes + 1)
    with stderr_path.open("rb") as stream:
        stderr_raw = stream.read(max_output_bytes + 1)
    trace = parse_trace(raw)
    complete = status == "exited" and process.returncode == 0 and trace["status"] == "complete"
    result = {
        "schema": "sacp-pi-capture/1", "status": status,
        "process_exit_code": process.returncode, "elapsed_seconds": time.monotonic() - started,
        "events_digest": digest(raw), "stderr_digest": digest(stderr_raw),
        "output_bytes": sizes, "trace_complete": complete,
        "digest_scope": "bounded captured prefixes" if sizes > max_output_bytes else "complete captured files",
        "isolation": "caller-declared launcher; not attested by SACP",
        "model_execution_permission": "explicit trusted caller",
    }
    (output_dir / "capture.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
