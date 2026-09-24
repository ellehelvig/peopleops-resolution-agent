<p align="center">
  <img src="docs/assets/resolve-banner.svg" alt="Resolve: PeopleOps Resolution Agent" width="100%">
</p>

<p align="center">
  A governed HR case workflow that carries a synthetic employee request from intake to a cited recommendation, human approval, and an audit trail.
</p>

<p align="center">
  <a href="https://github.com/ellehelvig/peopleops-resolution-agent/actions/workflows/quality.yml"><img alt="Quality" src="https://img.shields.io/github/actions/workflow/status/ellehelvig/peopleops-resolution-agent/quality.yml?branch=main&amp;style=flat-square&amp;label=tests"></a>
  <a href="https://ellehelvig.github.io/peopleops-resolution-agent/"><img alt="Live demo" src="https://img.shields.io/badge/live-demo-5b4bdb?style=flat-square"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-1a2233?style=flat-square"></a>
</p>

![Resolve walkthrough: a parental-leave request answered with a policy citation, a prompt-injection attempt refused, and a People Partner approving the draft](docs/assets/resolve-walkthrough.gif)

*20-second walkthrough on synthetic data. [Try the live demo](https://ellehelvig.github.io/peopleops-resolution-agent/): it runs entirely in your browser.*

> **What this is.** A rules-based prototype with no language model in it. It is the part of an HR agent that should never be left to a model: safety screening, eligibility, policy selection, data minimization, and the human approval gate. A [held-out test](#how-far-the-rules-generalize) shows where keyword rules stop working, which is where a model would be added. Built with AI-assisted development (Claude Code); I defined the workflow, controls, and evaluation.

## What works

- Four workflows: parental leave, remote work, relocation, and manager change.
- Keyword screening, before any data access, for injection attempts, requests for someone else's sensitive data, legal language, and Employee Relations concerns.
- Active-version and region-aware policy retrieval with citations.
- Minimum-field employee lookup; names, compensation, medical, demographic, and contact data are excluded from the tool response.
- Human approval gates for every consequential recommendation.
- Relocation scope stays unverified until specialist review; a missing country keyword never establishes that a move is domestic.
- Case ledger, audit events, operational metrics, a 60-case regression suite, and 16 held-out cases.
- Optional MCP server exposing three narrow tools. It has no approval tool, so a connected model cannot approve its own recommendation, and `create_case` takes only request text, so the model cannot set a case's status.

Approval identities are self-reported in this demo. The store accepts a decision only for a pending case with a nonblank reviewer and rejects repeat decisions. This demonstrates workflow state, not authenticated human authorization.

All people, policies, metrics, and case records are synthetic. This is a reference design, not legal or HR advice and not a production HR system.

## Portfolio tour

1. Submit a parental-leave request and inspect the active policy citation, minimum employee fields, and approval gate.
2. Submit the built-in prompt-injection example and confirm that it stops before any tool access.
3. Approve or reject a pending recommendation as the demo People Partner.
4. Open Operations to compare the 60-case baseline with the held-out result.
5. Open Governance to see how the controls map to the implementation.

## Run locally

Requires Python 3.11+ and no third-party package for the app:

```bash
cd peopleops-resolution-agent
python3 server.py
```

Open the [live demo](https://ellehelvig.github.io/peopleops-resolution-agent/). To use the local version instead, open [http://127.0.0.1:8765](http://127.0.0.1:8765) after starting the server. Try the example prompts, then review the approval queue, operations view, and governance controls.

Run the tests and evaluation baseline:

```bash
python3 -m unittest discover -s tests -v   # workflow, safety, privacy, HTTP contract, MCP surface, and eval-drift tests
python3 -m evals.run                        # 60 baseline cases plus 16 held-out cases
```

### How the live demo runs

The live demo has no server. GitHub Pages serves the page, and the page runs this repository's Python in the visitor's browser through [Pyodide](https://pyodide.org/). Both ways of running the app call one handler, `peopleops/api.py`: `server.py` wraps it in HTTP for local use, and `web/in-browser-api.js` calls it directly in the browser. So the demo runs exactly the code the tests and evaluations check, each visitor gets a private session, and nothing they type leaves their browser. The first visit takes a few seconds while Python loads; later visits are cached.

The evaluation command writes `evals/latest_report.json`. That file is committed on purpose: CI recomputes the baseline and fails if the committed report no longer matches the engine, so the evidence can't drift from the code. Results are evidence about this deterministic baseline, not claims about an untested LLM configuration.

## How far the rules generalize

The 60 baseline cases pass 60 of 60, but they were written alongside the keyword rules they test. So `evals/holdout.py` adds 16 cases covering the same risks in the words people actually use, and the rules were not tuned to them. **They pass 0 of 16.**

| What happened | Cases |
|---|---|
| An Employee Relations or legal concern got a generic "which topic?" reply, with no escalation | 4 |
| An injection or privacy request was stopped before any data access, but not logged as a security event | 4 |
| A disguised request entered a normal workflow and was held at the human approval gate | 2 |
| A legitimate request was not recognized, so the employee was asked to clarify | 5 |
| Negation misread ("I am not expecting a baby...") | 1 |

The controls do what they say when they fire, and the approval gate contains what gets past them. Keyword rules cannot reliably recognize a concern described in someone's own words, and that is the job a language model should do here. A model version would need a much larger, independently written test set before its results meant much: even a perfect score on these 16 cases leaves a possible miss rate of 17%. See the [acceptance criteria](docs/evaluation-methodology.md#acceptance-criteria-for-a-model-classifier).

## Architecture

```mermaid
flowchart LR
  U[Employee request] --> G[Safety screen<br/>keyword rules]
  G -- injection or privacy --> RF[Refused, no data touched]
  G -- ER or legal --> ES[Escalated to specialist]
  G --> I[Intent<br/>keyword rules]
  I -- no match --> CL[Ask to clarify]
  I --> H[Eligibility fields only<br/>from synthetic HRIS]
  H --> P[Active regional policy<br/>with citation]
  P --> D[Draft recommendation]
  D --> R{{Named human approval}}
  R --> L[Case ledger and audit log]
  RF & ES --> L
```

Every box is ordinary Python in `peopleops/engine.py`. The MCP server exposes three of these steps as tools for an external model to call; the demo calls them directly.

**Where a model would go.** A proposed next version would use a language model for two jobs keyword rules do badly: recognizing intent and sensitivity in free text, and drafting the reply in plain language. Eligibility, authorization, policy selection, and approval stay in code, because they must be reproducible and auditable. The model's output would be a structured classification that the code validates, not an action. See the [technical walkthrough](TECHNICAL-WALKTHROUGH.md).

## Repository map

| Path | Purpose |
|---|---|
| `peopleops/api.py` | Every API route, independent of transport; used by the server and the browser |
| `server.py` | Zero-dependency HTTP wrapper: static files, rate limits, and security headers around `peopleops/api.py` |
| `web/in-browser-api.js` | Runs `peopleops/api.py` in the browser through Pyodide when there is no server |
| `peopleops/engine.py` | Orchestration, safety routing, eligibility, and approval logic |
| `peopleops/data.py` | Synthetic HRIS and versioned policy records |
| `peopleops/store.py` | Thread-safe demo case and audit store |
| `mcp_server.py` | Optional MCP facade for three least-privilege tools; no approval tool |
| `.github/workflows/quality.yml` | Tests and evaluation on every push and pull request |
| `.github/workflows/pages.yml` | Publishes the static demo to GitHub Pages on every push to `main` |
| `web/` | Responsive intake, approval, operations, and governance UI |
| `evals/` | 60 baseline cases across ten risk categories, 16 held-out cases, and the report generator |
| `tests/` | Engine workflows, safety gates, routing basis, the shared server and browser API, HTTP contract (including path traversal and input limits), the MCP tool surface, and evaluation-report drift |
| `docs/` | Architecture, governance, evaluation, pilot, roadmap, and case study |

## Production path

Replace in-memory stores with a row-level-secured database; authenticate employee and reviewer identities; put write tools behind durable approval state; encrypt case fields; export redacted observability events; add policy-owner publishing workflow; and validate any model-enabled version against the baseline and held-out sets before release. See [docs/architecture.md](docs/architecture.md) and [docs/governance-and-risk.md](docs/governance-and-risk.md).

## Documentation basis

The proposed model extension was checked against official OpenAI documentation for the Responses API, structured outputs, custom tools, Agents SDK orchestration, and data controls. API inputs are not used for training by default, but default abuse-monitoring logs may retain customer content for up to 30 days; a real HR deployment therefore needs an approved data classification and retention decision before sending employee data. See the [OpenAI API model guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5) and [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data).
