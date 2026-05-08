# 参与贡献 SACP

SACP 目前是实验版本。我们的目标不是把它快速做成庞大标准，而是先保持核心小、可读、可用。

English version: [CONTRIBUTING.md](./CONTRIBUTING.md)

## 我们欢迎什么

好的贡献通常是下面几类：

- 一个真实或合成的脏场景
- 一个更清楚的例子
- validator 改进
- AgentOps Doctor 诊断改进
- 某个 agent 框架的兼容说明
- 让协议更容易理解的文档

## 修改规则

不要因为某个字段、方法、状态码“听起来有用”，就加入核心协议。

新增核心语义需要：

1. 一个能证明需求的脏场景。
2. 一个现有方案里尴尬或不安全的 workaround。
3. 一个最小新增方案。
4. 向后兼容说明。
5. 至少一个参考示例。

## 核心设计规则

- v0.1 保持 text-first。
- 优先使用 Markdown 和 YAML 示例。
- 必填字段要少。
- 厂商元数据放进 `extensions`。
- 未知扩展不应该破坏合法 packet。
- 不要宣称 SACP 保证正确性。
- 不要让 memory 或 skill 在没有人类批准时自动晋升。

## 安全和隐私

不要提交：

- API key
- credentials
- 私有本地路径
- 私有客户名或项目名
- 原始私有日志
- 带私密内容的截图
- 复制来的专有输出

尽量使用合成示例。

## 开发检查

运行：

```bash
python validator.py --examples --strict
python -m py_compile validator.py agentops-doctor/multi_model_dirty_run.py sample-corpus/collect_dirty_outputs.py agentops-doctor-skill/agentops_doctor.py
```

PowerShell 下检查 sample corpus receipts：

```powershell
$files = Get-ChildItem sample-corpus\translated-receipts -Filter *.yaml | ForEach-Object { $_.FullName }
python validator.py @files --strict
```

## PR 检查清单

- [ ] 修改保持核心协议足够小。
- [ ] 新协议语义包含脏场景。
- [ ] 示例能通过 validator。
- [ ] 没有 secret 或私有路径。
- [ ] 对外 claim 边界清楚，没有过度承诺。
- [ ] 用户可见文本变更时，中英文文档都已更新。

