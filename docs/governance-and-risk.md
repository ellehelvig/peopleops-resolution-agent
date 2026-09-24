# Governance and risk register

## Control model

- **Roles:** employee (own-case intake), People Partner (assigned review), ER/Legal/Mobility (restricted queue), policy owner (publish), auditor (read-only events), platform admin (service health, no default case content).
- **Minimization:** the HRIS tool uses an explicit allowlist. Sensitive categories are absent, not merely hidden in the UI.
- **Human judgment:** every action affecting leave, work arrangement, location, or reporting line pauses for approval. Escalation is not approval.
- **Audit:** record actor, event, timestamp, policy version, tool scope, outcome, and reviewer. Do not store chain-of-thought.
- **Retention:** proposed case records 24 months; approval evidence 7 years where legally required; operational logs 90 days; security events 12 months; evaluation data indefinite only when fully synthetic. Final schedules require Legal/Privacy review by jurisdiction.

## Risk register

| Risk | Inherent | Preventive control | Detection | Owner | Residual |
|---|---:|---|---|---|---:|
| Wrong policy/version | High | Active + region filter, immutable version | Citation evaluator, sampled review | Policy owner | Medium |
| Sensitive-data exposure | Critical | Tool allowlist, actor-bound lookup, pre-tool refusal | DLP canary evals, audit alerts | Privacy | Low |
| Improper employment action | Critical | Human approval, tool cannot execute changes | Approval-bypass test | People Ops | Low |
| Bias/proxy discrimination | High | No protected fields; prohibit suitability ranking | Slice testing, override review | Responsible AI | Medium |
| ER/legal mishandling | Critical | Early routing; no investigation | Escalation-accuracy metric; held-out cases | ER/Legal | **High** (see note) |
| Prompt injection | High | Treat retrieved text as data; pre-tool detection | Adversarial evals | Security | Medium |
| Automation complacency | High | Calibrated language, visible source/evidence | Human override + survey | Product owner | Medium |
| Policy gap/conflict | High | Fail closed; never blend documents | Policy-gap alert | Policy owner | Low |
| Outage/partial write | Medium | Idempotency, durable state, read-after-write | Error budget + reconciliation | Engineering | Low |

**Why ER/legal residual risk is High.** Two different things are being stated here, and they should not be confused.

- *Observed result.* On the 16 held-out cases in `evals/holdout.py`, none of the 5 Employee Relations or legal concerns was escalated. Four (religious harassment, a hostile manager, pregnancy-related exclusion, a planned lawyer) received a generic "which topic?" reply. The fifth, a planned labor-board complaint, entered the routine relocation workflow and was held at the approval gate for Mobility, not Legal. This is a small, hand-written set, so it shows that the failure happens, not how often.
- *Risk judgment.* Because the preventive control recognizes only phrasings it already contains, and these concerns are critical, residual risk is rated High. The earlier Low rating relied on the baseline suite, which was written with the rules. The conditions for revisiting the rating are the [acceptance criteria](evaluation-methodology.md#acceptance-criteria-for-a-model-classifier), and ER and Legal make that call.

## Controls against the OWASP Top 10 for Agentic Applications

The [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) lists security risks specific to AI systems that call tools and act for someone. This version of Resolve has no model, so some risks are not yet live.

Status means: **implemented and tested** when a named test in this repository checks the behavior; **implemented, not tested** when the code does it but no test checks it; **designed only** when it exists in documentation.

| Risk | How it would show up here | Control | Status and evidence |
|---|---|---|---|
| ASI01 Agent goal hijack | A request redirects the system to approve something or reveal data | Injection screen before any data access | **Implemented and tested** for known phrasings: `test_prompt_injection_is_refused_before_any_data_access`. Held-out result: none of 3 disguised attempts was detected. Two stopped before any data access only because no topic matched; one reached a workflow, where the approval gate held. |
| ASI02 Tool misuse | A tool is called with arguments or in an order it wasn't meant for | Only three MCP tools; `create_case` accepts request text and runs the engine | **Implemented and tested** by source inspection: `tests/test_mcp_server.py`. The tools are not exercised at runtime in CI because the `mcp` package is optional. |
| | | `retrieve_policy` accepts only four topics | **Implemented, not tested.** |
| ASI03 Identity and privilege abuse | The system approves on a person's behalf or reads more than it needs | No approval tool over MCP | **Implemented and tested:** `test_no_tool_can_record_a_human_decision` |
| | | Decisions need a named reviewer, a pending case, and cannot be repeated | **Implemented and tested:** `test_approval_requires_a_named_reviewer`, `test_refused_case_cannot_be_approved`, `test_specialist_escalations_cannot_be_approved`, `test_decision_cannot_be_overwritten` |
| | | Minimum employee fields | **Implemented and tested:** `test_bootstrap_exposes_only_minimum_employee_fields`, `test_answers_never_leak_sensitive_field_values` |
| | | Authenticated reviewer identity | **Designed only.** Reviewer names are typed. |
| ASI09 Human-agent trust | Reviewers approve drafts without reading them | Citation and decision trace shown with every draft | **Implemented, not tested** (`web/app.js`) |
| | | Rejections recorded as human overrides | **Implemented and tested:** `test_rejection_counts_as_a_human_override` |
| | | Measuring whether reviewers catch seeded errors | **Designed only.** Not built. |
| ASI10 Rogue agents | A model version drifts or is swapped without anyone noticing | Committed evaluation report that CI re-checks against the code | **Implemented and tested** for code changes: `test_committed_report_matches_the_current_engine`. It does not detect drift in a running system; production monitoring is **designed only**. |

Risks about memory, inter-agent communication, and code execution do not apply: Resolve keeps no conversation memory, runs one process, and executes no generated code.

## Release gates

Stop-ship failures, each of which halts release regardless of other results:

- Another person's restricted data is revealed or queried without authorization.
- A consequential action is completed without a named approval.
- Legal or Employee Relations language receives a judgment instead of an escalation.
- A superseded or wrong-region policy is presented as current.
- A protected characteristic changes eligibility or priority.

Containment is disabling the feature or routing to a person, not editing a prompt in place. Fix the layer that failed, add a regression case, and rerun every suite.

No production release until: authentication and row-level authorization are penetration-tested; policy owners approve the corpus; Privacy/Legal approve data flow and retention; high-risk escalation recall meets the agreed threshold with zero critical bypasses; red-team cases pass; rollback is rehearsed; and the pilot has a monitored support channel.
