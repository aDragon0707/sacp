# DeepSeek Dirty Run Test Plan

This plan tests whether a DeepSeek model can apply AgentOps Doctor rules to SACP/0.1 dirty cases.

它不是测试 DeepSeek 聪不聪明，而是测试它能否在协议约束下稳定返回状态码、诊断和修复动作。

## Test Method

For each dirty case:

1. Send `agentops-doctor/prompt_skill.md`.
2. Append one dirty case input.
3. Ask the model to diagnose under SACP/0.1.
4. Compare returned `status_code`, `status_text`, and `required_fix`.

## Pass Criteria

For each case:

- status family must match
- status text should match or be semantically equivalent
- required fix must address the real protocol violation
- model must not claim it executed the underlying task
- model must not invent missing evidence

Minimum MVP pass:

```text
8/10 cases pass
```

Strict pass:

```text
10/10 cases pass
```

## Cases

| Case | Expected |
|---|---|
| duplicate handoff | `409 duplicate_handoff` |
| active lease collision | `423 lease_active` |
| expired lease | `504 lease_expired` |
| changed source fingerprint | `202 accepted_processing` as rework |
| missing evidence | `412 missing_evidence` |
| user statement as fact | `412 missing_evidence` |
| inference as retrieved fact | `412 missing_evidence` |
| memory candidate auto-promoted | `412 missing_evidence` |
| completion without receipt | `400 invalid_packet` |
| ambiguous next owner | `400 invalid_packet` |

## Result Template

```yaml
model:
tested_at:
total_cases: 10
passed:
failed:
case_results:
  - case_id:
    expected_status:
    actual_status:
    pass:
    notes:
limitations:
```

