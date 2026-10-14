"""Run the LangGraph + SQLite + localhost HTTP provider integration."""

from __future__ import annotations

from datetime import datetime, timezone
from tempfile import TemporaryDirectory

from sacp_verify import DeploymentGate, RetryPolicy, StagingHTTPClient, StagingHTTPServer
from sacp_verify.langgraph_adapter import LangGraphReleaseExperiment


def main() -> None:
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)
    with TemporaryDirectory() as directory:
        experiment = LangGraphReleaseExperiment(
            now=now,
            store_database=f"{directory}/sacp.sqlite3",
            checkpoint_database=f"{directory}/langgraph.sqlite3",
        )
        server = StagingHTTPServer().start()
        try:
            experiment.invoke(approved=True, provider_event="none")
            reconciler = experiment.reconciler(
                RetryPolicy(max_attempts=2, compensation_owner="release-compensation")
            )
            timeout_at = datetime(2026, 9, 5, 0, 11, tzinfo=timezone.utc)
            reconciler.reconcile(timeout_at)
            print(f"1) graph ended without witness: {experiment.receipt_at(timeout_at).recovery_route}")

            client = StagingHTTPClient(server.base_url, experiment.store)
            accepted_event = client.deploy(experiment.action_id, "release-v1", datetime(2026, 9, 5, 0, 12, tzinfo=timezone.utc))
            accepted_payload = experiment.store.decode(
                next(row for row in experiment.store.events(experiment.action_id) if row["event_id"] == accepted_event)
            )["payload"]
            deployment_id = accepted_payload["receipt_id"]
            server.set_health(deployment_id, "healthy")
            client.health(experiment.action_id, deployment_id, "release-v1", datetime(2026, 9, 5, 0, 13, tzinfo=timezone.utc))

            final_at = datetime(2026, 9, 5, 0, 16, tzinfo=timezone.utc)
            decision = DeploymentGate(experiment.store, experiment.verifier).can_finalize(
                experiment.action_id, "release-v1", final_at
            )
            receipt = experiment.receipt_at(final_at)
            print(
                "2) HTTP provider converged: "
                f"external={receipt.external_status}, route={receipt.recovery_route}, "
                f"allowed={decision.allowed}, reason={decision.reason}"
            )
        finally:
            server.close()
            experiment.close()


if __name__ == "__main__":
    main()
