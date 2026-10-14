from __future__ import annotations

import unittest
from datetime import timedelta

from examples.github_api_payload_gate import BASE, payload
from sacp_verify import EventStore, GitHubActionsPayloadAdapter, ReleaseGate, Verifier


class GitHubPayloadAdapterTests(unittest.TestCase):
    def evaluate(self, data: dict):
        store = EventStore()
        self.addCleanup(store.close)
        GitHubActionsPayloadAdapter(store).ingest_release(data)
        return ReleaseGate(store, Verifier(store)).can_proceed(data["action_id"], now=BASE)

    def test_api_payload_without_review_blocks(self) -> None:
        decision = self.evaluate(payload(approval=False))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.receipt.host_status, "completed")
        self.assertEqual(decision.receipt.authority_status, "pending")
        self.assertEqual(decision.reason, "release_approval_missing_or_stale")

    def test_api_payload_with_matching_review_allows(self) -> None:
        decision = self.evaluate(payload())
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.receipt.overall_status, "ready_for_external_action")
        self.assertEqual(decision.receipt.next_action_owner, "github-review:release-manager")

    def test_api_payload_artifact_commit_mismatch_blocks(self) -> None:
        decision = self.evaluate(payload(artifact_commit="other-commit"))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "release_evidence_missing_or_invalid")
        self.assertEqual(decision.receipt.overall_status, "unverified")

    def test_expired_review_blocks(self) -> None:
        data = payload()
        data["approval_expires_at"] = (BASE - timedelta(seconds=1)).isoformat()
        decision = self.evaluate(data)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.receipt.authority_status, "expired")

    def test_paginated_review_arrays_are_flattened(self) -> None:
        data = payload(approval=False)
        data["reviews"] = [
            [{"state": "COMMENTED", "commit_id": "abc123", "user": {"login": "reviewer-1"}}],
            [{
                "state": "APPROVED",
                "commit_id": "abc123",
                "submitted_at": BASE.isoformat(),
                "user": {"login": "release-manager"},
            }],
        ]
        decision = self.evaluate(data)
        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
