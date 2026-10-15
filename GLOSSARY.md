# SACP evaluation vocabulary

本页区分 SACP 的验证对象与评测角色。实现选择与执行边界见 [ADR-0001](./docs/adr/0001-real-agent-evaluation-with-pi.md)。

## Language

**场景回归测试（Scenario regression harness）**：以明确构造的声明和证据为输入，检查 SACP 判定是否符合预期的测试集合。
_Avoid_: 真实 Agent 评测、Agent 能力 benchmark

**Agent 运行框架（Agent harness）**：承载模型调用、工具执行和会话生命周期的运行系统；在评测中是被驱动和观察的对象。
_Avoid_: 评测器、独立验收器

**真实 Agent 评测（Agent evaluation harness）**：围绕真实 Agent 执行任务，采集记录、组织独立验收并比较判定结果的评测系统。
_Avoid_: 仅凭模拟事件得到的真实准确率

**独立任务验收（Independent task acceptance）**：依据预先确定的任务条件，对实际交付进行的检查；不以 Agent 自述或 SACP 的判定作为正确性标准。
_Avoid_: Agent 自证、以被测规则作为标准答案

**任务完成（Task completion）**：实际交付满足该任务的验收条件。
_Avoid_: 进程正常退出、会话结束、测试命令返回成功

**完成声明（Completion claim）**：Agent 对任务或步骤已经完成的陈述，其支持程度须与对应证据分别判断。
_Avoid_: 完成证明

**预检通过（Preflight pass）**：记录输入满足指定证据与授权契约，允许调用方进入下一步。
_Avoid_: 任务必然正确、外部动作已成功、自动获准发布
