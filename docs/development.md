# 开发文档

## MVP 范围

第一版是独立 Python reference implementation，目标是验证证据边界和状态机，不接 LangGraph 核心、不接真实 provider、不引入密码学签名。

目标环境：Python 3.11+。数据存储使用标准库 SQLite，测试使用 `unittest`，时间使用注入式 clock。

## 模块边界

```text
model.py
  数据模型、枚举和不可变事件结构

store.py
  append-only SQLite observation store

verifier.py
  证据引用检查、权限边界和 receipt projection

provider.py
  mock provider 事件序列和 receipt ID

reconciler.py
  deadline、absence check、timeout、retry/compensation 路由

tests/
  failure-injection scenarios
```

## 已实现接口

```python
append_claim(claim: Claim) -> EventId
record_host_observation(observation: HostObservation) -> EventId
record_provider_observation(observation: ProviderObservation) -> EventId
record_authority_decision(decision: AuthorityDecision) -> EventId

project_receipt(action_id: str, now: datetime) -> DerivedReceipt
reconcile(now: datetime) -> list[str]  # created reconciliation event IDs
```

接口约束：append 只追加，不提供 update/delete；当前 `EventStore` 是内部完整写入接口，尚未提供独立的 Agent-facing facade；`project_receipt` 不接受外部传入的最终 `status`，而是返回 `host_status`、`authority_status`、`external_status` 和 `overall_status`；`.status` 仅是 `overall_status` 的兼容别名；非法 evidence reference、未引用的同 action evidence 或类型不匹配的 evidence 都会强制投影为 `unverified`；evidence reference 当前使用 store 返回的 event UUID。对 `tests_passed`，Claim 必须引用一条合格的 `host_observation(kind=test_run)`。

## 数据与错误处理

SQLite 表至少保存 immutable event ID、event type、action/thread/run/checkpoint IDs、actor/source、payload digest、时间戳和 reconciliation reference。第一阶段不承诺分布式一致性，但数据模型要能迁移到 PostgreSQL/event store。

- agent claim 缺证据：`unverified`；
- provider 认证或请求错误：`provider_error`/`undelivered`；
- approval scope 不匹配：`needs_human_review`；
- 需要授权但已产生外部 observation：`authority_violation`；
- deadline 超过：reconciler 记录一条 `absent` reconciliation event，之后投影为 `attestation_timed_out`；
- 状态矛盾：保留全部 observation，projection 标记降级或矛盾；
- 重复事件：按 provider event ID/action ID 去重，但不删除原始输入。

## Mock provider 与测试

Mock provider 固定支持 `accepted`、`accepted → delivered`、`accepted → delivered → bounced`、`unauthorized`、`bad_request` 和通过不发事件表示的 `no_event`。除具体故障案例外，`tests/test_properties.py` 使用固定随机种子生成 100 组 provider 事件序列，验证保守状态边界、投影幂等和事件历史单调增长。

必须测试：缺少测试证据、本地 deploy 成功但健康检查失败、accepted 不升级 delivered、400/401 不升级 declined、workflow 崩溃后的独立 reconciliation、deadline timeout、旧 approval、重复 retry、Agent 无法写 evidence、新 observation 改变 projection 但不改历史。

M4.1 已实现 file-backed store reopen 后的 reconciliation 恢复：独立 reconciler 重新读取历史 claim 和 observation，deadline 超过且没有 provider evidence 时追加一个 `absent` event；如果已有同一 action 的 `absent` event 且没有新 provider observation，则不重复追加。`next_check_at` 字段用于后续检查时间，并由 M4.2 的 `RetryPolicy` 驱动有限次数的恢复调度。

M4.2 增加 `RetryPolicy`。它用 `max_attempts`、`retry_delay` 和 `compensation_owner` 固定恢复边界。`ReconciliationEvent` 会记录 `attempt`、`route` 和 `next_check_at`；`route=retry` 表示安排下一次 reconciliation，`route=compensation` 表示达到上限并转交补偿 owner。它只调度恢复动作，不执行真实 provider retry 或 compensation。`DerivedReceipt.recovery_route`、`next_check_at`、`next_action_owner` 和 `retry_allowed` 是上层执行器的唯一读取接口。

M5.1 的 `sacp_verify.langgraph_adapter` 是可选集成实验。LangGraph 负责 `StateGraph`、节点执行和 `InMemorySaver` checkpoint；adapter 将 graph 的 logical thread/run/checkpoint 映射到 SACP 的 Claim、HostObservation 和 AuthorityDecision，并让 mock provider 写入 ProviderObservation。该模块依赖 `langgraph`，因此不从 `sacp_verify.__init__` re-export，也不改变核心 reference implementation 的零依赖入口。

持久化实验使用 `langgraph-checkpoint-sqlite` 的 `SqliteSaver`。`store_database` 保存 SACP 的 append-only events，`checkpoint_database` 保存 LangGraph graph state；两者可以在进程关闭后分别恢复。SQLite checkpointer 需要允许 LangGraph worker thread 使用连接，adapter 已显式设置 `check_same_thread=False`。这只是单进程/单 writer 实验，不代表生产级并发一致性。

