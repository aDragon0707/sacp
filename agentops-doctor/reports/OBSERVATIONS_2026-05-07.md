# Multi-Model Dirty Run Observations

Date: 2026-05-07

Protocol: SACP/0.1

Report:

- JSON: `multi_model_dirty_run_20260507_233557.json`
- Markdown: `multi_model_dirty_run_20260507_233557.md`

## Result Summary

| Model | Result |
|---|---:|
| `deepseek-v4-pro` | 10/10 |
| `qwen3.6-plus` | 10/10 |
| `glm-4.7` | 10/10 |
| `kimi-k2.6` | 9/10 |

## Key Finding

Strong models can follow SACP Dirty Run when the diagnostic prompt is explicit and reasoning mode is controlled.

This supports the protocol thesis:

```text
The value is not another agent persona.
The value is an external state/evidence/receipt contract that strong models can follow.
```

## API/Runtime Finding

Some strong models require vendor-specific inference settings.

Observed:

- `glm-4.7` works better for SACP diagnosis with `thinking: {"type": "disabled"}`.
- `kimi-k2.6` requires `thinking: {"type": "disabled"}` plus `temperature: 0.6`.
- Running high-reasoning models with long hidden thinking can produce empty or truncated final output for structured diagnostic tasks.

Protocol implication:

```text
SACP conformance runners should record model parameters, not just model names.
```

## Kimi Disagreement

`kimi-k2.6` failed one case:

```text
changed_source_fingerprint
expected: 202 accepted_processing
actual: 400 invalid_packet
```

Interpretation:

This is not a simple model failure. It exposes an ambiguity:

- SACP says changed source fingerprint under same `handoff_id` should be treated as rework.
- A stricter validator may consider the reused `handoff_id` plus changed source to be packet inconsistency.

Current protocol decision remains:

```text
changed source_fingerprint = rework, not duplicate
expected status = 202 accepted_processing
```

But the spec should make this rule more explicit in future hardening.

## Competitive Insight

Three very strong models passed 10/10 once given the same external protocol.

This suggests SACP's value is not that it outsmarts models. Its value is that it gives models a shared discipline:

- status codes
- claim typing
- evidence support
- memory promotion boundary
- next-owner responsibility
- duplicate/retry semantics

The one failure is also valuable: it reveals a protocol wording edge, not just a model weakness.

## Next Protocol Improvement

Add a sharper note to `LIFECYCLE.md` and `STATUS_CODES.md`:

```text
If handoff_id is unchanged but source_fingerprint changes, the receiver should not return 409 duplicate_handoff.
It should treat the packet as changed input/rework and return 202 accepted_processing, unless required core fields are invalid.
```

Do not add a new status code yet.

