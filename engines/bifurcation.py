# engines/bifurcation.py

"""
AarthSaathi Income Bifurcation Engine
--------------------------------------
Classify income stability and risk.
Feeds emergency fund targets to Readiness Score Engine.

NO AI. NO APIs. Pure deterministic rules.

Author: AarthSaathi Team
Version: 2.0

Key fix from v1:
- Negative income raises ValueError (no silent errors)
- Zero income handled as its own category
- Keys aligned with calculation.py (monthly_min/max)
- emergency_months added to output for Readiness Engine
"""


def classify_income(income: dict) -> dict:
    """
    Classify income type and stability.

    Parameters
    ----------
    income : dict
        Fixed user:
            {"monthly_fixed": 35000}

        Variable user:
            {"monthly_min": 15000, "monthly_max": 40000}

        Mixed user (base + gig):
            {"monthly_fixed": 12000,
             "monthly_min": 5000, "monthly_max": 20000}

    Returns
    -------
    dict
        Full classification with emergency fund target.
    """

    # ---------------------------------------------------
    # STEP 1: EXTRACT & VALIDATE
    # ---------------------------------------------------

    monthly_fixed = income.get("monthly_fixed", 0)
    monthly_min   = income.get("monthly_min", 0)
    monthly_max   = income.get("monthly_max", 0)

    # Validate — no silent negative processing
    for key, val in income.items():
        if val < 0:
            raise ValueError(
                f"Income value cannot be negative: {key} = {val}"
            )

    # ---------------------------------------------------
    # STEP 2: HANDLE ZERO INCOME (special case)
    # ---------------------------------------------------

    if monthly_fixed == 0 and monthly_min == 0 and monthly_max == 0:
        return {
            "income_type":         "none",
            "fixed_income":        0,
            "variable_min":        0,
            "variable_max":        0,
            "safe_income":         0,
            "variable_ratio":      0.0,
            "income_category":     "No Income",
            "risk_level":          "Critical",
            "emergency_months":    12,
            "recommendation": (
                "No income detected. Please check your input. "
                "Focus on income stability before any financial planning."
            )
        }

    # ---------------------------------------------------
    # STEP 3: CALCULATE VARIABLE RATIO
    # Uses max as the "potential variable" component
    # relative to total possible income
    # ---------------------------------------------------

    safe_income   = monthly_fixed + monthly_min
    total_max     = monthly_fixed + monthly_max

    # Variable component = what fluctuates above minimum
    variable_component = monthly_max - monthly_min

    if total_max == 0:
        variable_ratio = 0.0
    else:
        variable_ratio = (variable_component / total_max) * 100

    # ---------------------------------------------------
    # STEP 4: CLASSIFY CATEGORY
    # ---------------------------------------------------

    if monthly_min == 0 and monthly_max == 0:
        # Pure fixed salary — no variable component
        category = "Stable"

    elif variable_ratio <= 20:
        category = "Semi Variable"

    elif variable_ratio <= 60:
        category = "Variable"

    else:
        category = "Highly Variable"

    # ---------------------------------------------------
    # STEP 5: RISK LEVEL
    # ---------------------------------------------------

    risk_map = {
        "Stable":          "Low",
        "Semi Variable":   "Moderate",
        "Variable":        "High",
        "Highly Variable": "Very High"
    }
    risk_level = risk_map[category]

    # ---------------------------------------------------
    # STEP 6: EMERGENCY FUND MONTHS
    # Stable/Semi = 6 months (predictable income)
    # Variable/Highly Variable = 9 months (unpredictable)
    # ---------------------------------------------------

    emergency_months = 6 if category in ("Stable", "Semi Variable") \
                       else 9

    # ---------------------------------------------------
    # STEP 7: RECOMMENDATION
    # ---------------------------------------------------

    recommendations = {
        "Stable": (
            "Income is predictable. Eligible for long-term "
            "commitments like SIPs and EMIs after emergency fund is built."
        ),
        "Semi Variable": (
            "Income is mostly stable with some variation. "
            "Build a 6-month emergency fund before any investments."
        ),
        "Variable": (
            "Income fluctuates significantly. Build a 9-month "
            "emergency fund first. Avoid fixed EMI commitments."
        ),
        "Highly Variable": (
            "Income is highly unpredictable. Focus entirely on "
            "building a 9-month emergency buffer. "
            "No fixed financial commitments until income stabilises."
        )
    }
    recommendation = recommendations[category]

    # ---------------------------------------------------
    # OUTPUT — aligned with calculation.py key names
    # ---------------------------------------------------

    return {
        "income_type":       "fixed" if category == "Stable" else "variable",
        "fixed_income":      monthly_fixed,
        "variable_min":      monthly_min,
        "variable_max":      monthly_max,
        "safe_income":       safe_income,
        "variable_ratio":    round(variable_ratio, 2),
        "income_category":   category,
        "risk_level":        risk_level,
        "emergency_months":  emergency_months,
        "recommendation":    recommendation
    }


# =====================================================
# TESTS
# =====================================================

if __name__ == "__main__":

    # --- Priya: Pure fixed ---
    print("\n===== PRIYA (Fixed Salary) =====")
    result = classify_income({"monthly_fixed": 35000})
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- Rajesh: Variable gig worker ---
    print("\n===== RAJESH (Variable Gig Worker) =====")
    result = classify_income({"monthly_min": 15000, "monthly_max": 40000})
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- Rajesh: Mixed (base + gig) ---
    print("\n===== RAJESH (Mixed: Base + Gig) =====")
    result = classify_income({
        "monthly_fixed": 12000,
        "monthly_min": 3000,
        "monthly_max": 20000
    })
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- Zero income ---
    print("\n===== ZERO INCOME =====")
    result = classify_income({})
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- Negative income (should raise) ---
    print("\n===== NEGATIVE INCOME (should raise) =====")
    try:
        classify_income({"monthly_fixed": -5000})
    except ValueError as e:
        print(f"  Correctly caught: {e}")

    # --- Integration check: output feeds into calculation.py ---
    print("\n===== INTEGRATION CHECK =====")
    bifurcation_out = classify_income({
        "monthly_fixed": 12000,
        "monthly_min": 3000,
        "monthly_max": 20000
    })
    print(f"  emergency_months ready for Readiness Engine: "
          f"{bifurcation_out['emergency_months']}")
    print(f"  safe_income ready for Calculation Engine: "
          f"{bifurcation_out['safe_income']}")
    print(f"  income_type ready for Readiness Engine: "
          f"{bifurcation_out['income_type']}")
