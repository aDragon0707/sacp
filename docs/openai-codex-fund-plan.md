# OpenAI Codex Open Source Fund Plan

## Project

SACP: Scalable Audit and Control Protocol for AI Agents

Repository:

```text
https://github.com/aDragon0707/sacp
```

## Why This Project Fits

The Codex Open Source Fund supports open-source projects using Codex CLI and OpenAI models. SACP is a natural fit because coding agents are one of the clearest examples of long-horizon AI work:

- inspect a repository;
- edit files;
- run commands and tests;
- summarize evidence;
- delegate or resume tasks;
- claim completion.

These workflows need auditable receipts. SACP provides a text-first protocol and reference tool for checking whether agent work is supported by evidence, correctly scoped, and safe to continue.

## How API Credits Would Be Used

API credits would be used only for open-source development and evaluation.

### 1. Reference Implementation

Use Codex and OpenAI models to develop:

- stronger validator checks;
- JSON Schema drafts for receipts and envelopes;
- example packets for coding-agent workflows;
- documentation improvements;
- adapter notes for Codex-style CLI workflows.

### 2. Benchmark Task Generation

Generate and refine dirty-run tasks for:

- false completion;
- missing test evidence;
- unsupported citation claims;
- unsafe memory promotion;
- stale handoff continuation;
- duplicate handoff handling;
- tool-result misrepresentation.

### 3. Evaluation Runs

Run controlled GPT-based evaluations:

- baseline agent output;
- SACP-instrumented output;
- verifier-agent diagnosis;
- translated SACP receipt;
- cost and failure summary.

### 4. Public Outputs

Publish:

- improved schema and validator;
- benchmark tasks;
- raw public-safe runs;
- translated receipts;
- evaluation reports;
- a practical guide for open-source agent maintainers.

## Staged Use Of Credits

### First $1,000

- 20-40 benchmark tasks;
- 2-3 model/prompt variants;
- first public report;
- validator and docs upgrade.

### Additional Credits

If more credits are granted, expand to:

- more repeated trials per task;
- cross-model comparisons;
- larger sample corpus;
- framework adapter examples;
- verifier-agent ablations.

## Abuse And Boundary Controls

Credits will not be used for:

- production traffic;
- private customer work;
- resale;
- unrelated content generation;
- prohibited content;
- non-public model access requests.

The project will keep logs, prompt versions, task versions, and cost summaries where practical.

## Near-Term Milestones

### 30 Days

- Clarify README and research proposal.
- Add OpenAI/Codex workflow examples.
- Expand dirty-run benchmark cases.
- Publish first Codex-style receipt examples.

### 60 Days

- Add stricter validator checks.
- Publish benchmark run summaries.
- Add verifier-agent scoring notes.
- Prepare adapter notes for common agent workflows.

### 90 Days

- Publish a technical report.
- Release a v0.2 schema draft.
- Invite external dirty-run examples and adapter PRs.

