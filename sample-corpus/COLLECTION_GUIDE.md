# SACP Sample Corpus Collection Guide

This corpus tests whether real messy agent/workflow output can be translated into SACP receipts.

它不是为了制造漂亮样例，而是为了暴露协议在真实材料面前哪里够用、哪里含糊、哪里太重。

## Corpus Structure

```text
sample-corpus/
  raw-runs/
    001_source_title.md
  translated-receipts/
    001_source_title.yaml
  review-notes/
    001_source_title.md
```

Each sample keeps three artifacts:

1. raw original material
2. translated SACP receipt
3. review notes about translation friction

## Source Mix

Target first batch:

```text
5 from Solo-AI-Company-OS
5 from socrates-focus
5 from current SACP development process
5 from fresh model outputs
```

This first implementation may start smaller, but it should preserve the same source categories.

## Selection Criteria

Good raw samples contain at least one of:

- completion claim without clear receipt
- evidence/fact/inference mixing
- memory suggestion or promotion boundary
- unclear next owner
- retry or duplicate handoff behavior
- tool/test result
- human decision boundary
- cross-agent handoff

Bad samples:

- polished final docs with no workflow trace
- pure source code without agent/worklog context
- marketing copy with no work transaction

## Translation Question

For each sample, answer:

```text
Can this raw output become a SACP receipt without inventing facts?
```

If yes, translate it.

If no, produce a blocked receipt and explain what is missing.

## Review Questions

Each review note should answer:

- What did the raw output claim?
- What evidence existed?
- What had to be inferred?
- Was next_owner explicit?
- Was human_decision_required clear?
- Did the SACP fields feel sufficient?
- What protocol friction appeared?

## Pass Criteria

The second-round test passes if:

- at least 10 raw samples are collected
- each has a translated receipt
- each translated receipt passes `validator.py`
- review notes identify real friction instead of pretending everything is clean

