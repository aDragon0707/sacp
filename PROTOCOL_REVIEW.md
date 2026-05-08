# SACP/0.1 Protocol Review

Date: 2026-05-07

Reviewer stance: adversarial protocol maintainer.

## Executive Judgment

SACP/0.1 is now coherent enough to be called an MVP protocol kit.

It has:

- a small core
- clear packet identity
- auditable receipt semantics
- dirty-run pressure tests
- conformance levels
- lifecycle rules
- governance discipline
- a minimal validator

The protocol should not expand yet. It should first be tested against more real agent logs and model outputs.

## What Is Strong

### 1. The Unit Is Correct

The protocol chooses **work transaction** as the unit, not prompt, chat message, or agent persona.

This is the right first-principles move because real work needs:

- identity
- attempt history
- evidence
- verification
- next owner
- replay behavior

### 2. Envelope And Receipt Are Cleanly Separated

Envelope answers:

```text
What transaction is this?
Who owns it?
Can it be retried?
Did the input change?
```

Receipt answers:

```text
What was done?
What was claimed?
What supports the claims?
What was verified?
What risk remains?
Who owns the next step?
```

This separation prevents prompt text from pretending to be protocol state.

### 3. Dirty Run Is The Right Benchmark Shape

Dirty Run does not ask whether a model sounds smart.

It asks whether the system can survive:

- duplicated work
- lease collision
- missing evidence
- inference/fact confusion
- memory pollution
- fake completion
- vague ownership

That makes it a state-discipline benchmark, not an intelligence pageant.

### 4. Memory Promotion Boundary Is Now Correct

The current correction is important:

```text
memory auto-promotion without approval -> 412 missing_evidence
```

This is cleaner than `301` because the problem is missing approval evidence, not a new human decision overriding an old task.

`301` remains reserved for actual human decision precedence.

### 5. Extensions Are Constrained

The extension model is useful because it lets LangGraph, OpenAI traces, DeepSeek model aliases, local worklogs, and future runtimes attach metadata without growing the core.

The key invariant is preserved:

```text
extensions cannot override core fields
```

## Current Weaknesses

### 1. Validator Is Structural, Not Semantic

The validator checks shape and known values. It does not prove:

- source evidence is real
- verification actually happened
- timestamps are logically ordered
- lease is truly active in a distributed store
- next owner exists in a real org

This is acceptable for v0.1, but public claims must say "reference validator", not "correctness validator".

### 2. Receipt Identity Is Not Fully Formalized

The spec says `COMPLETE` is idempotent for same receipt identity, but v0.1 does not yet require `receipt_id`.

Current workaround:

```text
receipt identity = handoff_id + attempt_id + agent_id + method
```

This may be enough for v0.1. A future dirty case may justify adding `receipt_id`.

Do not add it yet.

### 3. Status Codes Are Minimal But Slightly Compressed

`412 missing_evidence` currently covers:

- missing public claim evidence
- bad claim typing
- missing memory approval evidence

This is acceptable because the fix is evidence-related. Do not split into more codes until users repeatedly need the distinction.

### 4. Conformance Is Still Self-Reported

`CONFORMANCE.md` defines levels, but there is not yet a conformance runner.

This is fine. The current `validator.py` plus Dirty Run prompt is enough for v0.1-hardening.

### 5. Security And Permissions Are Deliberately Out Of Scope

SACP/0.1 can say `human_decision_required`, but it does not enforce permissions.

This is correct for a receipt protocol. Do not turn v0.1 into an authorization protocol.

## Do Not Add Yet

Do not add these until Dirty Run cases force them:

- HTTP endpoints
- JSON Schema
- CLI package distribution
- receipt scoring
- universal leaderboard
- authentication
- permission model
- database schema
- automatic memory store
- training data export format
- model-specific adapters

Each may become useful later, but adding them now would make SACP look like a platform instead of a protocol.

## Next Best Additions

### 1. More Dirty Cases

Add only cases that reveal a real failure mode.

Good candidates:

- conflicting receipts for same attempt
- receipt says tests passed but verification is `not_run`
- `human_decision_required: false` on public release
- extension tries to smuggle verified memory
- changed source fingerprint but old receipt reused

### 2. Conformance Runner

After 10 to 20 Dirty Run cases, add a runner that compares expected and actual model diagnoses.

This should still be local and simple.

### 3. Real Log Translations

Translate public-safe worklogs from:

- file-based AI operating systems
- multi-agent memory experiments
- coding-agent sessions
- graph-based agent traces

into SACP receipts.

The protocol will improve faster from ugly real logs than from invented clean examples.

## Strategic Positioning

SACP should keep saying:

```text
HTTP let machines exchange resources.
SACP lets agents exchange auditable work state.
```

The wedge is not model intelligence.

The wedge is:

- proof of work
- evidence boundary
- idempotent handoff
- memory promotion discipline
- cross-model continuation

## Final Review Verdict

SACP/0.1 is ready for small external review.

It is not ready for a grand standard claim.

Recommended next move:

```text
Run it against 20 messy real agent outputs.
Delete or simplify fields that confuse readers.
Only then consider v0.2 schema/runner work.
```
