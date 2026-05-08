# Raw Sample 007: Socrates Multi-Agent Collaboration Extract

Source: `public-safe-alias:socrates-focus/multi-agent-adversarial-collaboration-extract`

Selected raw excerpt:

```text
The system is a 4-agent state machine driven by FastAPI WebSocket, LangGraph, and Evidence Ledger.

Runtime path:
user input -> Evaluator -> Agent 1 retrieval -> Agent 2 Socratic draft -> Agent 3 auditor -> Agent 4 communicator -> Data Sink -> Finalize.

Evidence Ledger separates:
- user_statement
- retrieved_fact
- tool_result
- inference

Rules:
- User input is user_statement, not verified fact.
- Graph retrieval result is retrieved_fact and must come from Agent 1.
- Agent 2 output is always inference, not retrieved_fact.
- If retrieval_status is empty/unavailable, Agent 2/4 can ask clarifying questions but cannot assert factual conclusions.
```
