# SACP/0.1 Specification Draft

Status: experimental draft

> No receipt, no trust.

## 1. Purpose

SACP/0.1 defines a minimal protocol for auditable AI agent work transactions.

SACP/0.1 的目标不是定义 agent 如何思考，而是定义一次 agent 工作如何被表示、验证、交接和审查。

The smallest reliable unit is not a prompt. It is a **work transaction**.

```text
request -> claim -> execute -> verify -> receipt -> next owner
```

## 2. Design Principles

### 2.1 Small Core

The core must remain small enough that a human can understand it in ten minutes.

v0.1 only standardizes:

- envelope
- receipt
- methods
- resource types
- status codes
- claim types
- support status
- extension rules
- dirty-run expectations

### 2.2 Text First

The canonical v0.1 format is Markdown plus YAML.

Later versions may add JSON Schema, validators, CLIs, HTTP bindings, and runtime adapters, but those must not change the core meaning.

### 2.3 State Outside The Model

LLM calls are stateless. SACP packets carry the minimum state identity required for continuation:

- `handoff_id`
- `attempt_id`
- `agent_id`
- `source_fingerprint`
- `status_code`
- `claims`
- `verification`
- `next_owner`

Long-term state belongs in logs, vaults, databases, ledgers, or user-approved memory systems, not silently inside model behavior.

### 2.4 Evidence Boundaries

Different claim sources have different trust levels.

SACP forbids mixing them silently:

- user statements are not verified facts
- model inference is not retrieved evidence
- pending memory is not verified memory
- completion without receipt is not trusted completion

## 3. Packet Types

SACP/0.1 defines two primary packet types.

| Type | Meaning |
|---|---|
| `handoff` | A work request, transfer, claim, retry, block, or other state transition around a work item |
| `receipt` | A proof-of-work record for one attempt under one handoff |

Other packet-like objects may exist in implementations, but v0.1 only requires handoff-style envelopes and receipts.

## 4. Envelope

An Envelope is the protocol wrapper. It is similar to HTTP headers or a shipping label.

Prompt text, task details, and human-readable instructions belong in the body. Protocol identity belongs in the envelope.

Required envelope fields:

| Field | Meaning |
|---|---|
| `protocol` | Protocol version, fixed as `SACP/0.1` for this draft |
| `type` | Packet type, usually `handoff` |
| `method` | Action requested or performed |
| `resource_type` | Resource category being acted on |
| `resource_id` | Concrete resource identifier |
| `handoff_id` | Stable idempotency key for the work request |
| `attempt_id` | Specific execution attempt under the handoff |
| `agent_id` | Actor claiming, processing, or reporting the work |
| `created_at` | ISO 8601 timestamp |
| `source_fingerprint` | Digest or stable identifier for the input source |
| `content_type` | Format of the body, for example `text/markdown` |

Optional envelope fields:

| Field | Meaning |
|---|---|
| `lease_owner` | Actor currently holding the lease |
| `lease_expires_at` | ISO 8601 lease expiration time |
| `extensions` | Namespaced non-core metadata |

## 5. Receipt

A Receipt is the proof of work for one attempt.

Required receipt fields:

| Field | Meaning |
|---|---|
| `protocol` | Protocol version |
| `type` | Must be `receipt` |
| `method` | Usually `COMPLETE`, `FAIL`, or `BLOCK` |
| `status_code` | SACP status code |
| `handoff_id` | Stable work request id |
| `attempt_id` | Attempt this receipt describes |
| `agent_id` | Actor that produced the receipt |
| `claims` | List of auditable assertions |
| `verification` | Verification status and method |
| `next_owner` | Actor responsible for the next step |
| `human_decision_required` | Whether human approval is required before further action |

Recommended receipt fields:

| Field | Meaning |
|---|---|
| `residual_risk` | Known remaining risk or unverified surface |
| `processed_at` | ISO 8601 timestamp for receipt creation |
| `source_fingerprint` | Source digest, repeated for audit convenience |
| `extensions` | Namespaced non-core metadata |

## 6. Methods

Keep methods few. New methods require dirty cases and evidence that existing methods are insufficient.

| Method | Meaning | Idempotency |
|---|---|---|
| `READ` | Read state without mutation | Idempotent |
| `CLAIM` | Claim a handoff lease | Idempotent for same lease owner |
| `COMPLETE` | Complete an attempt and write a receipt | Idempotent for same receipt identity |
| `FAIL` | Mark the attempt failed | Idempotent for same attempt |
| `BLOCK` | Stop for human or upstream decision | Idempotent |
| `RETRY` | Start a new attempt under the same handoff | Controlled mutation |
| `PROPOSE` | Propose memory, skill, or claim | Non-final |
| `PROMOTE` | Human or trusted system approves an upgrade | High risk, gated |

