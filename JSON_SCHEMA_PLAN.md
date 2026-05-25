# SACP v0.2 JSON Schema Plan

Chinese version: [JSON_SCHEMA_PLAN.zh-CN.md](./JSON_SCHEMA_PLAN.zh-CN.md)

## Status

Docs-only plan.

This document does not add enforcement, runtime behavior, or new required fields.

## Why This Exists

SACP already has enough real examples to justify a schema plan, but not enough pressure to freeze or harden the wrong things too early.

The schema work should help with:

- better editor and tool feedback
- clearer packet shape for implementers
- reusable validation drafts
- future adapter mapping

It should not:

- expand the core protocol
- add a runtime or scheduler
- replace the validator
- claim correctness
- invent new required fields before the profile field names settle

## Scope

Start with the smallest useful schema set:

1. envelope schema
2. receipt schema
3. extension shape rules
4. dirty-case-specific examples
5. report shape for validator output

The first pass should stay close to the current v0.1 packet shape and treat extensions as optional.

## Boundaries

The schema should express:

- required core fields
- allowed known values
- nested object shape
- extension containment rules
- obvious invalid packet forms

The schema should not express:

- agent execution semantics
- external evidence truth
- runtime leases
- scheduling policy
- human judgment
- completion guarantees

If a rule depends on workflow behavior or trust policy, it belongs in docs, examples, or validator logic before it belongs in schema.

## Order Of Work

1. Confirm field names in core docs and profiles are stable enough for draft schemas.
2. Draft JSON Schema for envelope and receipt.
3. Keep profile fields under `extensions.*` unless a future profile says otherwise.
4. Add schema examples only after the docs and dirty cases agree on the shape.
5. Use the schema as a support artifact, not as protocol expansion.

## Likely Outputs

- `schema/envelope.schema.json`
- `schema/receipt.schema.json`
- `schema/extensions.schema.json`
- schema examples embedded in docs
- a short schema validation note in roadmap or validator docs

These files are not created yet. This plan only defines the route.

## Acceptance

The plan is good if:

- it keeps SACP core small
- it avoids premature hardening
- it helps tool authors without forcing new runtime assumptions
- it stays consistent with dirty-case-first evolution
