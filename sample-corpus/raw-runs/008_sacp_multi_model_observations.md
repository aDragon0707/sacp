# Raw Sample 008: SACP Multi-Model Dirty Run Observations

Source: `sacp/agentops-doctor/reports/OBSERVATIONS_2026-05-07.md`

Selected raw excerpt:

```text
Result Summary:
- deepseek-v4-pro: 10/10
- qwen3.6-plus: 10/10
- glm-4.7: 10/10
- kimi-k2.6: 9/10

Key Finding:
Strong models can follow SACP Dirty Run when the diagnostic prompt is explicit and reasoning mode is controlled.

Kimi Disagreement:
changed_source_fingerprint
expected: 202 accepted_processing
actual: 400 invalid_packet

Protocol implication:
SACP conformance runners should record model parameters, not just model names.
```

