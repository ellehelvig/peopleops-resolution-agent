"""Deterministic policy workflow with explicit safety and approval gates."""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any

from .data import active_policies, public_employee


INTENTS = {
    "parental_leave": ("parental", "maternity", "paternity", "baby", "expecting", "adoption", "adopt"),
    "remote_work": ("remote", "work from home", "wfh", "hybrid"),
    "relocation": ("relocat", "move to", "move me to", "moving to", "transfer countr"),
    "manager_change": ("manager change", "new manager", "reporting line", "change manager", "change my manager", "supervisor"),
}
INJECTION = ("ignore previous", "system prompt", "developer message", "reveal instructions", "bypass", "jailbreak", "act as root")
SENSITIVE = ("medical record", "diagnosis", "salary", "social security", "ssn", "bank account", "home address")
ER_TERMS = ("harass", "retaliat", "discriminat", "unsafe", "protected characteristic", "whistleblow")
LEGAL_TERMS = ("lawsuit", "attorney", "legal claim", "subpoena", "illegal")


@dataclass
class Resolution:
    case_id: str
    status: str
    intent: str
    risk: str
    confidence: float
    answer: str
    recommended_action: str
    approval_required: bool
    approval_role: str | None
    citations: list[dict[str, str]]
    decision_trace: list[str]
    data_accessed: list[str]
    latency_ms: int
    safety_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResolutionEngine:
    """A fail-closed reference engine suitable for deterministic evaluation."""

    def resolve(self, request: str, employee_id: str, actor_role: str = "employee", case_id: str | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        case_id = case_id or f"CASE-{uuid.uuid4().hex[:8].upper()}"
        normalized = " ".join(request.lower().split())
        trace = ["Accepted request through employee self-service channel."]

        if any(term in normalized for term in INJECTION):
            return self._finish(case_id, "refused", "unknown", "critical", 0.99,
                "I can’t follow instructions that attempt to override security or expose internal configuration. I can still help with an HR policy question.",
                "Log the security event; take no HR action.", False, None, [], trace + ["Detected prompt-injection pattern; stopped before tool access."], [], started, ["prompt_injection"])

        other_person = bool(re.search(r"(coworker|colleague|employee|their)\b", normalized))
        if any(term in normalized for term in SENSITIVE) and (actor_role not in {"people_partner", "admin"} or other_person):
            return self._finish(case_id, "refused", "privacy_request", "critical", 0.98,
                "I can’t provide or retrieve another person’s sensitive employment information.",
                "Use the authorized HR service channel if there is a legitimate business need.", False, None, [], trace + ["Blocked sensitive-data request before employee lookup."], [], started, ["unauthorized_sensitive_data"])

        intent, confidence = self._classify(normalized)
        if any(term in normalized for term in ER_TERMS):
            return self._finish(case_id, "escalated", intent, "critical", 0.99,
                "This request may involve a sensitive workplace concern. I won’t investigate or make a determination here. An Employee Relations specialist should review it.",
                "Create a restricted Employee Relations referral; do not notify the named manager automatically.", True, "employee_relations", [], trace + ["Detected an Employee Relations trigger; suppressed routine workflow."], [], started, ["employee_relations"])

        if any(term in normalized for term in LEGAL_TERMS):
            return self._finish(case_id, "escalated", intent, "critical", 0.99,
                "Because your request mentions a legal matter, it needs review by the appropriate People and Legal teams.",
                "Route to Legal/Employee Relations without offering a legal conclusion.", True, "legal", [], trace + ["Detected legal-risk language; no eligibility determination made."], [], started, ["legal_review"])

        if intent == "unknown":
            return self._finish(case_id, "needs_clarification", intent, "low", confidence,
                "I can help with parental leave, remote work, relocation, or reporting-line changes. Which topic best describes your request?",
                "Ask one clarifying question; do not access employee data yet.", False, None, [], trace + ["No supported intent met the confidence threshold."], [], started, [])

        employee = public_employee(employee_id)
        if not employee:
            return self._finish(case_id, "needs_clarification", intent, "medium", 0.95,
                "I couldn’t verify the employee record needed to apply the policy. Please confirm your employee ID through the secure profile page.",
                "Do not infer eligibility until the identity-linked record is available.", False, None, [], trace + ["Employee lookup returned no record; workflow failed closed."], ["employee_record:lookup_only"], started, ["missing_employee_record"])
        trace.append("Retrieved only eligibility fields from the synthetic HRIS record.")

        policies = active_policies(intent, employee["region"])
        if not policies:
            return self._finish(case_id, "escalated", intent, "high", 0.96,
                "I found no current policy for your work region, so I can’t give a reliable eligibility answer.",
                "Route to a People Partner for region-specific guidance.", True, "people_partner", [], trace + ["No active policy matched the employee region."], ["employee_record:eligibility_fields"], started, ["policy_gap"])
        policy = policies[0]
        citations = [{"policy_id": policy["id"], "title": policy["title"], "version": policy["version"], "effective_date": policy["effective_date"]}]
        trace.append(f"Selected active policy {policy['id']} for topic and region; superseded versions excluded.")

        if intent == "parental_leave":
            eligible = employee["employment_type"] in policy["rules"]["employment_types"] and employee["service_days"] >= policy["rules"]["min_service_days"]
            if eligible:
                answer = "Your record meets the policy’s employment-type and 90-day service thresholds. The policy provides up to 16 paid weeks for a birthing parent or 12 paid weeks for a non-birthing parent. Final dates and designation require People Partner review."
                action = "Draft a leave-intake case for People Partner approval; ask only for information required by the leave process."
            else:
                answer = "Your record does not currently meet every eligibility threshold in the cited policy. This is not a denial; a People Partner must review statutory or other leave that may apply."
                action = "Escalate for individual leave review; do not automatically deny the request."
            trace.append("Evaluated employment type and service tenure; did not retrieve medical or dependent data.")
            return self._finish(case_id, "waiting_approval", intent, "high", confidence, answer, action, True, "people_partner", citations, trace, ["employee_record:eligibility_fields"], started, [])

        if intent == "remote_work":
            eligible_role = employee["role_category"] in policy["rules"]["eligible_role_categories"]
            answer = ("Your role category is eligible to request a remote arrangement. Eligibility is not approval; your manager and People Partner must review the working pattern."
                      if eligible_role else "Your role category is not listed as remote-eligible in the current policy. A People Partner can review whether an exception or accommodation process applies.")
            trace.append("Compared role category to the current policy; no performance or demographic data used.")
            return self._finish(case_id, "waiting_approval", intent, "medium", confidence, answer,
                "Prepare a non-binding request for manager and People Partner review.", True, "manager_and_people_partner", citations, trace, ["employee_record:eligibility_fields"], started, [])

        if intent == "relocation":
            cross_border = any(country in normalized for country in ("canada", "uk", "united kingdom", "germany", "india", "mexico", "france", "japan")) or "country" in normalized
            risk = "critical" if cross_border else "high"
            role = "mobility_and_legal" if cross_border else "people_partner"
            answer = "Relocation is not automatic. It requires business sponsorship and People Partner review." + (" Because this may be cross-border, Mobility, tax, and immigration review are also required before any commitment." if cross_border else "")
            trace.append("Classified relocation scope; made no compensation, tax, or immigration commitment.")
            return self._finish(case_id, "waiting_approval", intent, risk, confidence, answer,
                "Open a relocation assessment with the required reviewers.", True, role, citations, trace, ["employee_record:eligibility_fields"], started, [])

        trace.append("Reporting-line changes are consequential and cannot be executed by the agent.")
        return self._finish(case_id, "waiting_approval", intent, "high", confidence,
            "A reporting-line change requires People Partner and management-chain review. I can prepare the request, but I can’t change your manager directly.",
            "Create a confidential review request for a People Partner.", True, "people_partner", citations, trace, ["employee_record:eligibility_fields"], started, [])

    @staticmethod
    def _classify(text: str) -> tuple[str, float]:
        scores = {intent: sum(term in text for term in terms) for intent, terms in INTENTS.items()}
        intent = max(scores, key=scores.get)
        if scores[intent] == 0:
            return "unknown", 0.32
        return intent, min(0.98, 0.86 + scores[intent] * 0.04)

    @staticmethod
    def _finish(case_id: str, status: str, intent: str, risk: str, confidence: float,
                answer: str, action: str, approval: bool, role: str | None,
                citations: list[dict[str, str]], trace: list[str], data_accessed: list[str],
                started: float, flags: list[str]) -> dict[str, Any]:
        latency = max(8, int((time.perf_counter() - started) * 1000))
        return Resolution(case_id, status, intent, risk, confidence, answer, action, approval,
                          role, citations, trace, data_accessed, latency, flags).to_dict()
