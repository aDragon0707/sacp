from __future__ import annotations

import unittest
from datetime import timedelta

from examples.github_api_payload_gate import BASE, payload
from sacp_verify import EventStore, GitHubActionsPayloadAdapter, ReleaseGate, Verifier


class GitHubPayloadAdapterTests(unittest.TestCase):
    def evaluate(self, data: dict, reviewers=("release-manager",)):
        store = EventStore()
        self.addCleanup(store.close)
        GitHubActionsPayloadAdapter(store, authorized_reviewers=reviewers).ingest_release(data)
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

    def test_no_trusted_reviewers_means_no_authority(self):
        self.assertFalse(self.evaluate(payload(), reviewers=()).allowed)

    def test_untrusted_review_cannot_grant_authority(self):
        data = payload()
        data["reviews"][0]["user"]["login"] = "random-contributor"
        self.assertFalse(self.evaluate(data).allowed)

    def test_latest_changes_requested_or_dismissal_revokes_prior_approval(self):
        for state in ("CHANGES_REQUESTED", "DISMISSED"):
            data = payload()
            data["reviews"].append({"id": 3002, "state": state, "commit_id": "abc123", "submitted_at": (BASE + timedelta(seconds=1)).isoformat(), "user": {"login": "release-manager"}})
            self.assertFalse(self.evaluate(data).allowed)

    def test_new_approval_after_changes_requested_can_authorize(self):
        data = payload()
        data["reviews"].insert(0, {"id": 3000, "state": "CHANGES_REQUESTED", "commit_id": "abc123", "submitted_at": (BASE - timedelta(seconds=1)).isoformat(), "user": {"login": "release-manager"}})
        self.assertTrue(self.evaluate(data).allowed)

    def test_approval_for_old_commit_does_not_authorize_new_commit(self):
        data = payload()
        data["reviews"][0]["commit_id"] = "old-commit"
        self.assertFalse(self.evaluate(data).allowed)

    def test_other_authorized_reviewer_changes_requested_vetoes_approval(self):
        data = payload()
        data["reviews"].append({"state": "CHANGES_REQUESTED", "commit_id": "abc123", "user": {"login": "security-reviewer"}})
        self.assertFalse(self.evaluate(data, reviewers=("release-manager", "security-reviewer")).allowed)


if __name__ == "__main__":
    unittest.main()
