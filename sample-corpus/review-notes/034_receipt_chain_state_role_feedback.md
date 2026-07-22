# Review Note 034: Receipt Chain State And Role Feedback

Raw source: public-safe summary from a Codex-led multi-window maintenance workflow.

## What Was Done

- A coordinator window used a project entry file, machine-readable state file, handoff protocol, task file, and receipts to continue a long-running content-module project.
- The process avoided rereading the full chat history and kept the next task bounded.
- An independent reviewer later checked the coordinator's handoff/state discipline and the current delivery package.

## User-Style Feedback

The receipt-chain discipline helped the coordinator maintain the project. It made the next action clearer, reduced context drift, and forced the agent to preserve evidence instead of trusting memory.

The same workflow also exposed two friction points:

- Commit/status wording became ambiguous when `current_head`, verified content state, and verified handoff state were all described with "latest stable" language.
- The coordinator briefly treated a local subagent-style review as if it could stand in for a formal independent review. The user corrected this: local preflight is not the same authority as external review.

## What Felt Good

- A short entry file plus machine state file made onboarding much faster than reading old chat logs.
- Receipts gave later actors a compact evidence trail.
- Stop rules helped preserve "do not publish", "do not claim official acceptance", and "do not promise outcomes" boundaries.

## What Felt Awkward

- One status label was doing too much work: current workspace state, verified content commit, and verified handoff commit need different names.
- The protocol described next owners, but the example did not make review authority vivid enough. A coordinator-local check should be called preflight, not formal review.
- The best fix is probably not a new core field. It is a sharper good/bad example for long-running project handoffs.

## Suggested Improvement

Add Receipt Chain guidance that separates:

- current head
- latest verified content commit
- latest verified state or handoff commit
- review authority
- stop rule for self-review versus independent review

Keep this as documentation or optional extension guidance until multiple workflows show the same need.

## Verdict

PASS_WITH_NOTES

SACP improved continuity for a real multi-window workflow, but the docs should make state labels and review authority harder to confuse.
