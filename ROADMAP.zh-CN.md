# SACP 路线图

[English](./ROADMAP.md) · [当前状态](./STATUS.md) · 更新于 2026-10-15

SACP/0.1 是当前交换契约。下面描述能力成熟度，不意味着每项 runtime 能力都要升级协议版本。

## 已有：协议与可执行参考基线

已有 text-first spec、validator、dirty case、Receipt Chain profile、本地 Doctor、示例和样本集。Python runtime 已包含 SQLite 事件账本、按 claim 类型检查的证据策略、独立授权/provider 状态、发布/部署/退款 gate、有界对账、mock 幂等、GitHub payload 和 LangGraph adapter，以及 localhost HTTP 实验。

CI 已运行跨平台 core 矩阵、显式安装依赖的 LangGraph 集成、严格协议校验，以及包含正向控制的确定性 harness。默认分支上的可信实现交叉核对 GitHub 执行事实和当前 PR 身份，再生成 receipt。合并仍由维护者手动发起。参见[架构](./docs/architecture.md)与[验证范围](./docs/verification-2026-10-15.md)。

## 下一步：真实 Agent 评测试点

[ADR-0001](./docs/adr/0001-real-agent-evaluation-with-pi.md)决定保留现有确定性引擎场景测试，以 Pi 为首个真实 Agent 试点。计划使用 Python 外层 runner 与 Pi JSON 子进程接口，固定并隔离环境，采集实际代码任务轨迹并独立验收交付补丁。目前尚无 adapter、选定的 provider/model、运行预算或真实评测结果。

先用小规模固定任务集，在同一批记录上比较 SACP 与预先定义的测试基线，报告漏检、误拦、不可判定和额外开销；注入故障与自然失败分别统计。模型调用不进入 required PR CI。分阶段验收与停止条件见 ADR。

## 下一步：可信度与独立验收

- 完成真实、受控的 fork PR 烟测；合成 fork API 测试不能代替它。
- 增强测试进程隔离，防范同进程恶意测试代码；source inventory 和执行检查是必要条件，但还不充分。
- 针对具体接入增加经过认证的 host/provider 采集和写入隔离，不直接扩张为通用身份平台。
- 在对象重开和 SQLite 并发之外，覆盖进程崩溃窗口和实际运行恢复。
- 收集经过独立审查的真实失败与合法成功案例，包括误拦；保留版本化证据并审查隐私。
- 若启用 merge queue，先定义并验证 merge-group 正式 receipt 身份。

## 候选：Schema 与互操作

[JSON Schema 计划](./JSON_SCHEMA_PLAN.zh-CN.md)仍是计划。更强校验、MCP/A2A 映射和公开传输绑定需要实际 dirty case、最小契约、兼容说明和参考示例。LangGraph 与 GitHub 参考 adapter 已存在，不应继续写成纯未来工作。OpenClaw/Longju 的文档映射不等于 runtime 接入。

Receipt Chain 保持为可选 namespaced profile。[协议设计参考](./PROTOCOL_DESIGN_REFERENCES.md)约束演进。Storage、UI、runtime 和 provider 选择不进入必需核心。

## 稳定标准：以证据为前提

只有真实采用和兼容性证据充分后，才冻结稳定的最小契约。必填字段保持少量，厂商细节放在 `extensions`。不承诺正确性、不自动晋升记忆，也不把调度、支付、tracing 或部署控制都纳入协议核心。
