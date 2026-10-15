# SACP Examples

[中文](./README.zh-CN.md) · [Project overview](../README.md)

Start here to choose a runnable example or a protocol document. Python demos exercise runtime behavior; YAML files illustrate the exchange contract. Validating a YAML document does not execute the task described in it.

## Start with Three Commands

Use Python 3.11 or 3.12. Run all commands from the **repository root**, not from `examples/`:

```bash
python -m pip install -r requirements-ci.txt
python -m sacp_harness
python -m examples.github_release_gate
```

The harness checks eight fixed breaker cases and validates the public protocol examples and translated receipts. The release example then shows both positive and negative gate decisions:

```text
1) missing approval: allowed=False, reason=release_approval_missing_or_stale, overall=needs_approval
2) matching approval: allowed=True, reason=release_evidence_and_authority_verified, overall=ready_for_external_action
3) artifact belongs to another commit: allowed=False, reason=release_evidence_missing_or_invalid, overall=unverified
```

`allowed=True` is a preflight decision for local fixture data. Nothing is published or sent to GitHub.

## Runtime Demos

These demos need no provider credentials. They use in-memory data or temporary SQLite files; the optional HTTP demo starts a localhost server and closes it on exit. Test results, approvals, and provider callbacks inside the demos are synthetic unless explicitly described otherwise.

| Learn about | Run from the repository root | What to look for |
|---|---|---|
| Release evidence and approval | `python -m examples.github_release_gate` | Matching approval allows preflight; missing approval or an artifact from another commit blocks it |
| REST-shaped adapter input | `python -m examples.github_api_payload_gate` | Same gate boundary for supplied workflow, artifact, and review payloads; no authenticated REST call |
| Separate local, authority, and external states | `python -m examples.release_task` | Approval, accepted, delivered, then bounced change different receipt dimensions |
| Deployment completion | `python -m examples.deployment_verification` | Accepted alone is insufficient; matching health allows finalization; rollback blocks it again |
| Refund completion and mock idempotency | `python -m examples.refund_agent` | Repeated requests share an ID within one mock instance; only matching succeeded evidence permits finalization |
| Bounded recovery routing | `python -m examples.bounded_recovery` | First timeout routes to retry; exhausting the configured budget assigns compensation ownership |
| Reopen an event store | `python -m examples.reconciliation_restart` | Reopened SQLite history preserves timeout state; repeating the check does not append the same timeout again |

Source: [release gate](./github_release_gate.py), [payload adapter demo](./github_api_payload_gate.py), [release lifecycle](./release_task.py), [deployment](./deployment_verification.py), [refund](./refund_agent.py), [bounded recovery](./bounded_recovery.py), [store reopen](./reconciliation_restart.py).

Suggested order: release gate → release lifecycle → deployment → bounded recovery → store reopen. Choose refund when exploring domain-specific completion and idempotency.

The recovery demos record routes, not actual retry or compensation execution. Store-reopen examples close and reconstruct objects; they are not OS-level crash tests. Mock refund IDs persist within the same SQLite database across restarts and concurrent connections; this is not an end-to-end exactly-once guarantee. Deployment health checking and action authorization are separate responsibilities; use `can_dispatch` to require approval before dispatch. The payload demo explicitly configures its trusted reviewer fixture.

## Pi Integration: No-Model Replay

Run `python -m examples.pi_evaluation` from the repository root. It replays [scripted Pi-format events](./pi_eval/scripted-events.jsonl) and actually tests two trusted source fixtures independently: correct code becomes `host_completed`; incorrect code stays `unverified` despite the same success text. It needs no Pi installation or model. This is a regression demo, not a real-agent benchmark. See the [integration guide](../docs/pi-integration.md) for probing an installed Pi, API contracts and the isolation required before real tasks.

## Optional LangGraph Demos

Install the integration dependencies first:

```bash
python -m pip install -r requirements-integration.txt
python -m examples.langgraph_release_experiment
python -m examples.langgraph_sqlite_restart
python -m examples.langgraph_http_integration
```

