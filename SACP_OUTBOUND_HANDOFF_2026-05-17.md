# SACP Outbound Handoff

Date: 2026-05-17

Protocol: SACP/0.1

## Current Goal

Continue outbound adoption work for SACP by opening small, safety-oriented docs/example PRs or maintainer issues in official agent framework repositories.

Primary message:

```text
Agent final output is not proof.
For safety-sensitive workflows, agents should leave a receipt:
claims + evidence + next owner + human approval boundary.
```

Do not pitch SACP as a replacement for frameworks, tracing, guardrails, or protocols.

Pitch it as a tiny final-state receipt pattern.

## Trusted State

SACP local repo for the current operator:

```text
<local clone of https://github.com/aDragon0707/sacp>
```

Public repo:

```text
https://github.com/aDragon0707/sacp
```

Current proof:

- 30 messy agent outputs translated into SACP receipts.
- Batch 001: 10 real workflow/worklog excerpts.
- Batch 002: 20 natural dirty outputs from DeepSeek, Qwen, GLM, and Kimi.
- Repeated failure modes:
  - completion without receipt
  - tests passed without command output
  - memory auto-promotion without approval
  - publish/release readiness without human approval
  - incomplete handoff / ambiguous next owner

Core local files:

- `STATUS.md`
- `OUTBOUND_PR_PLAYBOOK.md`
- `SOCIAL_LAUNCH_PACKET.md`
- `OUTREACH_CAMPAIGN_LOG.md`
- `sample-corpus/BATCH_002_REVIEW.md`

## Completed External Contacts

### Open PRs

| Target | Link | Status | Next action |
|---|---|---|---|
| OpenAI Cookbook | https://github.com/openai/openai-cookbook/pull/2705 | open | Wait for maintainer review. Codex automated review only; no required action yet. |
| OpenAI Agents Python | https://github.com/openai/openai-agents-python/pull/3440 | open | Wait for maintainer review. |
| OpenAI Agents JS | https://github.com/openai/openai-agents-js/pull/1331 | open | Changeset bot says no changeset; docs-only is OK unless maintainer asks. |
| MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk/pull/2625 | open | CI mostly green; all-green passed. Wait for maintainer review. |
| CrewAI | https://github.com/crewAIInc/crewAI/pull/5840 | open | CodeRabbit requested changes; a fix commit was pushed using `verification_status`, `verification_agent`, and `output_pydantic` examples. Wait for re-review. |

### Open Issues

| Target | Link | Status | Next action |
|---|---|---|---|
| LangGraph | https://github.com/langchain-ai/langgraph/issues/7844 | open | Wait. Issue was opened instead of PR because repo examples are archived. |
| OWASP Agent Observability Standard | https://github.com/OWASP/www-project-agent-observability-standard/issues/75 | open | If positive response, submit docs-only receipt example. |
| Claude Code hooks observability demo | https://github.com/disler/claude-code-hooks-multi-agent-observability/issues/46 | open | If positive response, submit docs-only receipt example. |
| Agent Lens | https://github.com/dreadnode/agent-lens/issues/6 | open | If positive response, submit docs-only receipt example. |
| BigQuery Agent Analytics SDK | https://github.com/GoogleCloudPlatform/BigQuery-Agent-Analytics-SDK/issues/169 | open | If positive response, submit docs-only receipt example. |

### Closed / Rejected

| Target | Link | Outcome |
|---|---|---|
| run-llama agents-observability-demo | https://github.com/run-llama/agents-observability-demo/issues/2 | Maintainer said no more examples needed now. Do not argue. |

## Next Official Targets

Prioritize official projects where SACP can be framed as safety documentation.

### Tier 1: Claude / Anthropic

1. `anthropics/claude-code-action`
   - Best next PR target.
   - Why: GitHub Action runs Claude in PR/issue workflows, so final-output receipts fit CI safety.
   - Suggested file:
     ```text
     docs/receipt-guidance.md
     ```
     or a section in:
     ```text
     docs/security.md
     docs/usage.md
     examples/pr-review-comprehensive.yml
     ```
   - PR angle:
     ```text
     Docs: add final-output receipt guidance for Claude Code Action
     ```

2. `anthropics/claude-agent-sdk-python`
   - Good docs/example PR target.
   - Why: SDK examples include tools, permissions, sessions, streaming, and callbacks.
   - Suggested file:
     ```text
     examples/completion_receipt.py
     ```
     or a README section:
     ```text
     Auditing final agent output
     ```

3. `anthropics/claude-code`
   - Use issue first, not direct PR.
   - Why: main product repo has many issues and existing examples/plugins; a direct PR may be noisy.
   - Suggested issue title:
     ```text
     Docs safety guidance: final-output receipts for completed coding tasks?
     ```

