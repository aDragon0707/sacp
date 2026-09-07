# SACP Roadmap

Chinese version: [ROADMAP.zh-CN.md](./ROADMAP.zh-CN.md)

## v0.1-alpha: Text-First Protocol Kit

Status: current

Scope:

- Envelope
- Receipt
- Status codes
- Claim types
- Support status
- Dirty Run cases
- AgentOps Doctor reference skill
- Local validator
- Example packets
- Sample corpus receipts
- Protocol evolution rules

Protocol-core non-goals. The spec itself deliberately requires none of these; the reference engine (`sacp_verify/`) uses SQLite and a localhost HTTP staging provider to demonstrate verification/reconciliation, but a conforming implementation does not have to:

- no hosted platform
- no database requirement (spec core)
- no HTTP endpoint (spec core)
- no automatic memory promotion
- no model training pipeline
- no correctness guarantee

## Receipt Chain Profile

Status: documentation and examples first; validator enforcement later only if dirty cases prove the need.

Receipt Chain is a profile for long-running, multi-module, and multi-agent work. It keeps the SACP core small by storing chain metadata in namespaced extensions rather than adding new required fields. See [SACP_RECEIPT_CHAIN.md](./SACP_RECEIPT_CHAIN.md).

## Protocol Design References

Status: active design guidance.

SACP borrows protocol discipline from HTTP, Git, OpenTelemetry, MIME, and RFC-style normative wording. This is now the default design route for protocol wording and boundary decisions. See [PROTOCOL_DESIGN_REFERENCES.md](./PROTOCOL_DESIGN_REFERENCES.md).

## v0.2: Schemas And Stronger Validation

Status: docs-only plan first; validator enforcement later only if dirty cases prove the need.

Plan: [JSON_SCHEMA_PLAN.md](./JSON_SCHEMA_PLAN.md), [Chinese version](./JSON_SCHEMA_PLAN.zh-CN.md)

Candidate additions:

- JSON Schema for envelope and receipt
- stricter CLI validation
- structured receipt completeness report
- improved Dirty Run runner
- public-safe sample corpus expansion

## v0.3: Runtime Adapters

Candidate adapters:

- Docs-only adapter note template
- OpenClaw / Longju docs-only adapter note
- OpenClaw / Longju state ledger
- LangGraph checkpoint mapping
- MCP tool-call evidence mapping
- A2A task-message mapping
- local Markdown vault adapter

## v0.4: Transport Bindings

Possible HTTP binding:

```http
POST /sacp/handoffs/{handoff_id}/claim
POST /sacp/handoffs/{handoff_id}/attempts/{attempt_id}/complete
GET  /sacp/receipts/{receipt_id}
```

The transport must not change the protocol meaning.

## v0.5: Conformance Suite

Candidate additions:

- public Dirty Run benchmark
- conformance profiles
- receipt completeness badge
- compatibility reports for popular agent frameworks

## v1.0: Stable Minimal Standard

Freeze only after real adoption:

- required envelope fields
- required receipt fields
- method set
- claim taxonomy
- support status
- core status codes
- extension compatibility rules

Do not freeze:

- runtime
- UI
- storage
- model provider
- training method
