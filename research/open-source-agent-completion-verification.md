# 开源项目对 Agent 完成声明验证问题的解法

研究日期：2026-08-30

## 研究问题

当 agent 声称“任务完成、测试通过、已经部署、消息已送达、可以发布”时，现有开源项目如何保存执行证据、验证外部副作用、处理人工授权、重试和恢复？这些方案与 SACP 所关注的 `claim + evidence + authority` 有什么关系？

## 结论摘要

目前主流开源方案大致分为三类：

1. **Durable execution / workflow engine**：保存事件历史、恢复运行、重试任务、约束副作用和幂等性。
2. **Agent observability**：记录 trace、tool call、输入输出和异常，帮助人类事后检查。
3. **Human-in-the-loop / approval**：在高风险动作前暂停并取得人类授权。

这些项目能提供 SACP 所需的底层证据，但没有发现一个成熟开源项目完整覆盖以下闭环：

```text
agent claim
  -> non-agent host observation
  -> provider-authored external observation
  -> independent verification/reconciliation
  -> conservative derived state
  -> explicit authority and next owner
```

因此 SACP 仍有可区分的空间，但它不应重新实现 workflow engine 或 tracing 平台。最合理的位置是连接这些系统的“证据边界、状态派生和完成声明验证层”。

## 项目比较

| 项目 | 开源方案解决的部分 | 没有解决的关键部分 | 对 SACP 的价值 |
|---|---|---|---|
| Temporal | Durable Workflow、Event History、deterministic replay、Activity result、retry、推荐 Activity 幂等 | Activity 成功不自动证明外部世界最终状态；没有通用 claim/evidence/authority receipt | 可作为可靠执行与本地证据底座 |
| Restate | Durable execution、持久状态、可靠通信、工作流、人类审批、文档宣称 guaranteed execution / exactly-once semantics | “exactly once”不能自动赋予第三方业务事件语义；仍需 provider witness 和 reconciliation | 适合实现独立 verifier/reconciler 服务 |
| Inngest | Event-driven durable functions、steps、queueing、retries、checkpointing、flow control、observability | 重点是函数最终运行，不是 agent 完成声明的证据强度或外部效果语义 | 可作为轻量 orchestration 适配目标 |
| Hatchet | Durable task/workflow、durable event log、retry/replay、idempotency、OpenTelemetry、self-hosting | 记录 task invocation 不等于验证业务完成；未见通用外部 attestation 模型 | 适合验证 SACP 不依赖 LangGraph |
| LangSmith | Agent trace、生产监控、evaluation、feedback、automation、webhook | trace 是“发生过什么”的记录，不是独立 witness；不能自动阻止 self-attestation | SACP 可引用 trace/run ID，但不应把 trace 当证明 |
| AgentOps | Session replay、execution graph、输入输出和异常记录、框架集成 | README 将 external success validators 列在 roadmap；当前重心仍是 observability | 说明“可观察”与“可验证完成”之间仍有缺口 |
| HumanLayer | 人工介入/审批思路与 authority boundary 高度相关 | 当前公开仓库 README 明示代码基本已 deprecated；不能直接作为稳定实现基础 | 证明 approval 是独立维度，但需另选实现或自建 |
| OpenHands / Agent Canvas | Agent runtime、conversation/event、automation、run history、不同 backend 和 sandbox | 重点是执行与控制面；未见完整 provider attestation 和 completion receipt 语义 | 可作为 coding-agent failure corpus 和集成对象 |
| A2A Protocol | Agent-to-agent task lifecycle、状态枚举、Get/Subscribe/Push、messageId 幂等、细分 400/401/403/404/5xx | Task status 仍是 agent/server 声明；没有第三方 witness、签名 receipt 或外部业务结果验证 | 可作为 SACP 的 transport/task adapter，但不能作为完成证明 |
| agent-receipts-mcp | Canonical JSON、Ed25519、prev-receipt hash 链、offline verify、审计 bundle | 签名证明“谁签了什么”，不证明 action 真的发生；无 provider reconciliation 和权限隔离；项目成熟度很低 | 可借鉴 tamper evidence，但不能替代独立事实核验 |
| TheAxiomFoundation/receipt | Consumer-pinned trust anchors、Ed25519、RFC3161 timestamp、append-only provenance、offline fail-closed verifier | 验证记录完整性/来源/时间，不验证邮件、支付、部署等业务效果 | 可借鉴消费者控制信任根和 fail-closed 验证 |

## 逐项分析

### Temporal

Temporal 的 Workflow Execution 产生 Commands 并处理 Events，记录为 Event History。恢复时通过 replay 重建状态；与外部世界交互的操作放在 Activity 中，Activity 完成结果进入 Workflow Event History。官方文档还明确建议 Activity 应幂等。

