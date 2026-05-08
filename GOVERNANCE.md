# SACP Governance

SACP should grow through evidence, not imagination.

治理目标不是一开始就做委员会，而是保护协议的极简性，让每个新增字段、状态码、方法都经得起 Dirty Run 的压力。

## Governance Principle

```text
Rough consensus + running dirty cases.
```

## Change Rule

A new core field, method, resource type, claim type, support status, or status code requires:

1. A real or synthetic Dirty Run case.
2. At least one awkward workaround using the current spec.
3. A minimal proposed addition.
4. Backward compatibility notes.
5. A reference example.

If it cannot produce a dirty case, it should remain an extension.

## Extension First

New ideas should usually begin under `extensions`.

```yaml
extensions:
  sacp.experimental.some_new_field: value
```

Only repeated pain should move into core.

## Removal Rule

Before adding a field, ask:

```text
Can we make the example sharper instead?
Can this be represented by existing fields?
Can this stay in extensions?
Can this be a profile, not core?
```

## Deprecation Rule

Do not delete core fields quickly.

Use:

```yaml
deprecated_since: SACP/0.3
replacement: new_field_name
```

Deprecation must include:

- migration note
- old example
- new example
- compatibility behavior

## Compatibility Rule

Receivers should:

- validate core fields
- ignore or preserve unknown extensions
- avoid failing on extra body content
- never let extensions override core fields

## Release Rule

For v0.x:

- small drafts are acceptable
- breaking changes are allowed but must be documented
- Dirty Run cases are the source of pressure

For v1.0:

- core method set should freeze
- required receipt fields should freeze
- claim taxonomy should freeze
- support status should freeze
- status code core should freeze
- extension rules should freeze

## Public Claim Boundary

Safe public claims:

- SACP helps agents produce auditable work receipts.
- SACP defines minimal envelope, receipt, status, and dirty-run semantics.
- SACP can work in Markdown-first workflows and runtime state machines.
- SACP complements MCP/A2A/runtime frameworks by focusing on work receipts and evidence state.

Unsafe public claims:

- SACP guarantees correctness.
- SACP replaces agent runtimes.
- SACP solves all memory problems.
- SACP makes agents autonomous.
- SACP is legal or compliance proof.

