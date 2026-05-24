# SACP Outbound PR Playbook

Date: 2026-05-17

Goal: turn SACP from a local proof into something other agent builders try, link, and copy.

Do not pitch "a new protocol standard" first. Pitch one concrete failure:

```text
Your agent says "done". Where is the receipt?
```

## The Wedge

SACP already has enough local proof:

- 30 messy real outputs translated into SACP receipts.
- Batch 001: 10 real workflow/worklog excerpts.
- Batch 002: 20 natural dirty outputs from DeepSeek, Qwen, GLM, and Kimi.
- Repeated failure modes: no receipt, missing test evidence, memory auto-promotion, publish without approval, incomplete handoff, ambiguous next owner.
- AgentOps Doctor works from source as a local reference CLI.

The outbound move is not "please adopt SACP".

The outbound move is:

```text
I can add one docs-only receipt example to your agent project.
It documents claims, evidence, next owner, and human approval boundaries.
No architecture change.
```

## PR Types

Prefer small PRs that maintainers can merge in 15 minutes.

### 1. Docs-only Receipt Example

File:

```text
docs/sacp_receipt_example.md
```

PR title:

```text
docs: add SACP receipt example for agent completion
```

Use when the project has agents, workflows, tool calls, evals, or "done" style completion.

### 2. Framework Adapter Note

File:

```text
docs/sacp_adapter_note.md
```

PR title:

```text
docs: map agent completion output to SACP receipt fields
```

Use when the project already has task/run/trace/checkpoint/handoff concepts.

### 3. Dirty Case

File:

```text
examples/dirty_done_without_evidence.md
```

PR title:

```text
examples: add dirty agent completion case
```

Use when the project has examples or eval cases.

### 4. Link-only Mention

File:

```text
docs/related.md
```

PR title:

```text
docs: mention SACP as a receipt-layer reference
```

Use only when the project already has a related-work page. This is weaker than adding an example.

## PR Body Template

```text
This is a small docs-only PR.

It adds a SACP-style receipt example for agent completion claims:

- what the agent claimed
- what evidence supports it
- who owns the next step
- whether human approval is required

It does not change your runtime or require adopting SACP.

Why I think it may fit here:
<one sentence tied to their project: workflow, tools, traces, memory, evals, or handoff>

Context:
SACP is a text-first receipt protocol for AI agent work:
https://github.com/aDragon0707/sacp
```

## Issue-before-PR Template

Use this when the project is large or strict.

```text
Would you accept a tiny docs-only PR with a SACP receipt example?

I am working on SACP, a small receipt layer for AI agent work.
It does not replace agent frameworks. It just documents:

- what the agent claimed
- what evidence exists
- who owns the next step
- whether human approval is required

I noticed this project has <task runs / traces / tools / memory / evals / handoffs>.
I can add one example showing how a "done / tests passed / ready to publish" output becomes an auditable receipt.

No runtime changes, no dependency, no adoption requirement.
```

## Target Map

Start where SACP solves a visible pain:

- agent observability projects
- agent eval / benchmark projects
- MCP and A2A tools
- LangGraph / CrewAI / AutoGen / OpenAI Agents SDK examples
- coding-agent tools
- memory / continuity / long-context projects
- projects with "run", "trace", "handoff", "checkpoint", "task", "eval", "tool result", or "approval" docs

Useful GitHub searches:

```text
agent observability receipt
agent eval tool result
agent framework handoff
LangGraph examples tool result
CrewAI examples task output
AutoGen multi agent handoff
OpenAI Agents SDK handoff example
MCP agent memory provenance
AI agent tests passed no evidence
```

Useful X / Reddit angles:

```text
"agent says done" evidence
"AI agent tests passed" no logs
"agent memory" provenance approval
"multi-agent handoff" failure
"agent observability" traces claims evidence
"MCP agent" tool result provenance
```

## Public Post Angles

### X Short

```text
Agents keep saying "done".

SACP makes them leave a receipt:
- claims
- evidence
- next owner
- human approval boundary

I tested 30 messy agent outputs. The same failures kept repeating:
missing evidence, memory auto-promotion, publish without approval.

No receipt, no trust.
https://github.com/aDragon0707/sacp
```

### Reddit

```text
Title:
Agents keep saying "done". I’m trying to make them leave receipts.

Post:
I open-sourced SACP, a small text-first receipt protocol for AI agent work.

I already tested it on 30 messy agent outputs:
- 10 real workflow/worklog excerpts
- 20 outputs from DeepSeek, Qwen, GLM, and Kimi across dirty agent tasks

The repeated failure modes were boring but serious:
- "tests passed" with no command output
- memory saved/promoted without approval evidence
- publish/release recommended based on another model's confidence
- handoffs with no clear next owner
- "done" with no receipt

SACP does not make the agent smarter.
It makes claims, evidence, ownership, and human approval boundaries explicit.

Repo:
https://github.com/aDragon0707/sacp

Ask:
Give me one messy agent output from your workflow.
I will translate it into a SACP receipt and add it as a Dirty Run case if it reveals a useful failure mode.
```

### Maintainer DM

```text
Hi <name>, I found your project while looking at agent <traces/evals/memory/handoffs>.

I maintain SACP, a small receipt layer for agent outputs.
I think your project could use a docs-only example showing how an agent completion claim maps to claims/evidence/next-owner/human-approval fields.

No runtime change, no dependency.
Would a tiny PR like that be welcome?
```

## Daily Execution Loop

Do not spray 100 low-quality PRs.

Do this every day for 7 days:

```text
find 10 targets
open 3 issues or PRs
post 1 public proof/thread
reply to every serious comment
log results in STATUS.md or a small campaign note
```

Track:

```text
target:
project_url:
contact_type: issue | PR | DM | post | comment
angle: docs example | adapter note | dirty case | receipt translation
status: sent | replied | accepted | rejected | merged
lesson:
next_action:
```

## Acceptance Rules

Good outbound:

- tied to a specific file or concept in their project
- docs-only or example-only
- no dependency requirement
- one concrete failure mode
- clear "no adoption required" sentence

Bad outbound:

- generic "please support my protocol"
- many unrelated PRs with identical text
- arguing after rejection
- claiming SACP proves correctness
- exposing private local examples

If rejected, reply once:

```text
Thanks for checking. I will keep it out of scope here.
If you ever want a receipt example for agent completion claims, I can reopen with a smaller docs-only version.
```

Then leave.

## 14-Day Goal

```text
30 targeted contacts
10 serious replies
5 external messy outputs
3 docs-only PRs opened
1 external PR merged
1 Batch 003 review note published
```

The compounding loop is:

```text
external output -> SACP receipt -> Dirty Run case -> public post -> next target
```
