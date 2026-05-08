# Multi-Model Dirty Run Report

- Protocol: `SACP/0.1`
- Tested at: `2026-05-07T23:21:50+0800`
- Total cases: `10`

| Model | Passed | Failed | Notes |
|---|---:|---:|---|
| deepseek_pro / `deepseek-v4-pro` | 10 | 0 | endpoint `api.deepseek.com` |
| qwen_strong / `qwen3.6-plus` | 10 | 0 | endpoint `dashscope.aliyuncs.com` |
| glm_strong / `glm-4.7` | 10 | 0 | endpoint `open.bigmodel.cn` |
| kimi_strong / `kimi-k2.6` | 9 | 1 | endpoint `api.moonshot.cn` |

## Case Results

### deepseek_pro / `deepseek-v4-pro`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt (attempt_001, 200). Do not redo the work. |
| active_lease_collision | 423 | 423 | True | 等待租约过期、释放或协调者重新分配。 |
| expired_lease | 504 | 504 | True | ```yaml status_code: 504 status_text: lease_expired verdict: handoff_lease_expired receipt_completeness: no_receipt c... |
| changed_source_fingerprint | 202 | 202 | True | Treat as rework, not duplicate. |
| missing_evidence | 412 | 412 | True | Provide a verifiable source (e.g., a trusted source_id) or downgrade the claim’s support_status to 'unsupported'/'unv... |
| user_statement_as_fact | 412 | 412 | True | Change claim_type to user_statement and mark support_status as unsupported, or provide proper retrieval evidence. |
| inference_as_retrieved_fact | 412 | 412 | True | Change claim_type to 'inference' or cite a trusted source; set human_decision_required=true. |
| memory_candidate_auto_promoted | 412 | 412 | True | ```yaml status_code: 412 status_text: missing_evidence verdict: "Memory promotion request lacks supporting evidence; ... |
| completion_without_receipt | 400 | 400 | True | Produce a SACP receipt with claims, verification, next_owner, and human_decision_required. |
| ambiguous_next_owner | 400 | 400 | True | 将 next_owner 设为具体代理（agent）、角色、协调器（coordinator）或 "Human"。 |

### qwen_strong / `qwen3.6-plus`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| active_lease_collision | 423 | 423 | True | Wait for lease expiration, release, or coordinator reassignment. |
| expired_lease | 504 | 504 | True | Create a new attempt_id under the same handoff_id or reassign. |
| changed_source_fingerprint | 202 | 202 | True | Treat as rework, not duplicate. |
| missing_evidence | 412 | 412 | True | Attach verifiable source_id/evidence, or downgrade claim_type to inference/user_statement and support_status to unver... |
| user_statement_as_fact | 412 | 412 | True | Change claim_type to user_statement or provide external evidence. |
| inference_as_retrieved_fact | 412 | 412 | True | Change claim_type to inference or cite a verifiable external source. Downgrade support_status to unverified if no ext... |
| memory_candidate_auto_promoted | 412 | 412 | True | Keep memory pending and provide approval evidence before PROMOTE. |
| completion_without_receipt | 400 | 400 | True | Produce a SACP receipt with claims, verification, next_owner, and human_decision_required. |
| ambiguous_next_owner | 400 | 400 | True | Set next_owner to a concrete actor, role, coordinator, or Human. |

### glm_strong / `glm-4.7`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt. Do not redo the work. |
| active_lease_collision | 423 | 423 | True | Wait for lease expiration, release, or coordinator reassignment. |
| expired_lease | 504 | 504 | True | Create a new attempt_id under the same handoff_id or reassign. |
| changed_source_fingerprint | 202 | 202 | True | None |
| missing_evidence | 412 | 412 | True | Provide a trusted source for the fact or downgrade claim_type to 'inference' and support_status to 'unverified'. |
| user_statement_as_fact | 412 | 412 | True | Change claim_type to user_statement or provide external evidence. |
| inference_as_retrieved_fact | 412 | 412 | True | Change claim_type to inference or cite a trusted source. |
| memory_candidate_auto_promoted | 412 | 412 | True | Keep memory pending and provide approval evidence before PROMOTE. |
| completion_without_receipt | 400 | 400 | True | Produce a SACP receipt with claims, verification, next_owner, and human_decision_required. |
| ambiguous_next_owner | 400 | 400 | True | Set next_owner to a concrete actor, role, coordinator, or Human. |

### kimi_strong / `kimi-k2.6`

| Case | Expected | Actual | Pass | Required Fix Excerpt |
|---|---:|---:|---:|---|
| duplicate_handoff | 409 | 409 | True | Return or link the existing receipt for handoff_id hf_check_claims_001 (attempt_001, status 200). Do not redo the wor... |
| active_lease_collision | 423 | 423 | True | Wait for lease expiration, release, or coordinator reassignment. |
| expired_lease | 504 | 504 | True | Create a new attempt_id under the same handoff_id or reassign. |
| changed_source_fingerprint | 202 | 400 | False | Method must be REWORK for changed source_fingerprint; RETRY requires identical fingerprint. Or issue new handoff_id. |
| missing_evidence | 412 | 412 | True | Provide trusted source_id with retrievable evidence, or downgrade to user_statement/inference with support_status: un... |
| user_statement_as_fact | 412 | 412 | True | Change claim_type to user_statement or provide external evidence |
| inference_as_retrieved_fact | 412 | 412 | True | Change claim_type to 'inference' and adjust support_status to 'unverified' or 'unsupported'; or provide actual retrie... |
| memory_candidate_auto_promoted | 412 | 412 | True | Abort PROMOTE. Keep memory_item mem_strategy_001 in previous_state: pending_verification. Obtain human_approval_id wi... |
| completion_without_receipt | 400 | 400 | True | Produce a SACP receipt with claims, verification, next_owner, and human_decision_required. |
| ambiguous_next_owner | 400 | 400 | True | Set next_owner to a concrete actor, role, coordinator, or Human. Additionally, change claim_type to user_statement wi... |

