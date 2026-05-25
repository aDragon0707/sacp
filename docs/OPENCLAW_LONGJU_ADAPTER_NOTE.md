# OpenClaw / Longju Adapter Note

This is a docs-only adapter note.

It does not change runtime behavior, add SACP as a dependency, or claim that OpenClaw or Longju have official SACP support.

## Adapter Summary

```text
Project: OpenClaw-style local workspace / Longju local operator
Native concept: local task dispatch, worklog, evidence brief, and `.sacp/` shadow ledger
SACP target: SACP/0.1 receipt plus optional Receipt Chain extensions
Adapter status: docs-only example
```

This note maps a local agent task or worklog into a SACP receipt so completion claims can be audited for claims, evidence, next owner, and human approval boundary.

## Native Flow

The public-safe Longju adoption case used this local flow:

```text
human dispatch -> handoff -> attempt -> evidence -> receipt -> next owner
```

In an OpenClaw-style workspace, this can remain file-based:

```text
.sacp/
  handoffs/
  attempts/
  evidence/
  receipts/
  snapshots/
  memory-candidates/
  skill-candidates/
```

SACP does not require this directory layout. It only needs the final receipt to preserve enough state for audit and handoff.

## Field Mapping

| Native field or concept | SACP field | Notes |
|---|---|---|
| human dispatch id / task file path | `handoff_id` | Stable idempotency key for the work request. |
| dispatch body hash / source snapshot | `source_fingerprint` | Used to distinguish duplicate handoff from changed-source rework. |
| attempt packet | `attempt_id` | New attempt under the same handoff for retry or reassignment. |
| local operator name | `agent_id` | Example: `Longju`, `OpenClawAgent`, or a specific worker name. |
| worklog completion claim | `claims[]` | Split summary into auditable claims. The worklog is not evidence by itself. |
| command output / diff / evidence brief | `claims[].source_id` + `verification.evidence_id` | Tool and command outputs can support `tool_result` claims. |
| runtime guard gate | `verification.method` | Example: `PostTask receipt gate` or `public-safe local trial review`. |
| `.sacp/receipts/<id>.yaml` | receipt file path | Storage location is local convention, not core protocol. |
| next assigned reviewer / human | `next_owner` | Must be concrete. |
| release, memory, or skill approval gate | `human_decision_required` + `extensions.sacp.chain.decisions` | Durable promotion or risky side effects should require approval evidence. |
| local checkpoint / context snapshot | `extensions.sacp.chain.checkpoint` | Pointer to local snapshot or checkpoint; does not change core fields. |

## Minimal Receipt

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
handoff_id: hf_longju_public_safe_trial
attempt_id: attempt_001
agent_id: Longju
claims:
  - text: "The false-completion trial returned 412 missing_evidence."
    claim_type: tool_result
    source_id: ev_public_safe_core_trials
    support_status: supported
  - text: "The duplicate-handoff trial returned 204 no_action_needed."
    claim_type: tool_result
    source_id: ev_public_safe_core_trials
    support_status: supported
verification:
  status: passed
  method: "public-safe local trial review"
  evidence_id: ev_public_safe_core_trials
residual_risk: "This receipt describes one local setup; it does not prove universal agent safety."
next_owner: Human
human_decision_required: false
extensions:
  vendor.openclaw.workspace: local_workspace_path
  vendor.longju.ledger: .sacp
  sacp.chain.profile: sacp-chain
  sacp.chain.project: longju_public_safe_trials
  sacp.chain.module: runtime_guard
  sacp.chain.checkpoint: snapshot_public_safe_core_trials
  sacp.chain.evidence:
    - ev_public_safe_core_trials
  sacp.chain.stop_rule: "Stop before external action, memory promotion, or skill promotion unless approval evidence exists."
```

## Dirty Cases To Test Before Claiming Support

| Dirty case | Expected SACP result |
|---|---|
| Worklog says "done" but no receipt exists | `400 invalid_packet` |
| Worklog says "tests passed" with no command output | `412 missing_evidence` |
| Same handoff and same source are processed twice | `409 duplicate_handoff` or link existing receipt |
| Same handoff arrives with changed `source_fingerprint` | `202 accepted_processing` and rework |
| Attempt expires without a receipt | `504 lease_expired` and new attempt under same handoff |
| Memory or skill promotion lacks approval | `human_decision_required: true` |

## Claim Boundary Rules

- A worklog summary is not evidence by itself.
- A user instruction remains a `user_statement` unless external evidence exists.
- Model reasoning remains `inference` unless retrieved or tool evidence exists.
- Command output, diffs, test output, and structured evidence briefs can support `tool_result` claims.
- SACP may make a local workflow easier to resume, audit, block, and review; it does not prove the underlying work is correct.

## Relationship To The Adoption Case

See [ADOPTION_CASE_LONGJU.md](../ADOPTION_CASE_LONGJU.md) for the public-safe adoption case.

This note narrows that case into a reusable adapter mapping. The adoption case reports what one local setup tried; this adapter note shows how similar local records can be represented as SACP receipts.
