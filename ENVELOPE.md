# SACP Envelope

The Envelope is the protocol wrapper.

Envelope 是协议外壳。它像 HTTP header，也像快递面单。它不负责装全部任务内容，只负责让接收方先读懂这次工作事务的身份、版本、动作、资源、责任人和输入指纹。

## Principle

```text
Prompt belongs in the body.
Protocol identity belongs in the envelope.
```

如果一个字段决定“这是不是同一个任务、谁在处理、能不能重试、输入有没有变”，它应该在 Envelope 里。

如果一段文字只是任务说明、背景、prompt、解释，它应该在 body 里。

## Required Fields

| Field | Type | Meaning |
|---|---|---|
| `protocol` | string | Protocol version. v0.1 must be `SACP/0.1`. |
| `type` | string | Packet type. For work handoff, use `handoff`. |
| `method` | string | Protocol action, such as `CLAIM`, `RETRY`, or `BLOCK`. |
| `resource_type` | string | Resource category, such as `handoff`, `task`, or `memory_item`. |
| `resource_id` | string | Concrete resource id. |
| `handoff_id` | string | Stable idempotency key for the work request. |
| `attempt_id` | string | Execution attempt id under the handoff. |
| `agent_id` | string | Actor sending or claiming the packet. |
| `created_at` | string | ISO 8601 timestamp. |
| `source_fingerprint` | string | Stable digest or source identifier for the input. |
| `content_type` | string | Body format, such as `text/markdown` or `application/json`. |

## Optional Fields

| Field | Type | Meaning |
|---|---|---|
| `lease_owner` | string | Actor currently holding the lease. |
| `lease_expires_at` | string | ISO 8601 timestamp for lease expiration. |
| `reply_to` | string | Optional packet or receipt id this packet responds to. |
| `extensions` | map | Namespaced non-core metadata. |

## Valid Minimal Envelope

```yaml
protocol: SACP/0.1
type: handoff
method: CLAIM
resource_type: handoff
resource_id: hf_check_claims_001
handoff_id: hf_check_claims_001
attempt_id: attempt_001
agent_id: AI-04
created_at: 2026-05-07T20:30:00+08:00
source_fingerprint: sha256:abc123
content_type: text/markdown
```

Body:

```markdown
Review the public draft and identify claims that need evidence before publication.
```

## Valid Envelope With Lease

```yaml
protocol: SACP/0.1
type: handoff
method: CLAIM
resource_type: handoff
resource_id: hf_check_claims_001
handoff_id: hf_check_claims_001
attempt_id: attempt_001
agent_id: AI-04
created_at: 2026-05-07T20:30:00+08:00
source_fingerprint: sha256:abc123
content_type: text/markdown
lease_owner: AI-04
lease_expires_at: 2026-05-07T21:00:00+08:00
extensions:
  vendor.langgraph.checkpoint_id: checkpoint_123
  vendor.openai.trace_id: trace_abc
```

## Invalid Envelope Examples

### Missing Handoff Id

```yaml
protocol: SACP/0.1
type: handoff
method: CLAIM
resource_type: handoff
resource_id: hf_check_claims_001
attempt_id: attempt_001
agent_id: AI-04
created_at: 2026-05-07T20:30:00+08:00
source_fingerprint: sha256:abc123
content_type: text/markdown
```

Expected result:

```yaml
status_code: 400
status_text: invalid_packet
problem: "Missing required field: handoff_id."
```

### Prompt Mixed Into Protocol Identity

```yaml
protocol: SACP/0.1
type: handoff
method: "Please check this carefully and be smart"
resource_type: handoff
resource_id: hf_check_claims_001
handoff_id: hf_check_claims_001
attempt_id: attempt_001
agent_id: AI-04
created_at: 2026-05-07T20:30:00+08:00
source_fingerprint: sha256:abc123
content_type: text/markdown
```

Expected result:

```yaml
status_code: 400
status_text: invalid_packet
problem: "method must be a valid SACP method, not free-form prompt text."
required_fix: "Use method: CLAIM and move the prompt text into the body."
```

## Idempotency Rules

- `handoff_id` identifies the stable work request.
- `attempt_id` identifies one execution attempt.
- Same `handoff_id` and same `source_fingerprint` should not be processed twice unless a new `attempt_id` is explicitly created through `RETRY`.
- Same `handoff_id` with changed `source_fingerprint` means the input changed and should be reviewed as rework.

## Lease Rules

- A receiver should not claim a handoff while another actor has an active lease.
- Active lease collision should return `423 lease_active`.
- Expired lease should return `504 lease_expired` or create a new attempt with `RETRY`.
- Lease does not imply success. A receipt is still required.