### Tier 2: Other Official Agent / Coding Agent Projects

1. `google-gemini/gemini-cli`
   - Good PR target.
   - Angle: terminal coding agent final output should identify evidence, tests, and human approval before file/system changes.

2. `microsoft/autogen`
   - Good docs issue first, then PR.
   - Angle: multi-agent handoffs and final outputs need receipt-backed claims.

3. `microsoft/semantic-kernel`
   - Issue first.
   - Angle: planner/function/tool results can support a final-state receipt.

4. `pydantic/pydantic-ai`
   - Good PR target.
   - Angle: Pydantic typed outputs are perfect for a `TaskReceipt` / `AgentReceipt` model.

5. `langchain-ai/langchain`
   - Issue first.
   - Angle: agent executor output vs evidence-backed final state.

6. `browser-use/browser-use`
   - Good PR target.
   - Angle: browser automation agents often claim task completion; receipts can attach screenshots, URLs, DOM/tool output, and approval boundary.

## PR Rules

Use docs-only PRs unless maintainers explicitly ask for code.

Good PR shape:

```text
docs: add auditable final output receipt guidance
```

Keep one changed file if possible.

Do not require SACP adoption.

Do not add dependencies.

Do not claim SACP proves correctness.

Do not paste private local examples, private paths, or workspace data.

## Standard PR Body

```text
## Summary

Adds docs-only safety guidance for auditable final output receipts.

The section clarifies that an agent's final answer is not proof that every claim in the answer is supported. It shows a compact receipt pattern that separates:

- agent claims
- supporting evidence
- unsupported claims
- next owner
- human approval boundaries

## Motivation

Agent final answers can contain operational claims such as task completed, tests passed, ready to publish, memory saved, or deployment finished.

Those claims may require evidence from tool outputs, logs, traces, file diffs, command output, approvals, or human review.

A receipt complements traces, guardrails, and callbacks by summarizing the final work state for humans and downstream systems.

## Notes

- Docs-only change.
- No runtime dependency.
- No behavior change.
- Safety-oriented guidance for final output review.
```

## Standard Receipt Example

Prefer domain-native status labels instead of HTTP codes when contributing to other projects.

```yaml
verification_status: missing_evidence
summary: "The agent claimed completion and test success, but did not attach command output."
claims:
  - claim: "Task is complete."
    support_status: unverified
    evidence: []
    required_fix: "Attach the relevant tool output, file diff, trace item, or log."
  - claim: "All tests passed."
    support_status: unsupported
    evidence: []
    required_fix: "Attach the test command and output, or downgrade the claim."
next_owner: verification_agent
human_decision_required: false
```

Evidence-backed example:

```yaml
verification_status: completed
summary: "The task completed and the test claim is supported by command output."
claims:
  - claim: "All tests passed."
    support_status: supported
    evidence:
      - "pytest exit code: 0"
      - "test_output.log: All 47 tests passed in 12.3s"
    required_fix: null
next_owner: reviewer
human_decision_required: false
```

## Stop Rules

Stop and ask before:

- posting from X / Reddit accounts
- replying aggressively to rejection
- opening more than 3 PRs in the same organization in one day
- adding SACP branding too heavily to another project's docs
- touching code paths, tests, or build config unless required by maintainers

If rejected, reply once:

```text
Thanks for checking. I will keep it out of scope here.
If a smaller docs-only note about final-output evidence boundaries would be useful later, I am happy to adjust.
```

Then leave.

## Verification Plan

Before opening each PR:

1. Read target repo README and relevant docs file.
2. Confirm docs are not archived.
3. Prefer one-file docs-only change.
4. Run or inspect any lightweight docs/format requirement if available.
5. Check generated text for private paths, credentials, local project names, and unsupported claims.
6. Record the link in `OUTREACH_CAMPAIGN_LOG.md`.

## Resume Prompt

```text
Continue SACP outbound adoption from `SACP_OUTBOUND_HANDOFF_2026-05-17.md`.

First check current PR/issue status in `OUTREACH_CAMPAIGN_LOG.md`.
Fix any review feedback before opening new PRs.
Then target official agent/coding-agent projects in this order:
1. anthropics/claude-code-action
2. anthropics/claude-agent-sdk-python
3. google-gemini/gemini-cli
4. pydantic/pydantic-ai
5. microsoft/autogen

Use docs-only safety guidance.
Do not add dependencies.
Frame SACP as a final-output receipt pattern, not a replacement protocol.
Record every contact in `OUTREACH_CAMPAIGN_LOG.md`.
```
