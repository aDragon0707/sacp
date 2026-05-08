# Contributing To SACP

SACP is experimental. The goal is to keep the core small, readable, and useful before it becomes a larger standard.

Chinese version: [CONTRIBUTING.zh-CN.md](./CONTRIBUTING.zh-CN.md)

## What We Want

Good contributions usually include one of these:

- a real or synthetic dirty case
- a clearer example
- a validator improvement
- a better AgentOps Doctor diagnosis
- a compatibility note for an agent framework
- documentation that makes the protocol easier to understand

## Change Rule

New core fields, methods, status codes, or claim types should not be added just because they sound useful.

They need:

1. A dirty case that proves the need.
2. A current workaround that is awkward or unsafe.
3. A minimal proposed addition.
4. Backward compatibility notes.
5. At least one reference example.

## Core Design Rules

- Keep v0.1 text-first.
- Prefer Markdown and YAML examples.
- Keep required fields few.
- Put vendor metadata under `extensions`.
- Unknown extensions should not break valid packets.
- Do not claim SACP guarantees correctness.
- Do not auto-promote memory or skills without human approval.

## Security And Privacy

Do not submit:

- API keys
- credentials
- private local paths
- private customer or project names
- raw private logs
- screenshots with private content
- copied proprietary output

Use synthetic examples when possible.

## Development Checks

Run:

```bash
python validator.py --examples --strict
python -m py_compile validator.py agentops-doctor/multi_model_dirty_run.py sample-corpus/collect_dirty_outputs.py agentops-doctor-skill/agentops_doctor.py
```

For sample corpus receipts in PowerShell:

```powershell
$files = Get-ChildItem sample-corpus\translated-receipts -Filter *.yaml | ForEach-Object { $_.FullName }
python validator.py @files --strict
```

## Pull Request Checklist

- [ ] The change keeps the core small.
- [ ] New protocol semantics include a dirty case.
- [ ] Examples validate.
- [ ] No secrets or private paths are included.
- [ ] Claims are bounded and do not overpromise.
- [ ] English and Chinese docs are updated when user-facing text changes.

