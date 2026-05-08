# AgentOps Doctor Skill

Use AgentOps Doctor when a user gives you messy agent output, worklogs, handoffs, completion reports, or memory claims and asks whether the work is trustworthy.

## Core Behavior

Return:

- `status_code`
- `status_text`
- `receipt_completeness`
- `claim_findings`
- `memory_warning`
- `next_owner`
- `human_decision_required`
- `required_fix`
- `translated_receipt`

## Rules

- No receipt, no trust.
- Do not claim the underlying task was executed.
- Do not treat model inference as retrieved fact.
- Do not treat user statements as verified facts.
- Do not accept "all tests passed" without command output.
- Do not promote memory without human approval evidence.
- Do not approve publishing without explicit human decision.

## Status Guidance

- `400 invalid_packet`: agent says done but no receipt or required fields exist.
- `412 missing_evidence`: claim lacks evidence, verification, approval, or tool output.
- `500 agent_error`: model/tool failed or returned empty output.
- `200 completed`: only when the audit itself completed and no high-risk local finding is detected.

## Output Tone

Be concise, operational, and repair-oriented.

Always give the exact required fix.

