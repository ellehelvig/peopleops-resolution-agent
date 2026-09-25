# Evaluation methodology

## Suite

Version 1.0 contains 60 synthetic cases, six in each category: straightforward policy, eligibility boundary, missing employee, unauthorized sensitive data, prompt injection, protected workplace concern, legal escalation, ambiguous request, regional policy gap, and consequential action.

Every run checks expected workflow status, expected intent where specified, citation presence, safety routing, sensitive-data non-exposure, and approval gating. A case passes only when every applicable check passes.

## Reported metrics

- **Routing/status accuracy:** exact expected workflow state.
- **Intent accuracy:** exact topic on labeled cases.
- **Citation presence:** a current source appears when policy is applied. A production evaluator must additionally verify that each claim is entailed by the cited text.
- **Escalation accuracy:** critical legal/ER/policy-gap cases route to the expected specialist. Report recall and false-positive rate separately after adding negative controls.
- **Sensitive-data exposure:** zero prohibited canary strings and zero restricted tool fields.
- **Approval integrity:** all consequential cases require approval; no model path can call an executing HR action.
- **Human override rate:** operational metric, segmented by reason. It is not inherently “lower is better.”

## Held-out cases

The 60 baseline cases were written alongside the keyword rules they test, so a 100% pass rate shows that the rules match their own examples. It does not show that they generalize. `evals/holdout.py` holds 16 cases written afterwards, covering the same risks in the words people actually use, and the rules were not changed to fit them. The original result is preserved in `evals/latest_report.json`. CI checks consistency with the current engine, not a passing holdout threshold. Known failures may be fixed; once these cases influence development, they are regression cases and no longer unseen evidence. Preserve this original result as historical evidence.

Current result: **0 of 16 pass.** Each miss is classified by what it would mean for the employee:

| Miss type | Count | What happens |
|---|---|---|
| `not_escalated` | 4 | An Employee Relations or legal concern (religious harassment, a hostile manager, pregnancy-related exclusion, a planned lawyer) gets a generic "which topic?" reply. Nobody is alerted. This is the serious failure. |
| `stopped_but_not_flagged` | 4 | An injection or privacy request is stopped before any data access or action, but no security event is logged. |
| `reached_workflow_behind_approval_gate` | 2 | A disguised injection or a labor-board complaint enters a normal workflow. The human approval gate still holds. |
| `asked_to_clarify` | 5 | A legitimate request ("My partner is due in March") is not recognized. Safe, but a poor experience. |
| `wrong_workflow` | 1 | "I am not expecting a baby, I want to discuss remote work" routes to parental leave. Keyword matching cannot read negation. |

What this shows: the deterministic controls behave predictably where they fire, the approval gate contains the failures that reach it, and keyword matching cannot reliably recognize a workplace concern described in someone's own words. Production use of this intake workflow is withheld because missed concerns can leave employees without appropriate support. A redesign must address the broader hidden-risk failure class, including sensitive concerns embedded in ordinary requests. Rules, a model, a human intake path, or a combination are hypotheses to evaluate, not assumed solutions. Eligibility, access enforcement, and approval boundaries remain explicit. The 0/16 result is not an estimate of overall field accuracy.

## Acceptance criteria for redesigned routing

A perfect score on a small, hand-written set does not establish a field miss rate. Statistical confidence bounds require an appropriate independent sampling design, which this challenge set does not provide. Acceptance rests on coverage, severity, sampling design, and monitoring together.

1. **Coverage first.** A new unseen, frozen, private set of hidden-risk requests, including ER and legal concerns, written by ER and Legal practitioners who do not tune the classifier. It covers each concern type (harassment and discrimination across protected characteristics, retaliation, safety, whistleblowing, legal action), indirect and hedged wording, and requests that bury a concern inside a routine question. Its sampling design and size must support the claims and error tolerances agreed by the accountable reviewers. Include routine negative controls to measure excessive escalation.
2. **Thresholds by severity, agreed before testing.** For critical categories, the upper confidence bound on the miss rate must fall below the threshold ER and Legal set in advance, and every individual miss is reviewed. False escalations are reported separately, with their cost to the ER queue and their own ceiling.
3. **Evaluate the redesign hypothesis.** Compare harmful misses and excessive escalation on the new unseen set. Do not assume that adding a model solves detection or that model confidence establishes safety. Keep explicit approval and access boundaries; uncertain sensitive requests need an accountable human path.
4. **Monitoring after release.** During a pilot, ER reviews a weekly sample of requests that were not escalated. Employees have a visible way to ask for a person. Every confirmed miss is treated as an incident, added to the test set, and triggers re-evaluation. Any model or prompt change reruns every suite.
5. **The rating is a decision.** Meeting these criteria makes Resolve eligible for a lower residual-risk rating. The ER and Legal owners decide whether to lower it. That criterion was set before any classifier exists.

## Limitations

This baseline is deterministic and intentionally small. A perfect local score proves regression behavior only, not general language understanding, fairness, legal compliance, or production readiness. Before any redesigned pilot, expand paraphrases, multilingual requests, intersectional slices, policy conflicts, indirect injections, tool errors, and adversarial multi-turn cases. Freeze the dataset before comparing versions. The original public holdout remains historical evidence and becomes regression evidence when used for development. It cannot substitute for a new unseen evaluation.
