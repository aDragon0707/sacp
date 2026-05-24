# SACP HTTP-Like Strategy

Date: 2026-05-24

Architect stance: make SACP as easy to explain, copy, validate, and extend as early HTTP.

## 1. Core Judgment

SACP should not try to become an agent runtime, workflow engine, tracing platform, or compliance product.

It should become the smallest shared protocol for one question:

```text
When an AI agent says "done", can another person or machine audit what happened?
```

The public wedge is already correct:

```text
No receipt, no trust.
```

The next move is to make that wedge behave like HTTP:

```text
simple enough to paste
strict enough to validate
useful enough to copy into other systems
boring enough to become infrastructure
```

## 2. The HTTP Analogy

HTTP spread because it gave people a compact shared grammar:

```http
GET /resource
200 OK
Content-Type: text/html
```

SACP needs the same mental shape:

```yaml
protocol: SACP/0.1
method: COMPLETE
status_code: 200
handoff_id: hf_123
attempt_id: attempt_001
claims:
  - text: "Tests passed."
    claim_type: tool_result
    support_status: supported
verification:
  status: passed
next_owner: Human
human_decision_required: false
```

The protocol should be remembered as:

```text
method + status + receipt
```

Everything else is supporting machinery.

## 3. The One-Sentence Positioning

Use this everywhere:

```text
SACP is a receipt protocol for AI agent work: it records what was claimed, what evidence supports it, who owns the next step, and whether human approval is required.
```

Shorter social version:

```text
Agents say "done". SACP makes them leave a receipt.
```

Developer version:

```text
SACP is HTTP status codes plus receipts for agent handoffs.
```

Boundary version:

```text
SACP does not prove the work is correct. It makes the work auditable.
```

## 4. The Stable Core

To become HTTP-like, SACP should freeze the reader's mental model before expanding fields.

The stable core is:

```text
Handoff  = the work request identity
Attempt  = one try under that request
Receipt  = proof-of-work record for that try
Claim    = auditable assertion
Evidence = source or tool result supporting a claim
Status   = protocol-level outcome
Owner    = who acts next
Boundary = whether human approval is required
```

This gives SACP a durable lifecycle:

```text
handoff -> claim -> execute -> verify -> receipt -> next owner
```

Do not let the public narrative drift into:

```text
agent OS
memory system
workflow engine
observability platform
security framework
legal compliance proof
```

Those can become integrations. They must not become the core.

## 5. The Copy-Paste Protocol Block

SACP needs a canonical block that any agent framework, README, issue, PR, or worklog can copy.

Recommended name:

```text
SACP Receipt Block
```

Recommended Markdown shape:

```markdown
```sacp
protocol: SACP/0.1
type: receipt
method: COMPLETE
status_code: 200
handoff_id: hf_example
attempt_id: attempt_001
agent_id: agent-name
claims:
  - text: "The requested file was updated."
    claim_type: tool_result
    source_id: git_diff
    support_status: supported
verification:
  status: passed
  method: "local diff review"
residual_risk: "No external reviewer has approved the change."
next_owner: Human
human_decision_required: false
```
```

This should become the equivalent of a minimal HTTP response.

If a user understands this one block, they understand the protocol.

## 6. Status Codes As The Memetic Surface

Status codes are SACP's easiest propagation surface.

The codes should be used in posts, examples, issue titles, PR comments, and demos:

```text
200 completed
204 no_action_needed
400 invalid_packet
409 duplicate_handoff
412 missing_evidence
423 lease_active
504 lease_expired
```

The strongest meme is:

```text
"All tests passed." -> 412 missing_evidence unless command output is attached.
```

This is concrete, easy to argue about, and instantly useful.

## 7. Developer Experience Target

SACP should have a three-minute path:

```bash
git clone https://github.com/aDragon0707/sacp.git
cd sacp
python agentops-doctor-skill/agentops_doctor.py agentops-doctor-skill/examples/unsupported_test_claim.md
python validator.py --examples --strict
```

The desired first-time experience:

```text
1. Paste messy agent output.
2. Get status code + diagnosis + required fix.
3. Receive a translated SACP receipt.
```

This is stronger than asking people to adopt a standard.

The ask should stay:

```text
Give me one messy agent output. I will translate it into a receipt.
```

## 8. Naming The Adoption Units

SACP needs adoption units that are smaller than "support the protocol".

Use these units:

| Unit | Meaning | Good first target |
|---|---|---|
| Receipt Block | A pasted SACP receipt in docs, issues, or worklogs | Any agent project |
| Dirty Case | One failure mode with expected status and fix | Eval and benchmark projects |
| Adapter Note | Field mapping from a framework trace/run/task into SACP | LangGraph, CrewAI, AutoGen, MCP, A2A |
| Doctor Run | AgentOps Doctor output for one messy sample | Users with real logs |
| Conformance Claim | A narrow level claim, such as Level 1 or Level 2 | Framework maintainers later |

This lets maintainers say yes without accepting a full dependency.

## 9. CASYS-Inspired Presentation Pattern

