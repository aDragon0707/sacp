"""A real localhost HTTP staging target and evidence-producing client."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .model import ProviderObservation
from .store import EventStore


@dataclass
class _DeploymentState:
    deployment_id: str
    revision: str
    health: str = "pending"
    rolled_back: bool = False


class _Handler(BaseHTTPRequestHandler):
    server: "StagingHTTPServer"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        body = self._body()
        if self.path == "/deploy":
            revision = body.get("revision")
            if not revision:
                self._json(400, {"error": "revision is required"})
                return
            deployment = _DeploymentState(str(uuid.uuid4()), revision)
            with self.server.lock:
                self.server.deployments[deployment.deployment_id] = deployment
            self._json(202, {"deployment_id": deployment.deployment_id, "status": "accepted", "revision": revision})
            return
        if self.path == "/rollback":
            deployment_id = body.get("deployment_id")
            with self.server.lock:
                deployment = self.server.deployments.get(deployment_id)
                if deployment is None:
                    self._json(404, {"error": "deployment not found"})
                    return
                deployment.rolled_back = True
                deployment.health = "rolled_back"
            self._json(200, {"deployment_id": deployment_id, "status": "rolled_back", "revision": deployment.revision})
            return
        self._json(404, {"error": "not found"})

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self.path.startswith("/health"):
            self._json(404, {"error": "not found"})
            return
        query = self.path.split("?", 1)[1] if "?" in self.path else ""
        params = dict(item.split("=", 1) for item in query.split("&") if "=" in item)
        deployment_id = params.get("deployment_id")
        with self.server.lock:
            deployment = self.server.deployments.get(deployment_id)
            if deployment is None:
                self._json(404, {"error": "deployment not found"})
                return
            status = deployment.health
            revision = deployment.revision
        code = 200 if status == "healthy" else 503 if status == "failed" else 200
        self._json(code, {"deployment_id": deployment_id, "status": status, "revision": revision})


class StagingHTTPServer(ThreadingHTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.lock = threading.Lock()
        self.deployments: dict[str, _DeploymentState] = {}
        self.thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server_port}"

    def start(self) -> "StagingHTTPServer":
        self.thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.thread.start()
        return self

    def close(self) -> None:
        self.shutdown()
        self.server_close()
        if self.thread:
            self.thread.join(timeout=2)

    def set_health(self, deployment_id: str, status: str) -> None:
        if status not in {"healthy", "failed"}:
            raise ValueError(f"Unsupported health status: {status}")
        with self.lock:
            self.deployments[deployment_id].health = status


class StagingHTTPClient:
    def __init__(self, base_url: str, store: EventStore, provider: str = "staging-http") -> None:
        self.base_url = base_url.rstrip("/")
        self.store = store
        self.provider = provider

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def deploy(self, action_id: str, revision: str, observed_at) -> str:
        code, result = self._request("POST", "/deploy", {"revision": revision})
        if code != 202:
            raise RuntimeError(f"staging deploy failed with HTTP {code}")
        return self.store.record_provider_observation(
            ProviderObservation(
                action_id=action_id,
                provider=self.provider,
                receipt_id=result["deployment_id"],
                provider_event="accepted",
                observed_at=observed_at,
                raw_digest=f"http:{code}:{result['deployment_id']}",
                metadata={"revision": revision},
            )
        )

    def health(self, action_id: str, deployment_id: str, revision: str, observed_at) -> str:
        code, result = self._request("GET", f"/health?deployment_id={deployment_id}")
        event = "healthy" if code == 200 and result.get("status") == "healthy" else "failed"
        self.store.record_provider_observation(
            ProviderObservation(
                action_id=action_id,
                provider=self.provider,
                receipt_id=deployment_id,
                provider_event=event,
                observed_at=observed_at,
                raw_digest=f"http:{code}:{deployment_id}:{result.get('status')}",
                metadata={"revision": result.get("revision", revision)},
            )
        )
        return event

    def rollback(self, action_id: str, deployment_id: str, revision: str, observed_at) -> str:
        code, result = self._request("POST", "/rollback", {"deployment_id": deployment_id})
        if code != 200:
            raise RuntimeError(f"staging rollback failed with HTTP {code}")
        return self.store.record_provider_observation(
            ProviderObservation(
                action_id=action_id,
                provider=self.provider,
                receipt_id=deployment_id,
                provider_event="rolled_back",
                observed_at=observed_at,
                raw_digest=f"http:{code}:{deployment_id}:rolled_back",
                metadata={"revision": result["revision"]},
            )
        )
