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

## Limitations

This baseline is deterministic and intentionally small. A perfect local score proves regression behavior only—not general language understanding, fairness, legal compliance, or production readiness. Before an LLM-enabled pilot, expand paraphrases, multilingual requests, intersectional slices, policy conflicts, indirect injections, tool errors, and adversarial multi-turn cases. Freeze the dataset before comparing versions and keep a private holdout set.
