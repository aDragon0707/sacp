# SACP Research Proposal

## Title

SACP: Auditing Long-Horizon AI Agent Workflows

## Summary

SACP is an open-source protocol and benchmark harness for auditing long-horizon AI agents. The project studies failures that are not visible from final answers alone: memory drift, delegated task drift, unsupported completion claims, evidence loss, tool-use ambiguity, and unsafe promotion of inferred information into persistent memory.

The goal is not to make a new agent framework. The goal is to make agent work inspectable across frameworks and model providers.

## Research Question

How can humans and tools audit multi-step AI agent work when the important failures happen inside intermediate state, handoffs, tool calls, evidence summaries, and memory updates?

## Motivation

Agent systems increasingly perform work over long traces:

- read files or external sources;
- call tools;
- delegate subtasks;
- update memory;
- retry after failures;
- summarize evidence;
- claim completion.

Final-answer review misses many problems in this setting. A response can look polished while the work trace contains unsupported claims, stale memory, missing test evidence, or unclear ownership. SACP treats every agent task as a work transaction:

```text
request -> claim -> execute -> verify -> receipt -> next owner
```

The project asks whether a small receipt protocol can make these workflows more auditable without requiring a full runtime platform.

## Failure Modes

SACP focuses on practical agentic failure modes:

- **Missing evidence**: the agent claims tests, citations, or tool outputs exist but does not attach them.
- **Memory drift**: model inference or user preference is promoted into persistent memory without approval.
- **Delegation drift**: a subagent receives a narrower or different task than the user intended.
- **Tool-result ambiguity**: a tool result is summarized without preserving status, command, source, or failure context.
- **False completion**: the agent reports "done" without a receipt, validation, or next owner.
- **Duplicate or stale handoff**: multiple agents act on the same task without idempotency or lease discipline.
- **Human decision boundary failure**: the agent acts where approval should have been required.

## Current Artifacts

The repository already includes:

- `SPEC.md`: protocol semantics;
- `ENVELOPE.md` and `RECEIPT.md`: core packet shapes;
- `STATUS_CODES.md`: responsibility-oriented status codes;
- `validator.py`: local validation for examples and receipts;
- `agentops-doctor-skill/`: one-command reference diagnostic tool;
- `DIRTY_RUN_CASES.md`: adversarial state-discipline cases;
- `sample-corpus/`: messy outputs translated into SACP receipts;
- `ADOPTION_CASE_LONGJU.md`: public-safe local adoption case.

## Proposed Evaluation Plan

The next phase will turn SACP into a more reproducible benchmark harness.

### Phase 1: Schema And Reference Checks

- Publish a clearer event/receipt schema.
- Add stricter validation for claims, evidence, memory promotion, and human decision boundaries.
- Expand examples for coding-agent, research-agent, and handoff-agent workflows.

### Phase 2: Dirty-Run Benchmark

Create benchmark tasks where agents are likely to fail in auditable ways:

- claim tests passed without output;
- summarize evidence from missing sources;
- promote memory from unsupported inference;
- delegate a task with missing constraints;
- overwrite a human decision with a stale instruction;
- hand off work without a next owner.

Each run should produce:

- raw agent output;
- SACP diagnosis;
- translated receipt;
- failure labels;
- required fix;
- model and prompt metadata;
- cost estimate where available.

### Phase 3: Cross-Model Comparison

Run the benchmark across frontier and open-source models where credits allow:

- baseline prompt;
- SACP-instrumented prompt;
- verifier-agent review;
- receipt completeness scoring.

The comparison should not claim one model is universally safer. It should identify which scaffolds reduce specific auditable failures.

## Expected Outputs

- Open-source SACP schema and validator improvements.
- Public dirty-run benchmark tasks.
- Example receipts and diagnosis reports.
- A technical write-up with failure patterns, mitigations, limitations, and cost notes.
- Adapter notes for common agent stacks such as Codex-style coding agents, LangGraph, MCP, A2A, and local memory systems.

## Non-Goals

SACP does not:

- guarantee final-answer correctness;
- replace model evaluation, red teaming, or formal verification;
- require a hosted service;
- require private logs;
- grant automatic trust to model-generated receipts;
- promote memory or skills without human or trusted-system approval.

## Why This Is Useful

Open-source agent projects often need a small, shared audit layer before they need a complex platform. SACP aims to provide that layer: a way to say what happened, what was verified, what remains unsupported, and who owns the next action.

