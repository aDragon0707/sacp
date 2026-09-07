from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from sacp_verify import (
    AuthorityDecision,
    Claim,
    EventStore,
    MockRefundProvider,
    RefundGate,
    Verifier,
)


BASE = datetime(2026, 9, 5, tzinfo=timezone.utc)


def refund_claim(action_id: str = "refund-1") -> Claim:
    return Claim(
        action_id=action_id,
        claim_type="refund_requested",
        text="refund customer order",
        thread_id="refund-thread",
        run_id="refund-run",
        checkpoint_id="refund-checkpoint",
        input_digest="sha256:refund-input",
        action_scope="refund:order-123:4999:USD",
        requires_authority=True,
        attestation_deadline=BASE + timedelta(minutes=10),
        reconciliation_owner="refund-reconciliation",
        created_at=BASE,
        metadata={"order_id": "order-123", "amount": 4999, "currency": "USD"},
    )


class RefundProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = EventStore()
        self.verifier = Verifier(self.store)
        self.provider = MockRefundProvider(self.store)

    def tearDown(self) -> None:
        self.store.close()

    def approve(self, action_id: str = "refund-1") -> None:
        self.store.record_authority_decision(
            AuthorityDecision(
                action_id=action_id,
                decision="approved",
                owner="refund-manager",
                thread_id="refund-thread",
                run_id="refund-run",
                checkpoint_id="refund-checkpoint",
                input_digest="sha256:refund-input",
                action_scope="refund:order-123:4999:USD",
                expires_at=BASE + timedelta(hours=1),
                decided_at=BASE,
            )
        )

    def test_accepted_is_not_refund_succeeded(self) -> None:
        self.store.append_claim(refund_claim())
        self.approve()
        self.provider.request("refund-1", "order-123", 4999, "USD", "refund-key-1", BASE)
        receipt = self.verifier.project_receipt("refund-1", BASE)
        self.assertEqual(receipt.external_status, "transport_accepted")
        self.assertNotEqual(receipt.external_status, "refund_succeeded")
        decision = RefundGate(self.store, self.verifier).can_finalize("refund-1", refund_claim().metadata)
        self.assertFalse(decision.allowed)

    def test_idempotency_key_does_not_create_duplicate_refund(self) -> None:
        self.store.append_claim(refund_claim())
        first = self.provider.request("refund-1", "order-123", 4999, "USD", "refund-key-1", BASE)
        second = self.provider.request("refund-1", "order-123", 4999, "USD", "refund-key-1", BASE)
        self.assertEqual(first, second)
        self.assertEqual(self.store.event_count("refund-1"), 2)

    def test_matching_succeeded_webhook_allows_finalize(self) -> None:
        self.store.append_claim(refund_claim())
        self.approve()
        refund_id = self.provider.request("refund-1", "order-123", 4999, "USD", "refund-key-1", BASE)
        self.provider.webhook("refund-1", "succeeded", refund_id, "order-123", 4999, "USD", BASE + timedelta(minutes=1))
        receipt = self.verifier.project_receipt("refund-1", BASE + timedelta(minutes=1))
        self.assertEqual(receipt.external_status, "refund_succeeded")
        decision = RefundGate(self.store, self.verifier).can_finalize("refund-1", refund_claim().metadata)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "refund_succeeded")

    def test_wrong_amount_webhook_cannot_finalize(self) -> None:
        self.store.append_claim(refund_claim())
        self.approve()
        refund_id = self.provider.request("refund-1", "order-123", 4999, "USD", "refund-key-1", BASE)
        self.provider.webhook("refund-1", "succeeded", refund_id, "order-123", 3999, "USD", BASE + timedelta(minutes=1))
        decision = RefundGate(self.store, self.verifier).can_finalize("refund-1", refund_claim().metadata)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "refund_scope_mismatch")


if __name__ == "__main__":
    unittest.main()
