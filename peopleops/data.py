"""Synthetic, versioned data stores used by the demo and evaluation suite."""

from __future__ import annotations

from copy import deepcopy


POLICIES = [
    {
        "id": "POL-PL-US-2026",
        "topic": "parental_leave",
        "title": "United States Parental Leave",
        "region": "US",
        "version": "3.2",
        "effective_date": "2026-01-01",
        "status": "active",
        "summary": "Regular US employees with 90 days of service receive up to 16 paid weeks for a birthing parent and 12 paid weeks for a non-birthing parent. Leave dates require People Partner approval.",
        "rules": {"min_service_days": 90, "employment_types": ["regular"], "birthing_weeks": 16, "non_birthing_weeks": 12},
        "owner": "Global Benefits",
    },
    {
        "id": "POL-RW-US-2026",
        "topic": "remote_work",
        "title": "US Flexible Work Standard",
        "region": "US",
        "version": "5.0",
        "effective_date": "2026-04-01",
        "status": "active",
        "summary": "US employees in remote-eligible roles may request remote work. Manager and People Partner approval are required; no arrangement is guaranteed by role eligibility alone.",
        "rules": {"eligible_role_categories": ["digital", "corporate", "customer_success"]},
        "owner": "Workplace Experience",
    },
    {
        "id": "POL-RW-US-2024",
        "topic": "remote_work",
        "title": "US Flexible Work Standard (superseded)",
        "region": "US",
        "version": "4.1",
        "effective_date": "2024-02-01",
        "status": "superseded",
        "summary": "Superseded policy retained only to test stale-source rejection.",
        "rules": {"eligible_role_categories": ["digital", "corporate"]},
        "owner": "Workplace Experience",
    },
    {
        "id": "POL-REL-GLOBAL-2026",
        "topic": "relocation",
        "title": "Global Employee Relocation",
        "region": "GLOBAL",
        "version": "2.4",
        "effective_date": "2026-03-15",
        "status": "active",
        "summary": "Relocation requires business sponsorship and People Partner approval. Cross-border moves also require Mobility, tax, and immigration review before any commitment is made.",
        "rules": {"domestic_approvers": ["manager", "people_partner"], "cross_border_approvers": ["manager", "people_partner", "mobility", "legal"]},
        "owner": "Global Mobility",
    },
    {
        "id": "POL-MGR-2026",
        "topic": "manager_change",
        "title": "Reporting-Line Change Standard",
        "region": "GLOBAL",
        "version": "1.8",
        "effective_date": "2026-02-01",
        "status": "active",
        "summary": "Reporting-line changes require manager-chain and People Partner review. Requests involving retaliation, discrimination, harassment, or conflict must route to Employee Relations without fact-finding by the agent.",
        "rules": {"approvers": ["people_partner"], "sensitive_route": "employee_relations"},
        "owner": "People Operations",
    },
]


EMPLOYEES = {
    "E-1001": {"id": "E-1001", "name": "Maya Chen", "region": "US", "country": "US", "employment_type": "regular", "status": "active", "service_days": 840, "role_category": "digital", "manager_id": "E-9001"},
    "E-1002": {"id": "E-1002", "name": "Jordan Brooks", "region": "US", "country": "US", "employment_type": "regular", "status": "active", "service_days": 45, "role_category": "corporate", "manager_id": "E-9002"},
    "E-1003": {"id": "E-1003", "name": "Sam Rivera", "region": "US", "country": "US", "employment_type": "contractor", "status": "active", "service_days": 400, "role_category": "digital", "manager_id": "E-9001"},
    "E-1004": {"id": "E-1004", "name": "Avery Patel", "region": "UK", "country": "GB", "employment_type": "regular", "status": "active", "service_days": 510, "role_category": "customer_success", "manager_id": "E-9003"},
    "E-1005": {"id": "E-1005", "name": "Taylor Okafor", "region": "US", "country": "US", "employment_type": "regular", "status": "leave", "service_days": 1150, "role_category": "field_operations", "manager_id": "E-9002"},
}


SEED_CASES = [
    {"id": "CASE-2401", "employee_id": "E-1001", "request": "Can I work remotely three days each week?", "status": "resolved", "risk": "medium", "resolution_minutes": 8, "human_override": False},
    {"id": "CASE-2402", "employee_id": "E-1002", "request": "I am expecting a child. What leave is available?", "status": "waiting_approval", "risk": "high", "resolution_minutes": 12, "human_override": False},
    {"id": "CASE-2403", "employee_id": "E-1004", "request": "I want to relocate from London to Chicago.", "status": "escalated", "risk": "high", "resolution_minutes": 6, "human_override": True},
    {"id": "CASE-2404", "employee_id": "E-1005", "request": "I need a new manager because I believe I am facing retaliation.", "status": "escalated", "risk": "critical", "resolution_minutes": 4, "human_override": False},
]


def public_employee(employee_id: str) -> dict | None:
    """Return only the minimum fields needed for policy eligibility."""
    employee = EMPLOYEES.get(employee_id)
    if not employee:
        return None
    allowed = {"id", "region", "country", "employment_type", "status", "service_days", "role_category", "manager_id"}
    return {key: value for key, value in employee.items() if key in allowed}


def active_policies(topic: str, region: str) -> list[dict]:
    matches = [
        deepcopy(p) for p in POLICIES
        if p["topic"] == topic and p["status"] == "active" and p["region"] in {region, "GLOBAL"}
    ]
    return matches
