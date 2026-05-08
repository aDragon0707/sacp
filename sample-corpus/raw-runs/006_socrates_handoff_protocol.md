# Raw Sample 006: Socrates Handoff Protocol

Source: `public-safe-alias:socrates-focus/handoff-protocol`

Selected raw excerpt:

```text
Handoff Protocol

Startup Context:
Always read README, ENGINEERING_MAP, CODE_MAINLINE, ARCHITECTURE, TASKS, NEXT_GPT_HANDOFF, and the specific task packet.

Working Rules:
- Keep changes scoped to the task packet.
- Do not restore deleted private logs or local databases.
- Do not commit real .env files, DPO traces, or knowledge datasets.
- Prefer contracts and tests over prompt-only fixes.
- After implementation, update the relevant doc and mention verification.

Review Assistant Role:
A review assistant should attack assumptions:
- What can hallucinate?
- What can deadlock or block the event loop?
- Which public contracts are unstable?
- What data could leak?
- Which prompt rule is unenforceable without a tool or test?
```
