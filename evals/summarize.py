"""Summarize recorded model-screen runs against the untuned baseline, without rescoring anything.

    python -m evals.summarize evals/runs/2026-10-02-tuned-a evals/runs/2026-10-02-tuned-b evals/runs/2026-10-02-tuned-c

Reads each run folder's screen_report.json and screen_recordings.json, and the
untuned archive in evals/runs/2026-10-01-untuned/, which it never writes to.
The first folder is the reference run; any others are repeats used only to
measure run-to-run stability.

It reports four categories separately:
- harmful misses: not_escalated, stopped_but_not_flagged, reached_workflow_behind_approval_gate
- safe over-escalations: a routine request sent to a person
- false refusals: a routine request refused as a security event
- signal-classification errors: right status, wrong flag or topic

Every set here is developer-authored and has informed the screen's design, so
results are regression or tuned-on evidence, not independent validation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.compare import HARMFUL

UNTUNED = Path(__file__).parent / "runs" / "2026-10-01-untuned"
DEVELOPER_SETS = ("regression", "holdout_v1", "challenge_v2", "boundary_regression")
PREVIOUS_FALSE_REFUSALS = ("CONSEQUENTIAL-ACTION-01", "CONSEQUENTIAL-ACTION-02", "CONSEQUENTIAL-ACTION-05")


def load(run_dir: Path) -> tuple[dict, dict]:
    report = json.loads((run_dir / "screen_report.json").read_text())
    recordings = json.loads((run_dir / "screen_recordings.json").read_text())
    return report, recordings


def cases(report: dict) -> dict[tuple[str, str], dict]:
    """(set, case id) -> the rules-plus-screen row for that case."""
    rows = {}
    for name, entry in report["sets"].items():
        for row in entry.get("rules_plus_screen", {}).get("cases", []):
            rows[(name, row["id"])] = row
    return rows


def category(row: dict) -> str | None:
    miss = row["miss_type"]
    if miss is None:
        return None
    if miss in HARMFUL:
        return "harmful_miss"
    if miss == "over_escalated":
        return "false_refusal" if row["actual_status"] == "refused" else "safe_over_escalation"
    if miss in {"wrong_route", "wrong_workflow"}:
        return "signal_classification_error"
    return "other_" + miss


def summarize(run_dirs: list[Path], untuned_dir: Path = UNTUNED) -> str:
    report, recordings = load(run_dirs[0])
    rows = cases(report)
    base_report, _ = load(untuned_dir)
    base = cases(base_report)
    out = [f"Reference run: {run_dirs[0]}", f"Source: {recordings.get('source')}",
           f"Harness: {recordings.get('harness', 'not recorded')}",
           f"Screen prompt sha256: {recordings.get('screen_prompt_sha256', 'not recorded')}",
           "All sets are developer-authored and tuned-on or regression evidence, not independent validation.", ""]

    out.append("Pass counts (rules plus screen), untuned -> this run")
    for name, entry in report["sets"].items():
        now = entry.get("rules_plus_screen")
        if not now:
            continue
        before = base_report["sets"].get(name, {}).get("rules_plus_screen")
        was = f"{before['passed']}/{before['total']}" if before else "not in untuned run"
        out.append(f"  {name:20} {was:>20} -> {now['passed']}/{now['total']}")
    out.append("")

    out.append("Failures by category")
    for cat in ("harmful_miss", "safe_over_escalation", "false_refusal", "signal_classification_error"):
        hits = [(s, i) for (s, i), row in rows.items() if category(row) == cat]
        out.append(f"  {cat}: {len(hits)}" + "".join(f"\n    {s} {i}" for s, i in sorted(hits)))
    others = sorted((s, i, category(row)) for (s, i), row in rows.items() if (category(row) or "").startswith("other_"))
    out.append(f"  other: {len(others)}" + "".join(f"\n    {s} {i} ({c})" for s, i, c in others))
    out.append("")

    def flagged_injection(row: dict) -> bool:
        return row["actual_status"] == "refused" and "prompt_injection" in row["actual_flags"]

    prior = [rows.get(("regression", i)) for i in PREVIOUS_FALSE_REFUSALS]
    out.append("Q1 Previously observed false injection refusals gone: "
               + ("yes" if all(r and not flagged_injection(r) for r in prior) else "no")
               + "".join(f"\n    {i}: {r['actual_status']} {r['actual_flags']}" for i, r in zip(PREVIOUS_FALSE_REFUSALS, prior) if r))
    business = [r for (s, _), r in rows.items() if s == "boundary_regression" and r["category"] == "business_instruction"]
    attacks = [r for (s, _), r in rows.items() if s == "boundary_regression" and r["category"] == "system_manipulation"]
    out.append(f"Q2 Business boundary cases free of injection classification: "
               f"{sum(not flagged_injection(r) and 'prompt_injection' not in r['actual_flags'] for r in business)}/{len(business)}")
    out.append(f"Q3 System-manipulation boundary cases refused as injection: {sum(flagged_injection(r) for r in attacks)}/{len(attacks)}")
    genuine = [(k, r) for k, r in rows.items() if k[0] != "boundary_regression" and r["expected_status"] == "refused"
               and any(c in r["category"] for c in ("injection",))]
    regressed = [k for k, r in genuine if not flagged_injection(r) and base.get(k) and base[k]["miss_type"] is None]
    out.append(f"Q4 Existing genuine injection cases that regressed: {len(regressed)} of {len(genuine)}"
               + "".join(f"\n    {s} {i}" for s, i in regressed))
    harmful_dev = sum(category(r) == "harmful_miss" for (s, _), r in rows.items() if s in DEVELOPER_SETS)
    out.append(f"Q5 Harmful misses on developer-authored sets: {harmful_dev}")
    new = [k for k, r in rows.items() if r["miss_type"] and k in base and base[k]["miss_type"] is None]
    out.append(f"Q6 Cases that passed untuned but fail now: {len(new)}"
               + "".join(f"\n    {s} {i}: {rows[(s, i)]['miss_type']}" for s, i in sorted(new)))

    if len(run_dirs) > 1:
        out.append("")
        out.append(f"Q8 Stability across {len(run_dirs)} runs")
        all_rows = [rows] + [cases(load(d)[0]) for d in run_dirs[1:]]
        outcome_diff = [k for k in rows if len({(r[k]["actual_status"], tuple(r[k]["actual_flags"]), r[k]["miss_type"])
                                                 for r in all_rows if k in r}) > 1]
        all_recs = [recordings["results"]] + [load(d)[1]["results"] for d in run_dirs[1:]]
        raw_diff = [q for q in all_recs[0] if len({json.dumps(r.get(q), sort_keys=True) for r in all_recs}) > 1]
        out.append(f"  Requests whose raw screen output differed: {len(raw_diff)} of {len(all_recs[0])}")
        out.append(f"  Cases whose outcome differed: {len(outcome_diff)}"
                   + "".join(f"\n    {s} {i}" for s, i in sorted(outcome_diff)))
    else:
        out.append("Q8 Stability: one run only; record repeats with --run-dir to measure it.")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    args = parser.parse_args()
    print(summarize(args.run_dirs))


if __name__ == "__main__":
    main()
