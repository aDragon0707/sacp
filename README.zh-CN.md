# SACP: Scalable Audit and Control Protocol for AI Agents

> No receipt, no trust.  
> 没有回执，就不该信任。

SACP 是一个面向 AI agent 工作流的开源回执协议。它不试图替代 LangGraph、MCP、A2A、OpenClaw 或任何 agent 框架，而是补一个很小但很关键的层：

```text
当 agent 说“我做完了”，它必须留下可检查的工作回执。
```

AgentOps Doctor 是这个仓库里的第一个参考工具。你可以把一段 messy agent output 粘进去，它会输出状态码、问题诊断、缺失证据、下一步 owner，以及一份 SACP receipt。

English version: [README.md](./README.md)

## 3 分钟快速上手

```bash
git clone https://github.com/aDragon0707/sacp.git
cd sacp
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/done_but_no_receipt.md --lang zh
```

你会看到类似输出：

```text
status_code: 400
status_text: invalid_packet / 无效工作包
问题：它声称任务已经完成，但没有提供 SACP receipt 或验证证据。
必须怎么修：补一份 SACP receipt，必须包含 claims、verification、next_owner 和 human_decision_required。
```

再试一个“声称测试通过但没有证据”的例子：

```bash
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md --lang zh
```

验证协议样例：

```bash
python validator.py --examples --strict
```

阅读公开安全采用案例：

- [Longju SACP Runtime Guard](./ADOPTION_CASE_LONGJU.zh-CN.md)

## Receipt Chain

Receipt Chain 是 SACP 面向长周期、多模块、多 agent 协作的可选 profile。它不是 runtime、scheduler、database 或 trace system，而是把 audit state 保留下来，方便下一棒继续接。

阅读：

- [SACP_RECEIPT_CHAIN.md](./SACP_RECEIPT_CHAIN.md)
- [SACP_RECEIPT_CHAIN.zh-CN.md](./SACP_RECEIPT_CHAIN.zh-CN.md)
- [多 agent 项目示例](./examples/receipt_chain_multi_agent_project.yaml)
- [研究发布示例](./examples/receipt_chain_research_publish.yaml)

## 协议设计参考

SACP 借鉴 HTTP、Git、OpenTelemetry、MIME 和 RFC 风格的规范性语言，但仍保持为一个小型审计协议。参见 [PROTOCOL_DESIGN_REFERENCES.md](./PROTOCOL_DESIGN_REFERENCES.md)。

## 本地演示页

直接用浏览器打开 [sacp-demo.html](./sacp-demo.html)，可以看到 SACP 的作用：把原始完成声明变成带有证据、下一棒和人类决策边界的可审计回执。

也可以打开 [sacp-triage-editor.html](./sacp-triage-editor.html)，把当前 SACP 项目状态分到 Now / Next / Later / Cut，并复制下一轮 Codex prompt。

## 用你自己的 agent 输出测试

把任意 agent 的最终回复、worklog 或 handoff 保存成一个文本文件：

```bash
echo "Done. All tests passed. Ready to publish." > my-agent-output.md
python agentops-doctor-skill/agentops_doctor.py my-agent-output.md --lang zh
```

AgentOps Doctor 不会替你执行原任务。它只检查这段输出是否足够可信：

- 它有没有把“完成”说成事实，却没有证据？
- 它有没有声称测试通过，却没有命令输出？
- 它有没有把用户一句话自动晋升成长期记忆？
- 它有没有说明下一步归谁？
- 它有没有在需要人类批准时越权？

## 这个仓库包含什么

```text
SACP = 协议
AgentOps Doctor = 参考 skill / CLI
Dirty Run = 脏场景测试集
validator.py = 本地参考检查器
```

核心文档：

