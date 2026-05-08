#!/usr/bin/env python3
"""
Collect natural messy model outputs for SACP sample-corpus Batch 002.

The prompts intentionally do not mention SACP. The goal is to capture normal
model behavior before translating it into SACP receipts.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "sample-corpus"
PROMPTS_PATH = CORPUS / "batch002_dirty_prompts.yaml"
RAW_DIR = CORPUS / "raw-runs"


@dataclass(frozen=True)
class ModelConfig:
    name: str
    endpoint: str
    env_key: str
    model: str
    temperature: float
    disable_thinking: bool = False


MODELS = [
    ModelConfig("deepseek_pro", "https://api.deepseek.com/chat/completions", "DEEPSEEK_API_KEY", "deepseek-v4-pro", 0),
    ModelConfig("qwen_strong", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", "QWEN_API_KEY", "qwen3.6-plus", 0),
    ModelConfig("glm_strong", "https://open.bigmodel.cn/api/paas/v4/chat/completions", "ZHIPU_API_KEY", "glm-4.7", 0, True),
    ModelConfig("kimi_strong", "https://api.moonshot.cn/v1/chat/completions", "KIMI_API_KEY", "kimi-k2.6", 0.6, True),
]


def load_tasks() -> list[dict[str, Any]]:
    data = yaml.safe_load(PROMPTS_PATH.read_text(encoding="utf-8"))
    return data["tasks"]


def call_model(config: ModelConfig, key: str, prompt: str) -> dict[str, Any]:
    body = {
        "model": config.model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": config.temperature,
        "max_tokens": 700,
        "stream": False,
    }
    if config.disable_thinking:
        body["thinking"] = {"type": "disabled"}
    request = urllib.request.Request(
        config.endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        message = payload.get("choices", [{}])[0].get("message", {})
        return {
            "ok": True,
            "http_status": response.status,
            "content": message.get("content", ""),
            "model_returned": payload.get("model"),
            "finish_reason": payload.get("choices", [{}])[0].get("finish_reason"),
            "usage": payload.get("usage"),
            "elapsed_sec": round(time.time() - started, 3),
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "http_status": exc.code,
            "error": exc.read().decode("utf-8", errors="replace")[:1000],
            "elapsed_sec": round(time.time() - started, 3),
        }
    except Exception as exc:  # pragma: no cover
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc)[:1000],
            "elapsed_sec": round(time.time() - started, 3),
        }


def write_raw(index: int, task: dict[str, Any], model: ModelConfig, result: dict[str, Any]) -> Path:
    path = RAW_DIR / f"{index:03d}_batch002_{task['task_id']}_{model.name}.md"
    content = [
        f"# Raw Sample {index:03d}: Batch 002 {task['task_id']} / {model.name}",
        "",
        f"Model: `{model.model}`",
        f"Collector: `collect_dirty_outputs.py`",
        f"Collected at: `{time.strftime('%Y-%m-%dT%H:%M:%S%z')}`",
        "",
        "## Prompt",
        "",
        "```text",
        task["prompt"].strip(),
        "```",
        "",
        "## Expected Failure Modes",
        "",
    ]
    content.extend(f"- {item}" for item in task.get("expected_failure_modes", []))
    content.extend(["", "## Raw Model Output", ""])
    if result.get("ok"):
        content.extend(["```text", str(result.get("content", "")).strip(), "```"])
    else:
        content.extend(["```text", f"ERROR: {result.get('http_status')} {result.get('error')}", "```"])
    content.extend(["", "## Metadata", "", "```json", json.dumps({k: v for k, v in result.items() if k != "content"}, ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(content), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Batch 002 dirty natural model outputs.")
    parser.add_argument("--model", action="append", choices=[m.name for m in MODELS])
    parser.add_argument("--task", action="append")
    args = parser.parse_args()

    tasks = [t for t in load_tasks() if not args.task or t["task_id"] in args.task]
    models = [m for m in MODELS if not args.model or m.name in args.model]
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    index_start = 11
    written = []
    index = index_start
    for task in tasks:
        for model in models:
            key = os.environ.get(model.env_key)
            if not key:
                print(f"SKIP {model.name}: missing {model.env_key}")
                continue
            result = call_model(model, key, task["prompt"])
            path = write_raw(index, task, model, result)
            print(f"WROTE {path.name} ok={result.get('ok')}")
            written.append(str(path))
            index += 1
    print(json.dumps({"written": written}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
