# Verification scope — 2026-10-15

This is a scoped verification record, not a security certification. The executable baseline is [1b76ff3](https://github.com/aDragon0707/sacp/commit/1b76ff386d6091535aae94acbb7517c9170bd5d8). Use the [development commands](./development.md) to reproduce the suites on a later SHA.

## Merged changes

| PR | Scope | Post-merge run |
|---|---|---|
| [#17](https://github.com/aDragon0707/sacp/pull/17) | README architecture and examples navigation | [38665331411](https://github.com/aDragon0707/sacp/actions/runs/38665331411) |
| [#18](https://github.com/aDragon0707/sacp/pull/18) | Independent GitHub execution attestation and evidence validation | [38667178728](https://github.com/aDragon0707/sacp/actions/runs/38667178728) |
| [#19](https://github.com/aDragon0707/sacp/pull/19) | Execution identity, bounded recovery, durable mock idempotency and positive controls | [38667994352](https://github.com/aDragon0707/sacp/actions/runs/38667994352) |
| [#20](https://github.com/aDragon0707/sacp/pull/20) | Trusted reviewer configuration, latest decisions and wall-time expiry | [38668329378](https://github.com/aDragon0707/sacp/actions/runs/38668329378) |

The earlier split synchronization is recorded by PRs [#7](https://github.com/aDragon0707/sacp/pull/7), [#8](https://github.com/aDragon0707/sacp/pull/8), and [#11–#16](https://github.com/aDragon0707/sacp/pulls?q=is%3Apr+is%3Amerged). Private research notes and the comparison integration branch were not copied wholesale into main.

## Suite contract

Core: 100 tests on each configured OS/Python combination; LangGraph: 7; protocol: 49 strict-valid documents; harness: 8/8 breaker expectations and 3/3 positive controls. Every required suite must have zero failures, errors and unexpected skips. Test counts describe this baseline, not independent samples or production error rates.

The regression suite covers fake/inconsistent evidence, zero tests, wrong command/environment, missing attestation, independent job failure after passing evidence, stale SHA, empty fork event metadata, unsafe workflow syntax, cross-receipt completion, failed terminal results, reapproval, accepted-only waiting, restart/concurrency and idempotency conflicts.

## End-to-end smoke matrix

Controlled [PR #21](https://github.com/aDragon0707/sacp/pull/21) is a deliberately unmerged test fixture. Its run/receipt outcomes are recorded below after execution. Unit tests do not substitute for missing external smoke coverage.

| Scenario | Evidence status |
|---|---|
| Normal PR under new collector | #19 and #20: current-head COMPLETE, strict PASS |
| Deliberately failing tests | [38668371551](https://github.com/aDragon0707/sacp/actions/runs/38668371551): core and pr-gate fail; receipt BLOCK/412, strict PASS |
| Push a new SHA to the same PR | [38668935747](https://github.com/aDragon0707/sacp/actions/runs/38668935747): all checks pass, fresh COMPLETE/200 at b25a34e; old run rejected against current PR by live API collection |
| Modify execution workflow | [38669082774](https://github.com/aDragon0707/sacp/actions/runs/38669082774): all CI checks pass; [receipt run 38669162856](https://github.com/aDragon0707/sacp/actions/runs/38669162856) emits strict-valid BLOCK/412 for changed execution definitions, with automation-critical risk |
| Protocol change without companions | [38669529073](https://github.com/aDragon0707/sacp/actions/runs/38669529073): checks pass; [receipt run 38669584562](https://github.com/aDragon0707/sacp/actions/runs/38669584562) emits strict-valid COMPLETE/200 at f71afc9 with protocol classification and explicit dirty-case/compatibility/example/changelog review warnings |
| Actual fork PR | NOT RUN: no independent fork in the current source network; covered only by API-contract tests |
| Failed/cancelled/missing jobs and post-evidence failure | Unit/API-contract tests; no deliberate failing push to production main |

## Boundaries

Receipt construction uses GitHub job conclusions, current PR identity, commit parents, source fingerprints and source test inventory independently of artifact assertions. Execution-definition changes are blocked from automatic COMPLETE and require reviewed bootstrap handling. This does not prove arbitrary in-process tests are honest, authenticate general runtime writers, or execute remote compensation.

Real fork identity/permission behavior remains an acceptance gap until a controlled fork can be tested. Merge queue receipts are not enabled; `merge_group` runs suite CI, but the formal PR receipt path currently accepts pull_request events only. No automated comments, approvals, repairs or merges are configured.
