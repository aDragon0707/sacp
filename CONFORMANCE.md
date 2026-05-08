# SACP/0.1 Conformance

Conformance means a system can preserve SACP work-state discipline.

Conformance 不是“这个 agent 很聪明”的认证，而是“它能否按 SACP/0.1 守住回执、证据、交接、租约和记忆边界”。

## Core Rule

```text
No receipt, no trust.
```

No implementation may claim SACP/0.1 completion support unless it can produce or validate a receipt.

## Levels

### Level 0: Packet Reader

The system can read SACP packets.

Required abilities:

- identify `protocol: SACP/0.1`
- distinguish `handoff` from `receipt`
- read core fields
- reject missing required fields with `400 invalid_packet`
- ignore or preserve unknown `extensions`

Cannot claim:

- receipt generation
- Dirty Run support
- memory boundary support

### Level 1: Receipt Producer

The system can produce a valid receipt for one work attempt.

Required abilities:

- generate required receipt fields
- include at least one claim or explicitly state no factual claim was made
- classify claims by `claim_type`
- mark `support_status`
- include `verification`
- assign concrete `next_owner`
- set `human_decision_required`

Cannot claim:

- duplicate handoff protection
- lease protection
- benchmark conformance

### Level 2: Dirty Run Checked

The system can diagnose the v0.1 Dirty Run cases.

Required abilities:

- detect duplicate handoff
- detect active lease collision
- detect expired lease
- treat changed source fingerprint as rework
- detect missing evidence
- separate user statement from retrieved fact
- separate inference from retrieved fact
- block automatic memory promotion
- reject completion without receipt
- reject ambiguous next owner

Minimum pass condition:

```text
10/10 Dirty Run cases return the expected status family and repair direction.
```

Exact wording may vary, but status family and required fix must be correct.

### Level 3: Cross-Agent Handoff

The system can hand work from one actor to another without losing state.

Required abilities:

- preserve `handoff_id`
- create new `attempt_id` for retry or reassignment
- preserve or cite prior receipt
- maintain `source_fingerprint`
- prevent duplicate completion
- route to `next_owner`

### Level 4: Memory Boundary

The system can protect memory promotion.

Required abilities:

- distinguish pending memory from verified memory
- block auto-promotion without approval evidence
- require `PROMOTE` for memory upgrade
- set `human_decision_required: true` for memory promotion unless a trusted-system approval exists
- record approval source when promotion is allowed

## Claims A System May Make

Safe:

- "Supports SACP/0.1 Level 1 receipt production."
- "Passes SACP/0.1 Dirty Run Level 2."
- "Preserves SACP envelope and receipt fields."

Unsafe:

- "SACP guarantees correctness."
- "SACP certifies agent intelligence."
- "SACP makes memory safe automatically."
- "SACP replaces runtime-level security."

## Conformance Report Shape

```yaml
protocol: SACP/0.1
type: conformance_report
implementation: example-agent
tested_at: 2026-05-07T22:00:00+08:00
level_claimed: 2
dirty_run:
  total_cases: 10
  passed: 10
  failed: 0
limitations:
  - "No runtime lease lock; lease checks are diagnostic only."
human_decision_required: false
```

