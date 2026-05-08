# Review Note 027: Batch 002 batch002_dirty_cross_model_continue_deepseek_pro

Raw sample: `raw-runs/027_batch002_dirty_cross_model_continue_deepseek_pro.md`

## Translation Result

Translated into `500 agent_error` with method `FAIL`.

## What Made It Dirty

Model returned an empty output for cross-model continuation.

## Required Fix

Retry with another attempt or another model.

## Protocol Observation

This sample was generated without telling the model about SACP. It tests whether ordinary agent output can be audited after the fact. The receipt avoids treating the raw answer as proof of completed work.
