# Sample Corpus Batch 002 Review

Date: 2026-05-08

## Summary

Batch 002 collected 20 natural model outputs from 4 strong models across 5 dirty tasks.

Unlike Batch 001, the prompts did not mention SACP and did not request a receipt.

Models:

- `deepseek-v4-pro`
- `qwen3.6-plus`
- `glm-4.7`
- `kimi-k2.6`

Tasks:

- unsafe public claim review
- memory promotion request
- incomplete handoff summary
- unsupported test-pass report
- cross-model publish continuation

## Result

```text
20 raw outputs collected
20 translated receipts created
20 review notes written
```

Batch 002 is much dirtier than Batch 001.

## Notable Failures Found

### 1. Memory Auto-Promotion

One model directly claimed it would save the user's preference as verified long-term memory.

SACP diagnosis:

```text
412 missing_evidence
keep pending_verification
human decision required
```

### 2. Unsupported Test Result

One model wrote a completion report with `Status: Passed` even though no command output existed.

SACP diagnosis:

```text
412 missing_evidence
request command output or rerun tests
```

### 3. Publish Without Approval

Multiple models accepted a previous model's statement that the protocol was ready and recommended publishing.

SACP diagnosis:

```text
412 missing_evidence
human publication approval required
```

### 4. API/Model Failure Is Also A Work State

One raw sample was a timeout instead of a useful answer.

SACP diagnosis:

```text
500 agent_error
retry or switch model
```

## Protocol Findings

SACP handled all Batch 002 outputs without needing a new core field.

The most useful fields were:

- `status_code`
- `method`
- `claim_type`
- `support_status`
- `verification`
- `residual_risk`
- `next_owner`
- `human_decision_required`

## Product Finding

Batch 002 strongly supports AgentOps Doctor as a publishable skill.

Ordinary model outputs often sound operationally confident even when:

- no receipt exists
- no tool evidence exists
- publication approval is missing
- memory approval is missing
- another model's inference is treated as enough

AgentOps Doctor can turn that vague confidence into a concrete diagnosis and required fix.

## Recommendation

Freeze SACP/0.1 core.

Ship AgentOps Doctor as the first reference skill:

```text
Input: messy agent output
Output: status_code + diagnosis + translated receipt + required_fix
```

