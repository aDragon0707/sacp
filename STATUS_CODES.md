# SACP Status Codes

SACP status codes divide responsibility and guide retry behavior.

状态码的作用不是装饰，而是告诉下游：这次事务成功了吗，能不能重试，问题归谁，下一步该怎么办。

## Families

| Family | Meaning |
|---|---|
| `2xx` | Completed, accepted, or no action required |
| `3xx` | Direction changed by newer authority |
| `4xx` | Packet or work request problem |
| `5xx` | Agent, lease, or execution failure |

## v0.1 Required Codes

| Code | Name | Meaning | Typical Fix |
|---:|---|---|---|
| 200 | `completed` | Work completed and valid receipt exists | Continue to `next_owner` |
| 202 | `accepted_processing` | Work accepted or lease acquired | Wait for receipt or lease expiration |
| 204 | `no_action_needed` | Nothing new to process | Stop or archive |
| 301 | `superseded_by_human_decision` | A newer human decision overrides the work | Follow the human decision |
| 400 | `invalid_packet` | Required fields are missing or invalid | Repair packet |
| 409 | `duplicate_handoff` | Same handoff and same source already processed | Return existing receipt or no-op |
| 412 | `missing_evidence` | Claim lacks required evidence | Add evidence or downgrade claim |
| 423 | `lease_active` | Another owner holds active lease | Wait or ask coordinator |
| 500 | `agent_error` | Agent failed internally | Retry with same handoff and new attempt |
| 504 | `lease_expired` | Lease expired before completion | Retry or reassign |

## Retry Guidance

| Code | Retry? | Guidance |
|---:|---|---|
| 200 | No | Work is done. Continue to next owner. |
| 202 | Not yet | Wait for receipt or lease expiry. |
| 204 | No | No action required. |
| 301 | No | Human decision supersedes task. |
| 400 | No | Fix packet first. |
| 409 | No | Do not duplicate work. Use existing receipt. |
| 412 | After fix | Add evidence or change claim type/support status. |
| 423 | Later | Wait until lease expires or owner releases it. |
| 500 | Yes | New attempt under same `handoff_id`. |
| 504 | Yes | New attempt under same `handoff_id`. |

## Code Details

### 200 completed

Use when the attempt completed and a valid receipt exists.

Must include:

- valid `receipt`
- `claims`
- `verification`
- `next_owner`
- `human_decision_required`

### 202 accepted_processing

Use when a handoff was accepted or a lease was created, but no completion receipt exists yet.

Do not treat `202` as success.

Also use `202` when the same `handoff_id` arrives with a changed `source_fingerprint` and valid core fields. This means changed input or rework, not duplicate completion.

### 204 no_action_needed

Use when the packet is valid but no new work is required.

Common cases:

- duplicate handoff has already produced a receipt
- input has no actionable change
- task was intentionally empty

### 301 superseded_by_human_decision

Use when a newer human decision overrides the previous request.

This preserves human authority without pretending the agent solved the conflict.

### 400 invalid_packet

Use when the packet cannot be interpreted due to missing or invalid core fields.

Unknown `extensions` alone must not cause `400`.

### 409 duplicate_handoff

Use when the same `handoff_id` and same `source_fingerprint` were already processed.

The receiver should return or point to the existing receipt when possible.

### 412 missing_evidence

Use when a claim requires support but lacks it.

Common cases:

- `retrieved_fact` has no source
- `tool_result` has no tool output id
- a public claim is marked `supported` without evidence
- an inference is presented as fact

### 423 lease_active

Use when another owner holds an active lease.

The correct behavior is to wait, not to race.

### 500 agent_error

Use when the agent failed internally.

Examples:

- model call failed after accepting work
- agent crashed
- agent could not produce a valid receipt

### 504 lease_expired

Use when the lease expired before completion.

The coordinator may create a new `attempt_id` under the same `handoff_id`.
