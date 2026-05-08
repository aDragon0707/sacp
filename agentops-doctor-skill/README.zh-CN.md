# AgentOps Doctor

AgentOps Doctor 是一个本地 CLI，用来审查 AI agent 的最终输出是否足够可信。

它基于 SACP：State-Aware Collaboration Protocol。

英文版：[README.md](./README.md)

## 快速运行

从仓库根目录执行：

```bash
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/done_but_no_receipt.md --lang zh
```

或者进入本目录：

```bash
cd agentops-doctor-skill
python agentops_doctor.py examples/done_but_no_receipt.md --lang zh
```

JSON 输出：

```bash
python agentops_doctor.py examples/unsupported_test_claim.md --json
```

## 用自己的输出测试

准备一个文件，例如 `my-agent-output.md`：

```text
Done. All tests passed. Ready to publish.
```

运行：

```bash
python agentops_doctor.py my-agent-output.md --lang zh
```

你会得到：

- `status_code`
- `status_text`
- `receipt_completeness`
- `claim_findings`
- `memory_warning`
- `next_owner`
- `human_decision_required`
- `required_fix`
- `translated_receipt`

## 三个内置示例

```bash
python agentops_doctor.py examples/done_but_no_receipt.md --lang zh
python agentops_doctor.py examples/unsupported_test_claim.md --lang zh
python agentops_doctor.py examples/memory_auto_promotion.md --lang zh
```

它们分别会抓：

- 说 done 但没有 receipt
- 说 all tests passed 但没有命令输出
- 自动把用户偏好保存成 verified memory

## 什么时候有用

当你看到 agent 这样说：

```text
Done.
All tests passed.
I updated the repo.
I saved it to memory.
Ready to publish.
```

你可以先用 AgentOps Doctor 过一遍。它会把这些话拆成 claims，并检查有没有证据、有没有越权、有没有下一步 owner。

## 边界

AgentOps Doctor 不执行原任务。

它不证明事实正确。

它只产出一份 SACP 风格的审查回执，让人类或下游 agent 知道还缺什么。
