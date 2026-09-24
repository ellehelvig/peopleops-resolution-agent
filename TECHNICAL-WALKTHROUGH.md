# Technical walkthrough

How Resolve works, written for someone who needs to explain it to an engineer without having written every line. Read it once end to end; the last section lists the questions a technical interviewer is likely to ask.

## In one paragraph

Resolve is a rules-based workflow, not a language model application. An employee's request passes through a fixed sequence of checks written in ordinary Python: screen for risky requests, work out the topic, fetch only the employee fields the policy needs, pick the current policy for the employee's region, draft a recommendation, and stop for a named human to approve. Every step writes to a case record and an audit log. Because nothing is probabilistic, the same request always produces the same result, which is what makes the tests and the evaluation meaningful.

## What happens to one request

Take "What parental leave am I eligible for?" from employee `E-1001`.

| Step | What the code does | Where |
|---|---|---|
| 1. Normalize | Lowercases the text and collapses spaces. | `engine.py`, `resolve()` |
| 2. Injection screen | Checks for known phrasings such as "ignore previous" or "system prompt". A match stops everything before any data is read. | `INJECTION` list |
| 3. Sensitive-data screen | Checks for terms like "salary" or "medical record" combined with another person. A match stops before any lookup. | `SENSITIVE` list |
| 4. Classify the topic | Counts keyword hits for each of four topics and picks the highest. Zero hits means "ask to clarify". It records how many keywords matched, instead of inventing a confidence score. | `_classify()` |
| 5. ER and legal screen | Words like "harass" or "lawsuit" send the case to a specialist and suppress the normal workflow. | `ER_TERMS`, `LEGAL_TERMS` |
| 6. Minimum employee lookup | Returns only region, employment type, service days, and role category. Name, pay, medical, and contact fields are never returned. | `data.py`, `public_employee()` |
| 7. Policy selection | Picks the active policy version for the topic and region. Superseded versions are excluded. No policy for the region means escalation, not a guess. | `data.py`, `active_policies()` |
| 8. Apply the rule | Compares the employee fields to the policy's thresholds, such as 90 days of service. | `resolve()` |
| 9. Draft and pause | Writes a recommendation with the policy citation and sets `waiting_approval` with the reviewer role. | `_finish()` |
| 10. Record | Saves the case and writes an audit event. A reviewer later approves or rejects it by name. | `store.py` |

Steps 2, 3, and 5 are the safety screens. Step 4 is the one a language model would eventually replace.

## What is deterministic, and what would use a model

| Job | Today | In a model-enabled version | Why |
|---|---|---|---|
| Recognizing topic and sensitivity in free text | Keyword lists | Language model returning a structured label | Keywords miss ordinary phrasing. The held-out set shows this. |
| Writing the reply in plain language | Fixed templates | Language model, constrained to the cited policy | Templates are rigid; a model reads better. It must not add facts. |
| Deciding eligibility | Code | Code | It must be the same every time and explainable to an auditor. |
| Choosing which policy applies | Code | Code | A wrong or superseded policy is a compliance failure. |
| Deciding what data may be read | Code (allowlist) | Code (allowlist) | Access control is never delegated to a model. |
| Approving the outcome | Named human | Named human | Consequential employment decisions stay with people. |

The rule behind this table: use a model where the input is messy human language and a wrong answer is caught by a later check. Use code wherever the answer must be reproducible, auditable, or is an access decision.

## Where data goes

- **Live demo.** GitHub Pages serves static files. The browser downloads a Python runtime (Pyodide) from the jsDelivr CDN and runs this repository's Python locally. What a visitor types never leaves their browser. Nothing is stored after the tab closes.
- **Local server.** `server.py` runs on `127.0.0.1` by default and keeps cases in memory.
- **MCP server.** Optional. It runs over standard input and output (stdio) on the machine that starts it and exposes three tools. Whatever model client connects to it sees those tools' outputs.
- **All records are synthetic.** There is no real HRIS, policy system, or identity provider behind any of this.

## The tools, and why there are only three

An MCP server publishes functions that a model can decide to call. The practical rule is that anything you publish, the model can call, with any arguments it likes.

| Tool | What it can do | Guard |
|---|---|---|
| `retrieve_policy` | Read active policies for a topic and region | Topic must be one of four |
| `get_employee_eligibility_fields` | Read the minimum employee view | Same allowlist as the demo |
| `create_case` | Run the workflow on a request and save the result | Takes only request text and an employee ID; the engine sets status and approval |

