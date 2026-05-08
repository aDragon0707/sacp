# Multi-Model Dirty Run Report

- Protocol: `SACP/0.1`
- Tested at: `2026-05-07T23:20:47+0800`
- Total cases: `3`

| Model | Passed | Failed | Notes |
|---|---:|---:|---|
| kimi_strong / `kimi-k2.6` | 2 | 1 | endpoint `api.moonshot.cn` |

## Case Results

### kimi_strong / `kimi-k2.6`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| missing_evidence | 412 | 412 | True | ```yaml status_code: 412 status_text: missing_evidence verdict: invalid_receipt receipt_completeness: structurally_co... |
| memory_candidate_auto_promoted | 412 | 400 | False | Method PROMOTE is not defined in SACP/0.1 for memory state transitions. Memory promotion requires human_decision_requ... |

