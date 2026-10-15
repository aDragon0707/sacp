# Runtime contracts and compatibility

The Python reference engine is experimental. These contracts concern observations supplied by a trusted caller; the store does not authenticate that caller.

## Execution identity

Provider observations aggregate by `(action_id, provider, receipt_id)`. Within one execution, negative terminal evidence dominates positive evidence regardless of callback arrival order. Repeated event types are deduplicated. For retries, the latest acceptance by provider timestamp selects the current execution. Tied acceptances for different receipt IDs or multiple accepted providers are ambiguous and block successful projection. Provider clocks must be normalized by the adapter. Use a new action ID for a changed input or authorization scope.

Deployment health must match acceptance on provider, deployment ID and revision. Refund success must match acceptance on provider, refund ID, order, amount and currency, and match the authorized claim metadata. A bare terminal callback does not establish a completed execution without matching acceptance. Failures never disappear from the stored history when a later execution succeeds.

## Authority and time

`DeploymentGate.can_dispatch` requires an explicitly authority-required claim and matching approval. `can_finalize` preserves observation-only health checking for callers without an authority-required claim; pass `require_authority=True` when full authorization is mandatory. An authority-required claim always enforces approval during finalization. A health-only result must never authorize dispatch.

`RefundGate.can_finalize(..., now=...)` uses evaluation time, defaulting to current wall time. Deterministic examples and tests must pass their scenario clock explicitly. Approval binds thread, run, checkpoint, input, scope and expiry; reapproval after revocation is a distinct event.

Unknown claim types now return `unverified`. The supported lifecycle intentions are `notification_sent`, `publish_action`, `ask_counterparty`, `refund_requested` and `deployed`; these do not themselves prove success. `tests_passed`, `artifact_built` and `ready_to_publish` use explicit evidence policies. Host references must match thread/run/checkpoint, and test evidence must match commit when the claim specifies one.

## Bounded reconciliation

Claims opting into reconciliation need a deadline and owner. Acceptance alone does not end terminal-result waiting. Matching delivery, deployment health, refund success or a negative terminal event ends that wait. Due absence checks append a route once per claim/attempt, serialized through SQLite transactions. Restarting or concurrent callers cannot append the same due attempt twice. Exhaustion routes to a compensation owner, or human review if none is configured.

`retry` names a route and next check, not an executed retry. No scheduler, remote query, retry executor or compensation executor is provided. In particular, an accepted-but-unknown effect must not be blindly resent. Terminal completion clears the projected route while preserving history.

## Mock idempotency

Mock refund reservations and accepted observations commit atomically in the same SQLite database. `(provider, idempotency_key)` identifies one request including its action and scope; conflicting reuse raises `ValueError`. Separate connections to the same database share reservations across restarts and concurrent calls. Different databases do not share them. This moves no money and provides no end-to-end exactly-once guarantee.

## Migration

These changes tighten the experimental Python contracts; they add no SACP/0.1 wire fields. Callers relying on unknown claim pass-through, cross-receipt success, acceptance ending reconciliation, or historical-time refund checks must migrate. The optional `ReconciliationEvent.claim_ref` is a runtime field, not a core protocol field. Existing SQLite event tables remain readable; the mock reservation table is created alongside them. Historical mock observations without reservations cannot retroactively prove durable idempotency.
