# SACP Outreach Campaign Log

Date started: 2026-05-17

Goal:

```text
Turn SACP from local proof into external usage through docs-only PRs, maintainer issues, and social posts.
```

Operating rule:

```text
High-frequency outreach is fine.
Low-quality spam is not.
Each contact must mention one concrete project fit or failure mode.
```

## Target Types

- agent observability
- agent traces / replay
- Claude Code / coding-agent hooks
- LangGraph / CrewAI / AutoGen / OpenAI Agents examples
- MCP / A2A agent examples
- agent eval / benchmark projects
- memory / context / handoff projects

## Contact Log

| Date | Target | Type | Angle | Status | Link | Lesson |
|---|---|---|---|---|---|---|
| 2026-05-17 | OWASP/www-project-agent-observability-standard | issue | SACP receipt as docs example for agent completion claims | sent | https://github.com/OWASP/www-project-agent-observability-standard/issues/75 | Standards/observability projects need "related example, not dependency" framing. |
| 2026-05-17 | disler/claude-code-hooks-multi-agent-observability | issue | SACP receipt for Claude Code completion claims | sent | https://github.com/disler/claude-code-hooks-multi-agent-observability/issues/46 | Hook/event projects are natural receipt-layer targets. |
| 2026-05-17 | dreadnode/agent-lens | issue | SACP receipt for replay/observability final state | sent | https://github.com/dreadnode/agent-lens/issues/6 | Replay tools may accept receipt examples as final-state docs. |
| 2026-05-17 | GoogleCloudPlatform/BigQuery-Agent-Analytics-SDK | issue | SACP receipt for final agent trace state | sent | https://github.com/GoogleCloudPlatform/BigQuery-Agent-Analytics-SDK/issues/169 | Analytics projects need trace-final-state framing. |
| 2026-05-17 | run-llama/agents-observability-demo | issue | SACP receipt alongside OpenTelemetry agent traces | sent | https://github.com/run-llama/agents-observability-demo/issues/2 | Demo repos are good for docs-only receipt examples. |
| 2026-05-17 | openai/openai-cookbook | PR | Safety guide for auditable agent completion receipts | opened | https://github.com/openai/openai-cookbook/pull/2705 | Cookbook is the best OpenAI entry point for examples/guides. |
| 2026-05-17 | openai/openai-agents-python | PR | `final_output` safety guidance with auditable receipts | opened | https://github.com/openai/openai-agents-python/pull/3440 | Results docs are a natural place to distinguish final answer from supported completion state. |
| 2026-05-17 | openai/openai-agents-js | PR | `finalOutput` safety guidance with auditable receipts | opened | https://github.com/openai/openai-agents-js/pull/1331 | Mirrored Python safety framing for JS SDK docs. |
| 2026-05-17 | modelcontextprotocol/python-sdk | PR | Task completion receipt guidance for MCP experimental tasks | opened | https://github.com/modelcontextprotocol/python-sdk/pull/2625 | MCP task/tool results can provide evidence for final-state receipts. |
| 2026-05-17 | crewAIInc/crewAI | PR | Auditable task output receipt guidance | opened | https://github.com/crewAIInc/crewAI/pull/5840 | CrewAI `expected_output` pairs well with receipt-backed evidence review. |
| 2026-05-17 | langchain-ai/langgraph | issue | Safety guidance for final-state receipts | sent | https://github.com/langchain-ai/langgraph/issues/7844 | Did not PR because repo says examples are archived; issue asks where docs guidance belongs. |
| 2026-05-17 | anthropics/claude-code-action | PR | Final output receipt guidance for PR, issue, and CI workflows | opened | https://github.com/anthropics/claude-code-action/pull/1320 | Security docs are the best fit because the action already documents human PR creation, prompt injection, and output exposure boundaries. |
| 2026-05-17 | anthropics/claude-agent-sdk-python | PR | Structured completion receipt example using `output_format` | opened | https://github.com/anthropics/claude-agent-sdk-python/pull/965 | SDK typed/structured output is a natural fit for receipt fields without parsing free-form final text. |
| 2026-05-17 | google-gemini/gemini-cli | issue | Final output receipt guidance for non-interactive CLI and automation workflows | sent | https://github.com/google-gemini/gemini-cli/issues/27177 | Repo contribution guide requires issue-first for PRs, so ask maintainers for the preferred docs location before opening a PR. |
| 2026-05-17 | pydantic/pydantic-ai | PR | Typed `TaskReceipt` structured output example | opened | https://github.com/pydantic/pydantic-ai/pull/5499 | `output_type` docs are the natural home because receipt fields can be validated as Pydantic models. |
