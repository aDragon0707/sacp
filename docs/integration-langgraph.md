# LangGraph 集成说明

本文件描述未来适配方式，不修改 LangGraph 核心，也不把 checkpoint 自动解释成外部成功。

## 映射关系

```text
thread_id       → workflow identity
run_id          → execution identity
checkpoint_id   → state version
task_result     → HostObservation
interrupt       → AuthorityDecision boundary
checkpointer    → evidence locator
webhook/polling → ProviderObservation
reconciler      → timeout/retry/compensation owner
```

## 推荐数据流

```text
LLM node → emits Claim
deterministic verifier → reads graph state, task results, exit codes, artifacts
external provider adapter → writes ProviderObservation
approval service / policy engine → writes AuthorityDecision
SACP projection → derives conservative receipt and routes next action
```

## 禁止模式

```text
final assistant message → receipt.status="completed"
LLM tool output         → provider delivery proof
checkpoint exists       → external success
provider receipt ID     → automatically delivered
local exit code 0       → payment settled / deployed
```

## Approval 绑定

Approval 至少绑定：

```text
thread_id + run_id + checkpoint_id + input_digest + action_scope + expiry
```

Graph 恢复后如果 checkpoint、输入摘要或 action scope 变化，必须重新审批。approval 只证明有权尝试动作，不证明动作已经成功。

## 外部动作

LangGraph task 记录 dispatch intent 和 host observation；provider adapter 保存 provider 原生 event；reconciler 处理 webhook、轮询、缺失证据和 deadline；projection 只能使用 provider event 的实际语义。

## 兼容性原则

SACP adapter 不要求 LangGraph 修改现有 graph API。它可以通过 callback、middleware、wrapper node 或外部 event consumer 接入，但不能让 LLM 节点获得 receipt store 的写权限。
