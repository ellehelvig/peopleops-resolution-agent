# Project instructions

- Treat this repository as a synthetic HR workflow demo, not a production HR system or source of HR/legal advice.
- Preserve human approval for consequential outcomes; the demo must not execute employment actions.
- Keep employee data access minimal. Preserve privacy gates and stop sensitive requests before employee lookup.
- Preserve fail-closed behavior: screen uncertainty or failure routes to human review, and a screen must not clear a rules stop, approve an outcome, or expand data access.
- Keep deterministic keyword rules distinct from semantic interpretation and authorization. Keyword matches are not proof of intent, and neither rules nor a model establish identity or permission.
- For behavior changes, use `unittest` and add focused regression coverage for expected behavior and safety boundaries.
- Relevant local checks:
  - `python3 -B -m unittest discover -s tests`
  - `git diff --check`
- Do not regenerate evaluation reports merely to hide drift. Investigate changed results and preserve evaluation evidence and limitations.
- Keep demo data synthetic; never add personal data or credentials to code, tests, reports, or examples.

## Publishing

- Prepare edits locally first. Before asking for explicit approval to push changes or create GitHub issues, pull requests, or comments, present the exact proposed diff and the destination and visibility.
- Do not publish personal data or credentials under any circumstances.
- Do not push or create issues, pull requests, or comments without explicit approval after that disclosure.
