# AgentOps Doctor + SACP/0.1

> No receipt, no trust.

SACP is an open, text-first receipt protocol for AI agent work.

It does not replace LangGraph, MCP, A2A, OpenClaw, or agent SDKs. It adds a small audit layer:

```text
When an agent says "done", it should produce a checkable work receipt.
```

AgentOps Doctor is the first reference tool in this repo. Paste in messy agent output, and it returns a status code, claim findings, missing evidence, next owner, required fix, and a translated SACP receipt.

Chinese version: [README.zh-CN.md](./README.zh-CN.md)

## 3-Minute Quick Start

```bash
git clone https://github.com/aDragon0707/sacp.git
cd sacp
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/done_but_no_receipt.md
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

Try a missing-evidence example:

```bash
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md
```

Validate protocol examples:

```bash
python validator.py --examples --strict
```

Read the public-safe adoption case:

- [Longju SACP Runtime Guard](./ADOPTION_CASE_LONGJU.md)

## Test Your Own Agent Output

Save any final agent response, worklog, or handoff as a text file:

```bash
echo "Done. All tests passed. Ready to publish." > my-agent-output.md
python agentops-doctor-skill/agentops_doctor.py my-agent-output.md
```

AgentOps Doctor does not execute the original task. It checks whether the output is auditable:

- Did it claim completion without a receipt?
- Did it claim tests passed without command output?
- Did it promote memory without approval?
- Did it identify the next owner?
- Did it cross a human decision boundary?

## What Is In This Repo

```text
SACP = protocol
AgentOps Doctor = reference skill / CLI
Dirty Run = adversarial state-discipline benchmark
validator.py = local reference checker
```

Core docs:

- [SPEC.md](./SPEC.md): protocol semantics
- [ENVELOPE.md](./ENVELOPE.md): envelope fields and examples
- [RECEIPT.md](./RECEIPT.md): receipt fields and examples
- [STATUS_CODES.md](./STATUS_CODES.md): status codes
- [DIRTY_RUN_CASES.md](./DIRTY_RUN_CASES.md): adversarial cases
- [CONFORMANCE.md](./CONFORMANCE.md): conformance levels
- [agentops-doctor-skill/](./agentops-doctor-skill): one-command reference tool
- [examples/](./examples): valid and dirty packets
- [sample-corpus/](./sample-corpus): messy outputs translated into SACP receipts
- [ADOPTION_CASE_LONGJU.md](./ADOPTION_CASE_LONGJU.md): public-safe local adoption case
- [COMMUNITY_OUTREACH.md](./COMMUNITY_OUTREACH.md): community sharing and feedback prompts

## Real Adoption Case

SACP/0.1 has been tested as a local state layer for Longju, a single-agent operator running in an OpenClaw-style workspace.

The adoption used a file-based `.sacp/` ledger and a runtime guard with four gates:

```text
PreTask -> ContextCheck -> PreExternalAction -> PostTask
```

The public-safe trials covered false completion, prompt injection, skill distillation, and duplicate handoffs:

```text
false completion      -> 412 missing_evidence
prompt injection      -> human approval required
skill distillation    -> candidate only, no automatic promotion
duplicate handoff     -> 204 no_action_needed
```

Read the case study: [ADOPTION_CASE_LONGJU.md](./ADOPTION_CASE_LONGJU.md)

## Concrete Example

Raw agent output:

```text
Done. All tests passed. I saved the user preference to verified memory.
```

SACP breaks that into separate audit questions:

```text
1. "Done" without a receipt is not enough.
2. "All tests passed" needs command output or evidence.
3. "verified memory" requires human or trusted-system approval.
```

Likely diagnosis:

```text
412 missing_evidence
required_fix: attach test output, downgrade unsupported claims, require human approval for memory promotion.
```

SACP is not about making the model smarter. It is about making agent work state, evidence, ownership, and decision boundaries explicit.

## When To Use It

- You are building an agent skill and want to check whether its output is acceptable.
- You run multi-agent workflows and need handoff, attempt, receipt, and next-owner discipline.
- You compare models or frameworks and want to audit their completion claims.
- You collect hallucination, missing evidence, and memory-pollution examples.
- You want AI work to move from chat logs toward auditable work records.

## How To Contribute

The most useful contributions are concrete:

- Submit a messy agent output.
- Report a bad AgentOps Doctor diagnosis.
- Propose a Dirty Run case.
- Add adapter notes for LangGraph, CrewAI, MCP, A2A, OpenClaw, or another framework.
- Improve docs so new developers can run the project faster.

Open an issue using the templates in this repo.

See [CONTRIBUTING.md](./CONTRIBUTING.md).

If you want to share the project with developer communities, see [COMMUNITY_OUTREACH.md](./COMMUNITY_OUTREACH.md).

## Boundary

SACP helps agents produce auditable work receipts.

It does not guarantee correctness.

AgentOps Doctor audits the output. It does not execute the underlying task.

SACP/0.1 is an experimental alpha. The next useful step is more messy outputs, adapter examples, and adversarial test cases.