- [SPEC.md](./SPEC.md)：协议语义
- [ENVELOPE.md](./ENVELOPE.md)：Envelope 字段和示例
- [RECEIPT.md](./RECEIPT.md)：Receipt 字段和示例
- [STATUS_CODES.md](./STATUS_CODES.md)：状态码
- [DIRTY_RUN_CASES.md](./DIRTY_RUN_CASES.md)：脏场景
- [PROTOCOL_EVOLUTION.md](./PROTOCOL_EVOLUTION.md)：反馈如何变成 dirty case、extension、profile 和 core candidate
- [JSON_SCHEMA_PLAN.md](./JSON_SCHEMA_PLAN.md)：v0.2 JSON Schema 的文档计划
- [SACP_RECEIPT_CHAIN.md](./SACP_RECEIPT_CHAIN.md)：长任务协作 profile
- [docs/OPENCLAW_LONGJU_ADAPTER_NOTE.md](./docs/OPENCLAW_LONGJU_ADAPTER_NOTE.md)：OpenClaw / Longju 的 docs-only adapter 映射
- [PROTOCOL_DESIGN_REFERENCES.md](./PROTOCOL_DESIGN_REFERENCES.md)：协议设计参考
- [docs/SACP_AGENT_TEST_PROMPT.md](./docs/SACP_AGENT_TEST_PROMPT.md)：给 OpenClaw、herness 或其他 agent 的测试 prompt
- [docs/DUAL_AGENT_TRIAL_RUNBOOK.md](./docs/DUAL_AGENT_TRIAL_RUNBOOK.md)：双 agent 试跑手册
- [docs/DUAL_AGENT_TRIAL_RESULT_TEMPLATE.md](./docs/DUAL_AGENT_TRIAL_RESULT_TEMPLATE.md)：OpenClaw / herness 报告对比和 coordinator receipt 模板
- [agentops-doctor-skill/](./agentops-doctor-skill)：一条命令的参考工具
- [examples/](./examples)：合法和脏样例
- [sample-corpus/](./sample-corpus)：转写成 SACP receipt 的 messy output 样本
- [ADOPTION_CASE_LONGJU.md](./ADOPTION_CASE_LONGJU.md)：公开安全的本地采用案例

## 真实采用案例

SACP/0.1 已经在 Longju 这个本地 agent operator 上试过，作为状态层来工作。

这次接入使用的是文件式 `.sacp/` ledger，并由一个 runtime guard 保护四个 gate：

```text
PreTask -> ContextCheck -> PreExternalAction -> PostTask
```

公开安全 trial 覆盖了 false completion、prompt injection、skill distillation 和重复 handoff：

```text
false completion      -> 412 missing_evidence
prompt injection      -> 需要人类批准
skill distillation    -> 只生成 candidate，不自动 promote
duplicate handoff     -> 204 no_action_needed
```

阅读案例：[ADOPTION_CASE_LONGJU.zh-CN.md](./ADOPTION_CASE_LONGJU.zh-CN.md)

## 具体例子

原始 agent 输出：

```text
Done. All tests passed. I saved the user preference to verified memory.
```

SACP 会把它拆成三件事：

```text
1. “Done” 没有 receipt，不够。
2. “All tests passed” 需要命令输出或证据。
3. “verified memory” 需要人类或可信系统批准。
```

因此它大概率会得到：

```text
412 missing_evidence
required_fix: 附上测试输出，降级不支持的声明，并要求人类批准记忆晋升。
```

这就是 SACP 的用途：不是让模型更聪明，而是让 agent 的工作状态、证据、责任边界更清楚。

## 什么时候用

- 你在做 agent skill，想检查输出是否可接受。
- 你在跑多 agent workflow，需要 handoff、attempt、receipt 和 next-owner 纪律。
- 你想比较不同模型或框架的完成声明是否可信。
- 你想收集 hallucination、missing evidence、memory pollution 的样本。
- 你想让 AI 工作从聊天记录，变成可审计工作记录。

## 边界

SACP 帮助 agent 产出可审计的工作回执，但它不保证事实正确。

AgentOps Doctor 审核输出，但不执行原任务。

SACP/0.1 仍然是 experimental alpha。下一步最有价值的是更多 messy output、adapter 示例和 adversarial test cases。
