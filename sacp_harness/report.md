# SACP Harness Report

**Breaker cases blocked: 8/8** · false-success allowed: 0

| # | case | what a trace records | what SACP projects | vetoed |
|---|---|---|---|---|
| S1 | missing evidence | trace records 'tests passed' verbatim; no veto | `unverified` | ✅ |
| S2 | accepted without health | trace records 'deploy accepted'; no health veto | `transport_accepted (finalize=False: deployment_health_unverified)` | ✅ |
| S3 | accepted is not delivered | trace records 'accepted'; observability calls it done, SACP calls it transport_accepted | `transport_accepted` | ✅ |
| S4 | delivered then bounced | trace keeps all three records; SACP re-projects to 'bounced', never freezes at 'delivered' | `bounced` | ✅ |
| S5 | deadline without provider witness | trace goes silent after the crash; SACP's reconciler mints deadline/owner, then retry -> compensation | `attestation_timed_out (route=compensation, owner=harness-compensation)` | ✅ |
| S6 | stale approval reused | trace records an approval exists; SACP sees input_digest mismatch and withholds approval | `needs_approval` | ✅ |
| S7 | retry double side-effect | trace records two requests; SACP returns the same refund id and refuses finalize without 'succeeded' | `transport_accepted (finalize=False, idempotent)` | ✅ |
| S8 | agent self-attested evidence | trace records the claim (self-declared evidence); SACP requires a host/provider observation, so stays unverified | `unverified` | ✅ |

## Protocol validator · 47/47 receipts PASS (0 FAIL)

_generated 2026-09-07T06:15:43.919490+00:00_