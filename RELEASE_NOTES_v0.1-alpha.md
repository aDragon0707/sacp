# SACP v0.1-alpha Release Notes

Release date: 2026-05-08

Chinese version: [RELEASE_NOTES_v0.1-alpha.zh-CN.md](./RELEASE_NOTES_v0.1-alpha.zh-CN.md)

## Summary

SACP v0.1-alpha is the first public experimental protocol kit for auditable AI agent work receipts.

It ships with:

- SACP/0.1 protocol draft
- Envelope and Receipt specs
- v0.1 status codes
- Dirty Run cases
- AgentOps Doctor reference skill
- Local validator
- Valid and dirty YAML examples
- Sample corpus receipts
- OpenClaw / Longju integration blueprint

## Intended Use

Use this release to:

- understand the SACP receipt model
- audit messy agent outputs
- translate worklogs into SACP receipts
- test dirty agent behavior
- prototype integrations with agent frameworks

## Not Intended For

This release is not:

- a stable standard
- a production runtime
- a compliance proof
- a hosted service
- a replacement for agent frameworks
- a guarantee that the underlying work is correct

## Quick Test

```bash
python validator.py --examples --strict
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/done_but_no_receipt.md
```

Expected behavior:

- examples validate
- AgentOps Doctor returns a status code, findings, required fix, and translated receipt

## Release Boundary

Core motto:

```text
No receipt, no trust.
```

More precise boundary:

```text
SACP helps agents produce auditable work receipts.
It does not guarantee correctness.
```

