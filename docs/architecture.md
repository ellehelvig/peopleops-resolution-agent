# Architecture and tool specification

See the single [request-path diagram](../README.md#architecture). This document describes the implemented prototype and separately identifies production design intentions.

## Current operating boundary

The default API, browser demo, and MCP server use keyword classification and direct Python functions over synthetic employee and policy records. The evaluation harness can inject an optional model screen into the same engine; it is not enabled by the default entry points. The engine drafts recommendations and returns a result. API and MCP entry points save results. Approval changes case status only; no HR record change or specialist referral is executed. All caller identities and roles are unverified.

### State and logging

| State | Current contents and lifetime |
|---|---|
| Request | Caller-supplied text, employee ID, and API actor role; not authenticated |
| Case | Result including decision trace, request, employee ID, and any review metadata; bounded to 250 cases in memory |
| Events | `resolution_created`, `human_approved`, `human_rejected`; actor label, time, case ID, and event details; bounded to 500 in memory |
| Policy | Synthetic records in `peopleops/data.py`; active/date/region filtering, then first match; no publishing service or conflict detection |
| Trace | Engine-generated explanations in `decision_trace`, stored with the case; not a separate event per step |
| Conversation memory | None |

The API and optional MCP process each instantiate a separate store. Restart discards state. Creation events record status and policy IDs, not every read or the full policy version; citations in the case carry versions. MCP read tools emit no store events. The bootstrap UI also exposes synthetic names for persona selection; the engine lookup excludes names.

### Optional MCP boundary

| Tool | Actual input and behavior | Current boundary |
|---|---|---|
| `retrieve_policy` | Caller supplies topic and region; unsupported topic returns an empty list | Read-only, no caller authorization |
| `get_employee_eligibility_fields` | Caller supplies employee ID; returns `id`, `region`, `country`, `employment_type`, `status`, `service_days`, `role_category`, `manager_id`; missing ID returns an error object | Field allowlist, not actor-bound access |
| `create_case` | Request text and employee ID; runs the engine and saves its result | Engine determines status; no caller-supplied decision fields |

There is no MCP approval tool. The API decision route accepts only pending cases and a nonblank typed reviewer, once. Source-inspection tests protect the MCP surface; they do not constitute runtime MCP or authenticated authorization validation. API decisions do not operate on the separate MCP store.

## Proposed production controls

Authenticated identities, role/row authorization, durable storage, idempotent writes and recovery, policy-owner publishing and conflict resolution, redacted operational logging, timeouts, expiry, and rollback procedures remain proposals. None should be inferred from current demo state transitions. See the [risk register](governance-and-risk.md) and [release evidence](evaluation-methodology.md).

## Optional model-screen boundary

After keyword injection and sensitive-data stops, the engine classifies the topic and, when supplied, sends request text to a model screen. The screen can replace the topic label or add a refusal, specialist escalation, or uncertainty route. Keyword ER/legal checks still run before employee lookup; the screen cannot clear them. Structured-output validation checks the label contract, not whether the interpretation is safe or correct.

The Anthropic API path sends the text to that provider. The Claude Code path runs a signed-in local CLI whose model request also leaves the machine. Provider terms, retention, account settings, and permission to process the text require review before using anything beyond synthetic examples. No employee record or policy corpus is supplied to the screen by the engine.

Run artifacts are evaluation evidence, not a protected operational audit system. Use synthetic cases in public reports. Do not publish private practitioner sets, raw employee requests, credentials, or provider traces. The preserved first run is untuned, developer-authored evidence; it does not validate the newer prompt boundary or a production deployment.
