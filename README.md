# AgentOps Doctor + SACP/0.1

> No receipt, no trust.

AgentOps Doctor checks whether AI agents are pretending to be done.

Powered by **SACP: State-Aware Collaboration Protocol**.

Chinese version: [README.zh-CN.md](./README.zh-CN.md)

## 30-Second Demo

Many agent outputs look like this:

```text
Done.
All tests passed.
Ready to publish.
I saved it to memory.
```

AgentOps Doctor turns that into:

```text
status_code
claim_findings
missing evidence
required_fix
translated_receipt
```

Other skills do the work.

AgentOps Doctor audits the work.

## What This Is

SACP is an open, text-first protocol for auditable AI agent work receipts.

AgentOps Doctor is the first reference skill built on top of SACP.

Dirty Run is the benchmark suite.

Validator is the reference tool.

```text
SACP = protocol
AgentOps Doctor = skill
Dirty Run = benchmark
validator.py = reference checker
```

## One Sentence

An agent work item is not complete until it produces a receipt that identifies the task, attempt, claims, evidence, verification, remaining risk, next owner, and human decision boundary.

## Why It Exists

LLMs are stateless token predictors.

Real work needs:

- state
- ownership
- evidence
- retry
- handoff
- audit
- human approval
- memory boundaries

SACP defines a small shared contract for those needs.

## Core Objects

1. **SACP Envelope**

   The protocol wrapper. It identifies protocol version, method, resource, handoff, attempt, agent, source fingerprint, content type, and optional lease.

2. **SACP Receipt**

   The proof of work. It records what happened, what was claimed, what evidence supports those claims, what verification ran, what risk remains, and who owns the next step.

3. **SACP Dirty Run Benchmark**

   The adversarial state-discipline benchmark. It checks duplicate handoffs, missing evidence, bad claim typing, memory pollution, active leases, expired leases, and incomplete receipts.

4. **AgentOps Doctor Skill**

   The first reference skill. It takes messy agent output and returns a SACP-style diagnosis and translated receipt.

## Quick Start

Run the reference skill:

```bash
cd agentops-doctor-skill
python agentops_doctor.py examples/done_but_no_receipt.md
```

Expected output includes:

```text
status_code
status_text
receipt_completeness
claim_findings
memory_warning
next_owner
human_decision_required
required_fix
translated_receipt
```

Validate protocol examples:

```bash
python validator.py --examples --strict
```

Validate sample-corpus translated receipts in PowerShell:

```powershell
$files = Get-ChildItem sample-corpus\translated-receipts -Filter *.yaml | ForEach-Object { $_.FullName }
python validator.py @files --strict
```

## Repository Map

- [SPEC.md](./SPEC.md): core protocol semantics
- [ENVELOPE.md](./ENVELOPE.md): envelope fields and examples
- [RECEIPT.md](./RECEIPT.md): receipt fields and examples
- [STATUS_CODES.md](./STATUS_CODES.md): v0.1 status codes
- [EXTENSIONS.md](./EXTENSIONS.md): extension and compatibility rules
- [DIRTY_RUN_CASES.md](./DIRTY_RUN_CASES.md): adversarial state-discipline cases
- [CONFORMANCE.md](./CONFORMANCE.md): conformance levels
- [LIFECYCLE.md](./LIFECYCLE.md): packet lifecycle
- [GOVERNANCE.md](./GOVERNANCE.md): change and compatibility rules
- [VALIDATOR.md](./VALIDATOR.md): local reference validator
- [PROTOCOL_REVIEW.md](./PROTOCOL_REVIEW.md): adversarial protocol review
- [examples/](./examples): valid and dirty YAML examples
- [agentops-doctor/](./agentops-doctor): prompt workflow and multi-model Dirty Run runner
- [agentops-doctor-skill/](./agentops-doctor-skill): one-command reference skill
- [sample-corpus/](./sample-corpus): real messy workflow samples translated into SACP receipts

## AgentOps Doctor vs Other Skills

| Other Skills | AgentOps Doctor |
|---|---|
| summarize text | checks whether the summary has evidence |
| use GitHub | checks whether claimed changes were verified |
| write to Obsidian | checks whether memory was promoted safely |
| automate workflows | checks handoff, owner, retry, and receipt state |

Most skills help agents do work.

AgentOps Doctor audits whether that work is trustworthy.

## What SACP Is Not

SACP/0.1 is not:

- an agent runtime
- an AI operating system
- a database
- a cloud platform
- a model training pipeline
- a legal compliance proof
- a universal intelligence benchmark
- a replacement for MCP, A2A, LangGraph, or agent SDKs

SACP complements those systems by defining a small receipt layer for auditable work state.

## Current Test Assets

- Dirty Run: 10 adversarial state-discipline cases
- Multi-model run: DeepSeek, Qwen, GLM, and Kimi strong-model results
- Sample Corpus Batch 001: 10 real workflow excerpts
- Sample Corpus Batch 002: 20 natural messy model outputs

## Boundary

SACP helps agents produce auditable work receipts.

It does not guarantee correctness.

AgentOps Doctor audits the output. It does not execute the underlying task.
