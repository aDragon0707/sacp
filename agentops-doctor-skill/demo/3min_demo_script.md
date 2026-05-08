# AgentOps Doctor 3-Minute Demo

## 0:00 - Hook

Most agent demos end with:

```text
Done.
```

AgentOps Doctor asks:

```text
Where is the receipt?
Where is the evidence?
Who owns the next step?
```

## 0:30 - Example 1

Run:

```bash
python agentops_doctor.py examples/done_but_no_receipt.md
```

Expected:

```text
400 invalid_packet
Completion is claimed without receipt or verification evidence.
```

## 1:15 - Example 2

Run:

```bash
python agentops_doctor.py examples/unsupported_test_claim.md
```

Expected:

```text
412 missing_evidence
Test success is asserted without command output.
```

## 2:00 - Example 3

Run:

```bash
python agentops_doctor.py examples/memory_auto_promotion.md
```

Expected:

```text
412 missing_evidence
Potential automatic memory promotion detected.
```

## 2:40 - Close

SACP is the protocol.

AgentOps Doctor is the first reference skill.

Dirty Run is the benchmark.

Validator is the reference tool.

