# SACP Designer Feedback 032

Audience: SACP designer / maintainer

## What Was Verified

- `validator.py --examples --strict` passes all listed examples.
- `done_but_no_receipt` is diagnosed as `400 invalid_packet`.
- `unsupported_test_claim` is diagnosed as `412 missing_evidence`.
- Receipt Chain stays optional and does not turn SACP into a runtime.
- `same handoff_id + changed source_fingerprint` now has a clear rework path in lifecycle, status, and dirty-case guidance.

## What Should Be Kept

- Keep the core small.
- Keep claim typing strict.
- Keep `next_owner` concrete.
- Keep `human_decision_required` visible for approval boundaries.
- Keep Receipt Chain as an extension/profile, not core.

## One Remaining Sharp Edge

The changed-source rule is now present in multiple places, which is good, but maintainers should keep the wording aligned:

- `LIFECYCLE.md`
- `STATUS_CODES.md`
- `DIRTY_RUN_CASES.md`

If those drift apart, readers may again misread rework as duplicate handoff.

## Recommended Next Step

Run one more regression pass later on the changed-source case only, and keep the expected result fixed as:

```text
202 accepted_processing
verdict: rework
```

## Bottom Line

SACP/0.1 looks coherent as a receipt layer. The most useful design move now is not adding a new core field; it is keeping the rework/duplicate boundary wording consistent across the protocol docs and dirty cases.
