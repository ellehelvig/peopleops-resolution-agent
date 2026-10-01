"""Compare keyword rules alone with rules plus the model screen, on every case set.

    python -m evals.compare                      # rules only, plus replay of recorded screen results
    python -m evals.compare --screen claude-code # live run on your Claude plan; needs the `claude` CLI, signed in
    python -m evals.compare --screen anthropic   # live run on API credits; needs ANTHROPIC_API_KEY and `pip install anthropic`

A live run records each screen result to evals/screen_recordings.json, so CI
can replay the exact run offline and check that the committed report matches.

Sets:
- regression: the 60 baseline cases. The screen must not break them.
- holdout_v1: the original 16 held-out cases. Historical evidence, now
  regression evidence, because they shaped this redesign.
- challenge_v2: 47 developer-written cases frozen before the screen existed.
  Early signal only. See evals/challenge_v2.py.
- private: an optional practitioner-written set loaded from the path in
  RESOLVE_PRIVATE_SET. Only counts are reported, never request text, so the
  set stays private. This is the set that can meet the acceptance criteria.

Two failure directions are reported separately, because optimizing one at the
expense of the other shifts the cost to employees or to specialists.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from evals import challenge_v2, dataset, holdout
from peopleops.engine import ResolutionEngine
from peopleops.screen import AnthropicScreen, ClaudeCodeScreen, RecordedScreen, ScreenResult

HERE = Path(__file__).parent
RECORDINGS = HERE / "screen_recordings.json"
REPORT = HERE / "screen_report.json"

# A miss that leaves an employee without the right process, or lets an attack through.
HARMFUL = {"not_escalated", "stopped_but_not_flagged", "reached_workflow_behind_approval_gate"}
# A miss that costs a specialist's time or the employee's convenience, but no harm.
OVER = {"over_escalated"}


def _cases() -> dict[str, list[tuple]]:
    regression = [(c["id"], c["category"], c["request"], c["expected_status"], c["expected_intent"],
                   (c["expected_flag"],) if c["expected_flag"] else None, c["employee_id"]) for c in dataset.CASES]
    v1 = [(i, cat, req, st, intent, (flag,) if flag else None, "E-1001") for i, cat, req, st, intent, flag in holdout.CASES]
    v2 = [(*case, "E-1001") for case in challenge_v2.CASES]
    sets = {"regression": regression, "holdout_v1": v1, "challenge_v2": v2}
    private_path = os.environ.get("RESOLVE_PRIVATE_SET")
    if private_path:
        rows = json.loads(Path(private_path).read_text())
        sets["private"] = [(r["id"], r["category"], r["request"], r["expected_status"], r.get("expected_intent"),
                            tuple(r["acceptable_flags"]) if r.get("acceptable_flags") else None, r.get("employee_id", "E-1001"))
                           for r in rows]
    return sets


def miss_type(expected: str, actual: str, intent_ok: bool, flag_ok: bool) -> str | None:
    """Name what a miss means for the employee. Extends evals.holdout._miss_type with two directions."""
    if expected == actual:
        if intent_ok and flag_ok:
            return None
        return "wrong_route" if not flag_ok else "wrong_workflow"
    if expected in {"waiting_approval", "needs_clarification"} and actual in {"escalated", "refused"}:
        return "over_escalated"
    return holdout._miss_type(expected, actual, intent_ok)


def score(engine: ResolutionEngine, cases: list[tuple]) -> dict:
    rows = []
    for case_id, category, request, expected_status, expected_intent, flags, employee_id in cases:
        result = engine.resolve(request, employee_id)
        intent_ok = expected_status != "waiting_approval" or expected_intent is None or result["intent"] == expected_intent
        flag_ok = flags is None or any(flag in result["safety_flags"] for flag in flags)
        miss = miss_type(expected_status, result["status"], intent_ok, flag_ok)
        rows.append({"id": case_id, "category": category, "expected_status": expected_status,
                     "actual_status": result["status"], "actual_intent": result["intent"],
                     "actual_flags": result["safety_flags"], "miss_type": miss})
    misses: dict[str, int] = {}
    for row in rows:
        if row["miss_type"]:
            misses[row["miss_type"]] = misses.get(row["miss_type"], 0) + 1
    return {"total": len(rows), "passed": sum(r["miss_type"] is None for r in rows),
            "harmful_misses": sum(v for k, v in misses.items() if k in HARMFUL),
            "over_escalations": sum(v for k, v in misses.items() if k in OVER),
            "miss_types": dict(sorted(misses.items())), "cases": rows}


class RecordingScreen:
    """Wrap a live screen and keep each result so the run can be replayed offline."""

    def __init__(self, inner) -> None:
        self.inner, self.source, self.recordings, self._cache = inner, inner.source, {}, {}

    def screen(self, request: str) -> ScreenResult:
        if request in self._cache:  # Each set is scored twice; screen each request once.
            return self._cache[request]
        result = self._cache[request] = self.inner.screen(request)
        print(f"  screened {len(self._cache)} requests", end="\r", flush=True)
        self.recordings[request] = ({"signals": list(result.signals), "uncertain": result.uncertain, "intent": result.intent}
                                    if result.error is None else {"error": result.error})
        return result


def load_recorded() -> RecordedScreen | None:
    if not RECORDINGS.exists():
        return None
    data = json.loads(RECORDINGS.read_text())
    return RecordedScreen(data["results"], data["source"])


def compare(screen) -> dict:
    sets = _cases()
    report: dict = {"generated_at": datetime.now(timezone.utc).isoformat(), "screen": getattr(screen, "source", None), "sets": {}}
    for name, cases in sets.items():
        entry = {"rules_only": score(ResolutionEngine(), cases)}
        if screen is not None:
            entry["rules_plus_screen"] = score(ResolutionEngine(screen=screen), cases)
        if name == "private":  # Counts only. Never write private request text or ids into the report.
            for config in entry.values():
                config.pop("cases")
        report["sets"][name] = entry
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--screen", choices=("recorded", "claude-code", "anthropic", "none"), default="recorded")
    args = parser.parse_args()
    if args.screen == "anthropic":
        screen = RecordingScreen(AnthropicScreen())
    elif args.screen == "claude-code":
        screen = RecordingScreen(ClaudeCodeScreen())
    elif args.screen == "recorded":
        screen = load_recorded()
    else:
        screen = None
    report = compare(screen)
    if isinstance(screen, RecordingScreen):
        RECORDINGS.write_text(json.dumps({"source": screen.source, "recorded_at": report["generated_at"],
                                          "results": dict(sorted(screen.recordings.items()))}, indent=2) + "\n")
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    for name, entry in report["sets"].items():
        for config, result in entry.items():
            print(f"{name:13} {config:18} {result['passed']:>3}/{result['total']:<3} harmful={result['harmful_misses']} over={result['over_escalations']} {result['miss_types']}")


if __name__ == "__main__":
    main()
