# AgentOps Doctor

AgentOps Doctor audits whether AI agents actually did the work.

Powered by SACP: State-Aware Collaboration Protocol.

Chinese version: [README.zh-CN.md](./README.zh-CN.md)

## What It Does

AgentOps Doctor takes messy agent output and returns:

- status code
- receipt completeness
- claim findings
- memory warning
- next owner
- human decision requirement
- required fix
- translated SACP receipt

## Why It Exists

Most agent skills help agents do work.

AgentOps Doctor audits whether that work is trustworthy.

| Other Skills | AgentOps Doctor |
|---|---|
| summarize text | checks whether the summary has evidence |
| use GitHub | checks whether claimed changes were verified |
| write to Obsidian | checks whether memory was promoted safely |
| automate workflows | checks handoff, owner, retry, and receipt state |

## Quick Start

```bash
python agentops_doctor.py examples/done_but_no_receipt.md
```

JSON output:

```bash
python agentops_doctor.py examples/unsupported_test_claim.md --json
```

## Boundary

AgentOps Doctor does not execute the underlying task.

It does not prove correctness.

It produces a SACP-style audit receipt so humans and downstream agents can see what is missing.
