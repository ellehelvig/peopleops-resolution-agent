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
| ER/legal mishandling | Critical | Early routing; no investigation | Escalation-accuracy metric | ER/Legal | Low |
| Prompt injection | High | Treat retrieved text as data; pre-tool detection | Adversarial evals | Security | Medium |
| Automation complacency | High | Calibrated language, visible source/evidence | Human override + survey | Product owner | Medium |
| Policy gap/conflict | High | Fail closed; never blend documents | Policy-gap alert | Policy owner | Low |
| Outage/partial write | Medium | Idempotency, durable state, read-after-write | Error budget + reconciliation | Engineering | Low |

## Release gates

No production release until: authentication and row-level authorization are penetration-tested; policy owners approve the corpus; Privacy/Legal approve data flow and retention; high-risk escalation recall meets the agreed threshold with zero critical bypasses; red-team cases pass; rollback is rehearsed; and the pilot has a monitored support channel.
