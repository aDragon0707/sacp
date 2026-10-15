# SACP roadmap

[中文](./ROADMAP.zh-CN.md) · [Current status](./STATUS.md) · Updated 2026-10-15

SACP/0.1 is the current exchange contract. Roadmap milestones describe capability maturity; they are not promises that every runtime feature needs a new protocol version.

## Available: protocol and executable reference baseline

The text-first spec, validator, dirty cases, Receipt Chain profile, local Doctor, examples and corpus are present. The Python runtime includes SQLite event storage, claim-specific evidence policy, separate authority/provider state, release/deployment/refund gates, bounded reconciliation, mock idempotency, GitHub payload and LangGraph adapters, and localhost HTTP experiments.

CI runs a cross-platform core matrix, explicit LangGraph integration, strict protocol validation and a deterministic harness with positive controls. Trusted default-branch code cross-checks GitHub execution facts and current PR identity before constructing a receipt. Merging remains a manual maintainer action. See [architecture](./docs/architecture.md) and [verification scope](./docs/verification-2026-10-15.md).

## Next: real-agent evaluation pilot

[ADR-0001](./docs/adr/0001-real-agent-evaluation-with-pi.md) retains the existing deterministic engine scenarios and selects Pi as the first real-agent pilot. Implement a Python outer runner using Pi's JSON subprocess interface, isolate and pin its environment, then collect actual coding-task trajectories and independently verify the delivered patches. The adapter, provider/model, budget and real results are not yet available.

Start with a small fixed task set and compare SACP with a predefined test-based baseline on the same records. Report missed false completions, incorrect blocks, indeterminate outcomes and overhead; separate injected faults from naturally occurring failures. Keep model calls out of required PR CI. Acceptance stages and stop conditions are defined in the ADR.

## Next: trust and independent acceptance

- Complete an actual controlled fork PR smoke run; synthetic fork API tests are not equivalent.
- Strengthen test-process isolation and protect against adversarial in-process test code; source inventory and execution checks are necessary but insufficient.
- Add authenticated host/provider collection and writer isolation for a concrete integration, rather than inventing a general identity platform.
- Exercise process-crash windows and operational recovery beyond object reopen and SQLite concurrency tests.
- Collect independently reviewed real failure and valid-success cases, including false blocks, with versioned evidence and privacy review.
- If merge queue is enabled, define and verify formal merge-group receipt identity first.

## Candidate: schema and interoperability

The [JSON Schema plan](./JSON_SCHEMA_PLAN.md) is still a plan. Stronger validation, MCP/A2A mappings and public transport bindings require a demonstrated dirty case, minimal contract, compatibility note and reference example. LangGraph and GitHub reference adapters already exist; they are not future-only work. OpenClaw/Longju docs-only notes are not runtime integrations.

Receipt Chain remains an optional namespaced profile. [Protocol design references](./PROTOCOL_DESIGN_REFERENCES.md) guide evolution. Storage, UI, runtime and provider choice remain outside the required SACP core.

## Stable standard: only after evidence

Freeze a stable minimal contract only after real adoption and compatibility evidence. Keep required fields small; vendor details belong under `extensions`. Do not claim a correctness guarantee, automatically promote memory, or expand the core to absorb scheduling, payments, tracing or deployment control.
