# 社区传播说明

这个文件用来帮助你把 SACP 发给开发者、开源社区、agent 框架作者和同好。

English version: [COMMUNITY_OUTREACH.md](./COMMUNITY_OUTREACH.md)

## 应该找谁

先找已经有痛感的人：

- agent 框架开发者
- LangGraph / CrewAI / MCP / A2A 用户
- AI coding tool 用户
- 正在用 AI agent 的开源维护者
- 做 hallucination / eval / benchmark 的人
- 正在做 agent skill 的黑客松参赛者

不要一上来讲“我们定义了一个新协议标准”。先讲具体失败：

```text
Agent 说：All tests passed.
证据在哪里？
```

## 短帖模板

```text
我开源了 SACP/0.1 + AgentOps Doctor。

它用来审查 messy AI agent output：
- 它真的完成了吗？
- 证据在哪里？
- 下一步归谁？
- 有没有越过记忆或人类批准边界？

快速运行：
git clone https://github.com/aDragon0707/sacp.git
cd sacp
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md --lang zh

No receipt, no trust.
没有回执，就不该信任。
```

## 采用案例帖模板

```text
SACP 现在有一份公开安全采用案例了。

Longju 是一个本地单 Agent operator，它用 SACP 做 runtime guard：
PreTask -> ContextCheck -> PreExternalAction -> PostTask

公开安全 trial 覆盖：
- 假完成 -> 412 missing_evidence
- prompt injection -> 需要人类批准
- skill distillation -> 只生成 candidate
- duplicate handoff -> 204 no_action_needed

案例：
https://github.com/aDragon0707/sacp/blob/main/ADOPTION_CASE_LONGJU.zh-CN.md
```

## 征集反馈模板

```text
我在征集 messy agent output。

如果你的 agent 说过 done / tests passed / saved to memory / ready to publish，
但它没有给足证据，可以把脱敏后的例子发到这里：
https://github.com/aDragon0707/sacp/issues/new/choose

我会把有价值的失败模式整理成 Dirty Run 测试。
```

## 要不要 @ OpenAI 或技术大神

可以，但要克制。不要像广告一样群发 @，而是带着明确问题去问。

好的 @ 方式：

```text
我们在做一个 agent completion receipt layer。
如果要把它接到 tool calls / checkpoints / memory promotion 里，
你觉得哪些 evidence 字段是必须的？
```

或者：

```text
我们做了一个小工具，专门审查 agent 的 “done / tests passed / saved to memory” 声明。
想找真实 messy output 做 benchmark。欢迎拍砖。
```

不好的 @ 方式：

```text
我们做了伟大的新协议，请大佬看看。
```

## 可以发到哪里

- GitHub：相关项目 issue / discussion
- Hacker News：Show HN
- Reddit：r/LocalLLaMA、r/AI_Agents、r/LangChain、r/MachineLearning
- X / Twitter：agent builder、eval researcher、开源维护者
- Hugging Face forums
- LangChain / LangGraph 社区
- MCP / A2A 开发者社区
- 中文社区：V2EX、掘金、知乎、即刻、开源中国、AI 开发者微信群

## 最好的第一句话

```text
给我一段你见过的 messy agent output。
我帮你翻译成 SACP receipt，如果它暴露了有价值的失败模式，就加入 Dirty Run benchmark。
```

这比“请大家支持我的协议”更容易得到真实反馈。
