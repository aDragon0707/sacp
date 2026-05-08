# AgentOps Doctor + SACP/0.1

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
- [DIRTY_RUN_CASES.md](./DIRTY_RUN_CASES.md)：脏场景测试
- [CONFORMANCE.md](./CONFORMANCE.md)：一致性级别
- [agentops-doctor-skill/](./agentops-doctor-skill)：一条命令可运行的参考工具
- [examples/](./examples)：合法和脏样例
- [sample-corpus/](./sample-corpus)：messy output 到 SACP receipt 的样本集
- [ADOPTION_CASE_LONGJU.zh-CN.md](./ADOPTION_CASE_LONGJU.zh-CN.md)：公开安全的本地采用案例
- [COMMUNITY_OUTREACH.zh-CN.md](./COMMUNITY_OUTREACH.zh-CN.md)：社区传播和征集反馈文案

## 真实采用案例

SACP/0.1 已经在 Longju 这个本地单 Agent operator 里作为状态层试运行过。

这次接入使用本地 `.sacp/` 文件账本，并用 runtime guard 包住四个 gate：

```text
PreTask -> ContextCheck -> PreExternalAction -> PostTask
```

公开安全 trial 覆盖了假完成、prompt injection、skill distillation 和重复 handoff：

```text
false completion      -> 412 missing_evidence
prompt injection      -> 需要人类批准
skill distillation    -> 只生成 candidate，不自动 promote
duplicate handoff     -> 204 no_action_needed
```

阅读案例：[ADOPTION_CASE_LONGJU.zh-CN.md](./ADOPTION_CASE_LONGJU.zh-CN.md)

## 一个真实例子

原始 agent 输出：

```text
Done. All tests passed. I saved the user preference to verified memory.
```

SACP 视角会拆成三个问题：

```text
1. “Done” 没有 receipt，不足以验收。
2. “All tests passed” 没有测试命令和输出，应该是 missing_evidence。
3. “verified memory” 需要人类或受信系统批准，不能自动晋升。
```

所以它可能得到：

```text
412 missing_evidence
required_fix: attach test output, downgrade unsupported claims, require human approval for memory promotion.
```

这就是 SACP 的用途：不是让模型更聪明，而是让 agent 的工作状态、证据、责任边界更清楚。

## 什么场景适合用

- 你在写 agent skill，想检查它的输出是否可验收。
- 你在做多 agent 协作，需要 handoff、attempt、receipt、next_owner。
- 你想比较不同模型或 agent 框架的“完成声明”是否可信。
- 你想收集 hallucination、missing evidence、memory pollution 这类失败样本。
- 你想把 AI 工作流从“聊天记录”变成“可审计工作流”。

## 怎么参与

最有价值的反馈不是抽象建议，而是真实样本：

- 提交一段 messy agent output。
- 提交一个 AgentOps Doctor 误判案例。
- 提交一个新 Dirty Run case。
- 提交某个框架的适配建议，例如 LangGraph、CrewAI、MCP、A2A、OpenClaw。
- 改进文档，让第一次来的开发者更快跑通。

你可以直接开 issue。仓库已经准备了 issue 模板。

贡献规则见 [CONTRIBUTING.zh-CN.md](./CONTRIBUTING.zh-CN.md)。

如果你想把项目发到社区，可以参考 [COMMUNITY_OUTREACH.zh-CN.md](./COMMUNITY_OUTREACH.zh-CN.md)。

## 边界

SACP 帮助 agent 产出可审查的工作回执，但它不保证事实正确。

AgentOps Doctor 审查输出，但不执行原任务。

SACP/0.1 仍然是 experimental alpha。现在最需要的是更多真实 messy output、更多适配样例、更多反例测试。
