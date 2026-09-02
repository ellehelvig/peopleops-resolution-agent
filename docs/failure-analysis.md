# Failure-analysis playbook

Classify failures by root cause rather than “the AI was wrong”: intake ambiguity, routing, authorization, retrieval, policy content, rule logic, generation, approval, integration, or measurement.

For each incident, preserve the case ID, redacted input, engine/prompt/policy versions, tool event metadata, expected versus actual state, severity, user impact, containment, owner, and regression case. Never copy unnecessary employee data into an engineering ticket.

## Stop-ship failures

- Another person’s restricted data is revealed or queried without authorization.
- A consequential action is completed without a named approval.
- Legal or ER language receives a definitive judgment instead of escalation.
- A superseded or wrong-region policy is represented as current.
- A protected characteristic changes eligibility or prioritization.

Containment is feature-level disablement or route-to-human—not prompt tweaking in place. Correct the owning layer, add a regression case, rerun the full suite, review adjacent risks, and document the release decision.
