"""Demonstrate an approval-gated refund with provider evidence and idempotency."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sacp_verify import AuthorityDecision, Claim, EventStore, MockRefundProvider, RefundGate, Verifier


BASE = datetime(2026, 9, 5, tzinfo=timezone.utc)


def main() -> None:
    store = EventStore()
    try:
        action_id = "refund-demo"
        expected = {"order_id": "order-123", "amount": 4999, "currency": "USD"}
        store.append_claim(
            Claim(
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
                metadata=expected,
            )
        )
        store.record_authority_decision(
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
        provider = MockRefundProvider(store)
        refund_id = provider.request(action_id, **expected, idempotency_key="refund-key-1", observed_at=BASE)
        duplicate_id = provider.request(action_id, **expected, idempotency_key="refund-key-1", observed_at=BASE)
        before = Verifier(store).project_receipt(action_id, BASE)
        print(f"1) accepted only: status={before.external_status}, same_refund_id={refund_id == duplicate_id}")

        provider.webhook(action_id, "succeeded", refund_id, **expected, observed_at=BASE + timedelta(minutes=1))
        gate = RefundGate(store, Verifier(store)).can_finalize(action_id, expected)
        print(f"2) succeeded webhook: allowed={gate.allowed}, reason={gate.reason}")
    finally:
        store.close()


if __name__ == "__main__":
    main()
