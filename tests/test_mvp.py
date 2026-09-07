from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

from sacp_verify import (
    AuthorityDecision,
    Claim,
    EventStore,
    HostObservation,
    MockProvider,
    Reconciler,
    RetryPolicy,
    Verifier,
)


UTC = timezone.utc
BASE = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)


def claim(
    action_id: str,
    claim_type: str = "tests_passed",
    *,
    requires_authority: bool = False,
    deadline: datetime | None = None,
    owner: str | None = None,
    checkpoint_id: str = "cp-1",
    input_digest: str | None = "input-1",
    action_scope: str | None = "scope-1",
) -> Claim:
    return Claim(
        action_id=action_id,
        claim_type=claim_type,
        text=claim_type,
        thread_id="thread-1",
        run_id="run-1",
        checkpoint_id=checkpoint_id,
        input_digest=input_digest,
        action_scope=action_scope,
        requires_authority=requires_authority,
        attestation_deadline=deadline,
        reconciliation_owner=owner,
        created_at=BASE,
    )


class CompletionVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = EventStore()
        self.verifier = Verifier(self.store)
        self.provider = MockProvider(self.store)

    def tearDown(self) -> None:
        self.store.close()

    def test_claim_without_evidence_is_unverified(self) -> None:
        self.store.append_claim(claim("a1"))
        self.assertEqual(self.verifier.project_receipt("a1", BASE).status, "unverified")

    def test_host_test_success_requires_output_digest(self) -> None:
        self.store.append_claim(claim("a2"))
        self.store.record_host_observation(
            HostObservation(
                action_id="a2",
                kind="test_run",
                source="deterministic-test-runner",
                thread_id="thread-1",
                run_id="run-1",
                checkpoint_id="cp-1",
                payload={"exit_code": 0},
                observed_at=BASE,
            )
        )
        self.assertEqual(self.verifier.project_receipt("a2", BASE).status, "unverified")

    def test_host_test_success_with_digest_is_host_completed(self) -> None:
        host_event = self.store.record_host_observation(
            HostObservation(
                action_id="a3",
                kind="test_run",
                source="deterministic-test-runner",
                thread_id="thread-1",
                run_id="run-1",
                checkpoint_id="cp-1",
                payload={"exit_code": 0, "output_digest": "sha256:test"},
                observed_at=BASE,
            )
        )
        self.store.append_claim(Claim(**{**claim("a3").__dict__, "evidence_refs": (host_event,)}))
        self.assertEqual(self.verifier.project_receipt("a3", BASE).status, "host_completed")

    def test_host_evidence_for_same_action_without_claim_reference_is_unverified(self) -> None:
        self.store.record_host_observation(
            HostObservation(
                action_id="a3c",
                kind="test_run",
                source="deterministic-test-runner",
                thread_id="thread-1",
                run_id="run-1",
                checkpoint_id="cp-1",
                payload={"exit_code": 0, "output_digest": "sha256:test"},
                observed_at=BASE,
            )
        )
        self.store.append_claim(claim("a3c"))
        self.assertEqual(self.verifier.project_receipt("a3c", BASE).status, "unverified")

    def test_claim_reference_to_provider_event_cannot_verify_tests(self) -> None:
        self.store.append_claim(claim("a3d"))
        provider_event = self.provider.emit("a3d", "accepted", "p-3d", BASE)
        self.store.append_claim(
            Claim(**{**claim("a3d").__dict__, "evidence_refs": (provider_event,)})
        )
        self.assertEqual(self.verifier.project_receipt("a3d", BASE).status, "unverified")

    def test_unknown_evidence_reference_cannot_be_verified(self) -> None:
        self.store.append_claim(
            Claim(
                action_id="a3b",
                claim_type="tests_passed",
                text="tests_passed",
                thread_id="thread-1",
                run_id="run-1",
                checkpoint_id="cp-1",
                evidence_refs=("missing-event",),
                created_at=BASE,
            )
        )
        self.store.record_host_observation(
            HostObservation(
                action_id="a3b",
                kind="test_run",
                source="deterministic-test-runner",
                thread_id="thread-1",
                run_id="run-1",
                checkpoint_id="cp-1",
                payload={"exit_code": 0, "output_digest": "sha256:test"},
                observed_at=BASE,
            )
        )
        self.assertEqual(self.verifier.project_receipt("a3b", BASE).status, "unverified")

    def test_provider_accepted_does_not_mean_delivered(self) -> None:
        self.store.append_claim(claim("a4", "notification_sent"))
        self.provider.emit("a4", "accepted", "p-1", BASE)
        self.assertEqual(self.verifier.project_receipt("a4", BASE).status, "transport_accepted")

    def test_external_action_without_required_approval_is_violation(self) -> None:
        self.store.append_claim(claim("a4b", "publish_action", requires_authority=True))
        self.provider.emit("a4b", "accepted", "p-4b", BASE)
        receipt = self.verifier.project_receipt("a4b", BASE)
        self.assertEqual(receipt.authority_status, "pending")
        self.assertEqual(receipt.external_status, "transport_accepted")
        self.assertEqual(receipt.overall_status, "authority_violation")

    def test_bounce_downgrades_prior_delivery(self) -> None:
        self.store.append_claim(claim("a5", "notification_sent"))
        self.provider.emit("a5", "accepted", "p-2", BASE)
        self.provider.emit("a5", "delivered", "p-2", BASE + timedelta(minutes=1))
        self.provider.emit("a5", "bounced", "p-2", BASE + timedelta(minutes=2))
        self.assertEqual(self.verifier.project_receipt("a5", BASE).status, "bounced")

    def test_transport_errors_are_not_counterparty_declined(self) -> None:
        self.store.append_claim(claim("a6", "ask_counterparty"))
        self.provider.emit("a6", "unauthorized", "p-3", BASE)
        self.assertEqual(self.verifier.project_receipt("a6", BASE).status, "provider_error")

    def test_approval_must_match_checkpoint_and_input_digest(self) -> None:
        self.store.append_claim(claim("a7", "publish_action", requires_authority=True))
        self.store.record_authority_decision(
            AuthorityDecision(
                action_id="a7",
                decision="approved",
                owner="release-manager",
                thread_id="thread-1",
                run_id="run-1",
                checkpoint_id="cp-1",
                input_digest="different-input",
                action_scope="scope-1",
                expires_at=BASE + timedelta(hours=1),
                decided_at=BASE,
            )
        )
        receipt = self.verifier.project_receipt("a7", BASE)
        self.assertEqual(receipt.status, "needs_approval")
        self.assertIsNone(receipt.authority_ref)

    def test_approval_must_match_thread_and_run(self) -> None:
        self.store.append_claim(claim("a7b", "publish_action", requires_authority=True))
        self.store.record_authority_decision(
            AuthorityDecision(
                action_id="a7b",
                decision="approved",
                owner="release-manager",
                thread_id="other-thread",
                run_id="other-run",
                checkpoint_id="cp-1",
                input_digest="input-1",
                action_scope="scope-1",
                expires_at=BASE + timedelta(hours=1),
                decided_at=BASE,
            )
        )
        receipt = self.verifier.project_receipt("a7b", BASE)
        self.assertEqual(receipt.status, "needs_approval")
        self.assertIsNone(receipt.authority_ref)

    def test_matching_approval_allows_authority(self) -> None:
        self.store.append_claim(claim("a8", "publish_action", requires_authority=True))
        event_id = self.store.record_authority_decision(
            AuthorityDecision(
                action_id="a8",
                decision="approved",
                owner="release-manager",
                thread_id="thread-1",
                run_id="run-1",
                checkpoint_id="cp-1",
                input_digest="input-1",
                action_scope="scope-1",
                expires_at=BASE + timedelta(hours=1),
                decided_at=BASE,
            )
        )
        receipt = self.verifier.project_receipt("a8", BASE)
        self.assertEqual(receipt.authority_ref, event_id)
        self.assertEqual(receipt.next_action_owner, "release-manager")

    def test_reconciler_records_timeout_for_dead_workflow(self) -> None:
        self.store.append_claim(
            claim(
                "a9",
                "notification_sent",
                deadline=BASE + timedelta(minutes=5),
                owner="reconciliation-queue",
            )
        )
        event_ids = Reconciler(self.store, self.verifier).reconcile(BASE + timedelta(minutes=6))
        self.assertEqual(len(event_ids), 1)
        self.assertEqual(self.verifier.project_receipt("a9", BASE).status, "attestation_timed_out")

    def test_reconciliation_is_idempotent_at_same_check_time(self) -> None:
        self.store.append_claim(
            claim(
                "a10",
                "notification_sent",
                deadline=BASE + timedelta(minutes=5),
                owner="reconciliation-queue",
            )
        )
        reconciler = Reconciler(self.store, self.verifier)
        check_time = BASE + timedelta(minutes=6)
        self.assertEqual(len(reconciler.reconcile(check_time)), 1)
        self.assertEqual(len(reconciler.reconcile(check_time)), 0)
        self.assertEqual(self.store.event_count("a10"), 2)

    def test_reconciliation_recovers_after_restart_without_repeating_timeout(self) -> None:
        with TemporaryDirectory() as directory:
            database = f"{directory}/reconciliation.sqlite3"
            first_store = EventStore(database)
            first_store.append_claim(
                claim(
                    "a10-restart",
                    "notification_sent",
                    deadline=BASE + timedelta(minutes=5),
                    owner="reconciliation-queue",
                )
            )
            first_store.close()

            resumed_store = EventStore(database)
            resumed_verifier = Verifier(resumed_store)
            resumed_reconciler = Reconciler(resumed_store, resumed_verifier)
            timeout_at = BASE + timedelta(minutes=6)
            self.assertEqual(len(resumed_reconciler.reconcile(timeout_at)), 1)
            receipt = resumed_verifier.project_receipt("a10-restart", timeout_at)
            self.assertEqual(receipt.status, "attestation_timed_out")
            self.assertTrue(receipt.retry_allowed)
            resumed_store.close()

            restarted_store = EventStore(database)
            try:
                restarted_reconciler = Reconciler(restarted_store, Verifier(restarted_store))
                self.assertEqual(len(restarted_reconciler.reconcile(BASE + timedelta(minutes=7))), 0)
                self.assertEqual(restarted_store.event_count("a10-restart"), 2)
            finally:
                restarted_store.close()

    def test_late_provider_observation_supersedes_timeout_projection(self) -> None:
        self.store.append_claim(
            claim(
                "a10-late-provider",
                "notification_sent",
                deadline=BASE + timedelta(minutes=5),
                owner="reconciliation-queue",
            )
        )
        reconciler = Reconciler(self.store, self.verifier)
        timeout_at = BASE + timedelta(minutes=6)
        self.assertEqual(len(reconciler.reconcile(timeout_at)), 1)
        self.assertEqual(
            self.verifier.project_receipt("a10-late-provider", timeout_at).status,
            "attestation_timed_out",
        )

        self.provider.emit(
            "a10-late-provider",
            "accepted",
            "late-provider-receipt",
            BASE + timedelta(minutes=7),
        )
        receipt = self.verifier.project_receipt("a10-late-provider", BASE + timedelta(minutes=7))
        self.assertEqual(receipt.status, "transport_accepted")
        self.assertEqual(len(reconciler.reconcile(BASE + timedelta(minutes=8))), 0)

    def test_bounded_retry_then_compensation_route(self) -> None:
        self.store.append_claim(
            claim(
                "a10-retry",
                "notification_sent",
                deadline=BASE + timedelta(minutes=5),
                owner="reconciliation-queue",
            )
        )
        policy = RetryPolicy(
            max_attempts=2,
            retry_delay=timedelta(minutes=5),
            compensation_owner="compensation-queue",
        )
        reconciler = Reconciler(self.store, self.verifier, policy=policy)

        first = reconciler.reconcile(BASE + timedelta(minutes=6))
        self.assertEqual(len(first), 1)
        first_event = self.store.decode(self.store.events("a10-retry")[-1])
        self.assertEqual(first_event["payload"]["attempt"], 1)
        self.assertEqual(first_event["payload"]["route"], "retry")
        self.assertEqual(first_event["payload"]["next_check_at"], (BASE + timedelta(minutes=11)).isoformat())

        self.assertEqual(len(reconciler.reconcile(BASE + timedelta(minutes=10))), 0)
        second = reconciler.reconcile(BASE + timedelta(minutes=12))
        self.assertEqual(len(second), 1)
        second_event = self.store.decode(self.store.events("a10-retry")[-1])
        self.assertEqual(second_event["payload"]["attempt"], 2)
        self.assertEqual(second_event["payload"]["route"], "compensation")
        self.assertEqual(second_event["payload"]["owner"], "compensation-queue")
        receipt = self.verifier.project_receipt("a10-retry", BASE + timedelta(minutes=12))
        self.assertEqual(receipt.recovery_route, "compensation")
        self.assertFalse(receipt.retry_allowed)
        self.assertEqual(receipt.next_action_owner, "compensation-queue")
        self.assertEqual(len(reconciler.reconcile(BASE + timedelta(minutes=13))), 0)

    def test_provider_observation_stops_pending_retry_route(self) -> None:
        self.store.append_claim(
            claim(
                "a10-retry-stop",
                "notification_sent",
                deadline=BASE + timedelta(minutes=5),
                owner="reconciliation-queue",
            )
        )
        policy = RetryPolicy(max_attempts=2, retry_delay=timedelta(minutes=5))
        reconciler = Reconciler(self.store, self.verifier, policy=policy)
        self.assertEqual(len(reconciler.reconcile(BASE + timedelta(minutes=6))), 1)
        self.provider.emit("a10-retry-stop", "accepted", "late", BASE + timedelta(minutes=7))
        self.assertEqual(len(reconciler.reconcile(BASE + timedelta(minutes=12))), 0)

    def test_duplicate_provider_event_is_not_appended(self) -> None:
        self.store.append_claim(claim("a11", "notification_sent"))
        first = self.provider.emit("a11", "accepted", "p-11", BASE)
        second = self.provider.emit("a11", "accepted", "p-11", BASE)
        self.assertEqual(first, second)
        self.assertEqual(self.store.event_count("a11"), 2)

    def test_history_is_append_only_when_projection_changes(self) -> None:
        self.store.append_claim(claim("a12", "notification_sent"))
        self.provider.emit("a12", "accepted", "p-12", BASE)
        self.assertEqual(self.verifier.project_receipt("a12", BASE).status, "transport_accepted")
        self.provider.emit("a12", "delivered", "p-12", BASE + timedelta(minutes=1))
        self.assertEqual(self.verifier.project_receipt("a12", BASE).status, "provider_reported_delivered")
        self.assertEqual(self.store.event_count("a12"), 3)

    def test_file_backed_store_survives_reopen(self) -> None:
        with TemporaryDirectory() as directory:
            database = f"{directory}/receipt.sqlite3"
            first_store = EventStore(database)
            first_store.append_claim(claim("a13", "notification_sent"))
            first_provider = MockProvider(first_store)
            first_provider.emit("a13", "accepted", "p-13", BASE)
            first_receipt = Verifier(first_store).project_receipt("a13", BASE)
            first_events = first_store.events("a13")
            first_digests = [row["payload_digest"] for row in first_events]
            first_store.close()

            reopened = EventStore(database)
            reopened_receipt = Verifier(reopened).project_receipt("a13", BASE)
            reopened_events = reopened.events("a13")
            reopened_digests = [row["payload_digest"] for row in reopened_events]
            self.assertEqual(reopened_receipt.status, first_receipt.status)
            self.assertEqual(reopened_digests, first_digests)
            self.assertEqual(reopened.event_count("a13"), 2)
            reopened.close()


if __name__ == "__main__":
    unittest.main()
