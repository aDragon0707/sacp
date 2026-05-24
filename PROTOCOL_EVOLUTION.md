# SACP Protocol Evolution

SACP should evolve through receipts, dirty cases, and real adapter pressure, not through speculative fields.

The goal is to keep the core small while giving useful ideas a path to grow:

```text
feedback -> dirty case -> extension -> profile -> repeated proof -> core candidate -> stable core
```

## Evolution Rule

No new core field, method, claim type, support status, resource type, status code, or required behavior should be added unless it passes this gate:

```text
1. A real or synthetic dirty case shows the failure.
2. Existing fields create an awkward workaround.
3. An extension or profile has been tried first.
4. At least one reference example exists.
5. Backward compatibility behavior is clear.
```

If any part is missing, keep the idea out of core.

## Stages

| Stage | Purpose | Allowed form | Promotion condition |
|---|---|---|---|
| Feedback | Capture user or agent confusion | issue, report, review note | concrete failure, not preference |
| Dirty Case | Reproduce the failure | `DIRTY_RUN_CASES.md` or example | expected status and required fix are clear |
| Extension | Try without changing core | `extensions.*` | repeated use across examples or adapters |
| Profile | Group related extensions | profile doc and examples | multiple workflows use the same pattern |
| Core Candidate | Consider protocol-level adoption | proposal note | workaround is repeatedly awkward |
| Stable Core | Freeze semantics | spec update | external feedback confirms usefulness |

## What Counts As Evidence

Strong evidence:

- two or more independent messy agent outputs show the same failure
- two or more adapter notes need the same field
- an existing status code forces confusing or misleading diagnosis
- an extension appears in multiple useful examples
- a Dirty Run case cannot be expressed cleanly with current fields

Weak evidence:

- a field sounds elegant
- one agent suggests it without a dirty case
- a hypothetical enterprise use case
- a desire to match another framework's vocabulary
- a workaround is slightly verbose but still clear

## Change Packet Shape

Every protocol change proposal should fit this shape:

```yaml
proposal_id: sacp_change_short_name
stage: feedback | dirty_case | extension | profile | core_candidate
problem: "What fails today?"
dirty_case: "Path or short description."
current_workaround: "How SACP handles it now."
proposed_change: "Smallest proposed addition."
compatibility: "How old receivers behave."
reference_example: "Path to example."
decision: keep_out_of_core | try_extension | profile_candidate | core_candidate | reject
next_owner: Maintainer
human_decision_required: true
```

## Promotion Rules

### Feedback -> Dirty Case

Promote only if:

- the report includes a concrete output, handoff, receipt, or adapter mapping
- the failure can be reproduced or described as a public-safe synthetic case
- expected status and required fix can be written

### Dirty Case -> Extension

Promote only if:

- existing core fields are not enough or create repeated awkwardness
- the extension can be ignored by old receivers
- the extension does not override core fields

### Extension -> Profile

Promote only if:

- multiple related extensions are used together
- examples show a stable pattern
- the profile can remain optional

Receipt Chain is an example:

```text
long-running work needed parent handoff, dependency, evidence, checkpoint, and stop-rule references, but those did not need to become core fields.
```

### Profile -> Core Candidate

Promote only if:

- the same concept appears in unrelated profiles or adapters
- implementers cannot interoperate without it
- keeping it in extensions causes recurring mistakes
- a backward-compatible migration path exists

## Rejection Rules

Reject or delay changes that:

- make SACP look like a runtime
- require a database, server, account system, or auth model
- add scoring or certification without a benchmark
- turn model inference into evidence
- let extensions override core fields
- claim SACP guarantees correctness
- lack a dirty case

## Versioning

v0.x:

- experimental
- small breaking changes allowed with notes
- dirty cases are the main pressure source
- extensions and profiles are preferred over core growth

v1.0:

- freeze required fields
- freeze method set
- freeze claim taxonomy
- freeze support status
- freeze core status codes
- freeze extension compatibility rules

## Maintainer Checklist

Before accepting a protocol change, answer:

```text
Is there a dirty case?
Can existing fields solve it clearly?
Can it remain an extension?
Can it be a profile instead of core?
Does it preserve old receivers?
Does it keep "No receipt, no trust" understandable?
```

Default decision:

```text
Make the example sharper before making the protocol bigger.
```

