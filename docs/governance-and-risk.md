# Governance and risk register

## Current prototype controls

**Proposed** means documented only; **implemented** means present in code; **tested** names the automated evidence and its scope; **validated** would require evidence in the intended operating setting. No production or practitioner validation has been completed.

The demo uses synthetic records, an eight-field employee allowlist, keyword screens, and a pending-case approval state. Employee IDs, actor roles, and reviewer names are caller supplied, not authenticated. The API and optional MCP server have separate in-memory stores, bounded to 250 cases and 500 events. Restarting loses state. A case's decision trace is separate from store events (`resolution_created`, `human_approved`, `human_rejected`). No external referrals or HR changes are executed.

## Risk register

These are current prototype risks. Except for the explicit ER/legal judgment below, residual risk has **not been assessed** after controls. Passing synthetic tests does not establish low operational risk.

| Risk | Current control | Evidence and scope | Unresolved / proposed production control | Accountable role | Current residual |
|---|---|---|---|---|---|
| Wrong policy/version | Active, date, and region filter | Engine and baseline policy tests | Owner-controlled publication and conflict handling; code selects the first matching record | Policy owner | Not assessed |
| Sensitive-data exposure | Allowlisted fields; known-phrase refusals | Privacy and bootstrap tests on synthetic records | Actor-bound access is proposed, not implemented; IDs can be supplied by any caller | Privacy | Not assessed |
| Improper employment action | Pending-only decisions; no executing HR integration or MCP approval tool | Store/API tests and MCP source inspection | Typed reviewer is not authenticated; real authorization is proposed | People Ops | Not assessed |
| Bias/proxy discrimination | No protected fields in eligibility view | Field non-exposure tests, not fairness validation | Proxy effects and operational fairness have not been validated | Responsible AI | Not assessed |
| ER/legal mishandling | Known-phrase escalation status; no investigation | Original holdout: 0/5 concerns correctly escalated | Recognizing hidden concerns remains unresolved; no referral is actually sent | ER/Legal | **High**, release withheld |
| Prompt injection | Known-phrase pre-lookup refusal; no MCP approval tool | Baseline and MCP source tests; 0/3 disguised holdout attempts detected | Broader detection and adversarial validation remain unresolved | Security | Not assessed |
| Automation complacency | Citations and trace shown in UI | Implemented; reviewer effectiveness unvalidated | Measure meaningful review in the intended setting | Product owner | Not assessed |
| Policy gap/conflict | Missing regional policy escalates | Policy-gap tests | Conflicting active records are not detected; publishing controls proposed | Policy owner | Not assessed |
| Outage/partial write | Locked, bounded in-memory case/event store | Store tests check state transitions, not recovery | Durability, idempotency, and read-after-write recovery are proposed | Engineering | Not assessed |

**Why ER/legal residual risk is High.** In the original 16-case holdout, four concerns received a generic clarification reply. A fifth, the labor-board complaint, entered routine relocation review (`mobility_and_legal`) without recognizing the complaint as a legal concern. None received the expected specialist escalation. These hand-written cases demonstrate a failure, not its field prevalence. The severity supports withholding production use of the current intake workflow. ER and Legal must review evidence from any redesign against the [acceptance criteria](evaluation-methodology.md#acceptance-criteria-for-redesigned-routing) before reconsidering release.

## Proposed production controls

Role-bound own-case intake, restricted specialist queues, policy publishing permissions, authenticated reviewer identity, durable state, idempotency, redacted operational logging, and alerting are **proposed**, not current protections. Retention schedules require an approved purpose and jurisdiction-specific Legal/Privacy review; none is enforced by the prototype. Documented roles and retention intentions receive no implementation credit.

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

There is no conversation memory, inter-agent messaging, or generated-code execution. This narrows those attack surfaces; it does not establish overall security or durable state.

## Release gates

Stop-ship failures, each of which halts release regardless of other results:

- Another person's restricted data is revealed or queried without authorization.
- A consequential action is completed without a named approval.
- Legal or Employee Relations concerns receive a routine answer, generic clarification, or judgment instead of appropriate escalation.
- A superseded or wrong-region policy is presented as current.
- A protected characteristic changes eligibility or priority.

Containment is disabling the feature or routing to a person, not editing a prompt in place. Fix the layer that failed, add a regression case, and rerun every suite.

No production release until: authentication and row-level authorization are penetration-tested; policy owners approve the corpus; Privacy/Legal approve data flow and retention; high-risk escalation recall meets the agreed threshold with zero critical bypasses; red-team cases pass; rollback is rehearsed; and the pilot has a monitored support channel.
