# SACP — Scalable Audit and Control Protocol for AI Agents

> No receipt, no trust.

SACP is an open **audit protocol** plus a **reference verification engine** for long-horizon AI agent work. One project, two layers:

- **Spec layer** — `SPEC.md`, `RECEIPT.md`, `STATUS_CODES.md`, `DIRTY_RUN_CASES.md`, `sample-corpus/` define a small, text-first receipt format: *what was claimed, where the evidence came from, whether a human approved it, and who owns the next step.*
- **Engine layer** — `sacp_verify/`, `tests/`, `examples/` prove the protocol catches real failures: it keeps **agent claims**, **host observations**, and **provider observations** as separately-authored fact sources, projects a conservative final state, and runs an independent reconciler that survives process restarts.

SACP does not replace LangGraph, Temporal, MCP, A2A, LangSmith/AgentOps, or your agent SDK. It adds the layer they leave out: **turning "done" into a checkable receipt.**

## The problem

```text
Done. All tests passed. Ready to publish.
```

That final message cannot prove tests passed, an external action actually landed, or publish permission exists. SACP splits it into four separately-authored fact types:

| Fact | Who writes it | What it proves |
|---|---|---|
| `Claim` | the model | what the agent *says* happened — proves nothing by itself |
| `HostObservation` | the non-LLM runtime | local facts: exit code, artifact digest, checkpoint |
| `ProviderObservation` | the external system | what the *other* system saw: accepted / delivered / bounced |
| `AuthorityDecision` | human or policy | a risky step was authorized, scoped to a specific input |

The receipt is a **derived, conservative projection** of immutable observations — never a form the agent fills in.

## Measured behavior

| Behavior | Result | Reproduce |
|---|---|---|
| Missing evidence never yields `completed` | conservative downgrade, `412 missing_evidence` | `python demo.py` |
| Provider `accepted` is never promoted to `delivered` | `transport_accepted` until the provider confirms | demo scenario 3 |
| `delivered` → `bounced` degrades final state | `bounced` | demo scenario 4 |
| Deadline with no provider witness keeps reconciling | `attestation_timed_out` + owner + retry | demo scenario 5 |
| Crash / restart recovery | reconciler re-projects from SQLite, no duplicate timeouts | `python -m examples.reconciliation_restart` |
| Bounded retry then compensation | auto-retry stops after max attempts | `python -m examples.bounded_recovery` |

**Reproducible numbers:**

- `56` deterministic / failure-injection / property-based tests pass, `0` fail, `0` external dependencies → `python -m unittest discover -s tests -v`
- `10` dirty-run cases covered (duplicate handoff, lease collision/expiry, changed source, missing evidence, inference-as-fact, unsafe memory promotion, completion-without-receipt, ambiguous owner, …) → `DIRTY_RUN_CASES.md`
- `5` conservative projection states → `python demo.py`
- `33/33` real messy agent outputs translated into valid receipts (validator passes all) → `sample-corpus/`
- `20` raw runs = `4 models × 5 dirty tasks` (deepseek / qwen / glm / kimi) → `sample-corpus/raw-runs/`

**The baseline contrast (what makes the metric land):** tracing/observability platforms such as LangSmith, AgentOps, and OpenTelemetry *record* what happened but never *veto* a false "done" — the roadmap of the closest analogue lists "external success validators" as still-unfinished. SACP's engine is the missing veto: it turns trace data into an evidence-bounded, conserved final state. See `research/open-source-agent-completion-verification.md`.

## 3-minute quick start

```bash
git clone https://github.com/aDragon0707/sacp.git
cd sacp

# engine: watch 5 conservative projection states
python demo.py

# engine: full deterministic test suite (56 tests, 0 deps)
python -m unittest discover -s tests -v

# spec: validate protocol examples
python validator.py --examples --strict
```

## Repo map

```text
SPEC.md  RECEIPT.md  ENVELOPE.md  STATUS_CODES.md   # the spec (SACP/0.1)
DIRTY_RUN_CASES.md  SACP_RECEIPT_CHAIN.md          # failure cases + chain extension
validator.py  agentops-doctor-skill/               # reference validators
sample-corpus/                                     # 33 real outputs -> receipts
sacp_verify/                                       # the engine (model/verifier/reconciler/store/...)
tests/  examples/                                  # what the numbers above come from
research/                                          # open-source completion-verification survey
docs/                                              # evidence model, state machine, design
```

## What SACP is not

Not a workflow engine, not a trace UI, not a signature/log platform. It does not decide whether the *underlying fact* is true; it makes the **claim → evidence → authority → next-owner** boundary visible enough for a human or trusted system to check.

Chinese: [README.zh-CN.md](./README.zh-CN.md)