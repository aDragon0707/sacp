# 证据模型

## 四类事实

### Claim

Agent 或业务组件提出的声明，例如 `tests_passed`、`refund_reviewed`、`ready_to_publish`。它只能证明系统曾提出该声明，不能证明声明真实、证据充分或已经获得授权。原始 claim append-only，修正应产生新 claim。

### HostObservation

宿主直接观察到的本地事实，例如 command digest、exit code、test output artifact digest、artifact hash、checkpoint、task result。它能证明宿主观察到了某个本地执行结果，但不能证明外部系统接受、送达、结算或业务有效。

### ProviderObservation

外部系统原生返回的事件或状态，例如 `accepted`、`delivered`、`bounced`、`settled`、`unauthorized`，以及 provider receipt ID、webhook event 和 raw digest。它只能证明 provider 声称发生了什么；`accepted` 不自动证明 `delivered`。

### AuthorityDecision

人或策略系统对下一步动作的授权决定。它能证明指定主体在指定 scope 内作出授权，但不能证明被授权动作已经成功。必须关联 `thread_id`、`run_id`、`checkpoint_id`、`input_digest`、`action_scope` 和 `expires_at`。

## 写入边界

```text
agent              → Claim
deterministic host → HostObservation
provider adapter    → ProviderObservation
human/policy system → AuthorityDecision
verifier            → DerivedReceipt
```

Agent 不得直接写入 HostObservation、ProviderObservation 或 AuthorityDecision，也不得直接指定派生 `status`。同一个 `action_id` 下存在合格 observation 也不等于某条 Claim 已被证明；Claim 必须通过 `evidence_refs` 明确引用具体 event ID，验证器再检查引用的 event 类型和内容是否匹配。对 `tests_passed`，引用必须指向 `host_observation(kind=test_run)`，且包含成功 exit code 和 output digest。

## 声明与最低证据

| 声明 | 最低证据 |
|---|---|
| `node_completed` | durable host event |
| `tests_passed` | command/spec digest + exit status + output artifact digest |
| `artifact_built` | artifact identity + digest + build result |
| `transport_accepted` | provider-authored accepted event |
| `delivered` | provider-authored delivery event |
| `counterparty_declined` | counterparty observation |
| `ready_to_publish` | separate human/policy authority decision |

## 派生 receipt 示例

```yaml
status: needs_approval
action_id: refund-123
thread_id: support-ticket-123
run_id: run-456
checkpoint_id: checkpoint-789
claims:
  - claim: refund_reviewed
    evidence_refs:
      - <host-observation-event-id>
authority:
  required: true
  decision: pending
  owner: manager_approval_queue
next_action_owner: manager_approval_queue
```

`status` 必须由验证器根据 observation 和 authority 重新计算。

生产消费方应优先读取分维度结果：`host_status`、`authority_status`、`external_status`、`overall_status`。旧的 `status` 字段只保留为 `overall_status` 的兼容别名。
