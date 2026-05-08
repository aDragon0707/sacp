# SACP 路线图

English version: [ROADMAP.md](./ROADMAP.md)

## v0.1-alpha：Text-First 协议包

状态：当前版本

范围：

- Envelope
- Receipt
- 状态码
- claim 类型
- support status
- Dirty Run cases
- AgentOps Doctor 参考 skill
- 本地 validator
- 示例 packet
- sample corpus receipts

非目标：

- 不做托管平台
- 不强制数据库
- 不做 HTTP endpoint
- 不自动晋升记忆
- 不做模型训练管线
- 不保证正确性

## v0.2：Schema 和更强校验

候选新增：

- Envelope 和 Receipt 的 JSON Schema
- 更严格的 CLI 校验
- 结构化 receipt completeness 报告
- 改进 Dirty Run runner
- 扩展 public-safe sample corpus

## v0.3：运行时适配器

候选适配：

- OpenClaw / Longju state ledger
- LangGraph checkpoint mapping
- MCP tool-call evidence mapping
- A2A task-message mapping
- 本地 Markdown vault adapter

## v0.4：传输绑定

可能的 HTTP binding：

```http
POST /sacp/handoffs/{handoff_id}/claim
POST /sacp/handoffs/{handoff_id}/attempts/{attempt_id}/complete
GET  /sacp/receipts/{receipt_id}
```

传输层不能改变协议语义。

## v0.5：一致性测试套件

候选新增：

- 公开 Dirty Run benchmark
- conformance profiles
- receipt completeness badge
- 主流 agent 框架兼容报告

## v1.0：稳定最小标准

只有真实采用后才冻结：

- envelope 必填字段
- receipt 必填字段
- method set
- claim taxonomy
- support status
- core status codes
- extension compatibility rules

不冻结：

- runtime
- UI
- storage
- model provider
- training method

