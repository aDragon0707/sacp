"""Regression contracts for execution identity, authority and bounded recovery."""
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from itertools import permutations
from pathlib import Path
from tempfile import TemporaryDirectory

from sacp_verify import AuthorityDecision, Claim, DeploymentGate, EventStore, HostObservation, MockDeploymentProvider, MockProvider, MockRefundProvider, Reconciler, RefundGate, RetryPolicy, Verifier
from tests.test_mvp import BASE, claim
from tests.test_refund import refund_claim


class DomainBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.store = EventStore()
        self.addCleanup(self.store.close)
        self.verifier = Verifier(self.store)

    def approve(self, action, *, decision="approved", at=BASE, expiry=None):
        self.store.record_authority_decision(AuthorityDecision(action.action_id, decision, "manager", action.thread_id, action.run_id, action.checkpoint_id, action.input_digest, action.action_scope, expiry or BASE + timedelta(hours=1), at))

    def test_deployment_cannot_combine_different_execution_ids_or_providers(self):
        provider = MockDeploymentProvider(self.store)
        provider.emit("deploy", "accepted", "one", "rev", BASE)
        provider.emit("deploy", "healthy", "two", "rev", BASE + timedelta(seconds=1))
        self.assertFalse(DeploymentGate(self.store, self.verifier).can_finalize("deploy", "rev", BASE).allowed)
        MockDeploymentProvider(self.store, "other").emit("deploy", "healthy", "one", "rev", BASE)
        self.assertFalse(DeploymentGate(self.store, self.verifier).can_finalize("deploy", "rev", BASE).allowed)

    def test_authority_required_claim_cannot_finalize_without_approval(self):
        self.store.append_claim(claim("deploy", "publish_action", requires_authority=True))
        provider = MockDeploymentProvider(self.store)
        provider.emit("deploy", "accepted", "one", "rev", BASE)
        provider.emit("deploy", "healthy", "one", "rev", BASE)
        gate = DeploymentGate(self.store, self.verifier)
        self.assertFalse(gate.can_finalize("deploy", "rev", BASE).allowed)
        self.approve(claim("deploy", "publish_action", requires_authority=True))
        self.assertTrue(gate.can_finalize("deploy", "rev", BASE).allowed)

    def test_health_only_gate_cannot_stand_in_for_dispatch_authorization(self):
        gate = DeploymentGate(self.store, self.verifier)
        self.assertFalse(gate.can_dispatch("deploy", BASE).allowed)
        action = claim("deploy", "publish_action", requires_authority=True)
        self.store.append_claim(action)
        self.approve(action)
        self.assertTrue(gate.can_dispatch("deploy", BASE).allowed)

    def test_unknown_claim_policy_fails_closed(self):
        self.store.append_claim(claim("unknown", "made_up_success"))
        MockProvider(self.store).emit("unknown", "delivered", "id", BASE)
        self.assertEqual(self.verifier.project_receipt("unknown", BASE).overall_status, "unverified")

    def test_test_evidence_must_match_commit_and_execution_context(self):
        for changes in ({"run_id": "other"}, {"checkpoint_id": "other"}, {"payload": {"exit_code": 0, "output_digest": "sha256:test", "commit": "old"}}):
            store = EventStore()
            try:
                observation = HostObservation("test", "test_run", "host", "thread-1", "run-1", "cp-1", {"exit_code": 0, "output_digest": "sha256:test", "commit": "new"}, BASE)
                ref = store.record_host_observation(replace(observation, **changes))
                store.append_claim(replace(claim("test"), metadata={"commit": "new"}, evidence_refs=(ref,)))
                self.assertEqual(Verifier(store).project_receipt("test", BASE).overall_status, "unverified")
            finally:
                store.close()

    def test_refund_failure_after_success_never_finalizes(self):
        action = replace(refund_claim(), created_at=BASE)
        self.store.append_claim(action)
        self.approve(action)
        provider = MockRefundProvider(self.store)
        receipt_id = provider.request(action.action_id, "order-123", 4999, "USD", "key", BASE)
        provider.webhook(action.action_id, "succeeded", receipt_id, "order-123", 4999, "USD", BASE + timedelta(seconds=1))
        provider.webhook(action.action_id, "failed", receipt_id, "order-123", 4999, "USD", BASE + timedelta(seconds=2))
        self.assertFalse(RefundGate(self.store, self.verifier).can_finalize(action.action_id, action.metadata, now=BASE).allowed)

    def test_refund_scope_cannot_be_satisfied_by_another_receipt(self):
        action = replace(refund_claim(), created_at=BASE)
        self.store.append_claim(action)
        self.approve(action)
        provider = MockRefundProvider(self.store)
        provider.request(action.action_id, "order-123", 4999, "USD", "key", BASE)
        provider.webhook(action.action_id, "succeeded", "unrelated", "order-123", 4999, "USD", BASE)
        self.assertFalse(RefundGate(self.store, self.verifier).can_finalize(action.action_id, action.metadata, now=BASE).allowed)

    def test_refund_authorization_expires_at_evaluation_time(self):
        action = replace(refund_claim(), created_at=BASE)
        self.store.append_claim(action)
        self.approve(action, expiry=BASE + timedelta(minutes=1))
        provider = MockRefundProvider(self.store)
        receipt_id = provider.request(action.action_id, "order-123", 4999, "USD", "key", BASE)
        provider.webhook(action.action_id, "succeeded", receipt_id, "order-123", 4999, "USD", BASE)
        self.assertFalse(RefundGate(self.store, self.verifier).can_finalize(action.action_id, action.metadata, now=BASE + timedelta(minutes=2)).allowed)

    def test_reapproval_after_revocation_is_a_new_decision(self):
        action = claim("auth", "publish_action", requires_authority=True)
        self.store.append_claim(action)
        self.approve(action)
        self.approve(action, decision="revoked", at=BASE + timedelta(seconds=1))
        self.assertEqual(self.verifier.project_receipt("auth", BASE).authority_status, "denied")
        self.approve(action, at=BASE + timedelta(seconds=2))
        self.assertEqual(self.verifier.project_receipt("auth", BASE).authority_status, "approved")

    def test_accepted_without_terminal_keeps_bounded_reconciliation_active(self):
        self.store.append_claim(claim("wait", "notification_sent", deadline=BASE + timedelta(minutes=1), owner="queue"))
        MockProvider(self.store).emit("wait", "accepted", "one", BASE)
        reconciler = Reconciler(self.store, self.verifier, RetryPolicy(max_attempts=2, retry_delay=timedelta(minutes=1), compensation_owner="human"))
        self.assertEqual(len(reconciler.reconcile(BASE + timedelta(minutes=2))), 1)
        self.assertEqual(len(reconciler.reconcile(BASE + timedelta(minutes=2))), 0)
        self.assertEqual(len(reconciler.reconcile(BASE + timedelta(minutes=3))), 1)
        receipt = self.verifier.project_receipt("wait", BASE + timedelta(minutes=3))
        self.assertEqual(receipt.recovery_route, "compensation")
        MockProvider(self.store).emit("wait", "delivered", "one", BASE + timedelta(minutes=4))
        self.assertEqual(self.verifier.project_receipt("wait", BASE + timedelta(minutes=4)).recovery_route, "none")

    def test_new_attempt_success_is_not_poisoned_by_old_attempt_failure(self):
        self.store.append_claim(claim("retry", "notification_sent"))
        provider = MockProvider(self.store)
        provider.emit("retry", "accepted", "old", BASE)
        provider.emit("retry", "bounced", "old", BASE + timedelta(seconds=1))
        provider.emit("retry", "accepted", "new", BASE + timedelta(seconds=2))
        provider.emit("retry", "delivered", "new", BASE + timedelta(seconds=3))
        self.assertEqual(self.verifier.project_receipt("retry", BASE).external_status, "provider_reported_delivered")

    def test_reordered_same_attempt_callbacks_preserve_failure(self):
        for index, events in enumerate(permutations(("accepted", "delivered", "bounced"))):
            action_id = f"order-{index}"
            self.store.append_claim(claim(action_id, "notification_sent"))
            provider = MockProvider(self.store)
            for event in events:
                provider.emit(action_id, event, "same", BASE)
            self.assertEqual(self.verifier.project_receipt(action_id, BASE).external_status, "bounced")

    def test_mock_refund_idempotency_survives_restart_and_rejects_conflicts(self):
        with TemporaryDirectory() as directory:
            database = str(Path(directory, "refund.sqlite3"))
            first_store = EventStore(database)
            first = MockRefundProvider(first_store).request("refund", "order", 100, "USD", "key", BASE)
            first_store.close()
            store = EventStore(database)
            try:
                provider = MockRefundProvider(store)
                self.assertEqual(provider.request("refund", "order", 100, "USD", "key", BASE), first)
                with self.assertRaisesRegex(ValueError, "idempotency"):
                    provider.request("refund", "order", 200, "USD", "key", BASE)
                self.assertEqual(store.event_count("refund"), 1)
            finally:
                store.close()

    def test_concurrent_mock_refunds_share_one_reservation(self):
        with TemporaryDirectory() as directory:
            database = str(Path(directory, "refund.sqlite3"))
            EventStore(database).close()
            def request(_):
                store = EventStore(database)
                try:
                    return MockRefundProvider(store).request("refund", "order", 100, "USD", "key", BASE)
                finally:
                    store.close()
            with ThreadPoolExecutor(max_workers=4) as executor:
                ids = list(executor.map(request, range(8)))
            self.assertEqual(len(set(ids)), 1)

    def test_concurrent_reconcilers_append_one_due_attempt(self):
        with TemporaryDirectory() as directory:
            database = str(Path(directory, "events.sqlite3"))
            store = EventStore(database)
            store.append_claim(claim("wait", "notification_sent", deadline=BASE, owner="queue"))
            store.close()
            def check(_):
                store = EventStore(database)
                try:
                    return Reconciler(store, Verifier(store)).reconcile(BASE + timedelta(minutes=1))
                finally:
                    store.close()
            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(check, range(8)))
            self.assertEqual(sum(len(items) for items in results), 1)

    def test_duplicate_provider_event_does_not_leave_an_open_transaction(self):
        self.store.append_claim(claim("wait", "notification_sent", deadline=BASE, owner="queue"))
        provider = MockProvider(self.store)
        provider.emit("wait", "accepted", "one", BASE)
        provider.emit("wait", "accepted", "one", BASE)
        self.assertEqual(len(Reconciler(self.store, self.verifier).reconcile(BASE + timedelta(minutes=1))), 1)
