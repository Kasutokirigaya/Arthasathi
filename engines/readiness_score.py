# engines/readiness_score.py

"""
AarthSaathi Financial Readiness Engine
--------------------------------------
Deterministic scoring. No AI. No APIs.

Scores on 4 dimensions (25 points each):
  1. Surplus ratio       — how much is left after obligations
  2. Income stability    — how predictable is the income
  3. Debt exposure       — how much goes to loan repayments
  4. Emergency fund      — is there a safety buffer?

HARD GATE:
  Emergency fund coverage < 50% → cannot score above 60
  Regardless of other scores.
  Reason: Investing without emergency fund = dangerous.

Author: AarthSaathi Team
Version: 2.0

Fix from v1:
- Emergency fund added as 4th scoring dimension
- Hard gate: no "Excellent/Good" without emergency fund
- Verdict split: "stabilize_first" vs "ready_to_invest"
- next_steps added to output (actionable guidance)
- debt_ratio added as scoring input
"""


def calculate_readiness_score(
    budget_data: dict,
    income_data: dict,
    emergency_data: dict = None
) -> dict:
    """
    Calculate financial readiness score.

    Parameters
    ----------
    budget_data : dict
        Output from calculation.py
        Required keys:
          surplus_percentage, real_surplus, total_obligations

    income_data : dict
        Output from bifurcation.py
        Required keys:
          income_category, risk_level, emergency_months

    emergency_data : dict (optional)
        User's current emergency fund status
        {
            "current_savings": 50000,
            "monthly_emi_total": 4000
        }
        If not provided, assumes zero savings, zero debt.

    Returns
    -------
    dict
        score, verdict, level, explanation, next_steps
    """

    # ---------------------------------------------------
    # EXTRACT VALUES
    # ---------------------------------------------------

    surplus_pct       = budget_data.get("surplus_percentage", 0)
    real_surplus      = budget_data.get("real_surplus", 0)
    total_obligations = budget_data.get("total_obligations", 0)
    total_income      = budget_data.get("safe_income",
                        budget_data.get("total_income", 1))

    income_category   = income_data.get("income_category", "Variable")
    risk_level        = income_data.get("risk_level", "High")
    emergency_months  = income_data.get("emergency_months", 6)

    if emergency_data is None:
        emergency_data = {}

    current_savings   = emergency_data.get("current_savings", 0)
    monthly_emi       = emergency_data.get("monthly_emi_total", 0)

    # ---------------------------------------------------
    # CALCULATE TARGETS
    # ---------------------------------------------------

    emergency_target  = total_obligations * emergency_months
    emi_ratio         = (monthly_emi / total_income * 100) \
                        if total_income > 0 else 0

    ef_coverage       = (current_savings / emergency_target * 100) \
                        if emergency_target > 0 else 0

    # ---------------------------------------------------
    # DIMENSION 1: SURPLUS RATIO (0–25)
    # How much is genuinely left after all obligations
    # ---------------------------------------------------

    if surplus_pct >= 40:
        d1_surplus = 25
    elif surplus_pct >= 30:
        d1_surplus = 20
    elif surplus_pct >= 20:
        d1_surplus = 15
    elif surplus_pct >= 10:
        d1_surplus = 10
    elif surplus_pct > 0:
        d1_surplus = 5
    else:
        d1_surplus = 0

    # ---------------------------------------------------
    # DIMENSION 2: INCOME STABILITY (0–25)
    # How predictable and reliable is the income
    # ---------------------------------------------------

    stability_map = {
        "Stable":          25,
        "Semi Variable":   18,
        "Variable":        10,
        "Highly Variable":  4,
        "No Income":        0
    }
    d2_stability = stability_map.get(income_category, 10)

    # ---------------------------------------------------
    # DIMENSION 3: DEBT EXPOSURE (0–25)
    # How much income goes to loan repayments
    # ---------------------------------------------------

    if emi_ratio == 0:
        d3_debt = 25          # No debt = full score
    elif emi_ratio <= 20:
        d3_debt = 20          # Healthy debt level
    elif emi_ratio <= 35:
        d3_debt = 12          # Manageable but watch it
    elif emi_ratio <= 50:
        d3_debt = 5           # High debt load
    else:
        d3_debt = 0           # Debt trap territory

    # ---------------------------------------------------
    # DIMENSION 4: EMERGENCY FUND COVERAGE (0–25)
    # What % of target emergency fund exists
    # THIS IS THE MOST IMPORTANT DIMENSION
    # ---------------------------------------------------

    if ef_coverage >= 100:
        d4_emergency = 25     # Fully funded
    elif ef_coverage >= 75:
        d4_emergency = 18
    elif ef_coverage >= 50:
        d4_emergency = 12
    elif ef_coverage >= 25:
        d4_emergency = 6
    else:
        d4_emergency = 0      # No emergency fund

    # ---------------------------------------------------
    # TOTAL SCORE
    # ---------------------------------------------------

    raw_score = d1_surplus + d2_stability + d3_debt + d4_emergency

    # HARD GATE: Emergency fund < 50% caps score at 60
    # Prevents "Excellent" rating without safety buffer
    if ef_coverage < 50:
        raw_score = min(raw_score, 60)

    # Deficit penalty
    if real_surplus < 0:
        raw_score -= 15

    score = max(0, min(raw_score, 100))

    # ---------------------------------------------------
    # READINESS LEVEL
    # ---------------------------------------------------

    if score >= 80:
        readiness_level = "Excellent"
    elif score >= 65:
        readiness_level = "Good"
    elif score >= 45:
        readiness_level = "Moderate"
    elif score >= 25:
        readiness_level = "Low"
    else:
        readiness_level = "Critical"

    # ---------------------------------------------------
    # VERDICT — The key output your app shows Priya
    # ---------------------------------------------------

    if ef_coverage < 100 or real_surplus <= 0:
        verdict = "stabilize_first"
    else:
        verdict = "ready_to_invest"

    # ---------------------------------------------------
    # EXPLANATION — Why this verdict (transparent AI)
    # ---------------------------------------------------

    reasons = []

    if real_surplus < 0:
        reasons.append(
            f"You are spending more than you earn "
            f"by ₹{abs(real_surplus):,}/month."
        )
    if ef_coverage < 100:
        shortfall = emergency_target - current_savings
        months_away = round(shortfall / real_surplus, 1) \
                      if real_surplus > 0 else None
        msg = (
            f"Emergency fund is {round(ef_coverage)}% built "
            f"(target: ₹{emergency_target:,} for "
            f"{emergency_months} months)."
        )
        if months_away:
            msg += f" About {months_away} months away."
        reasons.append(msg)
    if emi_ratio > 35:
        reasons.append(
            f"Loan repayments are {round(emi_ratio)}% of income "
            f"— reduce this before investing."
        )
    if income_category in ("Variable", "Highly Variable"):
        reasons.append(
            "Income is unpredictable — stability needed "
            "before long-term commitments."
        )

    explanation = " ".join(reasons) if reasons else \
                  "Strong financial foundation in place."

    # ---------------------------------------------------
    # NEXT STEPS — Specific and actionable
    # ---------------------------------------------------

    next_steps = []

    if real_surplus < 0:
        next_steps.append(
            "Review obligations and identify any that can be reduced."
        )
    elif ef_coverage < 25:
        next_steps.append(
            f"Start building emergency fund. "
            f"Save ₹{min(real_surplus, 5000):,}/month toward "
            f"target of ₹{emergency_target:,}."
        )
    elif ef_coverage < 100:
        next_steps.append(
            f"Continue building emergency fund. "
            f"₹{int(emergency_target - current_savings):,} more needed."
        )
    else:
        next_steps.append(
            "Emergency fund complete. Ready to explore investments."
        )

    if emi_ratio > 35:
        next_steps.append(
            "Prioritize clearing high-interest loans before new investments."
        )

    if verdict == "ready_to_invest":
        next_steps.append(
            "Proceed to investment education — "
            "learn about SIP, FD, and insurance options."
        )

    # ---------------------------------------------------
    # OUTPUT
    # ---------------------------------------------------

    return {
        # Core verdict
        "verdict":           verdict,
        "readiness_score":   score,
        "readiness_level":   readiness_level,

        # Score breakdown (transparent)
        "score_breakdown": {
            "surplus_score":   d1_surplus,
            "stability_score": d2_stability,
            "debt_score":      d3_debt,
            "emergency_score": d4_emergency,
        },

        # Context
        "emergency_fund_coverage_pct": round(ef_coverage, 1),
        "emergency_fund_target":       emergency_target,
        "months_target":               emergency_months,

        # Guidance
        "explanation":  explanation,
        "next_steps":   next_steps,
    }


