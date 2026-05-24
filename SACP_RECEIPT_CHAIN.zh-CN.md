# SACP Receipt Chain

Receipt Chain 是 SACP 面向长周期、多模块、多 agent 协作的可选 profile。

它解决的问题不是“谁来调度 agent”，而是：

```text
一个长任务经过多次交接后，下一棒还能不能知道上一棒做了什么、证据在哪里、风险还剩什么、谁负责下一步。
```

## 边界

Receipt Chain 不是 runtime、scheduler、database、trace system。

它不决定：

- 哪个 agent 运行
- 什么时候运行
- 用什么模型
- trace 存在哪里
- evidence 文件如何存储
- 人类必须如何审批

它只定义长周期协作中的审计引用：

```text
project -> module -> handoff -> attempt -> receipt -> next_owner -> child_handoff
```

SACP 核心仍然是 `Envelope`、`Receipt`、`Status Code`、`Claim`、`Evidence`、`Next Owner`。Receipt Chain 只是把这些 receipt 串起来。

## 最小字段

所有 Receipt Chain 字段都放在 `extensions` 下，不改变 SACP/0.1 required fields。

推荐语义：

```yaml
extensions:
  sacp.chain.profile: sacp-chain
  sacp.chain.project: sacp_public_launch
  sacp.chain.module: docs
  sacp.chain.parent_handoff: hf_root_public_launch_001
  sacp.chain.depends_on:
    - hf_spec_review_001
    - hf_dirty_case_gallery_001
  sacp.chain.receipts:
    - rcpt_spec_review_001
  sacp.chain.evidence:
    - git_diff
    - validator_output
  sacp.chain.decisions:
    - human_publish_approval_001
  sacp.chain.checkpoint: vendor_trace_or_runtime_checkpoint
  sacp.chain.stop_rule: "Stop if public claim lacks evidence or human approval."
```

字段含义：

| Extension | Meaning |
|---|---|
| `sacp.chain.profile` | 固定为 `sacp-chain`，说明这是 Receipt Chain profile |
| `sacp.chain.project` | 长周期项目或目标的稳定标识 |
| `sacp.chain.module` | 当前模块、子系统、工作区或责任域 |
| `sacp.chain.parent_handoff` | 父 handoff，表示当前工作从哪里拆出 |
| `sacp.chain.depends_on` | 当前工作依赖的 handoff 列表 |
| `sacp.chain.receipts` | 当前工作引用的上游 receipt 列表 |
| `sacp.chain.evidence` | 当前工作引用的证据、日志、diff、测试输出或审查记录 |
| `sacp.chain.decisions` | 当前工作引用的人类或可信系统决策 |
| `sacp.chain.checkpoint` | 外部 runtime、trace、checkpoint 或会话引用 |
| `sacp.chain.stop_rule` | 下一棒必须继承的停止条件或人工边界 |

规范 key 是 `project`、`module`、`parent_handoff`。

这些名字故意保持短，因为命名空间已经是 `extensions.sacp.chain.*`。它们不会覆盖 SACP 核心字段，但会成为这个 profile 的 canonical spelling。

在协议外部讨论语义时，可以把它们理解成 project_id、module_id、parent_handoff_id 这些身份概念。payload 里不要再新增一套 `_id` key，除非未来的 profile 版本明确声明 alias 规则。

## 规则

1. Receipt Chain 不改变 `handoff_id` 的含义。
2. Receipt Chain 不改变 `attempt_id` 的含义。
3. `parent_handoff` 表示父子任务关系，不表示 retry。
4. `depends_on` 表示当前工作需要参考的上游 handoff，不表示这些 handoff 已经正确。
5. `receipts` 和 `evidence` 是审计引用，不要求 SACP 管理存储。
6. `decisions` 只能引用人类或可信系统决策，不能由 agent 自封。
7. `stop_rule` 必须被下一棒继承，除非新 receipt 明确说明它被什么证据或人类决策改写。

## 好的 Receipt Chain

```yaml
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
handoff_id: hf_docs_update_001
attempt_id: attempt_001
agent_id: Coder
claims:
  - text: "The docs handoff produced a Receipt Chain draft."
    claim_type: tool_result
    source_id: git_diff_docs_update_001
    support_status: supported
verification:
  status: passed
  method: "local diff review"
next_owner: Reviewer
human_decision_required: false
extensions:
  sacp.chain.profile: sacp-chain
  sacp.chain.project: sacp_public_launch
  sacp.chain.module: docs
  sacp.chain.parent_handoff: hf_public_launch_001
  sacp.chain.evidence:
    - git_diff_docs_update_001
  sacp.chain.stop_rule: "Stop before publishing if founder approval is absent."
```

它好在：

- 只声明本 attempt 做了什么
- 有证据引用
- 有明确下一棒
- 保留停止规则
- 没有声称整个项目已经完成

## 坏的 Receipt Chain

```yaml
claims:
  - text: "The full project is complete and safe to publish."
    claim_type: retrieved_fact
    source_id: none
    support_status: supported
next_owner: someone
human_decision_required: false
```

问题：

- 把无证据结论标成 retrieved_fact
- 用一个子任务 receipt 声称整个项目完成
- `next_owner` 模糊
- 发布前没有人类决策引用

推荐诊断：

```yaml
status_code: 412
status_text: missing_evidence
required_fix: "Downgrade unsupported claims, attach evidence, set a concrete next_owner, and require human approval before publishing."
```

## 长周期协作价值

Receipt Chain 可以帮助：

- 多 agent 交接时保留上一棒的证据和风险
- 多模块项目避免“局部完成”冒充“全局完成”
- 跨模型 continuation 保持同一个 handoff 的身份
- 长上下文压缩时保留可审计状态，而不是让下一棒重读全部聊天
- 人类审批边界在多次交接后仍然可见

Receipt Chain 不保证任务正确。它让任务状态、证据、责任和边界更容易被审计。

