# Multi-Model Dirty Run Report

- Protocol: `SACP/0.1`
- Tested at: `2026-05-07T23:13:25+0800`
- Total cases: `3`

| Model | Passed | Failed | Notes |
|---|---:|---:|---|
| deepseek_pro / `deepseek-v4-pro` | 3 | 0 | endpoint `api.deepseek.com` |
| qwen_strong / `qwen3.6-plus` | 3 | 0 | endpoint `dashscope.aliyuncs.com` |
| glm_strong / `glm-4.7` | 1 | 2 | endpoint `open.bigmodel.cn` |
| kimi_strong / `kimi-k2.6` | 0 | 3 | endpoint `api.moonshot.cn` |

## Case Results

### deepseek_pro / `deepseek-v4-pro`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| missing_evidence | 412 | 412 | True | ```yaml status_code: 412 status_text: missing_evidence verdict: receipt is invalid due to lack of evidence for a retr... |
| memory_candidate_auto_promoted | 412 | 412 | True | status_code: 412 status_text: missing_evidence verdict: Handoff rejected; auto-promotion of pending memory is not aud... |

### qwen_strong / `qwen3.6-plus`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| missing_evidence | 412 | 412 | True | Provide a trusted source or downgrade claim_type/support_status. |
| memory_candidate_auto_promoted | 412 | 412 | True | Keep memory pending and provide approval evidence before PROMOTE. |

### glm_strong / `glm-4.7`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| missing_evidence | 412 | None | False |  |
| memory_candidate_auto_promoted | 412 | None | False | {"error":{"code":"1302","message":"您的账户已达到速率限制，请您控制请求频率"}} |

### kimi_strong / `kimi-k2.6`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | None | False |  |
| missing_evidence | 412 | None | False | {"error":{"message":"Your account org-a2deddaeecef47409acc4befe05d13c5\u003cak-f9jk7ugf3um111atmp3i\u003e request rea... |
| memory_candidate_auto_promoted | 412 | None | False |  |

