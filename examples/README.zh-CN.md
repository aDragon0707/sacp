# SACP 示例导航

[English](./README.md) · [项目入口](../README.zh-CN.md)

从这里选择可运行示例或协议文档。Python demo 演示运行时行为，YAML 展示交换契约。校验 YAML 不会执行文档描述的任务。

## 先运行三条命令

使用 Python 3.11 或 3.12。所有命令都在**仓库根目录**运行，不要先进入 `examples/`：

```bash
python -m pip install -r requirements-ci.txt
python -m sacp_harness
python -m examples.github_release_gate
```

Harness 检查 8 个固定反例，并校验公开协议示例和转写 receipt。发布示例随后展示正向与反向 gate 决策：

```text
1) missing approval: allowed=False, reason=release_approval_missing_or_stale, overall=needs_approval
2) matching approval: allowed=True, reason=release_evidence_and_authority_verified, overall=ready_for_external_action
3) artifact belongs to another commit: allowed=False, reason=release_evidence_missing_or_invalid, overall=unverified
```

这里的 `allowed=True` 是基于本地 fixture 的预检决定，没有实际发布，也没有向 GitHub 发送请求。

## 运行时 Demo

这些 demo 不需要 provider 凭据，使用内存数据或临时 SQLite 文件；可选 HTTP demo 会启动 localhost 服务，并在退出时关闭。除非另有明确说明，demo 内部的测试结果、批准和 provider 回调均为合成数据。

| 想理解什么 | 在仓库根目录运行 | 重点观察 |
|---|---|---|
| 发布证据与授权 | `python -m examples.github_release_gate` | 匹配批准允许预检；缺少批准或产物 commit 不匹配会阻止 |
| REST 形状的 adapter 输入 | `python -m examples.github_api_payload_gate` | 给定 workflow、artifact、review payload 的相同 gate 边界；没有认证 REST 请求 |
| 本地、授权、外部状态的区别 | `python -m examples.release_task` | 批准、accepted、delivered、bounced 分别影响 receipt 的不同维度 |
| 部署何时算完成 | `python -m examples.deployment_verification` | accepted 不够，匹配健康证据才允许最终化；rollback 后再次阻止 |
| 退款完成与 mock 幂等 | `python -m examples.refund_agent` | 同一 mock 实例的重复请求返回相同 ID；匹配 succeeded 证据后才允许最终化 |
| 有界恢复路线 | `python -m examples.bounded_recovery` | 首次超时走 retry；耗尽配置的次数后交给 compensation owner |
| 重新打开事件账本 | `python -m examples.reconciliation_restart` | 重开 SQLite 后仍可看到超时状态；重复检查不再追加同一超时 |

源码：[发布 gate](./github_release_gate.py)、[payload adapter demo](./github_api_payload_gate.py)、[发布生命周期](./release_task.py)、[部署](./deployment_verification.py)、[退款](./refund_agent.py)、[有界恢复](./bounded_recovery.py)、[账本重开](./reconciliation_restart.py)。

建议顺序：发布 gate → 发布生命周期 → 部署 → 有界恢复 → 账本重开。想理解领域完成条件与幂等时，再看退款。

恢复 demo 记录路线，不执行实际重试或补偿。账本重开示例关闭并重建对象，不是操作系统级 crash test。Mock 退款 ID 仅在进程内保持，不提供持久化 exactly-once 保证。部署健康检查与动作授权也是不同职责。

## 可选 LangGraph Demo

先安装集成依赖：

```bash
python -m pip install -r requirements-integration.txt
python -m examples.langgraph_release_experiment
python -m examples.langgraph_sqlite_restart
python -m examples.langgraph_http_integration
```

| 源码 | 观察内容 | 边界 |
|---|---|---|
| [发布图](./langgraph_release_experiment.py) | 缺少批准时不 dispatch；获批后只有 accepted；无 witness 时产生恢复路线 | 真实 LangGraph 图，测试观察和授权输入仍是合成数据 |
| [SQLite 重开](./langgraph_sqlite_restart.py) | 关闭并重开两个 store 后，图状态和 SACP 事件仍存在 | 持久化与对象重建实验，没有注入进程崩溃 |
| [Localhost HTTP 集成](./langgraph_http_integration.py) | 延迟到达的 accepted 与 healthy 产生匹配部署决定，并结束恢复路线 | 使用真实本地 HTTP；provider 状态模拟，没有生产部署 |

