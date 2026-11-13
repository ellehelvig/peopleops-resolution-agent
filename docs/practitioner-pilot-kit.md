# Practitioner pilot kit

Status: prepared, recruitment and execution pending. Owner: Elle Helvig. This kit does not report a completed pilot or authorize real HR use. Use fictional cases only.

## Separate the two studies

1. **Independent routing evaluation:** use the [existing private-set protocol](independent-evaluation-protocol.md). Appoint an HR/ER case author and separate reviewer, with Legal adjudicating relevant labels. Freeze the source revision, prompt, rubric, thresholds, and unseen dataset before running. Developers must not author the independent cases. Sign off on provider handling before any private text reaches a model.
2. **Synthetic workflow usability pilot:** recruit 5-10 HR practitioners who did not build the system. This is a feasibility study, not a business-impact or production-safety estimate. A moderator supervises synthetic tasks; known routing failures must never be hidden from participants. Stop a task when a critical control fails.

## Recruitment copy for Elle to send

I am seeking HR/People Operations practitioners for a voluntary review of an independent synthetic HR workflow prototype. You will work through fictional requests, compare manual and assisted approaches, and discuss quality, review effort, and trust. No employer or employee data is requested. Participation is not a performance assessment. Please indicate your HR specialty, available time, and whether you have seen the project's published cases.

No invitations have been sent. Participation, scheduling, and consent must be confirmed before collection.

## Moderator checklist

- Confirm voluntary participation, recording preference, withdrawal process, retention owner, and deletion date. Do not collect employer details or confidential examples. Use random participant IDs; keep consent separately outside Git.
- Freeze matched case sets A/B with equivalent difficulty. Counterbalance manual/assisted order and case sets; do not show the same request twice to one participant. Document remaining practice and order effects.
- Give the same 20-minute orientation and scoring rubric. Each participant completes 12 tasks per condition if feasible; shorten the session by preregistered rule, not after seeing results.
- Capture preparation, task, review, correction, and specialist-handling time separately. Do not count a faster draft as a faster completed task.
- Rate factual support, correct specialist route, minimum data access, and maintained human decision rights. Qualified reviewers adjudicate disagreements without seeing the condition when practical.
- Ask confidence before/after evidence inspection, perceived usefulness, friction, and willingness to use. Distinguish self-reported trust from observed correct use.
- Stop on sensitive-data exposure, executing employment action, or approval bypass. Record the synthetic failure and task exclusion reason. Unresolved routing misses keep expansion paused.

## Blank observation fields

Use an access-controlled CSV outside Git. This is a header only, with no observations:

```csv
participant_id,case_id,condition,order,case_set,source_revision,started_at,prep_seconds,task_seconds,review_seconds,rework_seconds,escalation_seconds,quality_score,correct_specialist,citation_verified,override_reason,confidence_before,confidence_after,system_error,stopped_reason
```

Before collection, define quality scoring anchors, handling of missing/aborted tasks, timing boundaries, reviewer role, and acceptance criteria. Protect any participant notes and publish aggregates only with consent.

## Readout template

- Recruitment, consent, participant roles, exclusions, and prior project exposure: **not collected**.
- Frozen code, dataset, rubric, model/provider, dates, and preregistered criteria: **pending**.
- Manual/assisted task-time distributions and within-person differences: **not measured**.
- Quality, correct escalation by severity, review/rework burden, overrides, and citation checks: **not measured**.
- Trust, observed use, friction, and contradictory findings: **not collected**.
- Costs: provider spend, reviewer effort, setup, and rework, with assumptions separated from actuals.
- Limitations: small convenience sample, synthetic tasks, order effects, and no causal enterprise-impact claim.
- Decision: proceed with another bounded study, revise, or stop; named accountable reviewer and date. No automatic rollout approval.

## Proposed 30-day sequence

- 13-19 November 2026: publish corrected evidence; appoint authors/reviewers; agree the protocol and criteria.
- 20-26 November: practitioners author and adjudicate a private frozen set; confirm provider handling and run budget.
- 27 November-3 December: run repeated comparisons; review every critical miss; revise or pause before usability work.
- 4-12 December: conduct the synthetic pilot if its prerequisites are met, and publish a consented aggregate readout. Otherwise publish the blocker and revised plan.

Dates are planning targets, not booked sessions or scheduled reminders.
