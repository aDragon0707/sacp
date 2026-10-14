# 保守状态机

## 三个独立维度

不要把所有事情压进一个 `status`：

```text
host_status       本地执行是否有合格观察
authority_status  是否获得当前 action 的授权
external_status   provider 报告了什么
overall_status    由前三者派生的下一步判断
```

例如：

```yaml
host_status: completed
authority_status: approved
external_status: not_attempted
overall_status: ready_for_external_action
```

这表示“本地准备完成且获得授权，可以尝试外部动作”，不表示外部动作已经成功。

## 正常路径

```text
dispatch_intended
  → dispatched_unverified
  → transport_accepted
  → provider_reported_delivered
  → externally_verified
```

每一步都需要新的、来源更强的 observation，不是同义词。

## 异常和等待状态

```text
provider_error
undelivered
bounced
counterparty_declined
attestation_timed_out
needs_human_review
authority_violation
```

`unverified` 和 `dispatched_unverified` 表示宿主记录了 dispatch，但还没有足够 provider 事实。它们不是成功，也不是对方拒绝。

## 投影规则

1. Provider 只有 `accepted` 时，`external_status` 最多是 `transport_accepted`，`overall_status` 也不得升级为 delivered。
2. 只有 provider-authored delivery event 才能派生 `provider_reported_delivered`。
3. `accepted → delivered → bounced` 时，当前投影必须降级或暴露矛盾，不能永久保持 `delivered`。
4. HTTP `400`、`401`、credential failure 或 conversation missing 不能派生 `counterparty_declined`。
5. 本地 exit code 为 0 不能单独派生 `deployed`、`payment_settled` 或 `delivered`。
6. 缺少足够外部 witness 时，不能生成外部成功终态。
7. 新 observation 可以改变当前 projection，但不能改写历史 observation。
8. 任何 pending 状态都必须有 `attestation_deadline`、`reconciliation_owner` 和后续动作。
9. timeout 后只能进入 retry、compensation 或 human review 路径，不能静默当作失败或成功。
10. `status` 仅作为 `overall_status` 的兼容别名；新代码应读取三个维度和 `overall_status`。
11. 需要授权的 action 如果在 `authority_status != approved` 时已经产生外部 observation，`overall_status` 必须是 `authority_violation`，不能被外部状态覆盖。

部署动作另有一条外部效果路径：`deployment_accepted` 不等于 `deployment_healthy`；health observation 必须绑定相同 revision；后续 rollback 可以降级此前的健康投影。

这条路径应优先复用 Argo Rollouts、Flagger 或目标平台已有的 health/rollback 事件。SACP 负责验证这些事件与当前 action/revision 的关联，并决定是否允许最终化，不负责替代 deployment controller。

## Reconciliation 生命周期

```text
mint dispatch scope
  → schedule next_check_at
  → record attested / absent / provider_error
  → re-arm bounded checks
  → derive attestation_timed_out
  → route retry / compensation / human review
```

`attestation_deadline`、`reconciliation_owner` 和首次 `next_check_at` 应在 action scope 创建时固定。检查“没有找到证据”本身也要写成 reconciliation event。

## Authority 边界

Approval 必须绑定：

```text
thread_id + run_id + checkpoint_id + input_digest + action_scope + expiry
```

绑定不匹配时，即使存在 `approved` 记录，也不能授权当前 action。

## Retry 和补偿

所有可能产生外部副作用的动作都需要 `action_id`、`idempotency_key`、provider request/receipt ID、retry count、compensation owner 和明确的重复执行策略。系统不能把“本地未知”自动变成“安全重试”。
