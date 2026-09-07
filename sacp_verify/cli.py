"""Command-line entry point for running an evidence-bounded release gate."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .gate import ReleaseGate
from .github_actions import GitHubActionsPayloadAdapter
from .store import EventStore
from .verifier import Verifier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a GitHub Actions release payload with SACP.")
    parser.add_argument("--payload", required=True, help="Path to a GitHub REST-shaped release payload JSON file.")
    args = parser.parse_args(argv)
    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    store = EventStore()
    try:
        GitHubActionsPayloadAdapter(store).ingest_release(payload)
        now = datetime.fromisoformat(payload["observed_at"])
        decision = ReleaseGate(store, Verifier(store)).can_proceed(payload["action_id"], now=now)
        print(json.dumps(decision.as_dict(), ensure_ascii=False, indent=2))
        return 0 if decision.allowed else 1
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
