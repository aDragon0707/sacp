# SACP Adapter Note Template

Use this template when a framework, agent app, or workflow tool already has runs, traces, tasks, tool calls, checkpoints, handoffs, approvals, or eval outputs.

The adapter note should not ask the project to adopt SACP as a dependency. It should only show how one native completion record can be translated into a SACP receipt.

## Adapter Summary

```text
Project:
Native concept:
SACP target:
Adapter status: docs-only example | prototype | implemented | unknown
```

One sentence:

```text
This note maps <project native run/task/trace/handoff> into a SACP receipt so completion claims can be audited for claims, evidence, next owner, and human approval boundary.
```

## Field Mapping

| Native field or concept | SACP field | Notes |
|---|---|---|
| run id / task id / thread id | `handoff_id` | Use a stable idempotency key for the work request. |
| retry number / attempt number | `attempt_id` | New attempt under same handoff for retry or reassignment. |
| agent name / worker / model | `agent_id` | Actor that produced the receipt. |
| final status / outcome | `method` + `status_code` | `COMPLETE -> 200`, blocked evidence -> `412`, invalid completion -> `400`. |
| tool result / command output | `claims[].source_id` + `verification.evidence_id` | Tool outputs can support `tool_result` claims. |
| final answer / summary | `claims[]` | Split into auditable claims; do not treat summary as evidence by itself. |
| trace id / checkpoint id | `extensions.sacp.chain.checkpoint` or vendor extension | Preserve runtime pointer without changing SACP core fields. |
| next assignee / reviewer / human gate | `next_owner` + `human_decision_required` | Must be concrete. |
| approval event | `extensions.sacp.chain.decisions` | Reference human or trusted-system approval evidence. |

## Minimal SACP Receipt

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
handoff_id: native_task_or_run_id
attempt_id: attempt_001
agent_id: native_agent_or_worker
claims:
  - text: "The agent completed the requested code change."
    claim_type: tool_result
    source_id: native_diff_or_tool_output
    support_status: supported
verification:
  status: passed
  method: "native test or review result"
  evidence_id: native_test_output
residual_risk: "Human review has not approved release."
next_owner: Reviewer
human_decision_required: false
extensions:
  vendor.example.trace_id: native_trace_id
  sacp.chain.profile: sacp-chain
  sacp.chain.project: native_project
  sacp.chain.module: native_module
  sacp.chain.checkpoint: native_checkpoint_id
  sacp.chain.evidence:
    - native_test_output
  sacp.chain.stop_rule: "Stop before release if human approval is absent."
```

## Claim Boundary Rules

- A final answer is not evidence by itself.
- A user statement must remain `user_statement` unless external evidence exists.
- Model reasoning must remain `inference` unless retrieved or tool evidence exists.
- Tool or command output may support `tool_result` claims.
- A publish, release, memory promotion, or external side effect should require a human or trusted-system decision reference when the project requires approval.
- `next_owner` must be a concrete actor, role, coordinator, or `Human`.

## Dirty Cases To Test

Use these before claiming adapter support:

| Dirty case | Expected SACP result |
|---|---|
| Agent says "done" but no receipt exists | `400 invalid_packet` |
| Agent says "tests passed" with no command output | `412 missing_evidence` |
| Same native task id is processed twice | `409 duplicate_handoff` or link existing receipt |
| Retry uses same task id but new attempt | Same `handoff_id`, new `attempt_id` |
| Trace summary claims public fact with no source | `412 missing_evidence` |
| Memory or release approval is missing | `human_decision_required: true` |

## Docs-Only PR Note

```text
This is a docs-only adapter note.

It does not change runtime behavior or add SACP as a dependency.

It shows how a native agent run/task/trace can be represented as a SACP receipt:
- what the agent claimed
- what evidence supports it
- who owns the next step
- whether human approval is required
```

