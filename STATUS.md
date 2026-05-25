# Current Status

Date: 2026-05-25

SACP/0.1 is frozen for feedback.

## What Exists Now

- SACP/0.1 text-first spec, envelope, receipt, status codes, lifecycle, validator, conformance notes, and Dirty Run cases.
- Dirty Run benchmark: 10 spec cases for state, evidence, memory, lease, completion, and next-owner discipline.
- Sample corpus: 32 messy or review outputs translated into SACP receipts.
  - Batch 001: 10 real workflow/worklog excerpts.
  - Batch 002: 20 natural dirty outputs from DeepSeek, Qwen, GLM, and Kimi across 5 dirty tasks.
  - Review notes 031 and 032: local protocol review and designer feedback receipts.
- AgentOps Doctor: local reference skill / CLI works from source.
- Receipt Chain: optional profile documented with multi-agent and research-publish examples.
- Protocol Design References: HTTP, Git, OpenTelemetry, MIME, and RFC-style wording are the default guidance for protocol boundaries.
- Local static demo page: `sacp-demo.html` explains SACP's audit value without a backend.
- Local triage editor: `sacp-triage-editor.html` turns project state into a copyable next-round Codex prompt.
- JSON Schema plan: docs-only v0.2 route lives in `JSON_SCHEMA_PLAN.md`.
- Community materials: issue templates, contribution guide, outreach templates, and a public-safe adoption case.
- Outbound PR playbook for docs-only receipt examples, adapter notes, and dirty cases.

## Not Packaged Yet

- No `pip install sacp` package yet.
- No JSON Schema yet.
- No hosted service, database, HTTP binding, or framework adapter yet.
- No guarantee of task correctness. SACP audits claims, evidence, ownership, and decision boundaries.

## Looking For

The most useful contribution is a messy agent output from your own workflow.

Examples:

- An agent says "done" but provides no receipt.
- An agent says "tests passed" but shows no command output.
- An agent saves or promotes memory without approval.
- An agent recommends publishing based only on another model's claim.
- A handoff is incomplete, duplicated, or has no clear next owner.

Open an issue with the messy output, or add a new Dirty Run case.

## Next Milestone

Get 3 external users to submit 1 messy agent output each and translate each one into a SACP receipt.

Success means:

- 3 external cases added to the sample corpus.
- 3 review notes explaining what SACP caught or failed to catch.
- Any repeated failure mode converted into a Dirty Run case or AgentOps Doctor improvement.

## Maintainer Rhythm

- Every 2 weeks: update this file with current corpus counts and project status.
- When a good messy output arrives: translate it into a receipt, add a review note, and link it from the issue.
- When the spec changes: add a short changelog entry and keep v0.1 compatibility boundaries explicit.
- When a suggestion is out of scope: close it unless a real dirty case proves the need.
