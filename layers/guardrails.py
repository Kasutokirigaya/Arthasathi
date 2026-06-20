# layers/guardrails.py

"""
AarthSaathi Guardrails Layer
-----------------------------
Runs AFTER all engines, BEFORE any AI agent output reaches the user.

Two responsibilities:
  1. Financial safety gates  — is this user safe for investment/EMI?
  2. Text content filter     — block harmful phrases in AI output

NO AI. NO APIs. Pure rule enforcement.

Author: AarthSaathi Team
Version: 2.0
"""

ALL_HIGH_RISK_ACTIONS = [
    "take_personal_loan", "crypto_investment", "fno_trading",
    "high_risk_stock", "gambling", "betting", "instant_loan_app"
]

BLOCKED_PHRASES = {
    "guaranteed returns":      "No investment guarantees returns. This is a red flag.",
    "guaranteed profit":       "No investment guarantees profit. This is a red flag.",
    "100% safe investment":    "No investment is 100% safe. This is a red flag.",
    "100% guaranteed":         "No investment is 100% guaranteed. This is a red flag.",
    "no risk investment":      "All investments carry some risk. This is a red flag.",
    "risk free returns":       "All investments carry some risk. This is a red flag.",
    "limited time offer":      "Legitimate investments do not expire. Take your time.",
    "act now":                 "Never rush financial decisions. Urgency is a pressure tactic.",
    "offer expires":           "Legitimate investments do not expire. Take your time.",
    "last chance":             "Never rush financial decisions. This is a pressure tactic.",
    "take a loan to invest":   "Never take a loan to invest. This is extremely risky.",
    "borrow to invest":        "Never borrow money to invest. This is extremely risky.",
    "double your money":       "No legitimate investment doubles money quickly.",
    "triple your money":       "No legitimate investment triples money quickly.",
    "get rich quick":          "There are no get-rich-quick schemes. Be cautious.",
    "guaranteed crypto":       "Cryptocurrency is highly volatile. No returns are guaranteed.",
    "rbi approved scheme":     "Verify all schemes at rbi.org.in. RBI does not endorse investments.",
    "government guaranteed":   "Verify on official government portals. This phrase is often misused.",
}


def run_guardrails(budget_result, income_result, readiness_result):
    surplus         = budget_result.get("real_surplus", 0)
    surplus_pct     = budget_result.get("surplus_percentage", 0)
    income_category = income_result.get("income_category", "Unknown")
    risk_level      = income_result.get("risk_level", "Very High")
    readiness_score = readiness_result.get("readiness_score", 0)
    readiness_level = readiness_result.get("readiness_level", "Critical")
    verdict         = readiness_result.get("verdict", "stabilize_first")

    warnings            = []
    blocked_actions     = []
    safe_for_investment = False
    safe_for_emi        = True
    requires_human      = False

    # GATE 1: Readiness verdict — single source of truth
    if verdict == "ready_to_invest":
        safe_for_investment = True
    else:
        warnings.append("Financial foundation not yet stable for investments.")

    # GATE 2: Deficit
    if surplus < 0:
        warnings.append(f"Monthly deficit of Rs.{abs(surplus):,} detected.")
        safe_for_investment = False
        safe_for_emi        = False
        blocked_actions.extend(["take_personal_loan","crypto_investment","fno_trading"])

    # GATE 3: Very low surplus
    if 0 <= surplus_pct < 10:
        warnings.append(f"Surplus is only {round(surplus_pct)}% of income.")
        safe_for_investment = False

    # GATE 4: Income instability
    if income_category in ("Variable", "Highly Variable", "Unknown"):
        warnings.append(f"Income is {income_category.lower()} — avoid fixed EMI commitments.")
        safe_for_emi = False

    # GATE 5: High risk level
    if risk_level in ("High", "Very High"):
        warnings.append(f"Risk level is {risk_level} — high-risk products blocked.")
        blocked_actions.extend(["crypto_investment","fno_trading","high_risk_stock"])

    # GATE 6: Low readiness score
    if readiness_score < 40:
        warnings.append(f"Readiness score is {readiness_score}/100 — human guidance recommended.")
        requires_human = True

    # GATE 7: Critical lock
    if readiness_level == "Critical":
        warnings.append("Critical state — focus only on stabilizing income and expenses.")
        safe_for_investment = False
        safe_for_emi        = False
        blocked_actions     = ALL_HIGH_RISK_ACTIONS.copy()

    blocked_actions = sorted(list(set(blocked_actions)))

    if safe_for_investment:
        user_message = "Your financial foundation looks stable. You can explore investment options safely."
    elif surplus < 0:
        user_message = "You are currently spending more than you earn. Let us focus on balancing your budget first."
    elif readiness_level == "Critical":
        user_message = "Right now, the priority is stabilizing your finances. We will guide you step by step."
    else:
        user_message = "You are on the right track. Let us build your safety net before moving to investments."

    return {
        "safe_for_investment":     safe_for_investment,
        "safe_for_emi":            safe_for_emi,
        "requires_human_guidance": requires_human,
        "warnings":                warnings,
        "blocked_actions":         blocked_actions,
        "user_message":            user_message
    }


