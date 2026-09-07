"""Adapter from a deterministic GitHub Actions release fixture to SACP events."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .model import AuthorityDecision, Claim, HostObservation, ProviderObservation
from .store import EventStore


class GitHubActionsFixtureAdapter:
    """Ingest a local fixture; no GitHub network access is performed."""

    def __init__(self, store: EventStore) -> None:
        self.store = store

    def ingest(self, fixture: dict[str, Any]) -> dict[str, str]:
        action_id = fixture["action_id"]
        observed_at = _parse_time(fixture["observed_at"])
        common = {
            "thread_id": fixture["thread_id"],
            "run_id": fixture["run_id"],
            "checkpoint_id": fixture["checkpoint_id"],
        }
        commit = fixture["commit"]
        check = fixture["check_run"]
        artifact = fixture["artifact"]
        check_event = self.store.record_host_observation(
            HostObservation(
                action_id=action_id,
                kind="ci_check",
                source="github-actions",
                payload={**check, "head_sha": commit},
                observed_at=observed_at,
                idempotency_key=f"github:check:{check['check_run_id']}",
                **common,
            )
        )
        artifact_event = self.store.record_host_observation(
            HostObservation(
                action_id=action_id,
                kind="artifact",
                source="github-actions",
                payload={**artifact, "commit": artifact.get("commit", commit)},
                observed_at=observed_at,
                idempotency_key=f"github:artifact:{artifact['artifact_name']}:{artifact['digest']}",
                **common,
            )
        )
        metadata = {"commit": commit}
        self.store.append_claim(
            Claim(
                action_id=action_id,
                claim_type="tests_passed",
                text=f"Tests passed for {commit}",
                evidence_refs=(check_event,),
                metadata=metadata,
                created_at=observed_at,
                **common,
            )
        )
        self.store.append_claim(
            Claim(
                action_id=action_id,
                claim_type="artifact_built",
                text=f"Artifact built for {commit}",
                evidence_refs=(artifact_event,),
                metadata=metadata,
                created_at=observed_at,
                **common,
            )
        )
        ready_event = self.store.append_claim(
            Claim(
                action_id=action_id,
                claim_type="ready_to_publish",
                text=f"Release {commit} is ready to publish",
                evidence_refs=(check_event, artifact_event),
                metadata=metadata,
                requires_authority=True,
                input_digest=fixture["input_digest"],
                action_scope=fixture["action_scope"],
                created_at=observed_at,
                **common,
            )
        )
        approval = fixture.get("approval")
        approval_event = ""
        if approval:
            approval_event = self.store.record_authority_decision(
                AuthorityDecision(
                    action_id=action_id,
                    decision=approval["decision"],
                    owner=approval["owner"],
                    input_digest=approval["input_digest"],
                    action_scope=approval["action_scope"],
                    expires_at=_parse_time(approval["expires_at"]),
                    decided_at=observed_at,
                    rationale=approval.get("rationale"),
                    **common,
                )
            )
        for item in fixture.get("provider_observations", []):
            self.store.record_provider_observation(
                ProviderObservation(
                    action_id=action_id,
                    provider=item["provider"],
                    receipt_id=item["receipt_id"],
                    provider_event=item["provider_event"],
                    observed_at=_parse_time(item.get("observed_at", fixture["observed_at"])),
                    raw_digest=item["raw_digest"],
                )
            )
        return {"check_event": check_event, "artifact_event": artifact_event, "ready_claim": ready_event, "approval_event": approval_event}


class GitHubActionsPayloadAdapter:
    """Map GitHub REST-shaped payloads into the same evidence model as fixtures."""

    def __init__(self, store: EventStore) -> None:
        self.store = store

    def ingest_release(self, payload: dict[str, Any]) -> dict[str, str]:
        required = (
            "action_id",
            "thread_id",
            "run_id",
            "checkpoint_id",
            "input_digest",
            "action_scope",
            "workflow_run",
            "artifact",
            "observed_at",
        )
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"Missing GitHub release payload fields: {', '.join(missing)}")

        action_id = payload["action_id"]
        observed_at = _parse_time(payload["observed_at"])
        common = {
            "thread_id": payload["thread_id"],
            "run_id": payload["run_id"],
            "checkpoint_id": payload["checkpoint_id"],
        }
        workflow_run = payload["workflow_run"]
        artifact = payload["artifact"]
        commit = workflow_run.get("head_sha")
        if not commit:
            raise ValueError("workflow_run.head_sha is required")
        artifact_commit = artifact.get("workflow_run", {}).get("head_sha", commit)
        check_run_id = str(workflow_run.get("check_suite_id") or workflow_run.get("id") or "")
        conclusion = workflow_run.get("conclusion")
        output_digest = workflow_run.get("output_digest")
        check_event = self.store.record_host_observation(
            HostObservation(
                action_id=action_id,
                kind="ci_check",
                source="github-actions-rest",
                payload={
                    "check_run_id": check_run_id,
                    "name": workflow_run.get("name", "workflow"),
                    "conclusion": conclusion,
                    "head_sha": commit,
                    "output_digest": output_digest,
                },
                observed_at=observed_at,
                idempotency_key=f"github:workflow:{workflow_run.get('id', check_run_id)}",
                **common,
            )
        )
        artifact_event = self.store.record_host_observation(
            HostObservation(
                action_id=action_id,
                kind="artifact",
                source="github-actions-rest",
                payload={
                    "artifact_name": artifact.get("name"),
                    "digest": artifact.get("digest"),
                    "commit": artifact_commit,
                },
                observed_at=observed_at,
                idempotency_key=f"github:artifact:{artifact.get('id', artifact.get('name'))}:{artifact.get('digest')}",
                **common,
            )
        )
        metadata = {"commit": commit}
        self.store.append_claim(
            Claim(
                action_id=action_id,
                claim_type="tests_passed",
                text=f"Tests passed for {commit}",
                evidence_refs=(check_event,),
                metadata=metadata,
                created_at=observed_at,
                **common,
            )
        )
        self.store.append_claim(
            Claim(
                action_id=action_id,
                claim_type="artifact_built",
                text=f"Artifact built for {commit}",
                evidence_refs=(artifact_event,),
                metadata=metadata,
                created_at=observed_at,
                **common,
            )
        )
        ready_event = self.store.append_claim(
            Claim(
                action_id=action_id,
                claim_type="ready_to_publish",
                text=f"Release {commit} is ready to publish",
                evidence_refs=(check_event, artifact_event),
                metadata=metadata,
                requires_authority=True,
                input_digest=payload["input_digest"],
                action_scope=payload["action_scope"],
                created_at=observed_at,
                **common,
            )
        )
        approval_event = ""
        reviews = payload.get("reviews", [])
        if reviews and isinstance(reviews[0], list):
            reviews = [review for page in reviews for review in page]
        for review in reviews:
            if review.get("state") != "APPROVED" or review.get("commit_id") != commit:
                continue
            reviewer = review.get("user", {}).get("login", "github-reviewer")
            expires_at = _parse_time(
                payload.get("approval_expires_at", (observed_at + timedelta(hours=1)).isoformat())
            )
            approval_event = self.store.record_authority_decision(
                AuthorityDecision(
                    action_id=action_id,
                    decision="approved",
                    owner=f"github-review:{reviewer}",
                    input_digest=payload["input_digest"],
                    action_scope=payload["action_scope"],
                    expires_at=expires_at,
                    decided_at=_parse_time(review.get("submitted_at", payload["observed_at"])),
                    **common,
                )
            )
            break
        return {
            "check_event": check_event,
            "artifact_event": artifact_event,
            "ready_claim": ready_event,
            "approval_event": approval_event,
        }


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed
