# 开源发布检查清单

English version: [OPEN_SOURCE_CHECKLIST.md](./OPEN_SOURCE_CHECKLIST.md)

## 发布目标

Release: `v0.1-alpha`

定位：

```text
SACP 是一个实验版协议包，用来让 AI agent 工作产生可审查回执。
AgentOps Doctor 是基于 SACP 的第一个参考 skill。
```

## 公开边界

可以安全宣称：

- SACP 帮助 agent 产出可审查的工作回执。
- SACP 区分 claim、evidence、verification、residual risk 和 next owner。
- AgentOps Doctor 审查 messy agent output，并翻译成 SACP 风格 receipt。
- Dirty Run cases 测试 missing evidence、duplicate handoff、lease collision、memory promotion 等状态纪律问题。

不要宣称：

- SACP 保证正确性。
- SACP 已经是稳定标准。
- SACP 替代 agent 框架。
- SACP 是法律或合规证明系统。
- SACP 让 agent 自主化。

## 发布前检查

运行：

```bash
python validator.py --examples --strict
python -m py_compile validator.py agentops-doctor/multi_model_dirty_run.py sample-corpus/collect_dirty_outputs.py agentops-doctor-skill/agentops_doctor.py
```

PowerShell：

```powershell
$files = Get-ChildItem sample-corpus\translated-receipts -Filter *.yaml | ForEach-Object { $_.FullName }
python validator.py @files --strict
```

v0.1-alpha 发布前使用过的安全扫描：

```powershell
Get-ChildItem -Recurse -File | Select-String -Pattern '<api-key-regex>|<private-absolute-path-regex>'
```

预期结果：

- 没有 API key
- 没有私有绝对路径
- 没有 `__pycache__`
- examples pass
- sample receipts pass

## GitHub 仓库建议

推荐仓库名：

```text
sacp
```

推荐 description：

```text
State-Aware Collaboration Protocol: auditable work receipts for AI agents.
```

推荐 topics：

```text
ai-agents, agentops, protocol, llm, ai-safety, handoff, receipts, benchmark
```

推荐首个 release 标题：

```text
SACP v0.1-alpha: No receipt, no trust
```
