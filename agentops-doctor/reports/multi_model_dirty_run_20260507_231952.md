# Multi-Model Dirty Run Report

- Protocol: `SACP/0.1`
- Tested at: `2026-05-07T23:17:18+0800`
- Total cases: `3`

| Model | Passed | Failed | Notes |
|---|---:|---:|---|
| deepseek_pro / `deepseek-v4-pro` | 3 | 0 | endpoint `api.deepseek.com` |
| qwen_strong / `qwen3.6-plus` | 3 | 0 | endpoint `dashscope.aliyuncs.com` |
| glm_strong / `glm-4.7` | 3 | 0 | endpoint `open.bigmodel.cn` |
| kimi_strong / `kimi-k2.6` | 0 | 3 | endpoint `api.moonshot.cn` |

## Case Results

### deepseek_pro / `deepseek-v4-pro`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| missing_evidence | 412 | 412 | True | Provide a trusted source for the claim, or downgrade claim_type to inference/user_statement and adjust support_status... |
| memory_candidate_auto_promoted | 412 | 412 | True | Keep memory pending and provide approval evidence before PROMOTE. |

### qwen_strong / `qwen3.6-plus`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| missing_evidence | 412 | 412 | True | Attach a verifiable source_id or downgrade claim_type to inference/user_statement and support_status to unverified/un... |
| memory_candidate_auto_promoted | 412 | 412 | True | Keep memory pending and provide approval evidence before PROMOTE. |

### glm_strong / `glm-4.7`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| missing_evidence | 412 | 412 | True | Provide a trusted source for the fact or downgrade claim_type to 'inference' and support_status to 'unverified'. |
| memory_candidate_auto_promoted | 412 | 412 | True | Keep memory pending and provide approval evidence before PROMOTE. |

### kimi_strong / `kimi-k2.6`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | None | False | {"error":{"message":"invalid temperature: only 0.6 is allowed for this model","type":"invalid_request_error"}} |
| missing_evidence | 412 | None | False | {"error":{"message":"invalid temperature: only 0.6 is allowed for this model","type":"invalid_request_error"}} |
| memory_candidate_auto_promoted | 412 | None | False | {"error":{"message":"invalid temperature: only 0.6 is allowed for this model","type":"invalid_request_error"}} |

