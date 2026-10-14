from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

from sacp_verify import DeploymentGate, RetryPolicy, StagingHTTPClient, StagingHTTPServer

try:
    from sacp_verify.langgraph_adapter import LangGraphReleaseExperiment
except ModuleNotFoundError as exc:  # pragma: no cover - environment gate
    LangGraphReleaseExperiment = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


@unittest.skipIf(LangGraphReleaseExperiment is None, f"LangGraph unavailable: {_IMPORT_ERROR}")
class LangGraphReleaseExperimentTests(unittest.TestCase):
    def test_approval_gate_blocks_dispatch(self) -> None:
        experiment = LangGraphReleaseExperiment(now=datetime(2026, 9, 5, tzinfo=timezone.utc))
        result = experiment.invoke(approved=False)

        self.assertEqual(result["next_node"], "awaiting_approval")
        receipt = experiment.receipt()
        self.assertEqual(receipt.overall_status, "needs_approval")
        self.assertEqual(receipt.provider_evidence_refs, ())

    def test_approved_graph_records_accepted_but_not_delivered(self) -> None:
        experiment = LangGraphReleaseExperiment(now=datetime(2026, 9, 5, tzinfo=timezone.utc))
        result = experiment.invoke(approved=True)

        self.assertEqual(result["next_node"], "dispatched")
        receipt = experiment.receipt()
        self.assertEqual(receipt.external_status, "transport_accepted")
        self.assertEqual(receipt.overall_status, "transport_accepted")
        self.assertNotEqual(receipt.external_status, "provider_reported_delivered")
        self.assertEqual(result["thread_id"], "langgraph-release-thread")
        self.assertEqual(result["run_id"], "langgraph-release-run")

    def test_reconciler_continues_after_graph_ends_without_provider_event(self) -> None:
        experiment = LangGraphReleaseExperiment(now=datetime(2026, 9, 5, tzinfo=timezone.utc))
        try:
            result = experiment.invoke(approved=True, provider_event="none")
            self.assertEqual(result["next_node"], "dispatched")
            before = experiment.receipt()
            self.assertEqual(before.overall_status, "ready_for_external_action")

            reconciler = experiment.reconciler(
                RetryPolicy(max_attempts=2, compensation_owner="release-compensation")
            )
            timeout_at = datetime(2026, 9, 5, 0, 11, tzinfo=timezone.utc)
            self.assertEqual(len(reconciler.reconcile(timeout_at)), 1)
            timed_out = experiment.receipt_at(timeout_at)
            self.assertEqual(timed_out.external_status, "attestation_timed_out")
            self.assertEqual(timed_out.recovery_route, "retry")
        finally:
            experiment.close()

    def test_langgraph_run_reaches_compensation_after_bounded_retries(self) -> None:
        experiment = LangGraphReleaseExperiment(now=datetime(2026, 9, 5, tzinfo=timezone.utc))
        try:
            experiment.invoke(approved=True, provider_event="none")
            reconciler = experiment.reconciler(
                RetryPolicy(
                    max_attempts=2,
                    retry_delay=timedelta(minutes=5),
                    compensation_owner="release-compensation",
                )
            )
            first_timeout = datetime(2026, 9, 5, 0, 11, tzinfo=timezone.utc)
            second_timeout = datetime(2026, 9, 5, 0, 16, tzinfo=timezone.utc)
            self.assertEqual(len(reconciler.reconcile(first_timeout)), 1)
            self.assertEqual(len(reconciler.reconcile(second_timeout)), 1)
            receipt = experiment.receipt_at(second_timeout)
            self.assertEqual(receipt.recovery_route, "compensation")
            self.assertEqual(receipt.next_action_owner, "release-compensation")
            self.assertFalse(receipt.retry_allowed)
        finally:
            experiment.close()

    def test_delayed_provider_event_stops_langgraph_recovery(self) -> None:
        experiment = LangGraphReleaseExperiment(now=datetime(2026, 9, 5, tzinfo=timezone.utc))
        try:
            experiment.invoke(approved=True, provider_event="none")
            reconciler = experiment.reconciler(
                RetryPolicy(
                    max_attempts=2,
                    retry_delay=timedelta(minutes=5),
                    compensation_owner="release-compensation",
                )
            )
            first_timeout = datetime(2026, 9, 5, 0, 11, tzinfo=timezone.utc)
            delayed_event_at = datetime(2026, 9, 5, 0, 13, tzinfo=timezone.utc)
            second_check = datetime(2026, 9, 5, 0, 16, tzinfo=timezone.utc)
            self.assertEqual(len(reconciler.reconcile(first_timeout)), 1)
            experiment.provider.emit(
                experiment.action_id,
                "accepted",
                "delayed-langgraph-provider-receipt",
                delayed_event_at,
            )
            self.assertEqual(len(reconciler.reconcile(second_check)), 0)
            receipt = experiment.receipt_at(second_check)
            self.assertEqual(receipt.external_status, "transport_accepted")
            self.assertEqual(receipt.recovery_route, "none")
            self.assertFalse(receipt.retry_allowed)
        finally:
            experiment.close()

    def test_sqlite_checkpoint_and_sacp_store_survive_adapter_restart(self) -> None:
        with TemporaryDirectory() as directory:
            store_database = f"{directory}/sacp.sqlite3"
            checkpoint_database = f"{directory}/langgraph.sqlite3"
            first = LangGraphReleaseExperiment(
                now=datetime(2026, 9, 5, tzinfo=timezone.utc),
                store_database=store_database,
                checkpoint_database=checkpoint_database,
            )
            first.invoke(approved=True, provider_event="none")
            first.close()

            resumed = LangGraphReleaseExperiment(
                now=datetime(2026, 9, 5, tzinfo=timezone.utc),
                store_database=store_database,
                checkpoint_database=checkpoint_database,
            )
            try:
                snapshot = resumed.state_snapshot()
                self.assertEqual(snapshot.values["next_node"], "dispatched")
                self.assertEqual(resumed.receipt().overall_status, "ready_for_external_action")
                self.assertEqual(resumed.store.event_count(resumed.action_id), 3)
            finally:
                resumed.close()

    def test_langgraph_reconciliation_converges_with_localhost_http_provider(self) -> None:
        with TemporaryDirectory() as directory:
            experiment = LangGraphReleaseExperiment(
                now=datetime(2026, 9, 5, tzinfo=timezone.utc),
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
                self.assertEqual(len(reconciler.reconcile(timeout_at)), 1)
                self.assertEqual(experiment.receipt_at(timeout_at).recovery_route, "retry")

                client = StagingHTTPClient(server.base_url, experiment.store)
                accepted_event = client.deploy(
                    experiment.action_id,
                    "release-v1",
                    datetime(2026, 9, 5, 0, 12, tzinfo=timezone.utc),
                )
                accepted_payload = experiment.store.decode(
                    next(row for row in experiment.store.events(experiment.action_id) if row["event_id"] == accepted_event)
                )["payload"]
                deployment_id = accepted_payload["receipt_id"]
                server.set_health(deployment_id, "healthy")
                client.health(
                    experiment.action_id,
                    deployment_id,
                    "release-v1",
                    datetime(2026, 9, 5, 0, 13, tzinfo=timezone.utc),
                )

                final_at = datetime(2026, 9, 5, 0, 16, tzinfo=timezone.utc)
                self.assertEqual(len(reconciler.reconcile(final_at)), 0)
                receipt = experiment.receipt_at(final_at)
                self.assertEqual(receipt.external_status, "provider_reported_healthy")
                self.assertEqual(receipt.recovery_route, "none")
                gate = DeploymentGate(experiment.store, experiment.verifier)
                decision = gate.can_finalize(experiment.action_id, "release-v1", final_at)
                self.assertTrue(decision.allowed)
                self.assertEqual(decision.reason, "deployment_health_verified")
            finally:
                server.close()
                experiment.close()


if __name__ == "__main__":
    unittest.main()
