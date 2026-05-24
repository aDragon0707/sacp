# SACP Agent Test Prompt

Use this file to ask another agent, such as OpenClaw or herness, to inspect SACP and report whether it can understand and use the protocol.

This is a prompt-only test. The agent should not rewrite the protocol or build a runtime unless explicitly asked later.

## Quick Usage

Repository path:

```text
C:\Users\86181\Documents\Codex\2026-05-07\openclaw-llm\sacp
```

Recommended commands:

```powershell
cd C:\Users\86181\Documents\Codex\2026-05-07\openclaw-llm\sacp
python validator.py --examples --strict
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/done_but_no_receipt.md
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md
```

Read first:

```text
README.md
SPEC.md
RECEIPT.md
DIRTY_RUN_CASES.md
SACP_RECEIPT_CHAIN.md
docs/ADAPTER_NOTE_TEMPLATE.md
examples/receipt_chain_multi_agent_project.yaml
examples/receipt_chain_research_publish.yaml
```

Core idea:

```text
SACP is a text-first receipt protocol for AI agent work.
It does not replace agent frameworks, runtimes, MCP, A2A, LangGraph, OpenClaw, or herness.
It records claims, evidence, verification, next owner, residual risk, and human approval boundaries.
No receipt, no trust.
```

## Prompt For Another Codex / Agent

```text
You are helping audit SACP, an open text-first receipt protocol for AI agent work.

Workspace:
C:\Users\86181\Documents\Codex\2026-05-07\openclaw-llm\sacp

Context:
SACP is not an agent runtime, scheduler, database, tracing platform, or security framework. It is a receipt layer. When an AI agent says "done", SACP asks for a checkable receipt:
- what was claimed
- what evidence supports each claim
- what verification happened
- what residual risk remains
- who owns the next step
- whether a human decision is required

Important docs to read:
1. README.md
2. SPEC.md
3. RECEIPT.md
4. DIRTY_RUN_CASES.md
5. SACP_RECEIPT_CHAIN.md
6. docs/ADAPTER_NOTE_TEMPLATE.md
7. examples/receipt_chain_multi_agent_project.yaml
8. examples/receipt_chain_research_publish.yaml

Please do these checks:
1. Run:
   python validator.py --examples --strict
2. Run:
   python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/done_but_no_receipt.md
3. Run:
   python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md
4. Inspect the Receipt Chain docs and examples. Decide whether the profile helps long-running, multi-module, multi-agent handoff without expanding the SACP core.
5. Inspect docs/ADAPTER_NOTE_TEMPLATE.md. Decide whether another agent framework could map its run/task/trace/tool/checkpoint fields into a SACP receipt without adopting SACP as a runtime dependency.

Output format:

SACP Agent Test Report

1. Command Results
- validator:
- done_but_no_receipt:
- unsupported_test_claim:

2. Protocol Understanding
- In one paragraph, explain SACP in your own words.
- State what SACP is not.

3. Receipt Chain Review
- Does it help long-running and multi-agent work?
- Does it preserve the small core?
- Any confusing fields?

4. Adapter Note Review
- Can your agent framework map native fields into SACP?
- Which native fields map to handoff_id, attempt_id, agent_id, claims, evidence, verification, next_owner, and human_decision_required?

5. Issues Found
- List concrete issues only.
- Include file path and line if possible.
- Separate bugs from suggestions.

6. Final Verdict
Choose one:
- PASS: SACP is understandable and usable for a pilot.
- PASS_WITH_NOTES: usable, but docs/examples need small improvements.
- FAIL: core concept or examples are not usable yet.

Constraints:
- Do not rewrite the protocol.
- Do not add new fields unless a dirty case proves the need.
- Do not claim SACP guarantees correctness.
- Do not modify files unless explicitly asked.
- If you propose changes, keep them docs-only and small.
```

## Optional Her/Agent-Specific Adapter Note

If the testing agent has its own workflow concepts, ask it to fill this mapping:

```text
Native task id -> SACP handoff_id:
Native retry/run id -> SACP attempt_id:
Native agent/worker id -> SACP agent_id:
Native final answer -> SACP claims:
Native tool output -> SACP evidence:
Native tests/checks -> SACP verification:
Native reviewer/assignee -> SACP next_owner:
Native approval gate -> SACP human_decision_required / sacp.chain.decisions:
Native trace/checkpoint -> extensions.sacp.chain.checkpoint:
```

