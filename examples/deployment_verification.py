"""Run the post-deploy verification lifecycle with a mock deployment provider."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sacp_verify import DeploymentGate, EventStore, MockDeploymentProvider, StagingHTTPClient, StagingHTTPServer, Verifier


BASE = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)


def main() -> None:
    store = EventStore()
    verifier = Verifier(store)
    provider = MockDeploymentProvider(store)
    gate = DeploymentGate(store, verifier)
    try:
        provider.emit("deploy-demo", "accepted", "deployment-1", "abc123", BASE)
        print("1) accepted only:", gate.can_finalize("deploy-demo", "abc123", BASE).reason)
        provider.emit("deploy-demo", "healthy", "deployment-1", "abc123", BASE + timedelta(minutes=2))
        decision = gate.can_finalize("deploy-demo", "abc123", BASE + timedelta(minutes=2))
        print("2) health verified:", decision.allowed, decision.reason)
        provider.emit("deploy-demo", "rolled_back", "deployment-1", "abc123", BASE + timedelta(minutes=5))
        decision = gate.can_finalize("deploy-demo", "abc123", BASE + timedelta(minutes=5))
        print("3) later rollback:", decision.allowed, decision.reason)
    finally:
        store.close()


def http_main() -> None:
    store = EventStore()
    server = StagingHTTPServer().start()
    client = StagingHTTPClient(server.base_url, store)
    verifier = Verifier(store)
    gate = DeploymentGate(store, verifier)
    try:
        client.deploy("http-deploy-demo", "abc123", BASE)
        deployment_id = next(iter(server.deployments))
        print("1) HTTP accepted:", gate.can_finalize("http-deploy-demo", "abc123", BASE).reason)
        server.set_health(deployment_id, "healthy")
        client.health("http-deploy-demo", deployment_id, "abc123", BASE + timedelta(minutes=1))
        print("2) HTTP health:", gate.can_finalize("http-deploy-demo", "abc123", BASE + timedelta(minutes=1)).allowed)
        server.set_health(deployment_id, "failed")
        client.health("http-deploy-demo", deployment_id, "abc123", BASE + timedelta(minutes=2))
        print("3) HTTP health failed:", gate.can_finalize("http-deploy-demo", "abc123", BASE + timedelta(minutes=2)).reason)
        client.rollback("http-deploy-demo", deployment_id, "abc123", BASE + timedelta(minutes=3))
        print("4) HTTP rollback:", gate.can_finalize("http-deploy-demo", "abc123", BASE + timedelta(minutes=3)).reason)
    finally:
        server.close()
        store.close()


if __name__ == "__main__":
    main()
