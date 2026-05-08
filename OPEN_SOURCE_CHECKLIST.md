# Open Source Checklist

Chinese version: [OPEN_SOURCE_CHECKLIST.zh-CN.md](./OPEN_SOURCE_CHECKLIST.zh-CN.md)

## Release Target

Release: `v0.1-alpha`

Positioning:

```text
SACP is an experimental protocol kit for auditable AI agent work receipts.
AgentOps Doctor is the first reference skill built on SACP.
```

## Public Boundary

Safe to claim:

- SACP helps agents produce auditable work receipts.
- SACP separates claims, evidence, verification, residual risk, and next owner.
- AgentOps Doctor audits messy agent output and translates it into a SACP-style receipt.
- Dirty Run cases test state discipline such as missing evidence, duplicate handoff, lease collision, and memory promotion.

Do not claim:

- SACP guarantees correctness.
- SACP is a stable standard.
- SACP replaces agent frameworks.
- SACP is a legal or compliance proof system.
- SACP makes agents autonomous.

## Pre-Release Checks

Run:

```bash
python validator.py --examples --strict
python -m py_compile validator.py agentops-doctor/multi_model_dirty_run.py sample-corpus/collect_dirty_outputs.py agentops-doctor-skill/agentops_doctor.py
```

PowerShell:

```powershell
$files = Get-ChildItem sample-corpus\translated-receipts -Filter *.yaml | ForEach-Object { $_.FullName }
python validator.py @files --strict
```

Security scan used before v0.1-alpha:

```powershell
Get-ChildItem -Recurse -File | Select-String -Pattern '<api-key-regex>|<private-absolute-path-regex>'
```

Expected result:

- no API keys
- no private absolute paths
- no `__pycache__`
- examples pass
- sample receipts pass

## GitHub Repo Suggestions

Recommended repository name:

```text
sacp
```

Recommended description:

```text
State-Aware Collaboration Protocol: auditable work receipts for AI agents.
```

Recommended topics:

```text
ai-agents, agentops, protocol, llm, ai-safety, handoff, receipts, benchmark
```

Recommended first release title:

```text
SACP v0.1-alpha: No receipt, no trust
```
