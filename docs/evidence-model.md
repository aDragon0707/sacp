# 证据模型与信任边界

四类输入在类型与语义上分开，最终由 Verifier 派生状态。**当前 store API 没有认证写入者**；类型分工不是已经强制实现的权限隔离。完整关系见[架构](./architecture.md)。

| 输入 | 记录什么 | 单独不能证明什么 |
|---|---|---|
| `Claim` | Agent 或业务组件声称发生了什么 | 声明真实、任务完成、已经获批 |
| `HostObservation` | 本地执行、CI 或产物数据 | 外部送达、部署健康、退款成功 |
| `ProviderObservation` | Provider 报告的事件、receipt ID 和 metadata | Provider 被认证、accepted 等于业务完成 |
| `AuthorityDecision` | 特定输入和作用域的授权决定 | 被授权动作已经成功 |

## 预期写入角色

```text
agent -> Claim
trusted host -> HostObservation
authenticated provider adapter -> ProviderObservation
human / trusted policy -> AuthorityDecision
Verifier -> DerivedReceipt
```

这是接入契约。具有 Python store 写权限的调用方可以构造任何一种 observation；摘要也不是签名或来源认证。需要在宿主、adapter 和存储访问层约束写入权限。Append-only API 保留历史，不意味着数据库防篡改。

## 当前证据策略

| Claim type | 实现检查 |
|---|---|
| `tests_passed` | 显式引用宿主 test_run 或 ci_check；执行上下文匹配，成功结果和 output digest 存在；指定 commit 时证据必须匹配 |
| `artifact_built` | 显式引用 artifact observation；名称、digest 和指定 commit 匹配 |
| `ready_to_publish` | 同时满足测试与 artifact 证据；发布 gate 另查授权 |
| 支持的生命周期意图 | `notification_sent`, `publish_action`, `ask_counterparty`, `refund_requested`, `deployed`；意图本身不证明成功，provider 状态独立派生 |
| 未知类型 | `unverified`，需新增有测试的策略后才能得到支持 |

引用仅指向同 action 内已有 event ID；host thread/run/checkpoint 也必须匹配。当前 runtime 只检查 digest 存在和关联，不通用地认证文件内容或命令输出。生产 collector 必须独立读取、计算并绑定实际产物。

Provider accepted 与终态按 provider+receipt ID 关联，再检查 revision 或 order/amount/currency。Authority 绑定 thread/run/checkpoint/input/scope/expiry；GitHub payload adapter 的 reviewer 名单来自可信构造参数，默认空名单不授权。Payload 自己声明的角色不能提升权限。

## 两种 receipt

`DerivedReceipt` 是 Python 投影，包含宿主、授权、外部和 overall 状态、证据引用以及恢复路线。它不是 SACP/0.1 wire receipt。

CI builder 另行生成合法 SACP/0.1 receipt：COMPLETE/200、BLOCK/412 或 FAIL/500。默认分支 collector 通过 GitHub API、Git objects、当前 head、job 结果与测试清单交叉核对 artifact。它不执行 PR 代码。测试和 application code 同进程内的恶意行为仍需人工审查或更强隔离。

协议 strict PASS 仅证明该文档满足 validator；CI COMPLETE 仅证明记录 SHA 的预检契约通过；provider terminal 是 provider 声称的结果；人工授权是另一种事实。四者不能互相替代。所有数量和外部烟测边界见[验证记录](./verification-2026-10-15.md)。
