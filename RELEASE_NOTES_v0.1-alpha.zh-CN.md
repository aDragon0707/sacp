# SACP v0.1-alpha 发布说明

发布日期: 2026-05-08

仓库里现在还有一条最新的文档型演进说明，用来收紧 Receipt Chain 资料和 changed-source 重新工作规则。请看 [CHANGELOG.md](./CHANGELOG.md)。

English version: [RELEASE_NOTES_v0.1-alpha.md](./RELEASE_NOTES_v0.1-alpha.md)

## 摘要

SACP v0.1-alpha 是第一个公开实验版协议包，用来让 AI agent 工作产生可审查回执。

本版本包含：

- SACP/0.1 协议草案
- Envelope 和 Receipt 规范
- v0.1 状态码
- Dirty Run cases
- AgentOps Doctor 参考 skill
- 本地 validator
- 合法和脏 YAML 示例
- sample corpus receipts
- OpenClaw / Longju 接入蓝图

## 适合做什么

你可以用这个版本来：

- 理解 SACP receipt 模型
- 审核 messy agent output
- 把 worklog 翻译成 SACP receipt
- 测试 agent 的脏行为
- 给 agent 框架做集成原型

## 不适合做什么

这个版本不是：

- 稳定标准
- 生产级 runtime
- 合规证明
- 托管服务
- agent 框架替代品
- 对底层工作正确性的保证

## 快速测试

```bash
python validator.py --examples --strict
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/done_but_no_receipt.md
```

预期行为：

- examples 通过校验
- AgentOps Doctor 返回状态码、发现、required fix 和 translated receipt

## 发布边界

核心口号：

```text
No receipt, no trust.
```

更准确的边界：

```text
SACP 帮助 agent 产出可审查的工作回执。
它不保证正确性。
```