CASYS presents real work as concrete use cases and pairs the narrative with practical artifacts such as platforms, MCP workflows, and the "one process, one canvas" idea.

SACP should borrow the structure, not the product category.

Recommended SACP case structure:

```text
One messy output, one receipt.
```

Case page template:

```text
1. Raw agent output
2. What is unsafe or unauditable
3. SACP status code
4. Translated receipt
5. Required fix
6. What this teaches future agents
```

Good case titles:

```text
"Tests passed" without command output
"Ready to publish" without human approval
Memory promoted without approval evidence
Duplicate handoff already completed
Cross-model continuation lost the next owner
```

This is SACP's version of a use-case gallery.

The message should be:

```text
Do not imagine future agents. Inspect one already-running workflow.
```

## 10. Product Surface

SACP should have four public surfaces:

### 10.1 Spec

Purpose:

```text
Define the shared semantics.
```

Keep it small:

```text
SPEC.md
ENVELOPE.md
RECEIPT.md
STATUS_CODES.md
EXTENSIONS.md
DIRTY_RUN_CASES.md
```

### 10.2 AgentOps Doctor

Purpose:

```text
Turn messy output into diagnosis and receipt.
```

This is the practical first tool. It proves the protocol before adapters exist.

### 10.3 Dirty Run

Purpose:

```text
Make failure modes reusable.
```

Dirty Run is the benchmark, but it should be described as state discipline, not model intelligence.

### 10.4 Receipt Gallery

Purpose:

```text
Show real before/after examples.
```

This is what makes SACP spread. People copy examples faster than they read specs.

## 11. What To Build Next

Do not expand the protocol fields yet.

Build the adoption path:

```text
1. Receipt Block docs
2. Receipt Gallery
3. Agent framework adapter notes
4. Dirty Run runner report
5. JSON Schema after field names settle
6. pip package after CLI behavior settles
7. HTTP binding after text semantics are proven
```

Recommended near-term files:

```text
docs/RECEIPT_BLOCK.md
docs/CASE_TEMPLATE.md
docs/ADAPTER_NOTE_TEMPLATE.md
gallery/README.md
gallery/tests-passed-no-output.md
gallery/memory-auto-promotion.md
gallery/publish-without-approval.md
```

## 12. The HTTP Binding Should Wait

SACP should eventually support HTTP bindings, but only after the text semantics are boring and stable.

Future binding:

```http
POST /sacp/handoffs/{handoff_id}/claim
POST /sacp/handoffs/{handoff_id}/attempts/{attempt_id}/complete
GET  /sacp/receipts/{receipt_id}
```

Rule:

```text
HTTP binding transports SACP. It must not redefine SACP.
```

The same receipt must mean the same thing in:

```text
Markdown
YAML
JSON
CLI output
HTTP response
LangGraph trace
MCP tool result
local worklog
```

## 13. Compatibility Rule

SACP needs a simple rule everyone can remember:

```text
Validate core fields. Preserve unknown extensions. Never let extensions override truth.
```

This is the equivalent of HTTP's growth path through headers.

Recommended public wording:

```text
SACP is strict at the core and loose at the edge.
```

## 14. The 30-Day Plan

### Week 1: Make It Copyable

Deliver:

```text
Receipt Block doc
Case Template
3 polished gallery cases
README quick-start tightened around one command
```

Success:

```text
A maintainer can copy a receipt block into their own docs in 10 minutes.
```

### Week 2: Make It Comparable

Deliver:

```text
Dirty Run runner report format
5 additional dirty cases from real logs
Level 1 and Level 2 conformance examples
```

Success:

```text
People can say "this agent output is 412 missing_evidence" and agree on the fix.
```

### Week 3: Make It Portable

Deliver:

```text
Adapter notes for LangGraph, MCP, A2A, OpenAI Agents SDK, and local Markdown worklogs
```

Success:

```text
Each ecosystem can map its native run/task/tool fields into a SACP receipt without runtime changes.
```

### Week 4: Make It Public

Deliver:

```text
Receipt Gallery launch
3 docs-only PRs or issues
5 external messy outputs translated
Batch 003 review note
```

Success:

```text
External users start submitting outputs, not just opinions.
```

## 15. Decision Memo

Core decision:

```text
SACP should become the default receipt layer for AI agent work, not a workflow platform.
```

Current bottleneck:

```text
Distribution and copyability, not protocol depth.
```

Keep:

```text
No receipt, no trust.
Envelope / receipt split.
Status codes.
Dirty Run.
AgentOps Doctor.
Claim type and support status boundaries.
```

Cut:

```text
Any v0.1 expansion that makes the first receipt harder to write.
```

Delay:

```text
HTTP binding, hosted service, auth, database, leaderboard, broad certification.
```

Do today:

```text
Create the canonical Receipt Block doc and one polished gallery case.
```

Do this week:

```text
Publish three before/after receipt cases and ask for five messy outputs.
```

Operating rule:

```text
Every new field must earn its place through a dirty case.
```

Evidence to collect:

```text
External messy outputs, maintainer replies, copied receipt blocks, adapter field mappings, Dirty Run failures.
```

Review date:

```text
2026-06-01
```

