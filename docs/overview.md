# 问题与目标

生产 agent 经常用一条自然语言消息表示多个不同强度的结论：

```text
Done. All tests passed. Ready to publish.
```

它同时涉及流程完成、测试状态、外部动作和下一步授权。若这些结论只存在于 final assistant message 中，系统无法区分模型说了什么和系统观察到什么。

## Durable execution 的边界

Durable execution、checkpoint、event history 和 task result 可以定位 workflow 到达了哪里、某个 task 返回了什么、某个命令的 exit code 是多少、某次 interrupt 是否被请求或批准。

它们不能单独证明邮件送达、部署健康、付款结算或对方拒绝。执行历史是 execution truth，不自动是 external-world truth。

## SACP 的目标

SACP 将以下四类事实按类型与语义分别记录；当前 Python API 不认证写入者，权限隔离仍由接入方实现：

```text
Claim               agent 提出的声明
HostObservation     宿主观察到的本地事实
ProviderObservation 外部系统返回的事实
AuthorityDecision   人或策略系统授予的权限
```

运行时 `DerivedReceipt` 是历史事件的派生视图，不是 Agent 自填状态。它与 `SACP/0.1` 交换 receipt 不同；CI builder 单独生成后者。当前架构与边界参见[架构说明](./architecture.md)、[证据模型](./evidence-model.md)和[运行时契约](./runtime-contracts.md)。

## 目标用户

- 构建 LangGraph、Temporal、Restate、Inngest、Hatchet 等长运行 agent 的团队；
- 需要人工审批、外部副作用和重试控制的工作流；
- 需要审查完成声明是否有可定位证据的平台和运维人员。

## 不解决什么

SACP 不替代 durable workflow engine、trace 平台、provider 的业务状态系统，也不把签名变成真实性证明。它只约束声明是否超出了可验证证据边界。

## 成功标准

MVP 应能阻止或降级以下错误：没有测试输出却声称 tests passed；本地 deploy 成功却没有健康证据；provider accepted 被升级成 delivered；400/401 被解释成对方拒绝；workflow 死亡后 pending record 无人负责；旧 approval 被复用；retry 重复执行外部副作用。
