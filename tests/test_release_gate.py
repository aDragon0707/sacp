from __future__ import annotations

import unittest
from datetime import timedelta

from examples.github_release_gate import BASE, fixture
from sacp_verify import EventStore, GitHubActionsFixtureAdapter, ReleaseGate, Verifier


class ReleaseGateTests(unittest.TestCase):
    def evaluate(self, data: dict):
        store = EventStore()
        self.addCleanup(store.close)
        GitHubActionsFixtureAdapter(store).ingest(data)
        return ReleaseGate(store, Verifier(store)).can_proceed(data["action_id"], now=BASE)

    def test_missing_approval_blocks_release(self) -> None:
        decision = self.evaluate(fixture())
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "release_approval_missing_or_stale")
        self.assertEqual(decision.receipt.host_status, "completed")
        self.assertEqual(decision.receipt.authority_status, "pending")

    def test_matching_approval_allows_release_preflight(self) -> None:
        approval = {
            "decision": "approved",
            "owner": "release-manager",
            "input_digest": "sha256:release-v1.4.0",
            "action_scope": "publish-v1.4.0",
            "expires_at": (BASE + timedelta(hours=1)).isoformat(),
        }
        decision = self.evaluate(fixture(approval=approval))
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "release_evidence_and_authority_verified")
        self.assertEqual(decision.receipt.overall_status, "ready_for_external_action")

    def test_artifact_from_different_commit_blocks_release(self) -> None:
        approval = {
            "decision": "approved",
            "owner": "release-manager",
            "input_digest": "sha256:release-v1.4.0",
            "action_scope": "publish-v1.4.0",
            "expires_at": (BASE + timedelta(hours=1)).isoformat(),
        }
        decision = self.evaluate(fixture(approval=approval, artifact_commit="other-commit"))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "release_evidence_missing_or_invalid")
        self.assertEqual(decision.receipt.overall_status, "unverified")


if __name__ == "__main__":
    unittest.main()
