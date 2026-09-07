"""Run the optional LangGraph release verification experiment."""

from __future__ import annotations

from datetime import datetime, timezone

from sacp_verify import RetryPolicy
from sacp_verify.langgraph_adapter import LangGraphReleaseExperiment


def main() -> None:
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)
    with LangGraphReleaseExperiment(now=now) as blocked:
        blocked_state = blocked.invoke(approved=False)
        blocked_receipt = blocked.receipt()
        print(
            "1) approval missing: "
            f"next={blocked_state['next_node']}, status={blocked_receipt.overall_status}, "
            f"provider_events={len(blocked_receipt.provider_evidence_refs)}"
        )

    with LangGraphReleaseExperiment(now=now) as approved:
        approved_state = approved.invoke(approved=True)
        approved_receipt = approved.receipt()
        print(
            "2) approval matched: "
            f"next={approved_state['next_node']}, status={approved_receipt.overall_status}, "
            f"external={approved_receipt.external_status}, "
            f"provider_events={len(approved_receipt.provider_evidence_refs)}"
        )

    with LangGraphReleaseExperiment(now=now) as orphaned:
        orphaned.invoke(approved=True, provider_event="none")
        reconciler = orphaned.reconciler(
            RetryPolicy(max_attempts=2, compensation_owner="release-compensation")
        )
        timeout_at = datetime(2026, 9, 5, 0, 11, tzinfo=timezone.utc)
        reconciler.reconcile(timeout_at)
        timeout_receipt = orphaned.receipt_at(timeout_at)
        print(
            "3) graph ended without provider witness: "
            f"status={timeout_receipt.external_status}, route={timeout_receipt.recovery_route}, "
            f"retry_allowed={timeout_receipt.retry_allowed}"
        )

        compensation_at = datetime(2026, 9, 5, 0, 16, tzinfo=timezone.utc)
        reconciler.reconcile(compensation_at)
        compensation_receipt = orphaned.receipt_at(compensation_at)
        print(
            "4) retry budget exhausted: "
            f"route={compensation_receipt.recovery_route}, "
            f"owner={compensation_receipt.next_action_owner}, "
            f"retry_allowed={compensation_receipt.retry_allowed}"
        )

    with LangGraphReleaseExperiment(now=now) as delayed:
        delayed.invoke(approved=True, provider_event="none")
        delayed_reconciler = delayed.reconciler(
            RetryPolicy(max_attempts=2, compensation_owner="release-compensation")
        )
        delayed_reconciler.reconcile(timeout_at)
        delayed.provider.emit(
            delayed.action_id,
            "accepted",
            "delayed-langgraph-provider-receipt",
            datetime(2026, 9, 5, 0, 13, tzinfo=timezone.utc),
        )
        delayed_receipt = delayed.receipt_at(compensation_at)
        print(
            "5) delayed provider witness: "
            f"external={delayed_receipt.external_status}, "
            f"route={delayed_receipt.recovery_route}, "
            f"retry_allowed={delayed_receipt.retry_allowed}"
        )


if __name__ == "__main__":
    main()
