# AgentOps Doctor for SACP/0.1

AgentOps Doctor is the MVP diagnostic workflow for SACP.

它不是运行时，也不执行任务。它是一个粘贴式审查器：给它 handoff、worklog、receipt、claim 或 memory suggestion，它返回 SACP 状态码、问题诊断、证据边界和修复动作。

## Input

The user may paste:

- one SACP handoff
- one worklog
- one receipt
- optional public claim
- optional memory suggestion

## Output

AgentOps Doctor returns:

- SACP status code
- status text
- verdict
- receipt completeness
- claim boundary findings
- memory promotion warning
- next owner
- human decision requirement
- exact required fix

## Non-Goals

AgentOps Doctor must not:

- claim that it executed the task
- promote memory without approval
- mark unsupported claims as supported
- hide inference as retrieved fact
- create external side effects
- certify correctness

## Quick Use

1. Paste the handoff/worklog/receipt into an LLM.
2. Paste [prompt_skill.md](./prompt_skill.md) above or below it.
3. Ask for a SACP/0.1 diagnosis.
4. Review the returned status code and required fix.

## Minimal Output Shape

```yaml
status_code: 412
status_text: missing_evidence
verdict: revise
receipt_completeness: incomplete
claim_findings:
  - problem: "Claim marked as retrieved_fact but no source is provided."
    required_fix: "Provide source or downgrade claim_type."
memory_warning: null
next_owner: ClaimReviewer
human_decision_required: false
```

