# SACP v0.2 JSON Schema 计划

English version: [JSON_SCHEMA_PLAN.md](./JSON_SCHEMA_PLAN.md)

## 状态

仅文档计划。

这份文档不增加 enforcement，不增加运行时行为，也不增加新的必填字段。

## 为什么要写这个

SACP 已经有足够多的真实样例，可以开始规划 schema，但还没有足够压力去过早冻结或加厚协议。

schema 工作的价值在于：

- 给编辑器和工具更好的反馈
- 让实现者更清楚 packet 的形状
- 复用未来的校验草案
- 方便后续 adapter 映射

它不应该：

- 扩大核心协议
- 加 runtime 或 scheduler
- 取代 validator
- 声称正确性
- 在 profile 字段名稳定前引入新的必填字段

## 范围

先从最小有用集合开始：

1. envelope schema
2. receipt schema
3. extension 形状规则
4. dirty-case 专用样例
5. validator 输出的 report 形状

第一版应尽量贴近现有 v0.1 packet 结构，并把 extension 视为可选。

## 边界

schema 应该表达：

- 必填核心字段
- 已知取值范围
- 嵌套对象形状
- extension 归属规则
- 明显无效的 packet 形态

schema 不应该表达：

- agent 执行语义
- 外部证据真伪
- runtime lease
- 调度策略
- 人类判断
- 完成保证

如果某条规则依赖 workflow 行为或信任策略，它应该先留在文档、示例或 validator 逻辑里，而不是直接写进 schema。

## 工作顺序

1. 先确认核心文档和 profile 里的字段名已经稳定到足以出 draft schema。
2. 再给 envelope 和 receipt 写 JSON Schema 草案。
3. profile 字段继续留在 `extensions.*` 下，除非未来 profile 另有说明。
4. 先让文档和 dirty case 对齐，再补 schema 示例。
5. schema 作为支持性工件，不作为协议扩张。

## 可能产物

- `schema/envelope.schema.json`
- `schema/receipt.schema.json`
- `schema/extensions.schema.json`
- 嵌入文档中的 schema 示例
- roadmap 或 validator 文档里的简短 schema 说明

这些文件现在还没创建。此处只定义路线。

## 验收

如果满足以下条件，这个计划就成立：

- 保持 SACP core 小
- 避免过早硬化
- 对工具作者有帮助，但不强迫新的运行时假设
- 与 dirty-case-first 的演化方式一致
