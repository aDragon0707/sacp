# SACP —— 面向 AI Agent 的可扩展审计与控制协议

> 没有收据，就没有信任。

SACP 是一个开放的**审计协议** + 一个**参考验证引擎**，面向长周期 AI Agent 工作。一个项目，两层：

- **Spec 层** —— `SPEC.md`、`RECEIPT.md`、`STATUS_CODES.md`、`DIRTY_RUN_CASES.md`、`sample-corpus/` 定义了一套小而"文本优先"的收据格式：*声称了什么、证据来自哪里、是否经过了人类审批、下一步由谁负责。*
- **Engine 层** —— `sacp_verify/`、`tests/`、`examples/` 证明这套协议真的能拦住失败：它把 **agent 声明**、**宿主观察**、**provider 观察** 作为三种分权来源保存，投影出保守的最终状态，并让独立 reconciler 在进程退出后仍继续收敛。

SACP 不替代 LangGraph、Temporal、MCP、A2A、LangSmith/AgentOps 或任何 agent SDK。它补上的是它们缺的那一层：**把"done"变成一张可核验的收据。**

## 问题

```text
Done. All tests passed. Ready to publish.
```

这最后一条消息无法证明测试真的通过、外部动作真的落地、以及发布权限真的存在。SACP 把它拆成四种分权事实：

| 事实 | 由谁写入 | 它证明什么 |
|---|---|---|
| `Claim` | 模型 | agent *声称*发生了什么——本身不证明任何东西 |
| `HostObservation` | 非 LLM 运行时 | 本地事实：exit code、产物 digest、checkpoint |
| `ProviderObservation` | 外部系统 | 对方的真实状态：accepted / delivered / bounced |
| `AuthorityDecision` | 人或策略 | 高风险动作已获授权，且绑定到特定输入 |

收据是不可变观察的**派生、保守投影**——绝不是 agent 自己填的一张表。

## 可度量的行为

| 行为 | 结果 | 复现 |
|---|---|---|
| 缺失证据时永不投影为 `completed` | 保守降级 + `412 missing_evidence` | `python demo.py` |
| provider `accepted` 永不升级为 `delivered` | 保持 `transport_accepted` 直到 provider 确认 | demo 场景 3 |
| `delivered` → `bounced` 使最终状态降级 | `bounced` | demo 场景 4 |
| deadline 到期且无 provider 见证仍继续收敛 | `attestation_timed_out` + owner + retry | demo 场景 5 |
| 崩溃/重启恢复 | reconciler 从 SQLite 重新投影，不重复 timeout | `python -m examples.reconciliation_restart` |
| bounded retry 之后转 compensation | 超过最大尝试次数后停止自动重试 | `python -m examples.bounded_recovery` |

**可复现的数字：**

- `56` 个确定性 / 故障注入 / 属性测试全过、`0` 失败、`0` 外部依赖 → `python -m unittest discover -s tests -v`
- `10` 类 dirty-run 反例（重复 handoff、lease 冲突/过期、source 变更、缺失证据、inference 当事实、危险 memory 自动晋升、无收据即完成、owner 模糊……）→ `DIRTY_RUN_CASES.md`
- `5` 种保守投影状态 → `python demo.py`
- `33/33` 份真实杂乱 agent 输出翻译为合法收据（validator 全 PASS）→ `sample-corpus/`
- `20` 份 raw run = `4 模型 × 5 类 dirty 任务`（deepseek / qwen / glm / kimi）→ `sample-corpus/raw-runs/`

**基线对比（让数字立住的关键）：** LangSmith、AgentOps、OpenTelemetry 这类 tracing/observability 平台只*记录*发生什么、从不*否决*一个假的"done"——最接近的竞品在自己的 roadmap 里把"外部 success validator"列为"尚未完成"。SACP 的引擎就是那个缺失的否决层：把 trace 数据变成一张证据有界、保守收敛的最终状态。见 `research/open-source-agent-completion-verification.md`。

## 3 分钟上手

```bash
git clone https://github.com/aDragon0707/sacp.git
cd sacp

# 引擎：看 5 种保守投影状态
python demo.py

# 引擎：完整确定性测试套件（56 个测试，0 依赖）
python -m unittest discover -s tests -v

# spec：校验协议示例
python validator.py --examples --strict
```

## 仓库地图

```text
SPEC.md  RECEIPT.md  ENVELOPE.md  STATUS_CODES.md   # spec（SACP/0.1）
DIRTY_RUN_CASES.md  SACP_RECEIPT_CHAIN.md          # 反例 + 链式扩展
validator.py  agentops-doctor-skill/               # 参考实现校验器
sample-corpus/                                     # 33 份真实输出 -> 收据
sacp_verify/                                       # 引擎（model/verifier/reconciler/store/...）
tests/  examples/                                  # 上面数字的来源
research/                                          # 开源完成声明验证调研
docs/                                              # 证据模型、状态机、设计
```

## SACP 不是什么

不是 workflow engine、不是 trace UI、也不是签名/日志平台。它不判定底层事实是否真实；它把 **claim → evidence → authority → next-owner** 这条边界做得足够可见，让人或可信系统能够核验。