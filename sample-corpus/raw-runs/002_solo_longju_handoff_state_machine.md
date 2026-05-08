# Raw Sample 002: Solo Longju Handoff State Machine

Source: `public-safe-alias:solo-ai-company-os/worklog-handoff-state-machine`

Selected raw excerpt:

```text
type: worklog
protocol: SACP/0.1
agent_id: Longju
status: completed
verification: partial
human_approved: false

Background:
The first version of the handoff review logic was too aggressive and too absolute.

Two mistakes were identified:
1. source_handoff_id existing in a receiving worklog was treated as completed work.
2. Contradictory source worklog fields were treated as an automatic block verdict.

Corrected Retry Rule:
- same handoff_id + same source_fingerprint + expired lease -> retry with new attempt_id
- same handoff_id + new source_fingerprint -> rework or update, not duplicate
- new human decision or changed task identity -> create a new handoff_id

Verification Status:
- Logic was checked against the refined SACP handoff state machine.
- No publish action was taken.
- Human promotion has not been approved.
```