| Source | Observe | Boundary |
|---|---|---|
| [Release graph](./langgraph_release_experiment.py) | Missing approval stops dispatch; approved dispatch produces accepted; missing witness creates recovery routes | A real LangGraph graph with synthetic test observations and demo approval inputs |
| [SQLite reopen](./langgraph_sqlite_restart.py) | Graph state and SACP events survive closing and reopening both stores | A persistence/reconstruction experiment, not an injected process crash |
| [Localhost HTTP integration](./langgraph_http_integration.py) | Delayed acceptance and health produce a matching deployment decision and end the recovery route | Actual local HTTP; simulated provider state, no production deployment |

A recorded test-success observation in the graph does not mean the graph executed the test command. Run the [integration suite](../tests/test_langgraph_adapter.py) to verify the adapter wiring.

## Protocol Documents

Read [ENVELOPE.md](../ENVELOPE.md) and [RECEIPT.md](../RECEIPT.md) alongside these files. The `DerivedReceipt` returned by Python runtime demos is a different object from a `SACP/0.1` exchange receipt.

| Topic | Files | Read for |
|---|---|---|
| Minimal exchange | [valid_handoff.yaml](./valid_handoff.yaml), [valid_receipt.yaml](./valid_receipt.yaml), [valid_block_receipt.yaml](./valid_block_receipt.yaml) | A handoff, completion receipt, and blocked receipt |
| Small maintenance work | [micro_receipt_maintenance.yaml](./micro_receipt_maintenance.yaml) | A compact receipt that retains required core fields |
| Missing evidence | [dirty_missing_evidence.yaml](./dirty_missing_evidence.yaml) | An unsupported public claim and its expected correction |
| Duplicate vs. changed input | [dirty_duplicate_handoff.yaml](./dirty_duplicate_handoff.yaml), [dirty_changed_source_rework.yaml](./dirty_changed_source_rework.yaml) | Same input returns an existing result; changed input needs rework |
| Memory and authority | [dirty_memory_promotion.yaml](./dirty_memory_promotion.yaml), [human_decision_override.yaml](./human_decision_override.yaml) | Promotion boundaries and a human decision superseding prior work |
| Continued work | [cross_model_handoff.yaml](./cross_model_handoff.yaml), [solo_ai_company_handoff.yaml](./solo_ai_company_handoff.yaml) | Handoff identity, scope, and next-owner discipline |
| Receipt Chain | [receipt_chain_multi_agent_project.yaml](./receipt_chain_multi_agent_project.yaml), [receipt_chain_research_publish.yaml](./receipt_chain_research_publish.yaml) | Optional cross-handoff audit state; see the [profile](../SACP_RECEIPT_CHAIN.md) |
| Contextual audit examples | [longju_public_safe_receipt.yaml](./longju_public_safe_receipt.yaml), [socrates_focus_receipt.yaml](./socrates_focus_receipt.yaml) | How a receipt records a stated local trial or feedback snapshot and its limits |

Validate the public examples, or one document:

```bash
python validator.py --examples --strict
python validator.py --strict examples/valid_receipt.yaml
python validator.py --strict examples/dirty_missing_evidence.yaml
```

The `dirty_*.yaml` files are case fixtures with incoming data and an expected result. A strict PASS validates the case according to the validator; it does not mean the incoming claim is true or that a runtime lease/approval mechanism was exercised. Sample evidence IDs are references in an example, not newly authenticated observations.

## Saved Reports and Text Auditing

[sacp_sample_output.json](./sacp_sample_output.json) and [sacp_sample_report.md](./sacp_sample_report.md) are saved project-diagnosis examples. Their scores and narrative are not current CI results, runtime receipts, or measured verifier accuracy.

For an existing agent response, use Doctor's separate text-audit path:

```bash
python -X utf8 agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md
```

Doctor applies local heuristics and does not rerun the original task. Its inputs live in [agentops-doctor-skill/examples/](../agentops-doctor-skill/examples/).

## Add an Example

State the input, expected result, prerequisites, and what the example does not prove. For runtime behavior, add a corresponding positive or failure-boundary test under [tests/](../tests/); for protocol changes, follow the compatibility and dirty-case review in [CONTRIBUTING.md](../CONTRIBUTING.md). Update both example guides and keep generated reports outside tracked files.
