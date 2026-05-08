# Sample Corpus Batch 001 Review

Date: 2026-05-07

## Summary

Batch 001 translated 10 real workflow samples into SACP receipts.

Sources:

- Solo-AI-Company-OS: 3
- Socrates Focus: 4
- SACP development/testing process: 3

## Result

All 10 samples were translatable into SACP receipts without inventing facts.

Important distinction:

```text
Translatable does not mean fully verified.
```

Several receipts had to preserve claims as `user_statement` or `inference`, not `retrieved_fact` or `tool_result`.

## Main Findings

### 1. Existing Worklogs Already Want Receipt Semantics

Solo-AI-Company-OS worklogs already contain:

- task received
- files read
- work completed
- verification status
- known gaps
- next owner
- founder decision needed

SACP mostly formalizes what the better worklogs were already doing.

### 2. Task Packets Must Not Become Completion Receipts

The Socrates `MVP-MEM-002` work packet was a task request, not proof of implementation.

SACP handled this by producing a blocked receipt instead of pretending completion.

This is a major value point.

### 3. Claim Typing Prevents Overtrust

Many raw statements were not external facts. They were:

- worklog statements
- reviewer judgments
- design decisions
- historical handoff claims

SACP forced them into `user_statement` or `inference`, preserving honesty.

### 4. The Current Field Set Is Enough For Batch 001

No new core field was required.

Useful existing fields:

- `residual_risk`
- `verification.status`
- `next_owner`
- `human_decision_required`
- `claim_type`
- `support_status`

### 5. Friction Remains Around Status Code Meaning

`412 missing_evidence` covered:

- not enough evidence for fact claim
- not enough governance evidence for spec promotion
- task packet lacking completion evidence

This is acceptable for v0.1, but should be watched.

## Recommendation

Do not add fields yet.

Next test should collect 10 more samples that are uglier:

- raw model answers with no worklog structure
- failed coding-agent runs
- half-completed tool outputs
- contradictory agent summaries
- real handoff where next owner is unclear

Batch 001 passed because many sources were already disciplined. Batch 002 should be messier.

