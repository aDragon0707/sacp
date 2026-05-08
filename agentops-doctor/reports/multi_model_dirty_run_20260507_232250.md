# Multi-Model Dirty Run Report

- Protocol: `SACP/0.1`
- Tested at: `2026-05-07T22:57:27+0800`
- Total cases: `10`

| Model | Passed | Failed | Notes |
|---|---:|---:|---|
| deepseek_pro / `deepseek-v4-pro` | 9 | 1 | endpoint `api.deepseek.com` |
| qwen_strong / `qwen3.6-plus` | 10 | 0 | endpoint `dashscope.aliyuncs.com` |
| glm_strong / `glm-4.7` | 3 | 7 | endpoint `open.bigmodel.cn` |
| kimi_strong / `kimi-k2.6` | 1 | 9 | endpoint `api.moonshot.cn` |

## Case Results

### deepseek_pro / `deepseek-v4-pro`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | ```yaml status_code: 409 status_text: duplicate_handoff verdict: "The handoff hf_check_claims_001 was already complet... |
| active_lease_collision | 423 | 423 | True | 等待租约过期（2026-05-07T22:40:00+08:00）、人工释放租约，或由协调器重新分配。 |
| expired_lease | 504 | 504 | True | Create a new attempt_id under the same handoff_id, or reassign the handoff. |
| changed_source_fingerprint | 202 | 202 | True | ```yaml status_code: 202 status_text: accepted_processing verdict: "Valid rework, not duplicate. The source fingerpri... |
| missing_evidence | 412 | 412 | True | Provide a trusted source for the retrieved fact, or downgrade claim_type to 'inference' with support_status 'unverifi... |
| user_statement_as_fact | 412 | 412 | True | Change claim_type to 'user_statement' or provide external evidence supporting the factual claim. |
| inference_as_retrieved_fact | 412 | 412 | True | status_code: 412 status_text: missing_evidence verdict: "Claim classified as retrieved_fact but source is only model ... |
| memory_candidate_auto_promoted | 412 | None | False |  |
| completion_without_receipt | 400 | 400 | True | Produce a valid SACP/0.1 receipt containing claims, verification, next_owner, and human_decision_required. |
| ambiguous_next_owner | 400 | 400 | True | Set next_owner to a concrete actor, role, coordinator, or Human. |

### qwen_strong / `qwen3.6-plus`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| active_lease_collision | 423 | 423 | True | Wait for lease expiration, release, or coordinator reassignment. |
| expired_lease | 504 | 504 | True | Create a new attempt_id under the same handoff_id or reassign. |
| changed_source_fingerprint | 202 | 202 | True | Treat as rework, not duplicate. |
| missing_evidence | 412 | 412 | True | Provide a trusted source or downgrade claim_type/support_status. |
| user_statement_as_fact | 412 | 412 | True | Change claim_type to user_statement or provide external evidence. |
| inference_as_retrieved_fact | 412 | 412 | True | Change claim_type to inference or cite a trusted source. |
| memory_candidate_auto_promoted | 412 | 412 | True | Keep memory pending and provide approval evidence before PROMOTE. |
| completion_without_receipt | 400 | 400 | True | Produce a SACP receipt with claims, verification, next_owner, and human_decision_required. |
| ambiguous_next_owner | 400 | 400 | True | Set next_owner to a concrete actor, role, coordinator, or Human. |

### glm_strong / `glm-4.7`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | ```yaml status_code: 409 status_text: duplicate_handoff verdict: REJECT  |
| active_lease_collision | 423 | None | False |  |
| expired_lease | 504 | None | False |  |
| changed_source_fingerprint | 202 | None | False |  |
| missing_evidence | 412 | 412 | True | ```yaml status_code: 412 status_text: missing_evidence verdict: FAIL receipt_completeness: Present but invalid claim_... |
| user_statement_as_fact | 412 | None | False |  |
| inference_as_retrieved_fact | 412 | None | False | ```yaml status |
| memory_candidate_auto_promoted | 412 | None | False |  |
| completion_without_receipt | 400 | 400 | True | Produce a SACP/0.1 receipt containing claims, verification, next_owner, and human_decision_required fields. |
| ambiguous_next_owner | 400 | None | False |  |

### kimi_strong / `kimi-k2.6`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | None | False |  |
| active_lease_collision | 423 | None | False |  |
| expired_lease | 504 | None | False |  |
| changed_source_fingerprint | 202 | None | False |  |
| missing_evidence | 412 | 412 | True | ```yaml status_code: 412 status_text: missing_evidence verdict: unsupported_claim_marked_supported  |
| user_statement_as_fact | 412 | None | False |  |
| inference_as_retrieved_fact | 412 | None | False |  |
| memory_candidate_auto_promoted | 412 | None | False |  |
| completion_without_receipt | 400 | None | False |  |
| ambiguous_next_owner | 400 | None | False |  |