# =====================================================
# TESTS
# =====================================================

if __name__ == "__main__":

    # --- PRIYA: Good surplus, zero emergency fund ---
    print("\n===== PRIYA (Zero Emergency Fund) =====")
    result = calculate_readiness_score(
        {"surplus_percentage": 27.14, "real_surplus": 9500,
         "total_obligations": 25500, "safe_income": 35000},
        {"income_category": "Stable", "risk_level": "Low",
         "emergency_months": 6},
        {"current_savings": 0, "monthly_emi_total": 0}
    )
    print(f"  verdict:        {result['verdict']}")
    print(f"  score:          {result['readiness_score']}")
    print(f"  level:          {result['readiness_level']}")
    print(f"  ef_coverage:    {result['emergency_fund_coverage_pct']}%")
    print(f"  breakdown:      {result['score_breakdown']}")
    print(f"  explanation:    {result['explanation']}")
    print(f"  next_steps:     {result['next_steps']}")

    # --- PRIYA: 6 months emergency fund built ---
    print("\n===== PRIYA (Emergency Fund Complete) =====")
    result = calculate_readiness_score(
        {"surplus_percentage": 27.14, "real_surplus": 9500,
         "total_obligations": 25500, "safe_income": 35000},
        {"income_category": "Stable", "risk_level": "Low",
         "emergency_months": 6},
        {"current_savings": 153000, "monthly_emi_total": 0}
    )
    print(f"  verdict:        {result['verdict']}")
    print(f"  score:          {result['readiness_score']}")
    print(f"  level:          {result['readiness_level']}")
    print(f"  explanation:    {result['explanation']}")
    print(f"  next_steps:     {result['next_steps']}")

    # --- RAJESH: Variable income, no savings, has loan ---
    print("\n===== RAJESH (Variable + Loan + No Savings) =====")
    result = calculate_readiness_score(
        {"surplus_percentage": -31.33, "real_surplus": -4700,
         "total_obligations": 19700, "safe_income": 15000},
        {"income_category": "Highly Variable", "risk_level": "Very High",
         "emergency_months": 9},
        {"current_savings": 0, "monthly_emi_total": 4000}
    )
    print(f"  verdict:        {result['verdict']}")
    print(f"  score:          {result['readiness_score']}")
    print(f"  level:          {result['readiness_level']}")
    print(f"  explanation:    {result['explanation']}")
    print(f"  next_steps:     {result['next_steps']}")

    # --- PARTIAL EMERGENCY FUND ---
    print("\n===== PRIYA (Half Emergency Fund Built) =====")
    result = calculate_readiness_score(
        {"surplus_percentage": 27.14, "real_surplus": 9500,
         "total_obligations": 25500, "safe_income": 35000},
        {"income_category": "Stable", "risk_level": "Low",
         "emergency_months": 6},
        {"current_savings": 76500, "monthly_emi_total": 0}
    )
    print(f"  verdict:        {result['verdict']}")
    print(f"  score:          {result['readiness_score']}")
    print(f"  level:          {result['readiness_level']}")
    print(f"  ef_coverage:    {result['emergency_fund_coverage_pct']}%")
    print(f"  next_steps:     {result['next_steps']}")
