# SACP Social Launch Packet

Date: 2026-05-17

Primary repo:

```text
https://github.com/aDragon0707/sacp
```

Core line:

```text
Agents keep saying "done". SACP makes them leave a receipt.
```

Proof:

```text
30 messy agent outputs translated into SACP receipts:
- 10 real workflow/worklog excerpts
- 20 natural dirty outputs from DeepSeek, Qwen, GLM, and Kimi
```

Repeated failure modes:

```text
- "tests passed" without command output
- memory promoted without approval evidence
- publish/release recommended based on another model's confidence
- incomplete handoff with no clear next owner
- "done" with no receipt
```

Ask:

```text
Give me one messy agent output. I will translate it into a SACP receipt.
```

## X Post 1

```text
Agents keep saying "done".

SACP makes them leave a receipt:
- claims
- evidence
- next owner
- human approval boundary

I tested 30 messy agent outputs. Same failures kept repeating:
missing evidence, memory auto-promotion, publish without approval.

https://github.com/aDragon0707/sacp
```

## X Post 2

```text
"All tests passed."

Where is the command output?

That is the tiny gap SACP tries to close: turn agent completion claims into auditable receipts.

No receipt, no trust.

https://github.com/aDragon0707/sacp
```

## X Post 3

```text
I ran 4 strong models through dirty agent tasks.

They sounded confident, but repeated the same operational failures:
- unsupported test claims
- memory saved without approval
- publish-ready claims without human decision

So I made SACP: a receipt layer for agent work.

https://github.com/aDragon0707/sacp
```

## X Thread

```text
1/ Agents keep saying "done".

But in real workflows, "done" is not enough.
Where is the evidence?
Who owns the next step?
Did it cross a human approval boundary?

I open-sourced SACP to make agent work leave receipts:
https://github.com/aDragon0707/sacp

2/ I tested 30 messy agent outputs:

- 10 real workflow/worklog excerpts
- 20 natural dirty outputs from DeepSeek, Qwen, GLM, and Kimi

The prompts did not ask for SACP.
They were ordinary messy agent tasks.

3/ Repeated failures:

- "tests passed" with no command output
- memory promoted without approval evidence
- publish/release recommended from another model's confidence
- incomplete handoffs
- "done" with no receipt

4/ SACP does not make the model smarter.

It makes the work auditable:

- claims
- evidence
- status code
- next owner
- residual risk
- human decision required

5/ AgentOps Doctor is the first reference tool.

Paste messy agent output.
It returns:

- status_code
- diagnosis
- missing evidence
- required fix
- translated SACP receipt

6/ The ask:

Give me one messy agent output from your workflow.

I will translate it into a SACP receipt and add it as a Dirty Run case if it reveals a useful failure mode.

No receipt, no trust.
https://github.com/aDragon0707/sacp
```

## Reddit: r/LocalLLaMA

```text
Title:
Agents keep saying "done". I’m trying to make them leave receipts.

Post:
I open-sourced SACP, a small text-first receipt protocol for AI agent work.

The problem is simple: agent outputs often sound operationally confident even when the work is not auditable.

I tested 30 messy agent outputs:

- 10 real workflow/worklog excerpts
- 20 natural dirty outputs from DeepSeek, Qwen, GLM, and Kimi across 5 dirty tasks

The repeated failure modes were boring but serious:

- "tests passed" with no command output
- memory saved/promoted without approval evidence
- publish/release recommended based on another model's confidence
- handoffs with no clear next owner
- "done" with no receipt

SACP does not make the agent smarter.
It makes claims, evidence, ownership, and human approval boundaries explicit.

AgentOps Doctor is the first reference tool:

```bash
git clone https://github.com/aDragon0707/sacp.git
cd sacp
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md
```

Repo:
https://github.com/aDragon0707/sacp

Ask:
Give me one messy agent output from your workflow.
I will translate it into a SACP receipt and add it as a Dirty Run case if it reveals a useful failure mode.
```

## Reddit: r/AI_Agents / r/LangChain

