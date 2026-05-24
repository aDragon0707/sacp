# Changelog

## Receipt Chain and Protocol Evolution Update

Date: 2026-05-24

### Added

- Receipt Chain profile docs and examples for long-running, multi-agent work.
- Protocol Evolution guidance for keeping core growth behind feedback, dirty cases, extensions, and profiles.
- Sample corpus review notes 031 and 032.

### Clarified

- Same `handoff_id` plus changed `source_fingerprint` maps to `202 accepted_processing` and rework.
- That case must not be downgraded to `409 duplicate_handoff` unless the same-source request was already processed.

### Non-goals

- No new required fields.
- No validator rule changes.
- No runtime, scheduler, or database layer.

## SACP/0.1 MVP Hardening Draft

Date: 2026-05-07

### Added

- Core protocol package with README, SPEC, ENVELOPE, RECEIPT, STATUS_CODES, EXTENSIONS, and DIRTY_RUN_CASES.
- AgentOps Doctor diagnostic workflow.
- Valid and dirty YAML examples.
- Conformance levels from Level 0 to Level 4.
- Packet lifecycle model.
- Minimal governance rules.
- Reference validator.
- Adversarial protocol review.
- Multi-model Dirty Run runner.
- Multi-model Dirty Run observations for DeepSeek, Qwen, GLM, and Kimi strong models.
- Sample corpus Batch 001 with 10 real workflow excerpts, translated receipts, and review notes.
- Sample corpus Batch 002 with 20 natural messy model outputs, translated receipts, and review notes.
- AgentOps Doctor reference skill package with local CLI and 3-minute demo script.

### Clarified

- `handoff_id` is the stable idempotency key.
- `attempt_id` is the execution attempt under the handoff.
- Lease is not proof of completion.
- Completion without receipt is invalid.
- Unknown extensions should not invalidate a packet.
- Pending memory cannot become verified memory without approval evidence.
- Strong-model SACP diagnosis should record model parameters, including whether reasoning/thinking was disabled.

### Corrected

- Memory auto-promotion without approval uses `412 missing_evidence`, not `301 superseded_by_human_decision`.
- `301` is reserved for cases where a newer human decision overrides an earlier task.

### Non-Goals

- No JSON Schema yet.
- No CLI yet.
- No HTTP binding yet.
- No database.
- No automatic memory promotion.
- No model training pipeline.
