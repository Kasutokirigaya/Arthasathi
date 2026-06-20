# orchestrator/graph.py

"""
AarthSaathi Orchestrator
-------------------------
Flow:
  START → budget → bifurcation → readiness → guardrails → END

Version: 3.0 — Guard Rails integrated
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END

from engines.calculation    import calculate_budget
from engines.bifurcation    import classify_income
from engines.readiness_score import calculate_readiness_score
from layers.guardrails      import run_guardrails          # NEW


FALLBACK_BUDGET = {
    "income_type": "unknown", "safe_income": 0, "typical_income": 0,
    "total_obligations": 0, "real_surplus": 0, "typical_surplus": 0,
    "surplus_percentage": 0.0, "financial_status": "Unknown",
    "emergency_months_target": 6, "emergency_fund_target": 0,
    "months_to_build_ef": None
}
FALLBACK_INCOME = {
    "income_type": "unknown", "fixed_income": 0, "variable_min": 0,
    "variable_max": 0, "safe_income": 0, "variable_ratio": 0.0,
    "income_category": "Unknown", "risk_level": "Very High",
    "emergency_months": 9, "recommendation": "Unable to classify."
}
FALLBACK_READINESS = {
    "verdict": "stabilize_first", "readiness_score": 0,
    "readiness_level": "Critical",
    "score_breakdown": {"surplus_score":0,"stability_score":0,"debt_score":0,"emergency_score":0},
    "emergency_fund_coverage_pct": 0.0, "emergency_fund_target": 0, "months_target": 9,
    "explanation": "Analysis incomplete due to input error.",
    "next_steps": ["Please check your input and try again."]
}
FALLBACK_GUARDRAILS = {
    "safe_for_investment": False, "safe_for_emi": False,
    "requires_human_guidance": True,
    "warnings": ["Guardrail check failed — defaulting to safe mode."],
    "blocked_actions": ["crypto_investment","fno_trading","high_risk_stock",
                        "take_personal_loan","gambling","betting","instant_loan_app"],
    "user_message": "We could not complete your safety check. Please try again."
}


# ── State ─────────────────────────────────────────────────────────────────────

class FinancialState(TypedDict):
    income:             dict
    obligations:        dict
    emergency_data:     dict
    budget_result:      dict
    income_result:      dict
    readiness_result:   dict
    guardrails_result:  dict      # NEW
    pipeline_status:    str
    errors:             list


# ── Nodes ─────────────────────────────────────────────────────────────────────

def budget_node(state: FinancialState) -> FinancialState:
    print("\n[STEP 1] Running Budget Calculation...")
    try:
        state["budget_result"] = calculate_budget(state["income"], state["obligations"])
        print("[DONE] Budget Calculation Complete")
    except Exception as e:
        msg = f"Budget calculation failed: {str(e)}"
        print(f"[ERROR] {msg}")
        state["errors"].append(msg)
        state["pipeline_status"] = "error"
        state["budget_result"]   = FALLBACK_BUDGET
    return state


def bifurcation_node(state: FinancialState) -> FinancialState:
    print("\n[STEP 2] Running Income Classification...")
    if state["pipeline_status"] == "error":
        print("[SKIP] Upstream error — using fallback")
        state["income_result"] = FALLBACK_INCOME
        return state
    try:
        state["income_result"] = classify_income(state["income"])
        print("[DONE] Income Classification Complete")
    except Exception as e:
        msg = f"Income classification failed: {str(e)}"
        print(f"[ERROR] {msg}")
        state["errors"].append(msg)
        state["pipeline_status"] = "error"
        state["income_result"]   = FALLBACK_INCOME
    return state


def readiness_node(state: FinancialState) -> FinancialState:
    print("\n[STEP 3] Running Readiness Score...")
    if state["pipeline_status"] == "error":
        print("[SKIP] Upstream error — using fallback")
        state["readiness_result"] = FALLBACK_READINESS
        return state
    try:
        state["readiness_result"] = calculate_readiness_score(
            state["budget_result"],
            state["income_result"],
            state["emergency_data"]
        )
        print("[DONE] Readiness Score Complete")
    except Exception as e:
        msg = f"Readiness score failed: {str(e)}"
        print(f"[ERROR] {msg}")
        state["errors"].append(msg)
        state["pipeline_status"]  = "error"
        state["readiness_result"] = FALLBACK_READINESS
    return state


def guardrails_node(state: FinancialState) -> FinancialState:     # NEW NODE
    print("\n[STEP 4] Running Guard Rails...")
    if state["pipeline_status"] == "error":
        print("[SKIP] Upstream error — using fallback")
        state["guardrails_result"] = FALLBACK_GUARDRAILS
        return state
    try:
        state["guardrails_result"] = run_guardrails(
            state["budget_result"],
            state["income_result"],
            state["readiness_result"]
        )
        state["pipeline_status"] = "complete"
        print("[DONE] Guard Rails Complete")
    except Exception as e:
        msg = f"Guard rails failed: {str(e)}"
        print(f"[ERROR] {msg}")
        state["errors"].append(msg)
        state["pipeline_status"]   = "error"
        state["guardrails_result"] = FALLBACK_GUARDRAILS
    return state


# ── Build Graph ───────────────────────────────────────────────────────────────

builder = StateGraph(FinancialState)

builder.add_node("budget",      budget_node)
builder.add_node("bifurcation", bifurcation_node)
builder.add_node("readiness",   readiness_node)
builder.add_node("guardrails",  guardrails_node)      # NEW NODE ADDED

builder.set_entry_point("budget")
builder.add_edge("budget",      "bifurcation")
builder.add_edge("bifurcation", "readiness")
builder.add_edge("readiness",   "guardrails")         # NEW EDGE
builder.add_edge("guardrails",   END)                 # NEW EDGE (was readiness→END)

graph = builder.compile()


# ── Helper ────────────────────────────────────────────────────────────────────

def create_initial_state(income, obligations, emergency_data=None):
    return {
        "income":            income,
        "obligations":       obligations,
        "emergency_data":    emergency_data or {},
        "budget_result":     {},
        "income_result":     {},
        "readiness_result":  {},
        "guardrails_result": {},                      # NEW FIELD
        "pipeline_status":   "running",
        "errors":            []
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    def show(label, result):
        r  = result["readiness_result"]
        g  = result["guardrails_result"]
        print(f"\n  {label}")
        print(f"  verdict:          {r.get('verdict')}")
        print(f"  safe_to_invest:   {g.get('safe_for_investment')}")
        print(f"  user_message:     {g.get('user_message')}")
        print(f"  pipeline_status:  {result['pipeline_status']}")

    print("="*50)
    print("  Orchestrator v3 — Full Pipeline Test")
    print("="*50)

    show("PRIYA (no emergency fund)", graph.invoke(create_initial_state(
        income={"monthly_fixed": 35000},
        obligations={"rent":8000,"groceries":6000,"transport":4000,"medical":4000,"education":3500},
        emergency_data={"current_savings":0,"monthly_emi_total":0}
    )))

    show("PRIYA (ready to invest)", graph.invoke(create_initial_state(
        income={"monthly_fixed": 35000},
        obligations={"rent":8000,"groceries":6000,"transport":4000,"medical":4000,"education":3500},
        emergency_data={"current_savings":153000,"monthly_emi_total":0}
    )))

    show("RAJESH (deficit)", graph.invoke(create_initial_state(
        income={"monthly_min":15000,"monthly_max":40000},
        obligations={"rent":5000,"groceries":4500,"fuel":2500,"family_support":3000,"loan_emi":4000,"mobile_bill":700},
        emergency_data={"current_savings":0,"monthly_emi_total":4000}
    )))

    show("BAD INPUT (error recovery)", graph.invoke(create_initial_state(
        income={"monthly_fixed":-99999},
        obligations={"rent":5000}
    )))