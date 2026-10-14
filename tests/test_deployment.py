from __future__ import annotations

import unittest
from datetime import timedelta

from examples.deployment_verification import BASE
from sacp_verify import DeploymentGate, EventStore, MockDeploymentProvider, Verifier


class DeploymentVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = EventStore()
        self.verifier = Verifier(self.store)
        self.provider = MockDeploymentProvider(self.store)
        self.gate = DeploymentGate(self.store, self.verifier)

    def tearDown(self) -> None:
        self.store.close()

    def test_accepted_without_health_cannot_finalize(self) -> None:
        self.provider.emit("d1", "accepted", "dep-1", "abc123", BASE)
        decision = self.gate.can_finalize("d1", "abc123", BASE)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "deployment_health_unverified")

    def test_matching_health_allows_finalize(self) -> None:
        self.provider.emit("d2", "accepted", "dep-2", "abc123", BASE)
        self.provider.emit("d2", "healthy", "dep-2", "abc123", BASE + timedelta(minutes=1))
        decision = self.gate.can_finalize("d2", "abc123", BASE)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "deployment_health_verified")
        self.assertEqual(decision.receipt.external_status, "provider_reported_healthy")

    def test_health_for_old_revision_does_not_finalize_current_revision(self) -> None:
        self.provider.emit("d3", "accepted", "dep-3", "abc123", BASE)
        self.provider.emit("d3", "healthy", "dep-3", "old-revision", BASE + timedelta(minutes=1))
        decision = self.gate.can_finalize("d3", "abc123", BASE)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "deployment_health_unverified")

    def test_failed_health_blocks_finalize(self) -> None:
        self.provider.emit("d4", "accepted", "dep-4", "abc123", BASE)
        self.provider.emit("d4", "failed", "dep-4", "abc123", BASE + timedelta(minutes=1))
        decision = self.gate.can_finalize("d4", "abc123", BASE)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "deployment_health_failed")

    def test_rollback_downgrades_finalize(self) -> None:
        self.provider.emit("d5", "accepted", "dep-5", "abc123", BASE)
        self.provider.emit("d5", "healthy", "dep-5", "abc123", BASE + timedelta(minutes=1))
        self.provider.emit("d5", "rolled_back", "dep-5", "abc123", BASE + timedelta(minutes=2))
        decision = self.gate.can_finalize("d5", "abc123", BASE)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "deployment_rolled_back")
        self.assertEqual(decision.receipt.external_status, "deployment_rolled_back")


if __name__ == "__main__":
    unittest.main()