图里记录测试成功观察，不等于图实际执行了测试命令。验证 adapter 接线应运行[集成测试](../tests/test_langgraph_adapter.py)。

## 协议文档

结合 [ENVELOPE.md](../ENVELOPE.md) 与 [RECEIPT.md](../RECEIPT.md) 阅读。Python runtime demo 返回的 `DerivedReceipt`，与 `SACP/0.1` 交换 receipt 是不同对象。

| 主题 | 文件 | 阅读重点 |
|---|---|---|
| 最小交换 | [valid_handoff.yaml](./valid_handoff.yaml)、[valid_receipt.yaml](./valid_receipt.yaml)、[valid_block_receipt.yaml](./valid_block_receipt.yaml) | Handoff、完成 receipt 与阻断 receipt |
| 小型维护任务 | [micro_receipt_maintenance.yaml](./micro_receipt_maintenance.yaml) | 保留必需核心字段的精简 receipt |
| 缺少证据 | [dirty_missing_evidence.yaml](./dirty_missing_evidence.yaml) | 无支撑的公开声明及预期修正 |
| 重复与输入变化 | [dirty_duplicate_handoff.yaml](./dirty_duplicate_handoff.yaml)、[dirty_changed_source_rework.yaml](./dirty_changed_source_rework.yaml) | 同输入返回已有结果，输入变化需要 rework |
| 记忆与权限 | [dirty_memory_promotion.yaml](./dirty_memory_promotion.yaml)、[human_decision_override.yaml](./human_decision_override.yaml) | 记忆提升边界，以及人类决定覆盖原工作 |
| 工作延续 | [cross_model_handoff.yaml](./cross_model_handoff.yaml)、[solo_ai_company_handoff.yaml](./solo_ai_company_handoff.yaml) | 交接身份、作用域与 next-owner 纪律 |
| Receipt Chain | [receipt_chain_multi_agent_project.yaml](./receipt_chain_multi_agent_project.yaml)、[receipt_chain_research_publish.yaml](./receipt_chain_research_publish.yaml) | 跨交接保留的可选审计状态，参见 [profile](../SACP_RECEIPT_CHAIN.zh-CN.md) |
| 带上下文的审计示例 | [longju_public_safe_receipt.yaml](./longju_public_safe_receipt.yaml)、[socrates_focus_receipt.yaml](./socrates_focus_receipt.yaml) | Receipt 如何记录某次本地 trial 或反馈快照及其边界 |

校验全部公开示例，或某个文件：

```bash
python validator.py --examples --strict
python validator.py --strict examples/valid_receipt.yaml
python validator.py --strict examples/dirty_missing_evidence.yaml
```

`dirty_*.yaml` 是包含输入与预期结果的 case fixture。Strict PASS 表示按 validator 校验通过，不代表其中输入声明真实，也不代表运行时实际执行了 lease 或审批机制。示例 evidence ID 是文档引用，不是刚刚认证过的观察。

## 保存的报告与文本审计

[sacp_sample_output.json](./sacp_sample_output.json) 和 [sacp_sample_report.md](./sacp_sample_report.md) 是保存的项目诊断示例。其中的评分和叙述不代表当前 CI 结果、运行时 receipt 或 verifier 的实测准确率。

审计已有 Agent 回复，走 Doctor 的独立文本入口：

```bash
python -X utf8 agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md --lang zh
```

Doctor 使用本地启发式规则，不重跑原任务。它的输入样例位于 [agentops-doctor-skill/examples/](../agentops-doctor-skill/examples/)。

## 新增示例

说明输入、预期结果、依赖与示例不能证明什么。运行时行为应在 [tests/](../tests/) 下配对应正向或失败边界测试；协议变化遵循 [CONTRIBUTING.zh-CN.md](../CONTRIBUTING.zh-CN.md) 的兼容性与 dirty case 审查。同步更新两份示例导航，生成报告放在 tracked 文件之外。
