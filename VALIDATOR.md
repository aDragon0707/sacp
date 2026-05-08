# SACP Validator

The v0.1 validator is intentionally small.

它不是完整运行时，也不是安全审计器。它只是把 SACP/0.1 的最小协议规则变成可重复执行的本地检查。

## Goals

The validator checks:

- required envelope fields
- required receipt fields
- known methods
- known resource types
- known status codes
- known claim types
- known support status values
- verification shape
- concrete `next_owner`
- extension override attempts
- dirty example expected status presence

## Non-Goals

The validator does not:

- execute agent work
- call models
- verify external facts
- prove correctness
- manage leases in real time
- promote memory
- replace Dirty Run human review

## Usage

Validate one YAML file:

```bash
python validator.py examples/valid_receipt.yaml
```

Validate all examples:

```bash
python validator.py --examples
```

Strict mode:

```bash
python validator.py --examples --strict
```

Strict mode exits non-zero on warnings as well as errors.

## Result Shape

```yaml
file: examples/valid_receipt.yaml
valid: true
errors: []
warnings: []
```

## Design Boundary

This validator is a reference helper, not the protocol.

If the validator and the spec disagree, the spec wins. The validator should then be fixed.

