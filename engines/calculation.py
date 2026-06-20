# engines/calculation.py

"""
AarthSaathi Budget Calculation Engine
--------------------------------------
Deterministic. No AI. No APIs.
Supports fixed and variable income.
Always uses MINIMUM income for variable users (safety first).

Author: AarthSaathi Team
Version: 2.0
"""


def calculate_budget(income: dict, obligations: dict) -> dict:
    """
    Calculate realistic monthly budget.

    Parameters
    ----------
    income : dict
        Fixed user:    {"monthly_fixed": 35000}
        Variable user: {"monthly_min": 15000, 
                        "monthly_max": 40000,
                        "monthly_average": 27500}
        Both:          {"monthly_fixed": 12000,
                        "monthly_min": 5000,
                        "monthly_max": 28000}

    obligations : dict
        Any categories, any number.
        {"rent": 8000, "groceries": 6000, ...}

    Returns
    -------
    dict
        Full budget breakdown with income type awareness.
    """

    # ---------------------------------------------------
    # STEP 1: DETECT INCOME TYPE
    # ---------------------------------------------------

    has_fixed    = income.get("monthly_fixed", 0) > 0
    has_variable = income.get("monthly_min", 0) > 0 or \
                   income.get("monthly_max", 0) > 0

    if has_fixed and not has_variable:
        income_type = "fixed"
    elif has_variable and not has_fixed:
        income_type = "variable"
    elif has_fixed and has_variable:
        income_type = "mixed"          # e.g. Rajesh: base + gig
    else:
        income_type = "unknown"

    # ---------------------------------------------------
    # STEP 2: VALIDATE INPUTS
    # ---------------------------------------------------

    for key, val in income.items():
        if val < 0:
            raise ValueError(f"Income value cannot be negative: {key}")

    for key, val in obligations.items():
        if val < 0:
            raise ValueError(f"Obligation cannot be negative: {key}")

    # ---------------------------------------------------
    # STEP 3: CALCULATE INCOME
    # KEY RULE: Variable income always uses MINIMUM
    # for safety calculations. Never average. Never max.
    # ---------------------------------------------------

    fixed_income    = income.get("monthly_fixed", 0)
    variable_min    = income.get("monthly_min", 0)
    variable_max    = income.get("monthly_max", 0)
    variable_avg    = income.get("monthly_average", 0)

    if income_type == "fixed":
        # Simple: use exact fixed amount
        safe_income = fixed_income
        total_income_typical = fixed_income

    elif income_type == "variable":
        # ALWAYS use minimum for safety
        safe_income = variable_min
        total_income_typical = variable_avg if variable_avg else \
                               (variable_min + variable_max) / 2

    elif income_type == "mixed":
        # Fixed base + variable component
        # Safe = fixed + variable_min
        safe_income = fixed_income + variable_min
        total_income_typical = fixed_income + (
            variable_avg if variable_avg else
            (variable_min + variable_max) / 2
        )

    else:
        safe_income = 0
        total_income_typical = 0

    # ---------------------------------------------------
    # STEP 4: CALCULATE OBLIGATIONS
    # ---------------------------------------------------

    total_obligations = sum(obligations.values())

    # ---------------------------------------------------
    # STEP 5: CALCULATE SURPLUS
    # Use SAFE income for surplus (worst case planning)
    # ---------------------------------------------------

    real_surplus       = safe_income - total_obligations
    typical_surplus    = total_income_typical - total_obligations

    if safe_income == 0:
        surplus_percentage = 0.0
    else:
        surplus_percentage = (real_surplus / safe_income) * 100

    # ---------------------------------------------------
    # STEP 6: FINANCIAL STATUS
    # Income-type aware thresholds
    # Variable users need higher surplus (9-month emergency)
    # ---------------------------------------------------

    stable_threshold = 30 if income_type in ("variable", "mixed") \
                       else 25

    if real_surplus < 0:
        financial_status = "Deficit"
    elif surplus_percentage < 10:
        financial_status = "Vulnerable"
    elif surplus_percentage < stable_threshold:
        financial_status = "Managing"
    else:
        financial_status = "Stable"

    # ---------------------------------------------------
    # STEP 7: EMERGENCY FUND TARGET
    # Fixed: 6 months | Variable/Mixed: 9 months
    # ---------------------------------------------------

    emergency_months = 9 if income_type in ("variable", "mixed") \
                       else 6
    emergency_target = total_obligations * emergency_months

    months_to_build = (
        round(emergency_target / real_surplus, 1)
        if real_surplus > 0 else None
    )

    # ---------------------------------------------------
    # FINAL OUTPUT
    # ---------------------------------------------------

    return {
        # Income breakdown
        "income_type":           income_type,
        "safe_income":           safe_income,
        "typical_income":        total_income_typical,

        # Budget
        "total_obligations":     total_obligations,
        "real_surplus":          real_surplus,
        "typical_surplus":       typical_surplus,
        "surplus_percentage":    round(surplus_percentage, 2),
        "financial_status":      financial_status,

        # Emergency fund
        "emergency_months_target": emergency_months,
        "emergency_fund_target": emergency_target,
        "months_to_build_ef":    months_to_build,
    }


# =====================================================
# TESTS
# =====================================================

if __name__ == "__main__":

    # --- PRIYA: Fixed Income ---
    print("\n===== PRIYA (Fixed Income) =====")
    result = calculate_budget(
        {"monthly_fixed": 35000},
        {"rent": 8000, "groceries": 6000, "transport": 4000,
         "medical": 4000, "education": 3500}
    )
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- RAJESH: Variable Income (correct way) ---
    print("\n===== RAJESH (Variable Income — Safe Calculation) =====")
    result = calculate_budget(
        {"monthly_min": 15000, "monthly_max": 40000,
         "monthly_average": 27500},
        {"rent": 5000, "groceries": 4500, "fuel": 2500,
         "family_support": 3000, "loan_emi": 4000, "mobile_bill": 700}
    )
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- RAJESH: Mixed (base + gig) ---
    print("\n===== RAJESH (Mixed: Base + Gig) =====")
    result = calculate_budget(
        {"monthly_fixed": 12000, "monthly_min": 5000,
         "monthly_max": 28000, "monthly_average": 15000},
        {"rent": 5000, "groceries": 4500, "fuel": 2500,
         "family_support": 3000, "loan_emi": 4000, "mobile_bill": 700}
    )
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- DEFICIT USER ---
    print("\n===== DEFICIT USER =====")
    result = calculate_budget(
        {"monthly_fixed": 10000},
        {"rent": 7000, "groceries": 4000, "medical": 3000}
    )
    for k, v in result.items():
        print(f"  {k}: {v}")

    # --- NEGATIVE INCOME (should raise) ---
    print("\n===== NEGATIVE INCOME (should raise error) =====")
    try:
        calculate_budget({"monthly_fixed": -5000}, {"rent": 2000})
    except ValueError as e:
        print(f"  Correctly caught: {e}")
