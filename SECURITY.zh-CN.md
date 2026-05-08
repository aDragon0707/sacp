# 安全政策

English version: [SECURITY.md](./SECURITY.md)

## 支持版本

SACP 当前是实验版本。

| Version | Supported |
|---|---|
| v0.1-alpha | 是 |

## 报告安全问题

如果 GitHub security advisories 已启用，请提交 private report；或者通过 GitHub 联系仓库所有者。

不要在公开 issue 中包含：

- API key
- access token
- credentials
- 私有本地路径
- 私有日志
- 私有客户或项目数据

## 项目边界

SACP 是协议包和参考检查器。它不执行原始 agent 任务，不保证正确性，也不是法律或合规认证系统。

## 安全示例原则

尽量使用合成示例。如果使用真实 workflow sample，必须移除私有名称、本地路径、credentials 和原始私有数据。

