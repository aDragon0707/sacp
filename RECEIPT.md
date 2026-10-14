# SACP Receipt

The Receipt is the proof of work.

Receipt 是工作回执。它不是总结，不是聊天回复，也不是“我感觉完成了”。它是一份可审查的事务记录。

## Principle

```text
No receipt, no trust.
```

An attempt is not considered complete unless it produces a valid receipt or an explicit failure/block receipt.

## Required Fields

| Field | Type | Meaning |
|---|---|---|
| `protocol` | string | Protocol version. v0.1 must be `SACP/0.1`. |
| `type` | string | Must be `receipt`. |
| `method` | string | Usually `COMPLETE`, `FAIL`, or `BLOCK`. |
| `status_code` | integer | SACP status code. |
| `handoff_id` | string | Stable work request id. |
| `attempt_id` | string | Attempt id this receipt describes. |
| `agent_id` | string | Actor that produced the receipt. |
| `claims` | list | Auditable claims made by the actor. |
| `verification` | map | Verification status and method. |
| `next_owner` | string | Actor responsible for the next step. |
| `human_decision_required` | boolean | Whether a human decision is required before further action. |

## Recommended Fields

| Field | Type | Meaning |
|---|---|---|
| `processed_at` | string | ISO 8601 timestamp. |
| `source_fingerprint` | string | Source digest repeated for audit convenience. |
| `residual_risk` | string | Remaining uncertainty or uncovered risk. |
| `extensions` | map | Namespaced non-core metadata. |

## Claim Object

Each item in `claims` should use:

```yaml
- text: "The draft contains two over-strong public claims."
  claim_type: inference
  source_id: public_draft_v1
  support_status: supported
```

Required claim fields:

| Field | Meaning |
|---|---|
| `text` | The assertion being made |
| `claim_type` | Source category |
| `source_id` | Evidence, file, tool output, user message, or source reference |
| `support_status` | Evidence support state |

## Claim Types

| Claim Type | Meaning |
|---|---|
| `user_statement` | The user said or believed it |
| `retrieved_fact` | Retrieved from a trusted source |
| `tool_result` | Produced by a tool, test, command, API, or runtime |
| `inference` | Model reasoning, interpretation, or judgment |

Rules:

- User belief does not become fact by being stored.
- Model reasoning does not become retrieved evidence by sounding confident.
- Tool output should cite the tool or command.
- Retrieved facts should cite source identity.

## Support Status

| Support Status | Meaning |
|---|---|
| `supported` | Evidence exists and is cited |
| `unsupported` | Asserted without evidence |
| `unverified` | Plausible but not verified |
| `not_applicable` | Question, suggestion, preference, or non-factual content |

## Verification Object

Recommended shape:

```yaml
verification:
  status: passed
  method: "claim boundary review"
  evidence_id: review_notes_001
```

Allowed `verification.status` values:

| Status | Meaning |
|---|---|
| `passed` | Verification ran and passed |
| `failed` | Verification ran and failed |
| `not_run` | Verification did not run |
| `blocked` | Verification is blocked by missing input, permissions, tools, or human decision |

If verification did not run, the receipt must say why:

```yaml
verification:
  status: not_run
  reason: "User requested analysis only; no tests or external checks were available."
```

## Valid Complete Receipt

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
handoff_id: hf_check_claims_001
attempt_id: attempt_001
agent_id: AI-04
processed_at: 2026-05-07T20:42:00+08:00
source_fingerprint: sha256:abc123
claims:
  - text: "The draft contains two over-strong public claims."
    claim_type: inference
    source_id: public_draft_v1
    support_status: supported
  - text: "Publication approval has not been granted."
    claim_type: user_statement
    source_id: founder_message_2026-05-07
    support_status: supported
verification:
  status: passed
  method: "claim boundary review"
  evidence_id: review_notes_001
residual_risk: "No founder publish approval yet."
next_owner: Human
human_decision_required: true
```

## Micro Receipt For Small Maintenance Tasks

A micro receipt is not a new protocol type. It is the smallest useful way to write a normal SACP receipt for a small, low-risk maintenance task.

Use it when:

- the task is narrow
- the evidence is concrete
- no public release, memory promotion, spending, external contact, or high-impact action is involved
- one claim is enough to describe what was done

Do not use it to hide risk or skip required fields.

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
handoff_id: hf_merge_pr_001
attempt_id: attempt_001
agent_id: Codex
claims:
  - text: "PR #1 was merged and SACP examples validation passed."
    claim_type: tool_result
    source_id: gh_pr_merge_1_and_validator_output
    support_status: supported
verification:
  status: passed
  method: "GitHub CLI and local validator"
  evidence_id: gh_pr_merge_1_and_validator_output
residual_risk: "Only protocol examples were validated; no package release was tested."
next_owner: Human
human_decision_required: false
```

The micro form stays valid because it keeps the required receipt fields, cites evidence, names residual risk, and assigns a concrete next owner.

Reference example: [examples/micro_receipt_maintenance.yaml](./examples/micro_receipt_maintenance.yaml)

## Valid Block Receipt

```yaml
protocol: SACP/0.1
type: receipt
method: BLOCK
status_code: 412
handoff_id: hf_publish_claim_001
attempt_id: attempt_001
agent_id: AI-04
processed_at: 2026-05-07T20:50:00+08:00
claims:
  - text: "The claim says SACP guarantees correctness, but no evidence is provided."
    claim_type: inference
    source_id: draft_readme_v1
    support_status: supported
verification:
  status: failed
  method: "public claim boundary review"
  evidence_id: unsupported_claim_001
residual_risk: "Publishing this claim may overstate protocol guarantees."
next_owner: Human
human_decision_required: true
```

## Invalid Receipt Examples

### Completion Without Claims

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
handoff_id: hf_check_claims_001
attempt_id: attempt_001
agent_id: AI-04
verification:
  status: passed
  method: "review"
next_owner: Human
human_decision_required: true
```

Expected result:

```yaml
status_code: 400
status_text: invalid_packet
problem: "Receipt is missing required field: claims."
```

### Unsupported Fact Claim

```yaml
claims:
  - text: "SACP is already widely adopted by major AI companies."
    claim_type: retrieved_fact
    source_id: none
    support_status: supported
```

Expected result:

```yaml
status_code: 412
status_text: missing_evidence
problem: "Claim is marked as retrieved_fact and supported, but no source exists."
required_fix: "Provide a trusted source or downgrade the claim to inference/unverified."
```

## Human Decision Gate

Set `human_decision_required: true` when the next action involves:

- public release
- spending money
- legal, medical, financial, or safety-sensitive decisions
- contacting external people
- accessing private information
- promoting memory to verified memory
- promoting a skill into reusable procedure
- irreversible or high-impact execution

If this field is `true`, the agent may recommend but must not silently continue as if approval exists.
