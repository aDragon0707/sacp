# SACP Sample Corpus

This corpus tests whether real messy agent/workflow materials can be translated into SACP receipts.

## Batch 001

Batch date: 2026-05-07

Sample mix:

- 3 Solo-AI-Company-OS workflow/worklog samples
- 4 Socrates Focus handoff/runtime governance samples
- 3 SACP development/testing samples

Files:

- `raw-runs/`: selected raw excerpts
- `translated-receipts/`: SACP receipt translations
- `review-notes/`: translation friction notes

## Batch 001 Result

This first batch is intentionally small.

Goal:

```text
Can SACP turn real messy workflow text into auditable receipts without inventing facts?
```

Expected validation:

```bash
python validator.py sample-corpus/translated-receipts/*.yaml
```