M3 已加入独立的 `DeploymentGate.can_finalize()` 和 `MockDeploymentProvider`：`accepted` 只能表示部署请求被接受；只有匹配 revision 的 `healthy` observation 才允许最终化；`failed` 或后续 `rolled_back` 会阻止或降级当前结论。receipt 的 `external_status` 会分别反映 `transport_accepted`、`provider_reported_healthy`、`deployment_failed` 和 `deployment_rolled_back`。该 provider 仍是 mock，不接真实环境。

M3.5 增加 `StagingHTTPServer`/`StagingHTTPClient`，在 `127.0.0.1` 上通过真实 HTTP 请求验证 deploy acceptance、health check 和失败状态。它只模拟 staging provider，不访问公网；`tests/test_staging_http.py` 验证真实 socket、HTTP response、revision 绑定和 health 投影。

## M3 与现有部署系统的边界

Argo Rollouts 和 Flagger 已经提供 Kubernetes progressive delivery、metrics/health analysis、自动 promotion 和 rollback；OpenTelemetry 提供跨 vendor 的 traces、metrics 和 logs。这些项目解决的是“部署如何渐进、观察和回滚”，SACP 不重复实现这些能力。

SACP 的接入点是把现有系统的输出纳入 Agent Action 的证据链：

```text
Agent Claim
  + CI/artifact HostObservation
  + approval AuthorityDecision
  + Argo/Flagger/deployment ProviderObservation
  + health/rollback observation
  → can_finalize / conservative receipt
```

重点差异是：deployment provider 的 `accepted`、Rollout 的 promotion 或 OTel trace 都不能单独证明 agent 的最终业务 Claim；它们必须按 revision、action scope 和 provider-native semantics 组合后，才允许派生 `externally_verified`。

参考：

- [Argo Rollouts](https://argo-rollouts.readthedocs.io/en/stable/)
- [Flagger](https://docs.flagger.app/)
- [OpenTelemetry](https://opentelemetry.io/docs/)

## 验证命令

```powershell
python -m unittest discover -s tests -v
```

推荐先运行完整发布任务场景：

```powershell
python -m examples.release_task
```

该场景依次验证本地测试证据、人工审批、provider accepted、provider delivered 和后续 bounced 降级；它只使用 mock provider，不发送真实消息。

GitHub Actions release gate fixture 进一步验证 commit、CI check、artifact 和 release approval 的组合，并通过 `ReleaseGate.can_proceed()` 产生明确的 allow/block 决策；fixture 不访问 GitHub 网络。`GitHubActionsPayloadAdapter` 接受 GitHub REST-shaped `workflow_run`、`artifact` 和 PR `reviews` payload，仍然只做本地解析，不访问 GitHub 网络；它也支持 `gh api --paginate --slurp` 的分页数组。`.github/workflows/sacp-release-gate.yml` 将同一 gate 放进 GitHub Actions；它通过 `gh api` 读取 PR reviews，再由 `sacp_verify.cli` 以非零 exit code 阻止不满足条件的 release。

该 workflow 还提供 sandbox-only `workflow_dispatch` 的 `approved-fixture` acceptance smoke test，用于在真实 GitHub runner 上验证 allowed path；它不执行发布。pull request 路径仍只接受真实 matching review。

M4 重启验证可运行：

```powershell
python -m examples.reconciliation_restart
```

该示例只使用临时 SQLite 文件，模拟原 workflow 进程退出后由新的 reconciler 进程恢复。它不连接真实 provider；provider 延迟到达的投影由 `test_late_provider_observation_supersedes_timeout_projection` 覆盖。

bounded retry 验证可运行：

```powershell
python -m examples.bounded_recovery
```

LangGraph 实验可运行：

```powershell
python -m examples.langgraph_release_experiment
```

它覆盖五个路径：缺少 approval 时 graph 在 dispatch 前停止；匹配 approval 后 provider 只返回 `accepted`，receipt 仍保持 `transport_accepted`；graph 结束且没有 provider witness 时，由 graph 外部的 reconciler 继续推进 timeout/retry；retry 预算耗尽后转 compensation；provider 延迟到达后停止 recovery route。

SQLite 重启实验可运行：

```powershell
python -m examples.langgraph_sqlite_restart
```

完整集成测试可运行：

```powershell
python -m examples.langgraph_http_integration
```

它把 LangGraph SQLite checkpoint、SACP SQLite event store、`StagingHTTPServer`/`StagingHTTPClient`、独立 `Reconciler` 和 `DeploymentGate` 串在一条临时 localhost 流程中。它验证 provider evidence 到达后会停止 retry/compensation，并允许匹配 revision 的 deployment health finalize。

退款 Agent 实验可运行：

```powershell
python -m examples.refund_agent
```

`MockRefundProvider` 用 `idempotency_key` 去重 refund request，并把 provider `accepted` 与 webhook `succeeded` 分成两个事件。`RefundGate` 要求 approval 和 order/amount/currency 全部匹配后才允许 finalize；它不代表真实支付系统或真实资金到账。

若系统没有可用的 `python` 命令，使用 workspace bundled Python runtime 执行同一命令。实现阶段必须保留完整命令输出和 exit code。

## 未来适配

LangGraph 读取 checkpointer/task result/interrupt；Temporal 读取 Activity/Event History；Restate 读取 journal/durable message；Inngest/Hatchet 读取 step/event history；LangSmith/AgentOps 只作为 trace/evidence locator，不作为业务事实来源。

Claude Code 的接入边界和 SACP 的独立价值见 [SACP 与 Claude Code Hooks 的区别](comparison-claude-code-hooks.md)。
