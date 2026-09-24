# Executive case study: redesigning HR request resolution

## Opportunity

Routine HR requests often move through fragmented intake, policy search, HRIS lookup, judgment, handoff, and follow-up. Employees experience inconsistent answers; HR teams spend time gathering context; leaders lack outcome and failure data.

## Intervention

Resolve demonstrates a controlled workflow for four common requests. This version is rules-based and uses no language model, so every routing decision is reproducible. The system identifies sensitivity before retrieval, accesses only eligibility fields, grounds its response in an active policy version, pauses consequential recommendations for named approval, and writes an auditable decision record.

## Why it matters

The value is not a conversational front end. It is a redesigned operating model: routine evidence gathering becomes consistent and observable while human experts retain authority for consequential, ambiguous, legal, and employee-relations decisions.

## Evidence today

The working local product includes four workflow paths, three narrow MCP tools, an approval experience, operating metrics, and 60 synthetic regression cases across ten risk categories. Results are reproducible with one command. A separate held-out set of 16 realistically phrased requests passes 0 of 16, and in four of them an Employee Relations or legal concern gets a generic reply instead of an escalation. That gap is the main argument for adding a language-model classifier, and the reason it would need its own evaluation before a pilot. Adoption and time savings remain hypotheses until the practitioner pilot is completed.

## Decision requested

Authorize a synthetic-data practitioner pilot, subject to Privacy/Legal review of the protocol. Success unlocks an authenticated sandbox; failure patterns determine whether the product is narrowed, redesigned, or stopped.
