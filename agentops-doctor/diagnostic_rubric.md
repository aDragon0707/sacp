# AgentOps Doctor Diagnostic Rubric

Use this rubric to diagnose a SACP/0.1 packet or messy agent worklog.

## Step 1: Identify Packet Type

Decide whether the input is:

- valid envelope
- valid receipt
- incomplete receipt
- worklog without receipt
- dirty case
- non-SACP text

If required core fields are missing, return `400 invalid_packet`.

## Step 2: Check Idempotency

Inspect:

- `handoff_id`
- `attempt_id`
- `source_fingerprint`
- any existing receipt references

Rules:

- Same `handoff_id` and same `source_fingerprint` already completed: `409 duplicate_handoff`.
- Same `handoff_id` and changed `source_fingerprint`: treat as rework.
- New `attempt_id` under same `handoff_id`: retry, not new task.

## Step 3: Check Lease

Inspect:

- `lease_owner`
- `lease_expires_at`
- current actor
- current time if available

Rules:

- Another owner has active lease: `423 lease_active`.
- Lease expired without receipt: `504 lease_expired`.
- Lease alone never means completion.

## Step 4: Check Receipt Completeness

Required receipt fields:

- `protocol`
- `type`
- `method`
- `status_code`
- `handoff_id`
- `attempt_id`
- `agent_id`
- `claims`
- `verification`
- `next_owner`
- `human_decision_required`

If the agent says "done" without receipt, return `400 invalid_packet`.

## Step 5: Check Claim Boundaries

For each claim, inspect:

- `text`
- `claim_type`
- `source_id`
- `support_status`

Allowed claim types:

- `user_statement`
- `retrieved_fact`
- `tool_result`
- `inference`

Allowed support status:

- `supported`
- `unsupported`
- `unverified`
- `not_applicable`

Dirty patterns:

- user statement marked as `retrieved_fact`
- inference marked as `retrieved_fact`
- `retrieved_fact` without source
- `tool_result` without tool output or command evidence
- public claim marked `supported` without evidence

Use `412 missing_evidence` when evidence is missing or misclassified.

## Step 6: Check Memory Boundary

Dirty pattern:

```text
pending memory -> verified memory
```

without human or trusted-system approval.

Return:

```yaml
status_code: 412
status_text: missing_evidence
human_decision_required: true
next_owner: Human
```

## Step 7: Check Next Owner

`next_owner` must be concrete.

Acceptable:

- `Human`
- `Coordinator`
- `AI-04`
- `ClaimReviewer`
- a named role or system owner

Unacceptable:

- `someone`
- `later`
- empty value
- vague natural language

If invalid, return `400 invalid_packet`.

## Step 8: Produce Diagnosis

Return YAML first, then short explanation.

The YAML must include:

- `status_code`
- `status_text`
- `verdict`
- `receipt_completeness`
- `claim_findings`
- `memory_warning`
- `next_owner`
- `human_decision_required`
- `required_fix`

Do not over-explain. The goal is repairable diagnosis.
