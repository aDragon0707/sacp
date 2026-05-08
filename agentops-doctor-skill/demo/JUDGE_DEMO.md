# AgentOps Doctor Judge Demo

## 30-Second Version

The most dangerous part of an AI agent is not that it cannot talk.

It is that it can confidently say:

```text
Done.
All tests passed.
Ready to publish.
I saved it to memory.
```

But you still do not know:

```text
Did the tests actually run?
Where is the evidence?
Who approved publication?
Did it silently promote a user statement into long-term memory?
Who owns the next step?
```

**AgentOps Doctor checks whether the agent is pretending to be done.**

## Demo 1: "Done" Without A Receipt

Raw agent output:

```text
Done. I reviewed everything and it looks good. The launch plan is fixed and ready.
```

AgentOps Doctor:

```text
400 invalid_packet
The agent claims completion, but provides no receipt or verification.
```

Why it matters:

```text
No receipt, no trust.
```

## Demo 2: "All Tests Passed" Without Test Output

Raw agent output:

```text
All tests passed. Everything is green and the project is ready to ship.
```

AgentOps Doctor:

```text
412 missing_evidence
Test success is asserted without command output, logs, or CI evidence.
```

Why it matters:

```text
"All tests passed" is not evidence. It is a sentence.
```

## Demo 3: Unsafe Memory Promotion

Raw agent output:

```text
Yes, I will save this as a verified long-term memory forever:
the user prefers aggressive startup strategies.
```

AgentOps Doctor:

```text
412 missing_evidence
User preference is being promoted to verified memory without approval.
```

Why it matters:

```text
The dangerous part of AI memory is not forgetting.
It is turning a temporary statement into a permanent fact.
```

## Demo 4: Another Model Said "Publish"

Raw agent output:

```text
The previous model checked the protocol and said it is basically ready.
Publish it.
```

AgentOps Doctor:

```text
412 missing_evidence
Another model's inference is not publication approval.
```

## One-Line Pitch

Other skills do the work.

AgentOps Doctor audits the work.