```text
Title:
Would agent frameworks benefit from a small "receipt" layer?

Post:
I’m working on SACP, a small receipt protocol for AI agent work.

It does not replace LangGraph, CrewAI, AutoGen, MCP, A2A, or agent SDKs.
It just adds a tiny audit layer for completion claims:

- what the agent claimed
- what evidence supports it
- who owns the next step
- whether human approval is required

I tested it on 30 messy agent outputs and saw the same failure modes:

- done without receipt
- tests passed without command output
- memory promoted without approval
- publish-ready claims without human approval
- incomplete handoffs

I’m looking for maintainers/users who would accept small docs-only PRs like:

```text
docs/sacp_receipt_example.md
docs/sacp_adapter_note.md
examples/dirty_done_without_evidence.md
```

Repo:
https://github.com/aDragon0707/sacp

Question:
If your framework already has runs/traces/tasks/tool calls, what fields would you map into a receipt?
```

## Hacker News

```text
Title:
Show HN: SACP — receipts for AI agent work

Text:
I built SACP, a small text-first receipt protocol for AI agent work.

The idea is simple: when an agent says "done", it should produce a checkable work receipt.

SACP records claims, evidence, status code, next owner, residual risk, and whether a human decision is required.

I tested it on 30 messy agent outputs, including 20 natural outputs from DeepSeek, Qwen, GLM, and Kimi. The recurring failures were unsupported test claims, memory auto-promotion, publish without approval, incomplete handoffs, and "done" without a receipt.

AgentOps Doctor is the first reference tool. Paste messy agent output; it returns a diagnosis and translated SACP receipt.

Repo:
https://github.com/aDragon0707/sacp
```

## V2EX / Juejin

```text
标题：
AI Agent 老说“完成了”，我做了一个让它留下回执的协议

正文：
我开源了 SACP/0.1，一个面向 AI agent 工作流的文本优先回执协议。

它不替代 LangGraph、CrewAI、AutoGen、MCP、A2A 或任何 agent 框架。
它只补一层很小的审计：

- agent 声称做了什么
- 有没有证据
- 下一步归谁
- 有没有越过人类审批边界

我已经用 30 个 messy agent output 做过测试：

- 10 个真实 workflow/worklog excerpt
- 20 个来自 DeepSeek、Qwen、GLM、Kimi 的自然 dirty output

反复出现的问题很具体：

- “tests passed” 但没有命令输出
- 自动把 memory 晋升成 verified memory
- 根据另一个模型的信心就建议发布
- handoff 没有明确 next owner
- 只说 done，没有 receipt

仓库：
https://github.com/aDragon0707/sacp

我现在想收集更多真实 messy output。
你给我一段 agent 的脏输出，我帮你翻译成 SACP receipt。
```

## Maintainer Issue

```text
Title:
Would you accept a small docs-only SACP receipt example?

Body:
Hi, I’m working on SACP, a small text-first receipt layer for AI agent work:
https://github.com/aDragon0707/sacp

It does not replace agent frameworks or tracing systems.
It documents the final work state:

- what the agent claimed
- what evidence supports it
- who owns the next step
- whether human approval is required

I noticed this project works with agent runs / traces / workflows, so I wanted to ask:

Would you accept a tiny docs-only PR adding a SACP-style receipt example for an agent completion claim?

No runtime change, no dependency, no adoption requirement.
It would just be an example file such as:

```text
docs/sacp_receipt_example.md
```

The concrete failure mode is:
an agent says "done" or "tests passed", but there is no explicit receipt tying the claim to evidence and next owner.
```

## Docs-Only PR Body

```text
This is a small docs-only PR.

It adds a SACP-style receipt example for agent completion claims:

- what the agent claimed
- what evidence supports it
- who owns the next step
- whether human approval is required

It does not change runtime behavior or add a dependency.

Context:
SACP is a text-first receipt protocol for AI agent work:
https://github.com/aDragon0707/sacp

The concrete failure mode this documents:
an agent says "done" / "tests passed" / "ready to publish", but the output does not clearly attach evidence, owner, and approval boundary.
```
