# Anthropic 1P To SACP

This is a docs-only learning note.

It does not change SACP core fields, add a runtime, define a RAG system, or
make any correctness guarantee.

## One Sentence

Anthropic 1P improves how a model is prompted; SACP audits whether an agent
work transaction produced checkable claims, evidence, verification, and a next
owner.

```text
1P improves model calls.
SACP audits work transactions.
Retrieval is candidate evidence, not truth.
```

## Why This Mapping Exists

Prompt engineering can make a model clearer, more structured, and less likely
to hallucinate. It still does not prove that work was executed, verified, or
safe to hand off.

SACP starts after that boundary:

```text
request -> claim -> execute -> verify -> receipt -> next owner
```

The smallest reliable unit is not a prompt. It is a work transaction with a
receipt.

## 1P Concepts As SACP Audit Pressure

| Anthropic 1P concept | What it improves | SACP audit question |
|---|---|---|
| Clear and direct prompts | Reduces task ambiguity | Is the handoff body specific enough to audit? |
| Role prompting | Steers behavior and tone | Which `agent_id` owns the attempt? |
| Separating data and instructions | Reduces prompt injection risk | Are tool results and retrieved text treated as data, not authority? |
| XML/JSON/output formatting | Makes output parseable | Can claims and receipts be inspected by tools? |
| Step-by-step thinking | Encourages intermediate analysis | Which claims are evidence-backed, and which are inference? |
| Few-shot examples | Demonstrates expected behavior | Are dirty cases and example receipts concrete enough? |
| Avoiding hallucinations | Encourages refusal when evidence is missing | Should unsupported claims return `412 missing_evidence`? |
| Complex prompts | Assembles task context, rules, data, and format | Is the work represented as a packet, not only prose? |
| Prompt chaining | Splits work into stages | Are attempts, retries, and next owners preserved? |
| Tool use | Lets the agent request external execution | Are tool results cited as `tool_result` claims? |
| Search and retrieval | Supplies external candidate evidence | Are retrieved facts cited with source identity? |

## Four Practical Layers

### 1. Prompt Quality

Use 1P techniques to make each model call easier to follow:

- state the task clearly
- separate instructions from data
- provide examples only when they clarify boundaries
- ask for structured output when downstream tools need it
- ask for evidence before factual answers

SACP boundary: prompt quality is helpful, but it is not proof of completion.

### 2. Execution Chain

Use chaining for multi-step work:

```text
draft -> review -> repair -> verify -> receipt
```

SACP boundary: each meaningful attempt should be resumable and auditable with
`handoff_id`, `attempt_id`, `verification`, and `next_owner`.

### 3. Evidence Boundary

Keep claim sources separate:

- `user_statement`: the user said it
- `retrieved_fact`: a trusted source says it
- `tool_result`: a tool, test, command, API, or runtime produced it
- `inference`: the model concluded it

SACP boundary: user statements and model inferences must not be silently
promoted to retrieved facts.

### 4. Receipt Discipline

Do not trust final-answer fluency as proof of work.

A completion claim needs a receipt with:

- auditable `claims`
- cited support
- `verification`
- `residual_risk` when useful
- concrete `next_owner`
- `human_decision_required` when the next action crosses a human boundary

## RAG Boundary

RAG can reduce hallucination by adding external material, but it can also
amplify errors:

```text
bad query -> wrong chunk -> unsupported answer -> bad memory -> bad handoff
```

SACP does not make retrieval correct. It makes the retrieved material auditable:

- what source was retrieved
- what claim it supports
- whether support is exact or only related
- whether the answer should be downgraded to `unverified` or blocked with
  `412 missing_evidence`

## Minimal Rule Of Thumb

Use 1P to improve the step.

Use SACP to audit the step.

Do not let a better prompt replace evidence, verification, or a receipt.