## 7. Resource Types

| Resource Type | Meaning |
|---|---|
| `task` | Work goal |
| `handoff` | Transfer request or work claim |
| `attempt` | One execution try |
| `receipt` | Work proof |
| `claim` | Auditable assertion |
| `memory_item` | Persistent memory candidate or item |
| `skill_candidate` | Candidate reusable procedure |
| `human_decision` | Human authority record |

## 8. Claim Types

| Claim Type | Meaning |
|---|---|
| `user_statement` | The user said or believed it |
| `retrieved_fact` | Retrieved from a trusted source |
| `tool_result` | Produced by a tool, test, command, API, or runtime |
| `inference` | Model reasoning, interpretation, or judgment |

Rule: a receiver must not treat `user_statement` or `inference` as `retrieved_fact` unless new evidence is supplied.

## 9. Support Status

| Support Status | Meaning |
|---|---|
| `supported` | Evidence exists and is cited |
| `unsupported` | Asserted without evidence |
| `unverified` | Plausible but not verified |
| `not_applicable` | Question, suggestion, preference, or non-factual content |

## 10. Status Codes

SACP status codes divide responsibility.

| Family | Meaning |
|---|---|
| `2xx` | Completed, accepted, or no action required |
| `3xx` | Direction changed by newer authority |
| `4xx` | Packet or work request problem |
| `5xx` | Agent, lease, or execution failure |

v0.1 required codes:

| Code | Name |
|---:|---|
| 200 | `completed` |
| 202 | `accepted_processing` |
| 204 | `no_action_needed` |
| 301 | `superseded_by_human_decision` |
| 400 | `invalid_packet` |
| 409 | `duplicate_handoff` |
| 412 | `missing_evidence` |
| 423 | `lease_active` |
| 500 | `agent_error` |
| 504 | `lease_expired` |

See [STATUS_CODES.md](./STATUS_CODES.md).

## 11. Idempotency And Retry

`handoff_id` is the stable idempotency key.

Same `handoff_id` plus same `source_fingerprint` means the same work request.

Same `handoff_id` plus different `attempt_id` means a retry, not a new task.

If `source_fingerprint` changes, the receiver should treat the packet as rework or changed input, not as a simple duplicate.

## 12. Lease

A lease prevents multiple agents from working the same handoff at the same time.

```yaml
lease_owner: AI-04
lease_expires_at: 2026-05-07T21:00:00+08:00
```

Rules:

- If another actor owns an active lease, return `423 lease_active`.
- If a lease expired before completion, return `504 lease_expired` or start `RETRY` with the same `handoff_id` and a new `attempt_id`.
- A lease is not proof of completion. Only a valid receipt can complete an attempt.

## 13. Memory Boundary

SACP/0.1 supports memory boundaries but does not define a memory database.

Minimum rule:

```text
MemorySuggestion or pending memory must not become verified memory through agent assertion alone.
```

Promotion requires `PROMOTE` and human or trusted-system approval.

## 14. Extension Compatibility

Extensions go under `extensions`.

```yaml
extensions:
  vendor.langgraph.checkpoint_id: checkpoint_123
  vendor.openai.trace_id: trace_abc
  sacp.experimental.receipt_score: 0.82
```

Rules:

- Unknown extensions must not break a valid packet.
- Extensions must not override core fields.
- Core fields remain the source of protocol truth.
- Receivers should preserve unknown extensions when practical.

## 15. Conformance For v0.1

A minimal SACP/0.1 implementation can be as simple as a human or LLM checklist.

It must be able to:

- read envelope fields
- identify duplicate handoffs
- distinguish attempts from retries
- produce a receipt
- classify claims by source type
- mark evidence support status
- identify missing evidence
- block automatic memory promotion
- assign next owner
- decide whether human approval is required

It does not need:

- JSON Schema
- CLI validation
- server endpoints
- account system
- database
- automatic tool execution

See [CONFORMANCE.md](./CONFORMANCE.md) for conformance levels.

## 16. Lifecycle

SACP/0.1 work should follow a small lifecycle:

```text
handoff created
-> claimed
-> lease active
-> attempt running
-> completed / failed / blocked
-> receipt produced
-> next owner assigned
```

See [LIFECYCLE.md](./LIFECYCLE.md).

## 17. Governance

SACP changes should follow:

```text
rough consensus + running dirty cases
```

New core fields, methods, or status codes require dirty cases and reference examples.

See [GOVERNANCE.md](./GOVERNANCE.md).

## 18. Reference Validator

SACP/0.1 includes a small reference validator:

```bash
python validator.py --examples
```

The validator checks packet shape and known protocol vocabulary. It does not verify external facts or prove that work was actually executed.

See [VALIDATOR.md](./VALIDATOR.md).