这解决了：

- 运行过程不会因为进程崩溃而完全丢失；
- Workflow 可以从历史中重放；
- Activity 的本地完成结果有持久化记录；
- 重试、副作用封装和幂等性有成熟模型。

但 Temporal 的 `ActivityTaskCompleted` 只能证明 worker 向 Temporal 报告了 Activity 完成。若 Activity 的目标是发消息、部署或支付，最终外部效果仍需要 provider 事件、状态查询或 webhook 验证。Temporal 是 execution truth 的强底座，不是 external-world truth 的通用证明系统。

来源：

- [Temporal Workflows](https://docs.temporal.io/workflows)
- [Temporal Activities](https://docs.temporal.io/activities)

### Restate

Restate 将 agent、workflow 和 backend service 变为 durable process。官方首页列出 durable execution、built-in state、reliable communication、durable timers、human approvals，并宣称服务调用具有 guaranteed execution 和 exactly-once semantics。

它适合实现：

- receipt verifier service；
- 独立于原 graph thread 的 reconciliation owner；
- durable deadline、callback 和 retry；
- provider observation 的持久事件处理。

边界仍然存在：runtime 的 exactly-once/guaranteed execution 不能自动证明第三方业务语义。例如调用支付接口一次不等于支付已经结算；收到 message ID 不等于消息送达。

来源：

- [Restate Documentation](https://docs.restate.dev/)

### Inngest

Inngest 是 event-driven durable execution 平台，支持 TypeScript、Python、Go，提供 steps、queueing、scaling、concurrency、throttling、rate limiting 和 observability。文档还列出了 Durable Agents 和 Agent Evals。

它能解决函数的调度和恢复，但“函数最终运行完成”与“agent 声称的业务结果真实”仍是两回事。SACP 可将 Inngest step/run/event ID 当作 host evidence，再补外部 provider observation 和 authority decision。

来源：

- [Inngest Documentation](https://www.inngest.com/docs)

### Hatchet

Hatchet 将 task、worker 和 durable workflow 作为核心概念。其文档说明每个 task、DAG、event 或 agent invocation 都保存于 durable event log，可用于 debugging、retry 和 replay；同时提供 idempotency、timeouts、pausing、OpenTelemetry 和 self-hosting。

Hatchet 与 Temporal/Restate 类似，能证明 orchestrator 观察到的执行事实，但不能仅凭 durable event log 证明 provider 侧交付、支付、部署或对方决策。

来源：

- [Hatchet Documentation](https://docs.hatchet.run/)

### LangSmith

LangSmith 官方将 trace 定义为 agent 在生产环境中做了什么的记录，提供 trace 查看、比较、监控、evaluation、feedback、automation 和 webhook。

LangSmith 非常适合作为证据索引：receipt 可以引用 trace/run/span ID。但 trace 通常由被观测应用上报，因此仍需要区分：

- 应用声称某动作成功；
- collector 收到了这个声明；
- 独立 verifier 重新检查了结果；
- provider 确认了外部效果。

来源：

- [LangSmith Observability](https://docs.langchain.com/langsmith/observability)

### AgentOps

AgentOps 的开源 README 展示了 session replay、agent execution graph、input/output recording、exception handling、framework integrations 和 self-hosting。它能帮助开发者复盘 agent 做过什么。

但 README 的 roadmap 将 `Success validators (external)` 列为尚未完成的方向。这直接说明 observability 本身还没有解决独立完成验证。

来源：

- [AgentOps GitHub](https://github.com/AgentOps-AI/agentops)

### HumanLayer

HumanLayer 的历史定位与 human-in-the-loop、审批和高风险 tool call authority 很相关。但其当前 GitHub README 明确写着公开仓库代码“pretty much all deprecated”，并指向重建后的产品。

因此可以借鉴其 authority boundary 思路，但不能未经进一步代码和维护状态审计就把该仓库作为 SACP 的基础依赖。

来源：

- [HumanLayer GitHub](https://github.com/humanlayer/humanlayer)

### OpenHands / Agent Canvas

当前 OpenHands README 将 Agent Canvas 描述为 coding agents 和 automation 的 self-hosted control center，支持多种 agent backend、scheduled/webhook automation、sandbox，以及 automation run history。仓库边界也将 conversation、workspace、events 和 automation history 分开。

这提供了运行和审计控制面，但 README 中没有看到完整的 claim/evidence/authority schema、provider-side effect attestation 或 reconciliation lifecycle。它更适合作为 SACP 的集成目标和真实失败测试环境。

来源：

- [OpenHands GitHub](https://github.com/All-Hands-AI/OpenHands)

### A2A Protocol

A2A 规范标准化 agent-to-agent Task 生命周期，定义 `SUBMITTED`、`WORKING`、`COMPLETED`、`FAILED`、`CANCELED`、`INPUT_REQUIRED`、`REJECTED`、`AUTH_REQUIRED` 等状态，并支持查询、订阅和 push updates。规范还允许用 `messageId` 做幂等，并区分认证、授权、校验、资源和系统错误。

这对 SACP 很有用，因为它提供了可适配的传输层状态；但 `COMPLETED` 依然是 agent/server 发出的状态声明，不是第三方见证。A2A 没有规定 host observation、provider delivery witness、签名 receipt 或 reconciliation。

来源：

- [A2A GitHub](https://github.com/a2aproject/A2A)
- [A2A Specification](https://a2a-protocol.org/latest/specification/)

### agent-receipts-mcp

该项目把 consequential action 写成 canonical JSON receipt，用 Ed25519 签名，并以 `prev_receipt_hash` 构造链；支持 payload SHA-256、离线 CLI 验证和 signed audit bundle。它解决的是 custody、完整性和删除/篡改检测。

但签名只证明“某个 issuer 签了某份声明”，不证明 action 的业务效果。若 agent 能控制传入的 claim 和 evidence，签名可能只是把错误声明不可变地保存下来。项目公开仓库目前规模很小，不能视为市场成熟度证据。

来源：

- [agent-receipts-mcp GitHub](https://github.com/dhanushs1912-svg/agent-receipts-mcp)

### TheAxiomFoundation/receipt

该项目更偏通用审计基础设施：消费者在提交代码中固定 trust anchors，使用 Ed25519、RFC3161 双见证时间戳、append-only release-chain，并提供无需网络、凭据或 producer 配合的 fail-closed verifier。

它值得借鉴的不是业务 receipt 字段，而是信任根不能由 producer runtime 替换，以及 verifier 在无法验证时应拒绝给出绿色结论。它仍不验证“邮件已送达”“付款已结算”“部署已生效”等外部事实。

来源：

- [TheAxiomFoundation/receipt](https://github.com/TheAxiomFoundation/receipt)

## 对 SACP 的产品定位建议

SACP 不应与 Temporal、Restate、Inngest 或 Hatchet 竞争 durable orchestration，也不应与 LangSmith、AgentOps 竞争 trace UI。

建议定位为：

> A conservative completion-verification layer that turns workflow traces and provider observations into evidence-bounded final-state receipts.

最小模块：

1. `Claim`：LLM 可提出，不具备证明权。
2. `HostObservation`：由 non-LLM runtime 写入，例如 exit code、artifact digest、checkpoint/task result。
3. `ProviderObservation`：保存 provider 原生 event、receipt ID、raw digest 和语义来源。
4. `AuthorityDecision`：人工或策略系统签发，绑定 action scope、checkpoint/input digest 和 expiry。
5. `Projection`：从不可变观察中保守推导当前状态。
6. `Reconciler`：独立于原 workflow 生存，负责 deadline、provider polling/webhook、absence check、timeout 和 compensation。

## 建议的开源 MVP

先做一个 Python reference package，并支持 LangGraph + 一个通用 workflow backend：

- `Pydantic` 数据模型与 JSON Schema；
- append-only SQLite/PostgreSQL observation store；
- LangGraph checkpointer/task/interrupt adapter；
- Temporal 或 Restate verifier/reconciler demo；
- provider webhook/polling adapter interface；
- idempotency key 和 action scope digest；
- failure-injection tests。

必须覆盖的 breaker cases：

1. agent 声称测试通过，但没有 test runner evidence；
2. deploy command exit 0，但 health check 失败；
3. provider `accepted` 后出现 `bounced`；
4. HTTP 400/401 被错误映射成对方拒绝；
5. workflow 崩溃后没有继续验证；
6. approval 绑定旧 checkpoint，实际执行新输入；
7. timeout retry 导致重复外部动作；
8. agent 尝试自己填写或修改 evidence。

## 证据质量和限制

- 本笔记优先使用项目官方文档、官方 GitHub README 和公开仓库内容。
- 各项目文档中的性能、规模和“exactly once”等宣传性声明未做独立基准验证。
- HumanLayer 官方文档站点在本次访问中出现证书日期错误，因此未绕过安全提示；仅使用其官方 GitHub README。
- LangSmith 是相关方案，但不是纯粹的 OSS 项目；将其列入是因为它是 LangGraph 生态中最直接的 observability 对照组。
- “没有完整覆盖”是基于本次公开文档范围内未发现，不等于证明任何项目内部或商业版本绝对不存在相应能力。
