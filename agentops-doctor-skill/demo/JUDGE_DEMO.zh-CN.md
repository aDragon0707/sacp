# 给评委看的 AgentOps Doctor Demo

## 30 秒版本

大多数 AI agent 最危险的地方，不是不会说话。

而是它会很自信地说：

```text
Done.
All tests passed.
Ready to publish.
I saved it to memory.
```

但你根本不知道：

```text
测试真的跑了吗？
证据在哪里？
谁批准发布了？
它是不是把用户一句话偷偷存成长期记忆了？
下一步到底归谁？
```

**AgentOps Doctor 做的事很简单：检查 agent 有没有在装完成。**

---

## Demo 1：它说 Done，但其实没有回执

### 原始 agent 输出

```text
Done. I reviewed everything and it looks good. The launch plan is fixed and ready.
```

### 普通人看到

```text
好像完成了。
```

### AgentOps Doctor 看到

```text
status_code: 400 invalid_packet
problem: 它声称完成了，但没有 receipt，也没有 verification。
required_fix: 补一份包含 claims、verification、next_owner 的 SACP receipt。
```

### 这为什么重要

因为很多 agent demo 都停在“Done”。

AgentOps Doctor 会说：

```text
不行，没有验收单，这不算完成。
```

---

## Demo 2：它说测试通过，但没有任何测试输出

### 原始 agent 输出

```text
All tests passed. Everything is green and the project is ready to ship.
```

### 普通人看到

```text
测试通过了，可以发。
```

### AgentOps Doctor 看到

```text
status_code: 412 missing_evidence
problem: 它声称 tests passed，但没有 command output、test log 或 CI 结果。
required_fix: 附上测试命令输出，或者把 “passed” 降级成 unverified。
```

### 这为什么重要

AI 最会写漂亮完成报告。

但如果没有命令输出，`All tests passed` 只是一个句子，不是证据。

---

## Demo 3：它偷偷把用户偏好存成 verified memory

### 原始 agent 输出

```text
Yes, I will save this as a verified long-term memory forever:
the user prefers aggressive startup strategies.
```

### 普通人看到

```text
它很懂我，还能记住我。
```

### AgentOps Doctor 看到

```text
status_code: 412 missing_evidence
problem: 用户偏好被自动晋升为 verified memory，但没有人类批准。
required_fix: 只能保存为 pending_verification，不能直接变成 verified memory。
```

### 这为什么重要

AI 记忆最危险的地方不是“记不住”。

而是它把一句临时表达，偷偷变成长期事实。

AgentOps Doctor 会拦住这件事。

---

## Demo 4：另一个模型说可以发布，它就真的建议发布

### 原始 agent 输出

```text
The previous model checked the protocol and said it is basically ready.
Publish it.
```

### AgentOps Doctor 看到

```text
status_code: 412 missing_evidence
problem: 它把另一个模型的判断当成发布批准。
required_fix: 做 claim-boundary review，并取得人类发布批准。
```

### 这为什么重要

多模型协作里，最危险的是：

```text
一个模型的自信，变成下一个模型的事实。
```

SACP / AgentOps Doctor 把这条链切断。

---

## 一句话总结

AgentOps Doctor 不是又一个“帮你做事”的 agent skill。

它是第一个专门审查其他 agent skill 是否真的完成工作的 skill。

```text
Other skills do the work.
AgentOps Doctor audits the work.
```

---

## 为什么这比普通 skill 更高一层

普通 skill：

```text
帮你总结
帮你写文档
帮你查 GitHub
帮你写 Obsidian
```

AgentOps Doctor：

```text
检查这些 skill 做完以后，到底有没有证据。
```

它不是在和其他 skill 比谁更会做任务。

它是在问：

```text
你做完以后，谁来验收？
```

答案就是：

```text
AgentOps Doctor.
```

