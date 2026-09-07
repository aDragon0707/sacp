from __future__ import annotations

import unittest
from datetime import timedelta

from examples.release_task import ACTION_ID, BASE, claim
from sacp_verify import AuthorityDecision, EventStore, HostObservation, MockProvider, Verifier


class ReleaseScenarioTests(unittest.TestCase):
    def test_release_task_requires_approval_and_tracks_provider_downgrade(self) -> None:
        store = EventStore()
        verifier = Verifier(store)
        provider = MockProvider(store, provider="release-announcement-provider")
        try:
            test_event = store.record_host_observation(
                HostObservation(
                    action_id=ACTION_ID,
                    kind="test_run",
                    source="deterministic-ci",
                    thread_id="release-thread",
                    run_id="release-run-1",
                    checkpoint_id="release-checkpoint-1",
                    payload={"exit_code": 0, "output_digest": "sha256:tests-v1.4.0"},
                    observed_at=BASE,
                    idempotency_key="release-v1.4.0:test-run",
                )
            )
            store.append_claim(claim(claim_type="tests_passed", evidence_refs=(test_event,)))
            artifact_event = store.record_host_observation(
                HostObservation(
                    action_id=ACTION_ID,
                    kind="artifact",
                    source="deterministic-build",
                    thread_id="release-thread",
                    run_id="release-run-1",
                    checkpoint_id="release-checkpoint-1",
                    payload={"artifact_name": "release-v1.4.0.tgz", "digest": "sha256:artifact-v1.4.0", "commit": "release-v1.4.0"},
                    observed_at=BASE,
                    idempotency_key="release-v1.4.0:artifact",
                )
            )
            store.append_claim(claim(claim_type="artifact_built", evidence_refs=(artifact_event,)))
            store.append_claim(
                claim(claim_type="ready_to_publish", evidence_refs=(test_event, artifact_event), requires_authority=True)
            )
            before_approval = verifier.project_receipt(ACTION_ID, BASE)
            self.assertEqual(before_approval.overall_status, "needs_approval")
            self.assertEqual(before_approval.host_status, "completed")
            self.assertEqual(before_approval.authority_status, "pending")
            self.assertEqual(before_approval.external_status, "not_attempted")

            store.record_authority_decision(
                AuthorityDecision(
                    action_id=ACTION_ID,
                    decision="approved",
                    owner="release-manager",
                    thread_id="release-thread",
                    run_id="release-run-1",
                    checkpoint_id="release-checkpoint-1",
                    input_digest="sha256:release-v1.4.0",
                    action_scope="publish-release-announcement",
                    expires_at=BASE + timedelta(hours=1),
                    decided_at=BASE + timedelta(minutes=1),
                )
            )
            after_approval = verifier.project_receipt(ACTION_ID, BASE)
            self.assertIsNotNone(after_approval.authority_ref)
            self.assertEqual(after_approval.overall_status, "ready_for_external_action")

            provider.emit(ACTION_ID, "accepted", "provider-release-1", BASE + timedelta(minutes=2))
            accepted = verifier.project_receipt(ACTION_ID, BASE)
            self.assertEqual(accepted.overall_status, "transport_accepted")
            self.assertEqual(accepted.external_status, "transport_accepted")
            provider.emit(ACTION_ID, "delivered", "provider-release-1", BASE + timedelta(minutes=3))
            delivered = verifier.project_receipt(ACTION_ID, BASE)
            self.assertEqual(delivered.overall_status, "provider_reported_delivered")
            self.assertEqual(delivered.external_status, "provider_reported_delivered")
            provider.emit(ACTION_ID, "bounced", "provider-release-1", BASE + timedelta(minutes=4))
            receipt = verifier.project_receipt(ACTION_ID, BASE)
            self.assertEqual(receipt.overall_status, "bounced")
            self.assertEqual(receipt.external_status, "bounced")
            self.assertEqual(store.event_count(ACTION_ID), 9)
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
