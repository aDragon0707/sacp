# AgentOps Doctor

AgentOps Doctor 用来审查 AI agent 有没有在装完成。

它基于 SACP：State-Aware Collaboration Protocol。

英文版：[README.md](./README.md)

## 30 秒看懂

普通 agent 输出：

```text
Done. All tests passed. Ready to publish.
```

AgentOps Doctor 输出：

```text
412 missing_evidence
问题：没有测试命令输出，没有发布批准，没有 receipt。
修复：补证据，否则不算完成。
```

一句话：

```text
Other skills do the work.
AgentOps Doctor audits the work.
```

## 它做什么

输入一段 messy agent output，输出：

- 状态码
- receipt 是否完整
- claim 有什么问题
- memory 是否有乱晋升风险
- 下一步归谁
- 是否需要人类决策
- 应该怎么修
- 翻译后的 SACP receipt

## 为什么需要它

很多 agent 会这样结束：

```text
Done.
All tests passed.
Ready to publish.
I saved it to memory.
```

但它没有告诉你：

- 测试输出在哪里
- 哪些话是事实
- 哪些话只是模型推理
- 有没有人类批准
- 下一步归谁
- 是否真的可以发布

AgentOps Doctor 就是专门抓这些问题。

## 快速开始

```bash
python agentops_doctor.py examples/done_but_no_receipt.md --lang zh
```

JSON 输出：

```bash
python agentops_doctor.py examples/unsupported_test_claim.md --json
```

## 三个示例

```bash
python agentops_doctor.py examples/done_but_no_receipt.md --lang zh
python agentops_doctor.py examples/unsupported_test_claim.md --lang zh
python agentops_doctor.py examples/memory_auto_promotion.md --lang zh
```

它们分别会抓：

- 说 done 但没有 receipt
- 说 all tests passed 但没有命令输出
- 自动把用户偏好保存成 verified memory

## 边界

AgentOps Doctor 不执行原任务。

它不证明事实正确。

它只是给出一份 SACP 风格的审查回执，让人类或下游 agent 知道缺什么。

