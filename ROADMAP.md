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

Non-goals:

- no hosted platform
- no database requirement
- no HTTP endpoint
- no automatic memory promotion
- no model training pipeline
- no correctness guarantee

## v0.2: Schemas And Stronger Validation

Candidate additions:

- JSON Schema for envelope and receipt
- stricter CLI validation
- structured receipt completeness report
- improved Dirty Run runner
- public-safe sample corpus expansion

## v0.3: Runtime Adapters

Candidate adapters:

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

