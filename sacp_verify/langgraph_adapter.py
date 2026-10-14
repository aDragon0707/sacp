"""Minimal LangGraph adapter experiment for an approval-gated release action.

This module is intentionally an experiment seam. LangGraph owns node execution
and checkpointing; SACP owns evidence recording and receipt projection.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from .model import AuthorityDecision, Claim, HostObservation, RetryPolicy
from .provider import MockProvider
from .reconciler import Reconciler
from .store import EventStore
from .verifier import Verifier


class ReleaseState(TypedDict, total=False):
    approved: bool
    provider_event: str
    next_node: str
    thread_id: str
    run_id: str
    logical_checkpoint_id: str


class LangGraphReleaseExperiment:
    """Run a small real LangGraph graph against an isolated SACP store."""

    action_id = "langgraph-release-action"
    thread_id = "langgraph-release-thread"
    run_id = "langgraph-release-run"
    input_digest = "sha256:langgraph-release-input"
    action_scope = "publish-release-announcement"

    def __init__(
        self,
        now: datetime | None = None,
        *,
        store_database: str = ":memory:",
        checkpoint_database: str | None = None,
    ) -> None:
        self.now = now or datetime.now(timezone.utc)
        self.store = EventStore(store_database)
        self.verifier = Verifier(self.store)
        self.provider = MockProvider(self.store, provider="langgraph-mock-provider")
        self._checkpoint_connection: sqlite3.Connection | None = None
        if checkpoint_database is None:
            self._checkpointer = InMemorySaver()
        else:
            self._checkpoint_connection = sqlite3.connect(
                checkpoint_database, check_same_thread=False
            )
            self._checkpointer = SqliteSaver(self._checkpoint_connection)
            self._checkpointer.setup()
        self._graph = self._build_graph()

    def close(self) -> None:
        self.store.close()
        if self._checkpoint_connection is not None:
            self._checkpoint_connection.close()

    def __enter__(self) -> "LangGraphReleaseExperiment":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def invoke(self, *, approved: bool, provider_event: str = "accepted") -> ReleaseState:
        if provider_event not in {"accepted", "none"}:
            raise ValueError("provider_event must be 'accepted' or 'none'")
        return self._graph.invoke(
            {
                "approved": approved,
                "provider_event": provider_event,
                "thread_id": self.thread_id,
                "run_id": self.run_id,
                "logical_checkpoint_id": "cp-start",
            },
            config={"configurable": {"thread_id": self.thread_id}},
        )

    def receipt_at(self, now: datetime | None = None):
        return self.verifier.project_receipt(self.action_id, now or self.now)

    def receipt(self):
        return self.receipt_at()

    def state_snapshot(self):
        return self._graph.get_state(
            {"configurable": {"thread_id": self.thread_id}}
        )

    def reconciler(self, policy: RetryPolicy | None = None) -> Reconciler:
        return Reconciler(self.store, self.verifier, policy=policy)

    def _build_graph(self):
        graph = StateGraph(ReleaseState)
        graph.add_node("prepare", self._prepare)
        graph.add_node("approval", self._approval)
        graph.add_node("dispatch", self._dispatch)
        graph.add_edge(START, "prepare")
        graph.add_edge("prepare", "approval")
        graph.add_conditional_edges(
            "approval",
            lambda state: "dispatch" if state.get("approved") else "awaiting_approval",
            {"dispatch": "dispatch", "awaiting_approval": END},
        )
        graph.add_edge("dispatch", END)
        return graph.compile(checkpointer=self._checkpointer)

    def _prepare(self, state: ReleaseState) -> ReleaseState:
        host_event = self.store.record_host_observation(
            HostObservation(
                action_id=self.action_id,
                kind="test_run",
                source="langgraph-deterministic-runner",
                thread_id=self.thread_id,
                run_id=self.run_id,
                checkpoint_id="cp-prepare",
                payload={
                    "command": "python -m unittest discover -s tests -v",
                    "exit_code": 0,
                    "output_digest": "sha256:langgraph-tests",
                },
                observed_at=self.now,
                idempotency_key="langgraph-release:test-run",
            )
        )
        self.store.append_claim(
            Claim(
                action_id=self.action_id,
                claim_type="notification_sent",
                text="release announcement is ready to publish",
                thread_id=self.thread_id,
                run_id=self.run_id,
                checkpoint_id="cp-prepare",
                input_digest=self.input_digest,
                action_scope=self.action_scope,
                evidence_refs=(host_event,),
                requires_authority=True,
                attestation_deadline=self.now + timedelta(minutes=10),
                reconciliation_owner="langgraph-reconciliation-queue",
                created_at=self.now,
            )
        )
        return {"logical_checkpoint_id": "cp-prepare", "next_node": "approval"}

    def _approval(self, state: ReleaseState) -> ReleaseState:
        if not state.get("approved"):
            return {"logical_checkpoint_id": "cp-approval", "next_node": "awaiting_approval"}
        self.store.record_authority_decision(
            AuthorityDecision(
                action_id=self.action_id,
                decision="approved",
                owner="langgraph-release-manager",
                thread_id=self.thread_id,
                run_id=self.run_id,
                checkpoint_id="cp-prepare",
                input_digest=self.input_digest,
                action_scope=self.action_scope,
                expires_at=self.now + timedelta(hours=1),
                decided_at=self.now,
                rationale="Approved by the experiment input; this is not provider success.",
            )
        )
        return {"logical_checkpoint_id": "cp-approval", "next_node": "dispatch"}

    def _dispatch(self, state: ReleaseState) -> ReleaseState:
        if state.get("provider_event") == "accepted":
            self.provider.emit(
                self.action_id,
                "accepted",
                "langgraph-provider-receipt",
                self.now + timedelta(minutes=1),
            )
        return {"logical_checkpoint_id": "cp-dispatch", "next_node": "dispatched"}
