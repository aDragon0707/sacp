# SACP Extensions

SACP/0.1 keeps the core small and uses extensions for growth.

扩展不是偷渡核心语义的地方。扩展只能补充上下文，不能覆盖协议核心字段。

## Core Rule

```text
Unknown extensions must not break a valid packet.
Extensions must not override core fields.
Core fields remain the source of protocol truth.
Canonical extension keys must have one documented spelling.
If aliases exist, they must be documented with compatibility behavior.
```

## Extension Location

All extension fields must live under `extensions`.

```yaml
extensions:
  vendor.langgraph.checkpoint_id: checkpoint_123
  vendor.openai.trace_id: trace_abc
  vendor.anthropic.tool_use_id: toolu_123
  sacp.experimental.receipt_score: 0.82
```

## Namespacing

Use namespaced keys.

Recommended patterns:

| Pattern | Use |
|---|---|
| `vendor.<name>.<key>` | Vendor or framework metadata |
| `sacp.experimental.<key>` | Experimental SACP proposal |
| `org.<name>.<key>` | Organization-specific metadata |
| `profile.<name>.<key>` | Profile-specific metadata |

Examples:

```yaml
extensions:
  vendor.langgraph.checkpoint_id: checkpoint_123
  vendor.openai.trace_id: trace_abc
  org.solo_ai_company.worklog_path: 03_Company/AI_Worklogs/2026-05-07.md
  profile.memory.review_state: pending_verification
```

## Receiver Behavior

A receiver should:

- validate core fields
- ignore unknown extensions when it cannot use them
- preserve unknown extensions when practical
- never let extensions override core fields
- never fail a packet only because an unknown extension exists

## Invalid Extension Usage

### Extension Overriding Core Status

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 412
handoff_id: hf_claim_001
attempt_id: attempt_001
agent_id: AI-04
claims: []
verification:
  status: failed
  method: "claim review"
next_owner: Human
human_decision_required: true
extensions:
  vendor.example.status_code: 200
```

Expected behavior:

```yaml
status_code: 412
status_text: missing_evidence
problem: "Extension attempts to override core status. Core status_code remains authoritative."
```

### Core Field Hidden Inside Extensions

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
attempt_id: attempt_001
agent_id: AI-04
claims: []
verification:
  status: passed
  method: "review"
next_owner: Human
human_decision_required: true
extensions:
  sacp.core.handoff_id: hf_claim_001
```

Expected behavior:

```yaml
status_code: 400
status_text: invalid_packet
problem: "handoff_id is a required core field and cannot be supplied only through extensions."
```

## Extension Promotion Rule

An extension should be considered for the core only after:

1. A dirty case proves repeated need.
2. Existing fields create awkward workarounds.
3. The new field is minimal.
4. Backward compatibility is documented.
5. A reference example exists.

## Profiles

Profiles allow gradual adoption without creating one giant protocol.

| Profile | Purpose | v0.1 Status |
|---|---|---|
| `sacp-minimal` | Envelope, receipt, status | MVP |
| `sacp-evidence` | Claim type, support status, verification | MVP |
| `sacp-memory` | Pending memory and promotion boundary | Later |
| `sacp-runtime` | Runtime trace/checkpoint binding | Later |

MVP implements only:

```text
sacp-minimal
sacp-evidence
```
