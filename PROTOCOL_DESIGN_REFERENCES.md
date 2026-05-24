# SACP Protocol Design References

This note records the protocol patterns SACP borrows from and the design route that follows.

## Why These References Matter

SACP is not trying to become HTTP, Git, OpenTelemetry, MIME, or an RFC series. It borrows the parts that help a small audit protocol stay stable, extensible, and easy to reason about.

## What We Borrow

| Reference | What SACP borrows | What SACP does not borrow |
|---|---|---|
| HTTP | layered semantics, status codes, extensible fields, registered namespaces | transport binding as core behavior |
| Git | immutable objects, content-addressed history, named references | branching UI, merge workflow, repository mechanics |
| OpenTelemetry | explicit context propagation across boundaries | tracing backend requirements |
| MIME | stable core headers with optional parameters/extensions | free-form multipart transport design |
| RFC / BCP 14 | uppercase `MUST` / `SHOULD` / `MAY` for normative rules | vague requirement wording |

Sources:

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [RFC 9651: Structured Field Values for HTTP](https://www.rfc-editor.org/rfc/rfc9651)
- [RFC 2045: MIME Part One](https://www.rfc-editor.org/rfc/rfc2045.html)
- [RFC 2046: MIME Part Two](https://www.rfc-editor.org/rfc/rfc2046.html)
- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html)
- [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174.html)
- [Git data model](https://git-scm.com/docs/gitdatamodel.html)
- [Git references glossary](https://git-scm.com/docs/gitglossary.html)
- [OpenTelemetry context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)

## Technical Route Adjustment

1. Keep the SACP core small and immutable.
2. Treat receipts as append-only audit objects, not editable runtime state.
3. Propagate long-running work state with explicit references, not hidden memory.
4. Keep extensions namespaced, additive, and non-overriding.
5. Group repeated extension sets into optional profiles.
6. Use uppercase `MUST`, `SHOULD`, and `MAY` for normative requirements.
7. Give every canonical field or profile key one documented spelling.
8. If an alias is ever introduced, document it as an alias with compatibility rules.
9. Treat canonical spelling changes as protocol changes, not doc cleanup.
10. Prefer short names inside a strong namespace when the namespace already carries identity.

## Practical Consequences

- Core fields stay stable.
- `extensions` carry profile and vendor metadata.
- Unknown extensions are ignored, not rejected, unless they override or hide core fields.
- New protocol ideas should first appear as a dirty case, then an extension, then a profile.
- Receipt Chain remains a profile, not a runtime.
- Receipt Chain keys stay short and canonical because `sacp.chain.*` already names the domain.
