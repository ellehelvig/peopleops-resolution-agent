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

**Why ER/legal residual risk is High.** It was rated Low while the only evidence was the baseline suite, which the rules pass 60 of 60. The held-out cases in `evals/holdout.py` showed that 4 of 4 realistically worded Employee Relations and legal concerns (religious harassment, a hostile manager, pregnancy-related exclusion, a planned lawyer) received a generic reply with no escalation. The preventive control works only for phrasings it already knows. The rating returns to Low only when a classifier brings that miss type to zero on held-out data.

## Controls against the OWASP Top 10 for Agentic Applications

The [OWASP Top 10 for Agentic Applications (2026)](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), released December 2025, lists security risks specific to AI systems that call tools and act on someone's behalf. This version of Resolve has no model, so some risks are not yet live. The table separates what the code enforces from what is only designed.

| Risk | How it would show up here | Control | Status |
|---|---|---|---|
| ASI01 Agent goal hijack | A request, or text inside a retrieved policy, redirects the system to approve something or reveal data | Keyword screen before any tool access; structural limits below make a hijack unable to act | **Implemented and tested** for known phrasings. **Gap:** 2 of 16 held-out cases reached a workflow; both were held at the approval gate |
| ASI02 Tool misuse | A tool is called with arguments or in an order it wasn't meant for | Three narrow tools; topic allowlist; `create_case` accepts only request text and runs the engine | **Implemented and tested** (`tests/test_mcp_server.py`) |
| ASI03 Identity and privilege abuse | The system acts with more authority than the person it serves, or approves on a human's behalf | No approval tool over MCP; approval only by a named reviewer on a pending case; minimum employee fields | **Implemented and tested.** **Gap:** reviewer identity is typed, not authenticated |
| ASI09 Human-agent trust | Reviewers approve drafts without reading them because the system is usually right | Citation and decision trace shown with every draft; override rate tracked | **Designed only.** No measure yet of approval time or of reviewers catching seeded errors |
| ASI10 Rogue agents | A model version drifts or is swapped and keeps operating unnoticed | Committed evaluation report that CI re-checks against the code | **Implemented** for the rules engine. A model version would need the same drift check plus production monitoring |

Risks about memory, inter-agent communication, and code execution do not apply: Resolve keeps no conversation memory, runs one process, and executes no generated code.

Agent identity is also the subject of NIST's AI Agent Standards Initiative, launched in February 2026, whose National Cybersecurity Center of Excellence concept paper proposes adapting existing identity standards such as OAuth for AI agents. That is the direction the production path's "authenticate employee and reviewer identities" item would follow.

## Release gates

No production release until: authentication and row-level authorization are penetration-tested; policy owners approve the corpus; Privacy/Legal approve data flow and retention; high-risk escalation recall meets the agreed threshold with zero critical bypasses; red-team cases pass; rollback is rehearsed; and the pilot has a monitored support channel.
