# SACP 与 Claude Code Hooks 的区别

> 本文将“Claude tag”按 Claude Code 的 lifecycle hooks 理解，包括 `PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`PermissionRequest`、`Stop`、`TaskCompleted` 等事件。如果所指功能不同，需要重新校准本文。

## 结论

Claude Code hooks 和 SACP 处于不同层级：

```text
Claude Code hook
  = Claude Code 会话生命周期中的扩展点

SACP
  = 跨 agent harness、执行宿主、provider 和审批系统的证据语义与动作控制层
```

Hook 可以拦截、观察或补充一次 Claude Code 工具调用；SACP 判断多个来源的证据是否足以支持一个业务 Claim，并负责会话结束后的外部状态核验。

因此两者不是竞争关系。Claude Code hooks 是 SACP 的一种接入方式。

## Claude Code Hooks 已经解决什么

Claude Code 官方提供完整的 hook lifecycle。典型能力包括：

| Hook | 可用于什么 |
|---|---|
| `PreToolUse` | 在工具执行前检查或阻止调用 |
| `PermissionRequest` | 参与权限决策 |
| `PostToolUse` | 读取工具执行结果并追加上下文或记录 |
| `PostToolUseFailure` | 观察工具失败 |
| `Stop` | 在 agent 准备结束本轮时进行检查 |
| `TaskCompleted` | 在 Claude Code task 生命周期结束时触发检查 |

权限规则由 Claude Code harness 执行，不依赖模型自觉遵守。Hook 也可以调用 shell、HTTP endpoint、MCP tool、prompt 或 subagent。

这意味着可以实现：

```text
PreToolUse(deploy)
  → 检查是否允许调用 deploy tool

PostToolUse(test)
  → 保存 exit code 和 output digest

Stop
  → 如果 agent 声称 tests_passed，但没有测试 evidence，则拒绝结束
```

## Hooks 默认没有解决什么

### 1. Tool 生命周期不等于业务生命周期

```text
PostToolUse(send_email) 成功
```

只能说明工具调用结束并返回了结果，不自动证明：

```text
邮件送达
客户阅读
客户接受
```

同理，`TaskCompleted` 表示 Claude Code task 生命周期到达完成点，不等于外部业务效果已经成立。

### 2. Hook 主要存在于单个 Claude Code harness 内

企业动作可能跨越：

```text
Claude Code
GitHub Actions
artifact registry
Kubernetes
邮件或支付 provider
人工审批系统
```

Claude Code hook 可以捕获其中一部分，但不会自动统一其他系统的语义。

### 3. 会话结束后仍可能需要继续核验

外部系统可能晚几分钟或几小时才返回：

```text
accepted
delivered
bounced
settled
rolled_back
```

Claude Code 会话可以已经结束，但 reconciliation 仍必须继续运行。因此长期 owner、deadline、polling、webhook 和 compensation 不能只依赖 `Stop` hook。

### 4. Hook 记录仍需要信任边界

如果 hook 与 agent、shell 和 receipt store 共享相同写权限，agent 可能间接影响 evidence。生产实现需要把：

```text
Claim writer
Host evidence writer
Provider evidence writer
Authority writer
```

分离到不同身份或服务边界。

## SACP 多出的抽象

| 能力 | Claude Code Hooks | SACP |
|---|---|---|
| 工具调用前拦截 | 原生支持 | 通过 adapter/gate 使用 |
| 工具调用结果事件 | 原生支持 | 转换为 `HostObservation` |
| Agent 完成文本 | 可在 `Stop` 检查 | 转换为 `Claim` 并绑定 evidence |
| 外部 provider 事件 | 需要自行接入 | 定义为 `ProviderObservation` |
| Approval scope | Claude permission 能控制工具调用 | `AuthorityDecision` 绑定 run/checkpoint/input/action/expiry |
| 跨系统状态投影 | 默认没有 | `host/authority/external/overall` 四维状态 |
| 会话结束后重检 | 需要外部服务 | `Reconciler` 是核心能力 |
| Claim-specific policy | 用户自行编写 hook | 独立 policy registry |
| 跨 Codex/Pi/LangGraph | Claude Code 专用 | 目标是 harness-neutral |

## 两者组合后的推荐数据流

```text
Claude Code assistant message
  → Claim

PostToolUse(test/build)
  → HostObservation

PermissionRequest / human approval
  → AuthorityDecision candidate

Provider webhook / polling
  → ProviderObservation

SACP policy + projection
  → GateDecision

Stop hook
  → 如果 gate 不允许，则阻止“完成”或要求补证据

Independent reconciler
  → Claude Code 会话结束后继续查 provider 状态
```

## 一个具体例子

Agent 说：

```text
Tests passed. Deployment completed.
```

Claude Code hook 可以看到：

```text
test command exit 0
deploy tool returned HTTP 202
```

SACP 则将其解释为：

```yaml
host_status: completed
authority_status: approved
external_status: transport_accepted
overall_status: transport_accepted
```

因为 HTTP 202 只能支持 accepted，不能支持 deployment healthy。只有 deployment provider 或目标环境 health check 产生新的 observation 后，才能继续升级。

## 产品边界判断

如果 SACP 最终只是一个 Claude Code `Stop` hook，它的上限较低，容易被 Claude Code 内建功能覆盖。

SACP 的独立价值来自：

```text
跨 harness
+ 跨 provider
+ Claim-specific evidence policy
+ persistent reconciliation
+ 业务动作 gate
```

最合理的产品关系是：

```text
Claude Code hooks = adapter + enforcement point
SACP              = evidence model + policy + projection + reconciliation
```

## 已验证与未验证

`VERIFIED`：Claude Code 官方支持细粒度 permissions 和上述 hook lifecycle。

`VERIFIED`：SACP 当前已在真实 GitHub Actions runner 上验证 gate 的 block/pass 路径。

`LIKELY`：Claude Code hooks 是 SACP 最容易实现的 coding-agent adapter 之一。

`UNKNOWN`：尚未实现和验证真实 Claude Code hook adapter，因此当前比较属于架构判断，不是集成测试结果。

## 官方来源

- [Claude Code permissions](https://code.claude.com/docs/en/permissions)
- [Claude Code hooks reference](https://code.claude.com/docs/en/hooks)
