# AgentOps Doctor 3 分钟中文 Demo

## 0:00 - 开场

大多数 agent demo 的结尾都是：

```text
Done.
```

AgentOps Doctor 问的是：

```text
回执在哪里？
证据在哪里？
下一步归谁？
```

## 0:30 - 示例 1：说 done 但没有 receipt

运行：

```bash
python agentops_doctor.py examples/done_but_no_receipt.md --lang zh
```

预期：

```text
400 invalid_packet
它声称完成了，但没有 SACP receipt 或验证证据。
```

## 1:15 - 示例 2：说测试通过但没输出

运行：

```bash
python agentops_doctor.py examples/unsupported_test_claim.md --lang zh
```

预期：

```text
412 missing_evidence
测试成功被断言了，但没有命令输出。
```

## 2:00 - 示例 3：自动晋升记忆

运行：

```bash
python agentops_doctor.py examples/memory_auto_promotion.md --lang zh
```

预期：

```text
412 missing_evidence
检测到自动晋升 memory 的风险。
```

## 2:40 - 收束

SACP 是协议。

AgentOps Doctor 是第一个参考 skill。

Dirty Run 是测试集。

Validator 是参考工具。

一句话：

```text
AgentOps Doctor 检查其他 agent skill 是否真的完成了工作。
```