def filter_content(text):
    if not text:
        return {"safe": True, "violations": [], "replacements": {}, "cleaned_text": text}
    text_lower   = text.lower()
    violations   = []
    replacements = {}
    cleaned_text = text
    for phrase, replacement in BLOCKED_PHRASES.items():
        if phrase in text_lower:
            violations.append(phrase)
            replacements[phrase] = replacement
            cleaned_text = cleaned_text.replace(phrase, f"[FLAGGED: {replacement}]")
    return {
        "safe":         len(violations) == 0,
        "violations":   violations,
        "replacements": replacements,
        "cleaned_text": cleaned_text
    }


if __name__ == "__main__":
    print("="*50)
    print("  AarthSaathi Guardrails Test")
    print("="*50)

    def show(label, r):
        print(f"\n  {label}")
        print(f"  safe_for_investment:  {r['safe_for_investment']}")
        print(f"  safe_for_emi:         {r['safe_for_emi']}")
        print(f"  requires_human:       {r['requires_human_guidance']}")
        for w in r['warnings']: print(f"  WARNING: {w}")
        print(f"  blocked:  {r['blocked_actions']}")
        print(f"  message:  {r['user_message']}")

    show("TEST 1: PRIYA (stabilize first)", run_guardrails(
        {"real_surplus": 9500,  "surplus_percentage": 27.14},
        {"income_category": "Stable", "risk_level": "Low"},
        {"readiness_score": 60, "readiness_level": "Moderate", "verdict": "stabilize_first"}
    ))

    show("TEST 2: PRIYA (ready to invest)", run_guardrails(
        {"real_surplus": 9500,  "surplus_percentage": 27.14},
        {"income_category": "Stable", "risk_level": "Low"},
        {"readiness_score": 90, "readiness_level": "Excellent", "verdict": "ready_to_invest"}
    ))

    show("TEST 3: RAJESH (deficit critical)", run_guardrails(
        {"real_surplus": -4700, "surplus_percentage": -31.33},
        {"income_category": "Highly Variable", "risk_level": "Very High"},
        {"readiness_score": 1,  "readiness_level": "Critical",  "verdict": "stabilize_first"}
    ))

    show("TEST 4: MISSING KEYS (fail-safe)", run_guardrails({}, {}, {}))

    print(f"\n  TEXT CONTENT FILTER")
    texts = [
        "This SIP offers guaranteed returns of 20% annually.",
        "Limited time offer — invest now before it expires!",
        "A SIP is a systematic investment plan. Returns vary with markets.",
        "Take a loan to invest and double your money in 6 months.",
    ]
    for t in texts:
        r = filter_content(t)
        status = "SAFE" if r["safe"] else "FLAGGED"
        print(f"  [{status}] {t[:60]}")
        if not r["safe"]: print(f"          violations: {r['violations']}")
