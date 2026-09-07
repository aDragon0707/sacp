"""Demonstrate LangGraph SQLite checkpoint and SACP store recovery."""

from __future__ import annotations

from datetime import datetime, timezone
from tempfile import TemporaryDirectory

from sacp_verify.langgraph_adapter import LangGraphReleaseExperiment


def main() -> None:
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)
    with TemporaryDirectory() as directory:
        store_database = f"{directory}/sacp.sqlite3"
        checkpoint_database = f"{directory}/langgraph.sqlite3"
        first = LangGraphReleaseExperiment(
            now=now,
            store_database=store_database,
            checkpoint_database=checkpoint_database,
        )
        first.invoke(approved=True, provider_event="none")
        first.close()
        print("1) first process: graph ended, SQLite files written")

        resumed = LangGraphReleaseExperiment(
            now=now,
            store_database=store_database,
            checkpoint_database=checkpoint_database,
        )
        try:
            snapshot = resumed.state_snapshot()
            receipt = resumed.receipt()
            print(
                "2) resumed process: "
                f"next={snapshot.values['next_node']}, "
                f"status={receipt.overall_status}, "
                f"events={resumed.store.event_count(resumed.action_id)}"
            )
        finally:
            resumed.close()


if __name__ == "__main__":
    main()
