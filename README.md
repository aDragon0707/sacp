# SACP: State-Aware Collaboration Protocol

> No receipt, no trust.

SACP is a text-first protocol for making long-running AI agent work auditable. It helps humans and tools inspect what an agent claimed, what evidence supports it, who owns the next step, where review is required, and whether the work can safely continue.

It does not replace LangGraph, MCP, A2A, OpenAI Agents, Claude Code, or other agent frameworks. It adds a small audit layer around them:

```text
When an agent says "done", it should leave a checkable work receipt.
```

## Who This Is For

Use SACP if you:

- run coding agents, research agents, workflow agents, or multi-window AI work;
- need handoffs that future humans and agents can trust;
- want evidence before accepting "done";
- need local, Markdown/YAML records instead of opaque chat history;
- build agent tools and want a small protocol for receipts, ownership, and review boundaries.

## 30-Second Quick Start

Ask your agent to produce a receipt after a task:

```text
Summarize this run as an SACP receipt:
- objective
- claims made
- evidence for each claim
- files or systems changed
- tests or checks run
- next owner
- human approval needed
- unresolved risks
```

Then inspect the receipt before accepting completion.

## Core Idea

SACP treats agent work as a chain of reviewable states:

```text
Intent -> Task Packet -> Work -> Evidence -> Receipt -> Review -> Next State
```

The protocol is intentionally small:

- Markdown/YAML packets
- evidence-linked work receipts
- state and owner fields
- dirty-run examples
- validators and review checklists

## Ecosystem Around SACP

| Project | Role |
|---|---|
| [Solo-AI-Company-OS](https://github.com/aDragon0707/Solo-AI-Company-OS) | Operating memory for human-AI work: decisions, roles, worklogs, handoffs, and skills |
| [token-prompt-compiler](https://github.com/aDragon0707/token-prompt-compiler) | Turns messy human requests into bounded agent task contracts |
| [audit-evolution-agent-flight-recorder](https://github.com/aDragon0707/audit-evolution-agent-flight-recorder) | Converts agent runs into evidence packs, snapshots, evolution cards, and next-run bootstraps |
| [claude-code-html-skill](https://github.com/aDragon0707/claude-code-html-skill) | Builds readable HTML artifacts for plans, audits, reviews, and project operating surfaces |

## What A Receipt Should Answer

```yaml
objective: What was the agent trying to do?
state: planned | in_progress | partial | complete | blocked | failed
claims:
  - claim: What is being asserted?
    evidence: What proves it?
changes: What files, systems, or decisions changed?
checks: What validation ran, and what happened?
next_owner: human | current_agent | next_agent | external_system
approval_required: true | false
risks: What remains uncertain?
```

## Status

SACP is an evolving protocol and reference workspace. Treat it as useful for experiments, agent audits, local operating memory, and early tool integration. Do not treat every integration experiment as production-ready unless the target repository says so explicitly.

## Roadmap

- tighten the minimal receipt schema;
- collect dirty-run cases where agents overclaim completion;
- add validators for common receipt failures;
- publish example integrations with agent frameworks;
- document human review boundaries and memory promotion rules.

## Contributing

Useful contributions include:

- examples of good and bad agent receipts;
- validators for receipt structure or evidence gaps;
- integration notes for agent frameworks;
- docs that clarify review boundaries without overcomplicating the protocol.

## License

MIT.
