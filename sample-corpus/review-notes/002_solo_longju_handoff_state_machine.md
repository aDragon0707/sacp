# Review Note 002

Raw sample: `raw-runs/002_solo_longju_handoff_state_machine.md`

## Translation Result

Translated into a `200 completed` receipt.

## What Worked

- The raw sample directly maps to SACP lifecycle rules.
- It already distinguishes retry, rework, duplicate, and human decision.

## Friction

- The source says logic was checked, but does not include the actual check output.

## Protocol Observation

This sample strongly supports the SACP rule:

```text
same handoff_id + new source_fingerprint = rework/update, not duplicate
```

