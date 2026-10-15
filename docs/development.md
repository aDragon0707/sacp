# Development and verification

Use Python 3.11 or 3.12. Run commands from the repository root. The core runtime uses the standard library; protocol and CI tooling require PyYAML. LangGraph dependencies are optional and explicit.

## Setup

```bash
python -m pip install -r requirements-ci.txt
python -m pip install -r requirements-integration.txt
```

The second command is required for the integration suite, not for using the base engine. There is no published `pip install sacp` distribution in this snapshot.

## Stable suite interface

```bash
python scripts/run_tests.py --suite core --fail-on-skip --json .local/evidence/core.json
python scripts/run_tests.py --suite langgraph --fail-on-skip --json .local/evidence/langgraph.json
python scripts/run_tests.py --suite protocol --fail-on-skip --json .local/evidence/protocol.json
python scripts/run_tests.py --suite harness --fail-on-skip --json .local/evidence/harness.json
python -m unittest tests.test_harness -v
git diff --check
```

The code baseline linked from [README](../README.md) has 100 core tests, 7 integration tests, 49 protocol documents, 8 breakers and 3 positive controls. Counts are a versioned inventory, not a fixed success criterion. New tests should increase coverage; a missing dependency or skip is not a complete pass.

The core suite discovers `tests/test_*.py`, excluding the optional LangGraph and harness modules. `--suite harness` executes the breaker/positive report directly; `tests.test_harness` separately checks report output and deterministic artifact handling. Protocol validates root YAML examples and translated corpus receipts strictly.

CI runs core on Ubuntu Python 3.11/3.12 and Windows Python 3.12, and LangGraph integration on Ubuntu Python 3.12. The job names form a stable interface consumed by `pr-gate` and the receipt builder; renaming one requires updating all consumers and reviewing the migration.

## Focused changes

```bash
python -m unittest tests.test_domain_boundaries -v
python -m unittest tests.test_ci_automation -v
python -m unittest tests.test_github_payload_adapter tests.test_cli -v
python validator.py --examples --strict
python -m examples.github_release_gate
python -m examples.github_api_payload_gate
python -m examples.refund_agent
```

Choose the smallest relevant test first, reproduce the failure, fix the contract, then run the affected suite and required CI. Include a valid-success control beside important rejection paths. Callback ordering, duplicate events, restart and concurrency should be tested where they affect observable behavior.

## Time and side effects

Pass the scenario clock to gates/verifier in deterministic tests. Refund finalization and CLI otherwise use wall time; a historical payload timestamp cannot keep an expired approval current. CLI fixture replay requires explicit `--now` and trusted `--authorized-reviewer` options.

```bash
python -m sacp_verify.cli --payload fixture.json --authorized-reviewer release-manager --now 2026-08-31T17:00:00+00:00
```

This last command requires a caller-supplied REST-shaped fixture; see [payload example](../examples/github_api_payload_gate.py) for its shape. It evaluates a gate and does not publish anything. An allowlist is not authenticated collection; deployment callers must enforce `can_dispatch` before real execution.

## Artifacts and receipts

`.local/` is ignored. Default harness execution prints only; `python -m sacp_harness --output-dir .local/harness` explicitly writes a report. Do not commit timestamp-only generated results. Save run IDs, tested SHA, command, environment, exit code, totals and skips with verification evidence.

Formal CI receipts require an independent attestation from default-branch code. Local suite JSON alone cannot create a trustworthy COMPLETE. `build_ci_receipt.py` returning zero means a valid receipt was written; it may contain BLOCK or FAIL. Consumers must read `method`, verification status, recorded SHA and current GitHub checks. See [maintainer workflow](./maintainer-workflow.md).

## Public/private boundary

Public docs contain reproducible commands and scoped evidence. Keep personal interview notes, outreach drafts, credentials, private logs and local absolute paths outside public commits. Historical corpus documents and saved reports retain their historical meaning; do not rewrite them to imply a new evaluation occurred.
