# Maintainer Workflow

This document defines how an external change moves from an untrusted pull request to the trusted `main` branch. The objective is evidence-bound review, not automated approval.

```text
PR head
  -> pr-ci runs untrusted code with read-only permissions
  -> pr-gate rejects failed, cancelled, missing, or skipped dependencies
  -> pr-receipt re-checks policy with trusted main-branch code
  -> maintainer reviews semantics and risk
  -> squash merge
  -> main-verify reruns the same suites on the final main SHA
  -> post-merge receipt
```

## Trust Boundaries

`pr-ci` runs the pull request's code. It has `contents: read`, receives no repository secrets, and never uses `pull_request_target`. Its evidence artifacts are untrusted inputs.

`pr-receipt` is triggered by `workflow_run` and checks out the default branch. It downloads CI evidence, fetches PR objects without checking them out, and reads changed workflow files as text through the trusted policy checker. It does not execute PR code. A modified test runner can still forge its own evidence, so changes to workflows, policy, gates, or receipt generation are classified `automation-critical` and require direct maintainer inspection.

`main-verify` runs only after a push reaches `main`. Its receipt binds the final main SHA, not the earlier PR head or GitHub merge-test SHA.

## Change Classification

The policy checker records zero or more classes in CI evidence and the formal receipt:

| Class | Typical paths | Maintainer focus |
|---|---|---|
| `protocol` | protocol documents and YAML packets | semantics, compatibility, dirty case, example, changelog |
| `engine` | `sacp_verify/`, `sacp_harness/` | conservative state projection, append-only history, failure tests |
| `adapter` | GitHub, LangGraph, and CLI boundaries | external facts must not be promoted to stronger states |
| `automation` | workflows and CI scripts | permissions, action pins, self-modification, evidence binding |
| `corpus` | `sample-corpus/` | privacy, contamination, reproducibility |
| `docs` | Markdown and `docs/` | claims stay within current evidence |

The first release records these classes in artifacts; it does not add labels, comments, approvals, fixes, or merges.

## Required Checks

`pr-gate` depends on these stable jobs:

- `protocol-validation`
- `core-ubuntu-3.11`
- `core-ubuntu-3.12`
- `core-windows-3.12`
- `integration-langgraph-ubuntu-3.12`
- `harness`
- `pr-policy`

The gate uses `if: always()`. Every dependency must have result `success`. Failure, cancellation, missing jobs, and unexpected skips all block the gate. The LangGraph job installs `requirements-integration.txt` explicitly and must execute all seven integration tests.

## Evidence Contract

Every executable suite emits `sacp-ci-evidence/1` JSON containing:

- stable job and suite identity;
- tested base, head, and merge SHA;
- Git tree fingerprint;
- exact command and exit code;
- platform, runner OS, and Python version;
- test totals, failures, errors, and skips;
- generated timestamp.

A new push changes `head_sha`; earlier evidence no longer validates. Evidence with a missing command, environment, digest, SHA, or unexpected skip cannot produce a successful receipt.

Run the same interface locally:

```bash
python scripts/run_tests.py --suite core --job core-local --fail-on-skip --json evidence.json
python scripts/run_tests.py --suite langgraph --job langgraph-local --fail-on-skip --json evidence-langgraph.json
```

## Receipt Meaning

The trusted builder emits an ordinary `SACP/0.1` receipt:

- `COMPLETE / 200`: automated preflight evidence is complete and passed;
- `BLOCK / 412`: checks failed, skipped, or are missing;
- `FAIL / 500`: evidence is malformed, inconsistent, or bound to the wrong SHA.

Every PR receipt has `human_decision_required: true`. A `200` receipt does not mean approved, mergeable by policy, released, deployed, or correct. It only means the automated preflight contract completed for the recorded SHA.

## Human Review Checklist

Before merging, inspect the diff and answer the relevant questions:

- Protocol: Is there a dirty case, compatibility note, reference example, and changelog entry?
- Engine: Does a falsification test cover the changed behavior and failure boundary?
- Adapter: Can partial, stale, or transport-only evidence be promoted to success?
- Automation: Can untrusted PR code gain write permission, secrets, approval, or a false green gate?
- Corpus: Does the change contain private data, contamination, or irreproducible claims?
- Documentation: Does public text claim more than current commands and artifacts prove?

Warnings are not automatically waived. Resolve the issue or record the reason in the PR before clicking merge.

## Merge and Recovery

Use squash merge. Do not enable auto-merge or automatic branch deletion in the first phase. If `main-verify` fails after merge, treat the main receipt as `BLOCK` or `FAIL`, open a corrective PR from the current `main`, and keep the failed receipt as evidence. Do not rewrite `main` to erase the failure.

The initial ruleset requires `pr-gate` and a manual merge click but zero approving reviews. `CODEOWNERS` routes review; it should become a required non-author approval only after a second active maintainer exists.
