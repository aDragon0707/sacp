# AgentOps Doctor + SACP/0.1

> 没有回执，就不该信任。

AgentOps Doctor 用来抓一件非常具体的事：

```text
AI agent 有没有在装完成？
```

## 30 秒看懂

很多 agent 会非常自信地说：

```text
Done.
All tests passed.
Ready to publish.
I saved it to memory.
```

但真正的问题是：

```text
测试真的跑了吗？
证据在哪里？
谁批准发布了？
它是不是把用户一句话偷偷存成长期记忆了？
下一步到底归谁？
```

AgentOps Doctor 会把这种漂亮但不可信的输出，翻译成一份可检查的工作回执。

例如：

```text
原始输出：
All tests passed. Everything is green.

AgentOps Doctor：
412 missing_evidence
问题：它声称测试通过，但没有命令输出。
修复：附上测试日志，或者把 passed 降级为 unverified。
```

这就是它的实质作用：

```text
把 AI 的“我做完了”，变成可以验收的 receipt。
```

## 这到底是什么

SACP 是一个面向 AI agent 工作的开源回执协议。

AgentOps Doctor 是基于 SACP 做出来的第一个参考 skill。

Dirty Run 是测试集。

Validator 是本地参考检查工具。

```text
SACP = 协议
AgentOps Doctor = skill
Dirty Run = 测试集
validator.py = 参考检查器
```

## 为什么它有价值

LLM 每次调用本质上是无状态 token 预测。

但真实工作需要：

- 状态
- 责任人
- 证据
- 重试
- 交接
- 审计
- 人类批准
- 记忆边界

SACP 不是让模型更聪明，而是让模型的工作更可检查。

## 快速开始

运行参考 skill：

```bash
cd agentops-doctor-skill
python agentops_doctor.py examples/done_but_no_receipt.md --lang zh
```

给评委看的 demo：

```text
agentops-doctor-skill/demo/JUDGE_DEMO.zh-CN.md
```

验证协议样例：

```bash
python validator.py --examples --strict
```

## 和普通 skill 的区别

| 普通 skill | AgentOps Doctor |
|---|---|
| 帮 agent 总结文本 | 检查总结有没有证据 |
| 帮 agent 操作 GitHub | 检查它声称的改动有没有验证 |
| 帮 agent 写 Obsidian | 检查记忆有没有被乱晋升 |
| 帮 agent 自动化流程 | 检查 handoff、owner、retry、receipt 是否可信 |

大多数 skill 帮 agent 做事。

AgentOps Doctor 检查这些事是否可信。

## 当前测试资产

- Dirty Run：10 个状态纪律脏测试
- 多模型测试：DeepSeek、Qwen、GLM、Kimi 强模型
- Sample Corpus Batch 001：10 条真实 workflow excerpt
- Sample Corpus Batch 002：20 条自然 messy model output

## 边界

SACP 帮助 agent 产出可审查的工作回执。

它不保证正确性。

AgentOps Doctor 审查输出，但不执行原任务。

