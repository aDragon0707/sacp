"""Append-only SQLite storage for claims and observations."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

from .model import (
    AuthorityDecision,
    Claim,
    HostObservation,
    ProviderObservation,
    ReconciliationEvent,
)


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported payload value: {type(value)!r}")


def _payload(value: Any) -> str:
    raw = asdict(value) if is_dataclass(value) else value
    return json.dumps(raw, default=_json_default, sort_keys=True, separators=(",", ":"))


class EventStore:
    """Small append-only event store; callers never receive a mutable row."""

    def __init__(self, database: str = ":memory:") -> None:
        self._connection = sqlite3.connect(database)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                action_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                dedupe_key TEXT,
                UNIQUE(event_type, action_id, dedupe_key)
            )
            """
        )
        self._connection.commit()
        self._connection.execute("CREATE TABLE IF NOT EXISTS mock_refund_requests (provider TEXT NOT NULL, request_key TEXT NOT NULL, request_json TEXT NOT NULL, receipt_id TEXT NOT NULL, PRIMARY KEY(provider, request_key))")
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    @contextmanager
    def transaction(self):
        """Serialize a read/decision/append unit across SQLite connections."""
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def _append(
        self,
        event_type: str,
        action_id: str,
        actor: str,
        value: Any,
        created_at: datetime,
        dedupe_key: str | None = None,
    ) -> str:
        payload_json = _payload(value)
        digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        event_id = str(uuid.uuid4())
        managed_transaction = self._connection.in_transaction
        try:
            self._connection.execute(
                "INSERT INTO events (event_id, event_type, action_id, actor, created_at, payload_json, payload_digest, dedupe_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    event_type,
                    action_id,
                    actor,
                    created_at.isoformat(),
                    payload_json,
                    digest,
                    dedupe_key,
                ),
            )
            if not managed_transaction:
                self._connection.commit()
            return event_id
        except sqlite3.IntegrityError:
            if not managed_transaction:
                self._connection.rollback()
            if dedupe_key is None:
                raise
            row = self._connection.execute(
                "SELECT event_id FROM events WHERE event_type=? AND action_id=? AND dedupe_key=?",
                (event_type, action_id, dedupe_key),
            ).fetchone()
            if row is None:
                raise
            return str(row["event_id"])

    def append_claim(self, claim: Claim) -> str:
        created_at = claim.created_at or datetime.now().astimezone()
        return self._append("claim", claim.action_id, claim.actor, claim, created_at)

    def record_host_observation(self, observation: HostObservation) -> str:
        observed_at = observation.observed_at or datetime.now().astimezone()
        key = observation.idempotency_key or f"{observation.kind}:{observed_at.isoformat()}"
        return self._append(
            "host_observation",
            observation.action_id,
            "deterministic_host",
            observation,
            observed_at,
            key,
        )

    def record_provider_observation(self, observation: ProviderObservation) -> str:
        return self._append(
            "provider_observation",
            observation.action_id,
            f"provider:{observation.provider}",
            observation,
            observation.observed_at,
            f"{observation.provider}:{observation.receipt_id}:{observation.provider_event}",
        )

    def record_authority_decision(self, decision: AuthorityDecision) -> str:
        decided_at = decision.decided_at or datetime.now().astimezone()
        return self._append(
            "authority_decision",
            decision.action_id,
            f"authority:{decision.owner}",
            decision,
            decided_at,
            hashlib.sha256(_payload(decision).encode("utf-8")).hexdigest(),
        )

    def record_reconciliation(self, event: ReconciliationEvent) -> str:
        return self._append(
            "reconciliation",
            event.action_id,
            f"reconciler:{event.owner}",
            event,
            event.checked_at,
            f"{event.claim_ref}:{event.attempt}:{event.result}" if event.claim_ref else f"{event.result}:{event.checked_at.isoformat()}",
        )

    def record_mock_refund_request(self, observation: ProviderObservation, key: str) -> str:
        """Atomically reserve a mock identity and append its accepted event.

        Scoped to this SQLite database and provider; no external payment executes.
        Reusing a key for a different action or request raises ValueError.
        """
        request = _payload({"action_id": observation.action_id, "metadata": observation.metadata})
        with self.transaction():
            row = self._connection.execute("SELECT request_json, receipt_id FROM mock_refund_requests WHERE provider=? AND request_key=?", (observation.provider, key)).fetchone()
            if row:
                if row["request_json"] != request:
                    raise ValueError("idempotency key conflicts with an existing refund request")
                return str(row["receipt_id"])
            self._connection.execute("INSERT INTO mock_refund_requests VALUES (?, ?, ?, ?)", (observation.provider, key, request, observation.receipt_id))
            self.record_provider_observation(observation)
            return observation.receipt_id

    def events(self, action_id: str | None = None) -> list[sqlite3.Row]:
        if action_id is None:
            return list(self._connection.execute("SELECT * FROM events ORDER BY sequence"))
        return list(
            self._connection.execute(
                "SELECT * FROM events WHERE action_id=? ORDER BY sequence", (action_id,)
            )
        )

    def event_count(self, action_id: str | None = None) -> int:
        if action_id is None:
            return int(self._connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])
        return int(
            self._connection.execute("SELECT COUNT(*) FROM events WHERE action_id=?", (action_id,)).fetchone()[0]
        )

    @staticmethod
    def decode(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "event_id": row["event_id"],
            "event_type": row["event_type"],
            "action_id": row["action_id"],
            "actor": row["actor"],
            "created_at": row["created_at"],
            "payload": json.loads(row["payload_json"]),
            "payload_digest": row["payload_digest"],
        }
