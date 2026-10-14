from __future__ import annotations

import unittest
from datetime import timedelta

from examples.deployment_verification import BASE
from sacp_verify import DeploymentGate, EventStore, StagingHTTPClient, StagingHTTPServer, Verifier


class StagingHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = EventStore()
        self.server = StagingHTTPServer().start()
        self.client = StagingHTTPClient(self.server.base_url, self.store)
        self.gate = DeploymentGate(self.store, Verifier(self.store))

    def tearDown(self) -> None:
        self.server.close()
        self.store.close()

    def test_real_http_health_lifecycle(self) -> None:
        self.client.deploy("http-1", "abc123", BASE)
        deployment_id = next(iter(self.server.deployments))
        self.assertEqual(self.gate.can_finalize("http-1", "abc123", BASE).reason, "deployment_health_unverified")

        self.server.set_health(deployment_id, "healthy")
        self.client.health("http-1", deployment_id, "abc123", BASE + timedelta(minutes=1))
        self.assertTrue(self.gate.can_finalize("http-1", "abc123", BASE).allowed)

        self.server.set_health(deployment_id, "failed")
        self.client.health("http-1", deployment_id, "abc123", BASE + timedelta(minutes=2))
        self.assertEqual(self.gate.can_finalize("http-1", "abc123", BASE).reason, "deployment_health_failed")

    def test_health_for_wrong_revision_is_not_used(self) -> None:
        self.client.deploy("http-2", "abc123", BASE)
        deployment_id = next(iter(self.server.deployments))
        self.server.set_health(deployment_id, "healthy")
        self.client.health("http-2", deployment_id, "abc123", BASE + timedelta(minutes=1))
        self.assertFalse(self.gate.can_finalize("http-2", "other-revision", BASE).allowed)

    def test_real_http_rollback_blocks_finalize(self) -> None:
        self.client.deploy("http-3", "abc123", BASE)
        deployment_id = next(iter(self.server.deployments))
        self.server.set_health(deployment_id, "healthy")
        self.client.health("http-3", deployment_id, "abc123", BASE + timedelta(minutes=1))
        self.assertTrue(self.gate.can_finalize("http-3", "abc123", BASE).allowed)
        self.client.rollback("http-3", deployment_id, "abc123", BASE + timedelta(minutes=2))
        decision = self.gate.can_finalize("http-3", "abc123", BASE)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "deployment_rolled_back")


if __name__ == "__main__":
    unittest.main()
