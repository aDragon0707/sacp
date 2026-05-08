# Community Outreach Kit

This file is for people sharing SACP with developers, open-source communities, and agent builders.

Chinese version: [COMMUNITY_OUTREACH.zh-CN.md](./COMMUNITY_OUTREACH.zh-CN.md)

## Who To Reach

Start with people who already feel the pain:

- agent framework builders
- LangGraph / CrewAI / MCP / A2A users
- AI coding tool users
- open-source maintainers using AI agents
- people collecting hallucination or evaluation examples
- hackathon participants building agent skills

Do not lead with "a new protocol standard." Lead with a concrete failure:

```text
An agent says "All tests passed."
Where is the evidence?
```

## Short Post

```text
I open-sourced SACP/0.1 + AgentOps Doctor.

It audits messy AI agent output and asks:
- Did it really finish?
- Where is the evidence?
- Who owns the next step?
- Did it cross a memory or human-approval boundary?

Run:
git clone https://github.com/aDragon0707/sacp.git
cd sacp
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md

No receipt, no trust.
```

## Adoption Case Post

```text
SACP now has a public-safe adoption case.

Longju, a local single-agent operator, uses SACP as a runtime guard:
PreTask -> ContextCheck -> PreExternalAction -> PostTask

The trials covered:
- false completion -> 412 missing_evidence
- prompt injection -> human approval required
- skill distillation -> candidate only
- duplicate handoff -> 204 no_action_needed

Case study:
https://github.com/aDragon0707/sacp/blob/main/ADOPTION_CASE_LONGJU.md
```

## Ask For Feedback

```text
Looking for messy agent outputs.

If your agent ever said "done", "tests passed", "saved to memory", or "ready to publish" without enough evidence, paste a sanitized example here:
https://github.com/aDragon0707/sacp/issues/new/choose

I want to turn real failure cases into Dirty Run tests.
```

## Who To Tag

Tagging can help, but do it carefully. Prefer people and projects with direct interest in agents, evals, workflows, or protocols.

Good patterns:

- tag a framework when you add a concrete adapter proposal
- tag an expert when asking one specific technical question
- tag a community when asking for messy outputs or benchmark cases

Weak pattern:

- mass-tagging famous accounts with a vague announcement

## OpenAI / Frontier Labs

It is reasonable to mention OpenAI, Anthropic, LangChain, Microsoft AutoGen, CrewAI, and other frontier-agent communities, but the ask should be concrete:

```text
Would a receipt layer for agent completion claims be useful in your framework?
What evidence fields would you map from tool calls/checkpoints?
```

## Community Targets

- GitHub: issues, discussions, related repos
- Hacker News: Show HN
- Reddit: r/LocalLLaMA, r/AI_Agents, r/LangChain, r/MachineLearning
- X / Twitter: agent builders, eval researchers, open-source maintainers
- Hugging Face forums
- LangChain / LangGraph community
- MCP / A2A developer communities
- Chinese communities: V2EX, 掘金, 知乎, 即刻, 开源中国, AI 开发者微信群

## Best First Ask

```text
Give me one messy agent output.
I will translate it into a SACP receipt and add it to the benchmark if it reveals a useful failure mode.
```
