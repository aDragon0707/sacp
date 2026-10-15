"""Run a caller-trusted acceptance contract on an immutable source snapshot.

This separates acceptance from the Pi process and workspace. It is not a security
sandbox for hostile Python: product code still runs with the OS user's rights.
Real agent-produced code must be evaluated inside a separately enforced boundary.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .pi import MAX_BYTES, digest, json_object


def _relative_files(root: Path, names: list[str]) -> dict[str, bytes]:
    root = root.resolve()
    result = {}
    if not names or len(names) > 100 or not all(isinstance(name, str) for name in names) or len(set(names)) != len(names):
        raise ValueError("expected 1..100 unique relative source/test paths")
    for name in names:
        if not isinstance(name, str) or "\\" in name or ":" in name:
            raise ValueError("paths must be portable relative paths")
        path = Path(name)
        if name != path.as_posix() or path.is_absolute() or any(part in {"..", ".git"} for part in path.parts) or path.suffix != ".py":
            raise ValueError("only relative Python files are supported")
        target = root / path
        if any(item.is_symlink() for item in (target, *target.parents) if item != root) or not target.resolve().is_relative_to(root):
            raise ValueError("symlinks and escaping paths are forbidden")
        with target.open("rb") as stream:
            content = stream.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise ValueError("source file exceeds 8 MiB")
        result[path.as_posix()] = content
    if len({name.casefold() for name in result}) != len(result):
        raise ValueError("case-colliding snapshot paths are forbidden")
    if sum(map(len, result.values())) > MAX_BYTES:
        raise ValueError("snapshot exceeds 8 MiB")
    return result


def snapshot_digest(files: dict[str, bytes]) -> str:
    checksum = hashlib.sha256()
    for name, raw in sorted(files.items()):
        for item in (name.encode("utf-8"), raw):
            checksum.update(len(item).to_bytes(8, "big"))
            checksum.update(item)
    return "sha256:" + checksum.hexdigest()


def verify_source(
    contract: Path,
    source: Path,
    *,
    allow_local_execution: bool = False,
    timeout: float = 15,
    trace_digest: str | None = None,
) -> dict[str, Any]:
    """Verify explicit Python files against trusted unittest IDs in a clean copy.

    The contract and its sibling oracle/ directory belong to the caller, outside
    the candidate tree. No commands, tests or expected results come from Pi logs.
    Local execution is opt-in, for trusted fixtures only; this cannot sandbox code.
    """
    if not allow_local_execution:
        raise ValueError("local code execution requires explicit opt-in; use trusted fixtures only")
    if timeout <= 0 or timeout > 300:
        raise ValueError("timeout must be in (0, 300] seconds")
    with contract.open("rb") as stream:
        spec_raw = stream.read(1024 * 1024 + 1)
    if len(spec_raw) > 1024 * 1024:
        raise ValueError("contract exceeds 1 MiB")
    spec = json_object(spec_raw)
    required = spec.get("required_test_ids")
    if spec.get("schema") != "sacp-eval-task/1" or not isinstance(spec.get("task_id"), str) or not spec["task_id"]:
        raise ValueError("invalid task contract")
    if not isinstance(required, list) or not required or not all(isinstance(name, str) and name for name in required) or len(set(required)) != len(required):
        raise ValueError("a nonempty unique required test inventory is mandatory")
    if not isinstance(spec.get("source_files"), list) or not isinstance(spec.get("test_files"), list):
        raise ValueError("source_files and test_files must be lists")
    source = source.resolve()
    if contract.resolve().is_relative_to(source) or (contract.parent / "oracle").resolve().is_relative_to(source):
        raise ValueError("acceptance contract must be outside the candidate tree")
    source_files = _relative_files(source, spec["source_files"])
    test_files = _relative_files(contract.parent / "oracle", spec["test_files"])
    fingerprint = snapshot_digest(source_files)
    contract_fingerprint = digest(spec_raw + snapshot_digest(test_files).encode("ascii"))
    with tempfile.TemporaryDirectory(prefix="sacp-acceptance-") as directory:
        root = Path(directory)
        for group, files in (("source", source_files), ("tests", test_files)):
            for name, raw in files.items():
                target = root / group / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        worker = Path(__file__).with_name("_oracle_worker.py").resolve()
        env = {key: value for key, value in os.environ.items() if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATHEXT"}}
        env["PYTHONIOENCODING"] = "utf-8"
        timed_out = False
        with (root / "stdout").open("wb") as out, (root / "stderr").open("wb") as err:
            try:
                process = subprocess.run([sys.executable, "-I", "-B", str(worker), str(root)], cwd=root, env=env, stdout=out, stderr=err, timeout=timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                exit_code = None
        # Bound accepted evidence. OS disk/process quotas still belong to the sandbox.
        oversized = any((root / name).stat().st_size > MAX_BYTES for name in ("stdout", "stderr", "result.json") if (root / name).exists())
        output = b""
        for name in ("stdout", "stderr"):
            with (root / name).open("rb") as stream:
                chunk = stream.read(MAX_BYTES)
            output += len(chunk).to_bytes(8, "big") + chunk
        result = {}
        if (root / "result.json").is_file() and not oversized:
            try:
                result = json_object((root / "result.json").read_bytes())
            except (ValueError, UnicodeError):
                pass
    inventory = result.get("executed_test_ids")
    valid = (
        not oversized and not timed_out and exit_code in {0, 1}
        and isinstance(inventory, list) and all(isinstance(item, str) for item in inventory)
        and sorted(inventory) == sorted(required)
        and result.get("total") == len(required)
        and all(type(result.get(name)) is int and result[name] >= 0 for name in ("total", "failures", "errors", "skipped", "expected_failures", "unexpected_successes"))
    )
    passed = valid and exit_code == 0 and all(result[name] == 0 for name in ("failures", "errors", "skipped", "expected_failures", "unexpected_successes"))
    return {
        "schema": "sacp-task-acceptance/1", "task_id": spec["task_id"],
        "trace_digest": trace_digest,
        "snapshot_digest": fingerprint, "contract_digest": contract_fingerprint,
        "source_files": sorted(source_files), "test_files": sorted(test_files),
        "status": "passed" if passed else "failed" if valid else "indeterminate",
        "exit_code": exit_code, "timed_out": timed_out, "output_oversized": oversized,
        "output_digest": digest(output), "results": result,
        "execution_boundary": "explicitly opted-in local trusted fixture; not sandboxed",
    }
