# Current status

Updated: 2026-10-15. **Experimental alpha.** SACP/0.1 remains the exchange contract; the repository now also includes an executable reference engine, adapters, harness and CI governance.

Start with [README](./README.md) / [中文](./README.zh-CN.md), then [architecture](./docs/architecture.md), [development](./docs/development.md) and [maintainer workflow](./docs/maintainer-workflow.md). Historical research and corpus notes describe their original trials, not the current executable baseline.

## Implemented and bounded

| Area | Present now | Boundary |
|---|---|---|
| Protocol | Spec, envelope, receipt, validator, status codes, conformance, Receipt Chain profile | Document validity does not prove task truth; no JSON Schema release yet |
| Runtime | Claims/host/provider/authority events, SQLite persistence, evidence policy, derived receipts | Caller-trusted write API; no authentication or tamper-proof database |
| Domain gates | Release preflight, deployment health + explicit dispatch authority, refund completion | Supplied provider facts; no real deployment, release or payment execution |
| Recovery | Deadline checks after missing or accepted-only evidence, bounded routes, SQLite serialization | Caller invokes checks; no scheduler or compensation executor |
| Mock idempotency | Same-database refund reservations, conflict rejection, restart and concurrent calls | Simulated effect identity, not end-to-end exactly-once |
| Adapters | REST-shaped GitHub payload mapping, trusted reviewer allowlist, CLI, real LangGraph wiring/checkpointers | Payload source authentication remains an integration responsibility |
| HTTP experiments | Real localhost provider transport, simulated health/rollback | No public SACP API or production provider |
| Harness | Eight synthetic breakers and three positive controls | Fixed small set; no measured population accuracy |
| Governance | Read-only PR CI, trusted independent attestation, formal receipt, manual squash merge, main revalidation | Semantic review required; real fork E2E still outstanding |
| Corpus and Doctor | 34 translated receipts, YAML examples, local text-audit CLI | Historical/synthetic inputs; Doctor uses heuristics and does not rerun tasks |

## Verification baseline

Code baseline [1b76ff3](https://github.com/aDragon0707/sacp/commit/1b76ff386d6091535aae94acbb7517c9170bd5d8): 100 core tests, 7 LangGraph tests, 49 strict protocol documents, 8 breakers and 3 positive controls. Core CI covers Ubuntu Python 3.11/3.12 and Windows Python 3.12; LangGraph runs on Ubuntu Python 3.12. Zero failures/errors/unexpected skips are required.

See the [dated verification record](./docs/verification-2026-10-15.md) for exact runs and smoke coverage. A successful receipt-generation job can write a BLOCK or FAIL receipt; inspect content and current SHA, not just a green job.

## Not implemented or not established

No hosted service, public package distribution, authenticated general event gateway, managed scheduler, production deployment, real money movement or correctness guarantee. No claim of population error rate, broad external adoption, zero external dependencies or end-to-end exactly-once.

The protocol itself does not require a database or HTTP transport. The Python reference implementation uses SQLite and localhost HTTP experiments; those facts are compatible.

## Next work

Finish controlled real fork end-to-end acceptance, strengthen isolation against arbitrary malicious Python tests, authenticate external collectors where used, and gather independently reviewed real-world false-completion and false-block cases. Keep schema/transport expansion behind concrete dirty cases and compatibility review. See [ROADMAP](./ROADMAP.md).
