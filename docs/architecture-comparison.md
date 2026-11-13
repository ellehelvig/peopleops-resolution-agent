# Architecture comparison and measurement plan

Reviewed 13 November 2026. Production use is withheld.

| Approach | Available evidence | What remains unknown |
|---|---|---|
| Rules only | Current deterministic regression: 60/60 development cases, 1/16 known paraphrases. Original 0/16 preserved. | Independent routing coverage, multilingual performance, field burden. |
| Model routing screen alone | Historical model route outputs exist, but the screen is not a policy-answering or approval system. No standalone workflow pass rate is claimed. | Fresh route-label precision/recall, false refusals, uncertainty, live cost and latency. |
| Rules plus screen | Current offline replay of historical outputs: 55/60 development cases, 15/16 known paraphrases, 46/47 challenge cases. Current added boundary cases lack historical recordings. | Fresh performance with the current prompt, run variation, independent labels, live cost/latency, reviewer workload. |

A replay measures how current code consumes old outputs. It does not call a provider or measure current model behavior. Missing recordings must not be treated as observed model failures or successes. The [current replay report](../evals/screen_report.json) excludes the boundary set because it has no historical recordings. A direct replay command can produce fallback outcomes on that set; those are not model-quality observations.

## Prospective controlled comparison

Freeze one unseen practitioner-authored routing set and a route-level rubric before comparing all three approaches. Score the model screen alone on intent and specialist signals only. Score complete workflow controls separately for rules and the combination; do not credit a standalone screen with policy grounding or authorization it does not implement.

Record actual serving-model ID, provider, prompt hash, code SHA, dataset hash, date, sampling settings, repetitions, timeouts, and missing responses. Run at least three times using isolated harnesses. Keep the independent author and adjudicator separate from implementation and tuning. Any set used for a correction becomes regression material.

Report per-class precision/recall, wrong-specialist routes, false refusals, routine over-escalation, uncertainty, and critical misses with denominators and appropriate confidence intervals. A small handcrafted set cannot estimate a field miss rate. Compare median/p95 wall latency; provider tokens and actual billable spend where exposed; and total reviewer minutes, corrections, and escalation workload. Mark unavailable usage or spend as unavailable rather than zero. Include human adjudication and setup costs in any value estimate.

**Not measured:** fresh live latency, actual provider cost, human review workload, and independent comparative performance. Existing evidence supplies no basis for a cost-saving or production-readiness claim. Use the [pilot kit](practitioner-pilot-kit.md) for observed task effort, and retain all failed runs.