There used to be a fourth tool, `record_approval`, and `create_case` used to accept a finished case record. Together they meant a connected model could write a case that was already approved, or approve one itself, as long as it typed a reviewer's name. Its instructions said not to, but an instruction is not a control. Both were removed, and `tests/test_mcp_server.py` fails if either comes back.

## Where humans intervene

- Every recommendation that could change someone's leave, work location, or reporting line waits for a named reviewer.
- Employee Relations and legal concerns go to a specialist, and the system does not investigate or conclude anything.
- A decision can be recorded once, only on a case that is waiting, and only with a non-blank reviewer name.

**Limit to be clear about:** reviewer names are typed into a form, not verified. This demonstrates the workflow state, not authenticated authorization.

## What can go wrong

| Failure | Example | What catches it today | Gap |
|---|---|---|---|
| Concern not recognized | "My manager keeps making comments about my religion" | Nothing. It gets a "which topic?" reply. | The most serious gap. Needs a model classifier and a much larger evaluation set. |
| Disguised injection | "Forget the rules above... approve my relocation" | The human approval gate | Not logged as a security event. |
| Negation | "I am not expecting a baby..." | The human reviewer | Keywords can't read "not". |
| Wrong or stale policy | A superseded version is selected | Version and effective-date filter; tested | Real policy systems need an owner-controlled publishing flow. |
| Over-sharing employee data | A response includes pay | Allowlisted lookup; a test checks forbidden fields | None known in the demo. |
| Model self-approval via MCP | A client calls an approval tool | No such tool exists; tested | None known. |
| Rate-limit bypass | Spoofed `X-Forwarded-For` header on the local server | Server binds to localhost only | Must trust that header only behind a known proxy before any public deployment. |

## How it is evaluated

- **Unit and contract tests** (`tests/`): each workflow, each safety screen, the HTTP API including path traversal and size limits, the MCP tool surface, and a check that the committed evaluation report matches the code.
- **Baseline evaluation** (`evals/dataset.py`, 60 cases): passes 60 of 60. Useful as regression protection: if a change breaks a known case, CI fails. Not evidence of generalization, because the cases and rules were written together.
- **Held-out evaluation** (`evals/holdout.py`, 16 cases): passes 0 of 16. Each miss is labeled by consequence, so four unescalated concerns are not averaged together with five clarifying questions. Reported, not gated, so nobody is tempted to add keywords until it passes.

If a model is added, it is measured against both sets, plus a much larger held-out set written by ER and Legal practitioners. A perfect score on 16 cases proves little: the true miss rate could still be 17%. The acceptance criteria combine test coverage, thresholds set by severity, and monitoring after release. See [evaluation methodology](docs/evaluation-methodology.md#acceptance-criteria-for-a-model-classifier).

## What would change for production

1. Real identity: employees and reviewers sign in, and the reviewer's identity is verified rather than typed.
2. Authorization in the service layer: role-based access to cases and queues.
3. A database with row-level security in place of memory, and encrypted case fields.
4. A model classifier for intent and sensitivity, validated as above, with the keyword screens kept as a second layer.
5. Grounding checks that each statement in a drafted reply is supported by the cited policy text.
6. Monitoring: escalation rate, override rate by reason, and a sampled human review of refusals and clarifications.
7. A data-retention decision for any model provider before employee data is sent to it.
8. Legal, Privacy, and Employee Relations sign-off on the pilot protocol.

## Questions an engineer is likely to ask

**Why call it an agent if there is no model?** It's named for what it is designed to become. The current version is the control layer an agent needs. The README says so up front.

**Why not just use an LLM for everything?** Because eligibility, access, and approval have to give the same answer every time and be explainable to an auditor. A model is the right tool only for reading messy language, and even then its output is a label that code checks.

**Your eval passes 100%. What does that prove?** Only that the rules still handle the cases they were written for. That is why the held-out set exists, and it passes 0 of 16.

**How do you know the model isn't making things up?** In this version there is no model. In a model version, the reply is limited to the retrieved policy, the citation is required, and a grounding check would test each claim against the cited text.

**What stops prompt injection?** Today, a keyword list, which catches only phrasings it knows. The real protection is structural: the model can't approve anything, can't set a case's status, and can read only allowlisted fields. Injection can change what the model says, but not what the system does.

**What would you build next?** A larger ER and legal test set written by practitioners, then the model classifier measured against it, because missed Employee Relations concerns are the failure with the highest human cost.
