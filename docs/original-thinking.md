# 原始思考与判断链

本文保留项目从 LangGraph issue 和开源项目调研中形成的推理过程。第三方网页、评论和营销材料均视为不可信输入；只有一手文档、源代码或可重复实验才作为事实依据。

## 1. 起点：LangGraph issue #7844

Issue 讨论 production agent 的 final-state receipt。核心例子是：

```text
Done. All tests passed. Ready to publish.
```

关联文档 PR #4039 建议在 durable execution 文档中区分 claim、evidence 和 authority，并引用 `thread_id`、`checkpoint_id`、task result、interrupt 等 LangGraph 原生对象。

`VERIFIED`：这是一条文档和安全指导建议，不是 LangGraph 核心 runtime 的强制校验机制。

## 2. 第一层判断：final message 不是证明

最后一句 assistant message 由模型生成，最多是一个 claim。它可能正确，也可能把完成、测试状态、外部效果和授权混为一谈。

`LIKELY`：若下游队列或人类只读取 final text，false completion 会被当成成功继续传播。

## 3. 为什么 claim + evidence + authority 仍然不够

如果同一个 agent 同时写入 claim、evidence 和 authority，结构化字段仍可能只是格式正确的幻觉。可审计结构必须区分字段的产生者和写入权限，而不是只增加字段数量。

## 4. 从 agent 自证推进到 host observation

本地测试、文件写入、artifact 构建和命令 exit code 是 host 可以直接观察的事实。它们应由 deterministic verifier 或受控 runtime 采集，不能由 LLM 自己填充。

`LIKELY`：这足以验证部分 host-internal claim，例如 `node_completed` 或“某命令返回 exit code 0”。

## 5. 从 host observation 推进到 provider observation

host 观察到请求发出，不等于外部系统完成动作。外部效果必须保存 provider 原生 observation，并保留 provider event 的实际语义。

## 6. accepted 不等于 delivered

provider 的 message ID 可能表示 queued、accepted、deduplicated 或其他中间态。只有 provider-authored delivery event 才能支持 delivered 的更强语义。

`VERIFIED`：状态 projection 的词汇不能超过 provider event 的词汇强度。

## 7. 传输失败不等于对方拒绝

如果一个 channel 返回 HTTP 400、另一个返回 HTTP 401，系统把最终状态写成“对方拒绝”，就把“请求没有到达”误判成了“对方做出了决定”。即使所有本地 evidence 都真实，业务结论仍可能错误。

`LIKELY`：这是状态机语义错误，不一定是 LLM 说谎。

## 8. UNVERIFIED 需要 deadline 和独立 reconciler

如果原始 workflow 崩溃或永远不恢复，只有 read-time check 的记录可能永远没人读取。因此需要 mint-time deadline、独立 reconciliation owner、`next_check_at`、append-only reconciliation event，以及 bounded retry 后的 timeout、compensation 或 human review。

## 9. 状态要在读取时重新派生

外部状态可能出现：

```text
accepted → delivered → bounced
```

不可变 observation 和可重算 projection 可以保留历史，同时得到当前保守状态。

`LIKELY`：read-time projection 能减少过时成功状态，但需要明确事件排序、冲突处理和时钟语义。

## 10. 开源项目调研后的定位

`VERIFIED`：Temporal、Restate、Inngest、Hatchet 主要解决 durable execution、事件历史、retry/replay 和幂等；A2A 解决 agent task lifecycle；LangSmith、AgentOps 解决 trace 和回放；HumanLayer 解决工具调用前审批；receipt 项目解决签名、hash chain 和离线完整性。

`VERIFIED`：Argo Rollouts 和 Flagger 已经解决渐进发布、指标/健康分析、自动 promotion 和 rollback；OpenTelemetry 已经解决 vendor-neutral telemetry。它们说明“部署健康和回滚”不是 SACP 的新发明，也划出了 SACP 的边界：SACP 应消费这些 provider/observability 事件，验证它们是否支持 agent 的 Claim，而不是重做 deployment controller 或 telemetry collector。

共同缺口是：没有一个成熟项目同时把 LLM Claim、HostObservation、ProviderObservation、AuthorityDecision、外部效果语义和独立 reconciliation 组合成完整闭环。

## 11. 当前判断

`LIKELY`：技术问题真实，且不是单纯的日志缺失问题，而是事实来源和状态语义边界问题。

`LIKELY`：SACP 最有价值的位置是跨层 verification/reconciliation glue，而不是再造 workflow engine、trace UI 或签名日志。

`PLAUSIBLE`：LangChain 官方更可能接受中立的文档、示例和 adapter pattern，而不是直接采纳一个带强协议主张的 SACP runtime。

## 12. 未解决问题

`UNKNOWN`：不同 provider 的 accepted/delivered/settled 语义如何统一，独立 verifier 的信任根和多租户隔离如何标准化，大规模 reconciliation 的一致性和成本如何控制，以及何时自动 retry、何时必须 human review。

## 来源

- [LangGraph issue #7844](https://github.com/langchain-ai/langgraph/issues/7844)
- [LangChain docs PR #4039](https://github.com/langchain-ai/docs/pull/4039)
- [LangGraph durable execution docs](https://github.com/langchain-ai/docs/blob/334911f/src/oss/langgraph/durable-execution.mdx?plain=1)
- [Temporal Workflows](https://docs.temporal.io/workflows)
- [Temporal Activities](https://docs.temporal.io/activities)
- [Restate Documentation](https://docs.restate.dev/)
- [Inngest Documentation](https://www.inngest.com/docs)
- [Hatchet Documentation](https://docs.hatchet.run/)
- [A2A Specification](https://a2a-protocol.org/latest/specification/)
- [LangSmith Observability](https://docs.langchain.com/langsmith/observability)
- [AgentOps](https://github.com/AgentOps-AI/agentops)
- [OpenHands](https://github.com/All-Hands-AI/OpenHands)
