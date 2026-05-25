# SACP Dual-Agent Trial Runbook

Use this runbook to test SACP with two independent agents, such as OpenClaw and herness.

Goal:

```text
Confirm that two agents can read SACP, run the local checks, explain the protocol, map their own workflow fields into receipts, and return comparable audit reports.
```

This is a docs-first trial. Do not ask the agents to modify the protocol during the first pass.

## Roles

| Agent | Role | Main question |
|---|---|---|
| OpenClaw | Runtime/operator reviewer | Can SACP fit an agent workspace with tasks, handoffs, tools, and context rotation? |
| herness | Independent framework reviewer | Can SACP be understood and mapped by another agent system without adopting a runtime dependency? |
| Human | Coordinator | Compare reports, accept small docs fixes, reject scope expansion. |

## Inputs

Send each agent the prompt in:

```text
docs/SACP_AGENT_TEST_PROMPT.md
```

Ask each agent to produce exactly one report using the requested `SACP Agent Test Report` format.

## Trial Steps

### Step 1: Dispatch

For each agent:

```text
1. Paste the prompt from docs/SACP_AGENT_TEST_PROMPT.md.
2. Tell the agent whether it is acting as OpenClaw or herness.
3. Ask it not to edit files.
4. Ask it to include command results and concrete issue paths.
```

### Step 2: Required Commands

Each agent should run:

```powershell
cd C:\Users\86181\Documents\Codex\2026-05-07\openclaw-llm\sacp
python validator.py --examples --strict
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/done_but_no_receipt.md
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md
```

### Step 3: Required Review Targets

Each agent should inspect:

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

### Step 4: Result Collection

Save each returned report as a local note or paste it into the coordinator thread.

Use [DUAL_AGENT_TRIAL_RESULT_TEMPLATE.md](./DUAL_AGENT_TRIAL_RESULT_TEMPLATE.md) to compare the two reports and write the coordinator receipt.

Suggested filenames:

```text
sample-corpus/review-notes/openclaw_sacp_trial_YYYYMMDD.md
sample-corpus/review-notes/herness_sacp_trial_YYYYMMDD.md
```

Do not commit raw private logs, secrets, or hidden prompts.

## Result Table

Use this table to compare outputs:

| Field | OpenClaw | herness |
|---|---|---|
| validator command | pass / fail / not run | pass / fail / not run |
| done_but_no_receipt diagnosis | expected / unexpected | expected / unexpected |
| unsupported_test_claim diagnosis | expected / unexpected | expected / unexpected |
| explains SACP correctly | yes / partial / no | yes / partial / no |
| understands SACP is not runtime | yes / partial / no | yes / partial / no |
| maps native task id to `handoff_id` | yes / partial / no | yes / partial / no |
| maps retry/run to `attempt_id` | yes / partial / no | yes / partial / no |
| maps tool output to evidence | yes / partial / no | yes / partial / no |
| maps reviewer/human gate | yes / partial / no | yes / partial / no |
| Receipt Chain useful? | yes / partial / no | yes / partial / no |
| confusing field | list | list |
| verdict | PASS / PASS_WITH_NOTES / FAIL | PASS / PASS_WITH_NOTES / FAIL |

## Expected Command Results

Expected validator result:

```text
All examples PASS.
```

Expected `done_but_no_receipt` diagnosis:

```text
status_code: 400
status_text: invalid_packet
required_fix: Produce a SACP receipt with claims, verification, next_owner, and human_decision_required.
```

Expected `unsupported_test_claim` diagnosis:

```text
status_code: 412
status_text: missing_evidence
required_fix: Attach command output or downgrade the test claim to unverified.
```

## Acceptance Rules

PASS:

```text
Both agents can run or understand the checks, explain SACP as a receipt layer, and map their native fields into a receipt without treating SACP as a runtime.
```

PASS_WITH_NOTES:

```text
The protocol is usable, but one or both agents find wording or mapping confusion that can be fixed in docs or examples.
```

FAIL:

```text
An agent cannot distinguish SACP from a runtime, cannot map core fields, or finds examples structurally invalid.
```

## Follow-Up Rules

Turn feedback into changes only if it is concrete.

Good follow-up:

- clarify a confusing field
- add one example
- add one dirty case
- improve a mapping table
- fix a broken command or path

Bad follow-up:

- add new core fields without a dirty case
- turn SACP into an agent runtime
- add a database, server, or auth layer
- claim SACP proves correctness
- accept vague feedback like "make it more enterprise"

## Trial Receipt

After both reports are collected, write one SACP receipt for the trial:

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
handoff_id: hf_dual_agent_sacp_trial_001
attempt_id: attempt_001
agent_id: HumanCoordinator
claims:
  - text: "OpenClaw and herness trial reports were collected and compared."
    claim_type: tool_result
    source_id: openclaw_herness_trial_reports
    support_status: supported
verification:
  status: passed
  method: "dual-agent report comparison"
  evidence_id: openclaw_herness_trial_reports
residual_risk: "Follow-up docs fixes may still be needed if either report is PASS_WITH_NOTES."
next_owner: Human
human_decision_required: false
extensions:
  sacp.chain.profile: sacp-chain
  sacp.chain.project: sacp_dual_agent_trial
  sacp.chain.module: external_agent_review
  sacp.chain.evidence:
    - openclaw_sacp_trial_report
    - herness_sacp_trial_report
  sacp.chain.stop_rule: "Do not change core fields unless both reports identify the same dirty-case-backed need."
```

