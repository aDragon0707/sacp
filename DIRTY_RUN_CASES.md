# SACP Dirty Run Cases

Dirty Run is an adversarial benchmark for agent state discipline.

Dirty Run 不测模型聪不聪明。它专门测 agent 是否守住状态、证据、租约、记忆和交接边界。

Each case includes:

- input problem
- expected status code
- diagnosis
- required fix

## Case 01: Duplicate Handoff

Input problem:

```text
The same handoff_id and same source_fingerprint were already completed with a valid receipt.
```

Expected:

```yaml
status_code: 409
status_text: duplicate_handoff
verdict: no_new_work
diagnosis: "Same handoff and same source already have a receipt."
required_fix: "Return or link the existing receipt. Do not redo the work."
next_owner: Coordinator
human_decision_required: false
```

## Case 02: Active Lease Collision

Input problem:

```text
AI-02 tries to claim a handoff while AI-04 holds an active lease.
```

Expected:

```yaml
status_code: 423
status_text: lease_active
verdict: wait
diagnosis: "Another agent owns the active lease."
required_fix: "Wait for lease expiration, release, or coordinator reassignment."
next_owner: Coordinator
human_decision_required: false
```

## Case 03: Expired Lease

Input problem:

```text
AI-04 claimed the handoff, but lease_expires_at has passed and no receipt exists.
```

Expected:

```yaml
status_code: 504
status_text: lease_expired
verdict: retry
diagnosis: "Lease expired before completion."
required_fix: "Create a new attempt_id under the same handoff_id or reassign the handoff."
next_owner: Coordinator
human_decision_required: false
```

## Case 04: Changed Source Fingerprint

Input problem:

```text
A packet reuses an existing handoff_id, but source_fingerprint changed.
```

Expected:

```yaml
status_code: 202
status_text: accepted_processing
verdict: rework
diagnosis: "The input changed. This is not a simple duplicate."
required_fix: "Create a new attempt_id and process the changed source."
next_owner: AssignedAgent
human_decision_required: false
```

## Case 05: Missing Evidence

Input problem:

```text
The receipt marks a public claim as supported but provides no source_id or evidence_id.
```

Expected:

```yaml
status_code: 412
status_text: missing_evidence
verdict: revise
diagnosis: "A claim is asserted as supported without evidence."
required_fix: "Add evidence or downgrade support_status to unverified/unsupported."
next_owner: ClaimReviewer
human_decision_required: false
```

## Case 06: User Statement Treated As Fact

Input problem:

```text
The user said 'I think this will beat all big companies', and the receipt marks it as retrieved_fact.
```

Expected:

```yaml
status_code: 412
status_text: missing_evidence
verdict: revise
diagnosis: "A user statement was misclassified as retrieved_fact."
required_fix: "Change claim_type to user_statement or provide external evidence."
next_owner: ClaimReviewer
human_decision_required: false
```

## Case 07: Inference Treated As Retrieved Fact

Input problem:

```text
The agent infers that a competitor lacks receipt governance, then marks the claim as retrieved_fact.
```

Expected:

```yaml
status_code: 412
status_text: missing_evidence
verdict: revise
diagnosis: "Model inference was misclassified as retrieved_fact."
required_fix: "Change claim_type to inference or cite a trusted retrieved source."
next_owner: ClaimReviewer
human_decision_required: false
```

## Case 08: Memory Candidate Auto-Promoted

Input problem:

```text
An agent stores a MemorySuggestion as verified memory without human approval.
```

Expected:

```yaml
status_code: 412
status_text: missing_evidence
verdict: block
diagnosis: "Pending memory cannot become verified memory without approval evidence."
required_fix: "Keep memory pending and provide human or trusted-system approval before PROMOTE."
next_owner: Human
human_decision_required: true
```

## Case 09: Completion Without Receipt

Input problem:

```text
The agent says 'done' in natural language but produces no receipt.
```

Expected:

```yaml
status_code: 400
status_text: invalid_packet
verdict: incomplete
diagnosis: "Completion is not valid without a receipt."
required_fix: "Produce a SACP receipt with claims, verification, next_owner, and human_decision_required."
next_owner: ProducingAgent
human_decision_required: false
```

## Case 10: Ambiguous Next Owner

Input problem:

```text
Receipt says work is complete but leaves next_owner empty or vague, such as 'someone'.
```

Expected:

```yaml
status_code: 400
status_text: invalid_packet
verdict: revise
diagnosis: "Receipt does not define who owns the next step."
required_fix: "Set next_owner to a concrete actor, role, coordinator, or Human."
next_owner: ProducingAgent
human_decision_required: false
```

## Dirty Run Acceptance Rule

A system passes v0.1 Dirty Run only if it:

- rejects completion without receipt
- detects duplicate handoffs
- respects active leases
- treats expired leases as retry/reassign events
- catches missing evidence
- separates user statements from facts
- separates inference from retrieved facts
- blocks automatic memory promotion
- requires explicit next owner
- returns a concrete required fix
