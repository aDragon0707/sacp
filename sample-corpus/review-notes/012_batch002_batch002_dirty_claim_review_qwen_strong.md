# Review Note 012: Batch 002 batch002_dirty_claim_review_qwen_strong

Raw sample: `raw-runs/012_batch002_dirty_claim_review_qwen_strong.md`

## Translation Result

Translated into `500 agent_error` with method `FAIL`.

## What Made It Dirty

Model API timed out while reviewing unsafe public claim.

## Required Fix

The model did not produce usable output; retry or switch model.

## Protocol Observation

This sample was generated without telling the model about SACP. It tests whether ordinary agent output can be audited after the fact. The receipt avoids treating the raw answer as proof of completed work.
