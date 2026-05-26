# SACP Receipt Chain

Receipt Chain is an optional SACP profile for long-running, multi-module, and multi-agent work.

It does not answer "which agent should run next?" It answers:

```text
After many handoffs, can the next actor still audit what was done, what evidence exists, what risk remains, and who owns the next step?
```

Chinese version: [SACP_RECEIPT_CHAIN.zh-CN.md](./SACP_RECEIPT_CHAIN.zh-CN.md)

## Boundary

Receipt Chain is not a runtime, scheduler, database, or trace system.

It does not decide:

- which agent runs
- when an agent runs
- which model is used
- where traces are stored
- how evidence files are stored
- how human approval systems are implemented

It only defines audit references for long-running collaboration:

```text
project -> module -> handoff -> attempt -> receipt -> next_owner -> child_handoff
```

The SACP core remains Envelope, Receipt, Status Code, Claim, Evidence, and Next Owner. Receipt Chain only links receipts together.

## Minimal Fields

All Receipt Chain fields live under `extensions`. They do not change the SACP/0.1 required fields.

Recommended shape:

```yaml
extensions:
  sacp.chain.profile: sacp-chain
  sacp.chain.project: sacp_public_launch
  sacp.chain.module: docs
  sacp.chain.parent_handoff: hf_root_public_launch_001
  sacp.chain.depends_on:
    - hf_spec_review_001
    - hf_dirty_case_gallery_001
  sacp.chain.receipts:
    - rcpt_spec_review_001
  sacp.chain.evidence:
    - git_diff
    - validator_output
  sacp.chain.decisions:
    - human_publish_approval_001
  sacp.chain.checkpoint: vendor_trace_or_runtime_checkpoint
  sacp.chain.stop_rule: "Stop if public claim lacks evidence or human approval."
```

| Extension | Meaning |
|---|---|
| `sacp.chain.profile` | Fixed as `sacp-chain` |
| `sacp.chain.project` | Stable long-running project or goal identifier |
| `sacp.chain.module` | Current module, subsystem, workspace, or responsibility area |
| `sacp.chain.parent_handoff` | Parent handoff that produced this child work item |
| `sacp.chain.depends_on` | Upstream handoffs this work depends on |
| `sacp.chain.receipts` | Upstream receipts referenced by this work |
| `sacp.chain.evidence` | Evidence, logs, diffs, test output, or review records referenced by this work |
| `sacp.chain.decisions` | Human or trusted-system decisions referenced by this work |
| `sacp.chain.checkpoint` | External runtime, trace, checkpoint, or session reference |
| `sacp.chain.stop_rule` | Stop condition or human boundary that the next actor must preserve |

The canonical keys are `project`, `module`, and `parent_handoff`.

These names are intentionally short because `extensions.sacp.chain.*` already carries the namespace. They do not override SACP core fields, but they do become the canonical spelling for this profile.

When discussing semantics outside the wire format, you can read them as project_id, module_id, and parent_handoff_id identity concepts. Do not add separate `_id` keys in the payload unless a future profile version explicitly declares an alias rule.

## Role And State Clarity

Receipt Chain works best when the next actor can tell which state is current, which state was verified, and who is allowed to review it.

In long-running work, one word like `latest_stable_commit` can become overloaded:

```text
current Git HEAD        -> what the workspace currently contains
verified content commit -> last commit whose product/content changes were reviewed
verified state commit   -> last commit whose handoff/status documents were reviewed
```

If all three are called "latest stable", the next agent receives three batons and has to guess which one is the race baton. This is especially risky when a coordinator, worker, and external reviewer all touch the same project.

Receipt Chain does not require Git. When Git or another versioned store is used, prefer explicit labels under `extensions` instead of overloading one status field:

```yaml
extensions:
  sacp.chain.profile: sacp-chain
  sacp.chain.project: botlearn_content_module
  sacp.chain.module: handoff_state
  sacp.chain.current_head: a49c24c
  sacp.chain.latest_verified_content_commit: b19a081
  sacp.chain.latest_verified_state_commit: ce58d66
  sacp.chain.review_authority: external_reviewer_required
  sacp.chain.stop_rule: "Do not treat coordinator self-review as the formal external review."
```

These keys are examples, not SACP/0.1 core requirements. They show a safe pattern:

- separate current state from verified state
- separate content verification from handoff/state verification
- name the review authority when self-review would be misleading
- keep the stop rule visible for the next actor

Bad handoff wording:

```yaml
latest_stable_commit: a49c24c
next_owner: Reviewer
```

This is ambiguous because it does not say whether `a49c24c` is current, content-reviewed, state-reviewed, or only ready for review.

Better handoff wording:

```yaml
current_head: a49c24c
latest_verified_content_commit: b19a081
latest_verified_state_commit: ce58d66
next_owner: ExternalReviewer
stop_rule: "Coordinator-local checks are preflight only; formal review must come from an independent reviewer."
```

This is longer, but it prevents a local coordinator from accidentally treating its own preflight as the formal review.

## Rules

1. Receipt Chain does not change the meaning of `handoff_id`.
2. Receipt Chain does not change the meaning of `attempt_id`.
3. `parent_handoff` describes a parent-child task relationship, not a retry.
4. `depends_on` means the current work should reference upstream handoffs; it does not prove those handoffs are correct.
5. `receipts` and `evidence` are audit references. SACP does not require a storage backend.
6. `decisions` must reference human or trusted-system decisions. Agents must not self-approve decision boundaries.
7. `stop_rule` must be inherited by the next actor unless a later receipt explicitly names the evidence or human decision that changes it.

## Good Receipt Chain

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
handoff_id: hf_docs_update_001
attempt_id: attempt_001
agent_id: Coder
claims:
  - text: "The docs handoff produced a Receipt Chain draft."
    claim_type: tool_result
    source_id: git_diff_docs_update_001
    support_status: supported
verification:
  status: passed
  method: "local diff review"
next_owner: Reviewer
human_decision_required: false
extensions:
  sacp.chain.profile: sacp-chain
  sacp.chain.project: sacp_public_launch
  sacp.chain.module: docs
  sacp.chain.parent_handoff: hf_public_launch_001
  sacp.chain.evidence:
    - git_diff_docs_update_001
  sacp.chain.stop_rule: "Stop before publishing if founder approval is absent."
```

This is good because it:

- only claims what this attempt did
- cites evidence
- names a concrete next owner
- preserves a stop rule
- does not claim the whole project is complete

## Bad Receipt Chain

```yaml
claims:
  - text: "The full project is complete and safe to publish."
    claim_type: retrieved_fact
    source_id: none
    support_status: supported
next_owner: someone
human_decision_required: false
```

Problems:

- unsupported conclusion marked as `retrieved_fact`
- child-task receipt claiming full project completion
- ambiguous `next_owner`
- no human decision reference before publishing

Recommended diagnosis:

```yaml
status_code: 412
status_text: missing_evidence
required_fix: "Downgrade unsupported claims, attach evidence, set a concrete next_owner, and require human approval before publishing."
```

## Why It Matters

Receipt Chain helps with:

- preserving evidence and risk across multi-agent handoffs
- preventing local completion from masquerading as global completion
- keeping cross-model continuation tied to the same work identity
- compressing long context into auditable state instead of rereading whole chats
- keeping human approval boundaries visible after many handoffs

Receipt Chain does not guarantee correctness. It makes task state, evidence, ownership, and boundaries easier to audit.

