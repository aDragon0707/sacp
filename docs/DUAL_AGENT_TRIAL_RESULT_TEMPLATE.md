# Dual-Agent Trial Result Template

Use this template after OpenClaw and herness return their SACP Agent Test Reports.

This is a coordination note, not a protocol change. Do not use it to add core fields or claim framework support.

## Metadata

```text
Trial id:
Date:
Coordinator:
OpenClaw report path:
herness report path:
Related prompt: docs/SACP_AGENT_TEST_PROMPT.md
Runbook: docs/DUAL_AGENT_TRIAL_RUNBOOK.md
```

## Command Results

| Check | OpenClaw | herness | Evidence path or excerpt |
|---|---|---|---|
| `python validator.py --examples --strict` | pass / fail / not run | pass / fail / not run | |
| `done_but_no_receipt` diagnosis | expected / unexpected | expected / unexpected | |
| `unsupported_test_claim` diagnosis | expected / unexpected | expected / unexpected | |

Expected:

- `done_but_no_receipt` -> `400 invalid_packet`
- `unsupported_test_claim` -> `412 missing_evidence`
- validator examples -> pass

## Protocol Understanding

| Question | OpenClaw | herness | Coordinator note |
|---|---|---|---|
| Explains SACP as a receipt layer | yes / partial / no | yes / partial / no | |
| Understands SACP is not a runtime | yes / partial / no | yes / partial / no | |
| Does not claim SACP guarantees correctness | yes / partial / no | yes / partial / no | |
| Understands Receipt Chain as optional profile | yes / partial / no | yes / partial / no | |

## Native Field Mapping

| SACP field | OpenClaw mapping | herness mapping | Notes |
|---|---|---|---|
| `handoff_id` | | | |
| `attempt_id` | | | |
| `agent_id` | | | |
| `claims[]` | | | |
| `claims[].source_id` | | | |
| `verification.evidence_id` | | | |
| `next_owner` | | | |
| `human_decision_required` | | | |
| `extensions.sacp.chain.checkpoint` | | | |

## Issues Found

Record only concrete issues.

| Issue | Agent | File/path | Severity | Proposed action |
|---|---|---|---|---|
| | OpenClaw / herness / both | | bug / confusion / suggestion | docs-only / dirty case / reject |

## Coordinator Decision

Choose one:

```text
PASS
PASS_WITH_NOTES
FAIL
```

Decision:

Reason:

Accepted follow-up:

Rejected follow-up:

## SACP Receipt For The Trial

Fill this only after both reports are collected.

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

## Save Locations

Suggested report paths:

```text
sample-corpus/review-notes/openclaw_sacp_trial_YYYYMMDD.md
sample-corpus/review-notes/herness_sacp_trial_YYYYMMDD.md
sample-corpus/review-notes/033_dual_agent_trial_result.md
```

Do not commit private raw logs, secrets, hidden prompts, or provider credentials.
