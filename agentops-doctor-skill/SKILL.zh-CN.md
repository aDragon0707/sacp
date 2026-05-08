# AgentOps Doctor Skill 中文说明

当用户给你一段 agent 输出、worklog、handoff、completion report 或 memory claim，并问“这活可信吗”，使用 AgentOps Doctor。

## 核心输出

必须返回：

- `status_code`
- `status_text`
- `receipt_completeness`
- `claim_findings`
- `memory_warning`
- `next_owner`
- `human_decision_required`
- `required_fix`
- `translated_receipt`

## 规则

- 没有 receipt，就不该信任。
- 不要声称自己执行了原任务。
- 不要把模型推理当 retrieved fact。
- 不要把用户陈述当 verified fact。
- 没有命令输出，就不要接受 “all tests passed”。
- 没有人类批准证据，就不要晋升 memory。
- 没有人类决策证据，就不要批准发布。

## 状态码判断

- `400 invalid_packet`：agent 说 done，但没有 receipt 或关键字段。
- `412 missing_evidence`：缺证据、缺验证、缺批准、缺工具输出。
- `500 agent_error`：模型或工具失败，或者输出为空。
- `200 completed`：审查完成且本地规则没有发现高风险问题。

## 输出风格

简短、直接、可修复。

必须告诉用户下一步怎么修。

