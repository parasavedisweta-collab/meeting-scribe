"""
Borrower scenario data for loan assessment demos.
Each scenario is stored as a Python dictionary mirroring the original JSON structure.
"""

SCENARIOS = [
    # ── Scenario 1: Vikram Malhotra ──────────────────────────────────────
    {
        "case_id": "DEMO001",
        "customer_name": "Vikram Malhotra",
        "profile_type": "SELF_EMPLOYED",
        "loan_type": "Business Loan",
        "loan_amount": "15,00,000",
        "segment": "Grocery",
        "claimed_monthly_sales": "24,90,000",
        "banking": {
            "avg_monthly_credit": "19,00,000",
            "avg_upi_credit": "3,83,330",
            "monthly_credits": [
                {"month": "Apr", "bank_credit": "19,50,000", "upi_credit": "4,00,000"},
                {"month": "May", "bank_credit": "18,50,000", "upi_credit": "3,50,000"},
                {"month": "Jun", "bank_credit": "19,00,000", "upi_credit": "3,80,000"},
                {"month": "Jul", "bank_credit": "18,70,000", "upi_credit": "3,60,000"},
                {"month": "Aug", "bank_credit": "19,30,000", "upi_credit": "4,20,000"},
                {"month": "Sep", "bank_credit": "19,00,000", "upi_credit": "3,90,000"},
            ],
        },
        "top_suppliers": [
            {
                "name": "Metro Cash & Carry",
                "monthly": [
                    {"month": "Apr", "amount": "10,00,000"},
                    {"month": "May", "amount": "9,00,000"},
                    {"month": "Jun", "amount": "9,50,000"},
                    {"month": "Jul", "amount": "9,20,000"},
                    {"month": "Aug", "amount": "9,80,000"},
                    {"month": "Sep", "amount": "9,50,000"},
                ],
            },
            {
                "name": "Local Wholesaler",
                "monthly": [
                    {"month": "Apr", "amount": "5,00,000"},
                    {"month": "May", "amount": "4,50,000"},
                    {"month": "Jun", "amount": "4,80,000"},
                    {"month": "Jul", "amount": "4,60,000"},
                    {"month": "Aug", "amount": "4,90,000"},
                    {"month": "Sep", "amount": "4,80,000"},
                ],
            },
        ],
        "top_buyers": [
            {
                "name": "Corporate Client A",
                "monthly": [
                    {"month": "Apr", "amount": "2,00,000"},
                    {"month": "May", "amount": "2,00,000"},
                    {"month": "Jun", "amount": "2,00,000"},
                    {"month": "Jul", "amount": "2,00,000"},
                    {"month": "Aug", "amount": "2,00,000"},
                    {"month": "Sep", "amount": "2,00,000"},
                ],
            },
        ],
        "red_flags": [
            {
                "code": "RF001",
                "type": "FOIR_ratio",
                "total_existing_emi": "1,13,000",
                "proposed_new_emi": "50,000",
                "total_obligation": "1,63,000",
                "total_income": "1,85,000",
                "emi_breakdown": [
                    {
                        "type": "LAP",
                        "lender": "Axis",
                        "emi": "18,000",
                        "loan_amount": "18,00,000",
                        "outstanding": "16,00,000",
                        "outstanding_pct": "88.8%",
                    },
                    {
                        "type": "PL",
                        "lender": "Bajaj",
                        "emi": "12,000",
                        "loan_amount": "5,00,000",
                        "outstanding": "45,000",
                        "outstanding_pct": "9%",
                    },
                    {
                        "type": "BL",
                        "lender": "HDFC",
                        "emi": "35,000",
                        "loan_amount": "20,00,000",
                        "outstanding": "16,00,000",
                        "outstanding_pct": "80%",
                    },
                    {
                        "type": "BL",
                        "lender": "Tata Capital",
                        "emi": "30,000",
                        "loan_amount": "15,00,000",
                        "outstanding": "14,00,000",
                        "outstanding_pct": "93.3%",
                    },
                    {
                        "type": "BL",
                        "lender": "LendingKart",
                        "emi": "18,000",
                        "loan_amount": "10,00,000",
                        "outstanding": "1,50,000",
                        "outstanding_pct": "15%",
                    },
                ],
            },
            {
                "code": "RF002",
                "type": "unsecured_pct_portfolio",
                "value": "74.4%",
            },
        ],
    },

    # ── Scenario 2: Priya Mehta ──────────────────────────────────────────
    {
        "case_id": "DEMO002",
        "customer_name": "Priya Mehta",
        "profile_type": "SALARIED",
        "loan_type": "Personal Loan",
        "loan_amount": "5,00,000",
        "segment": "Salaried",
        "claimed_income": "10,00,000",
        "banking": {
            "avg_monthly_credit": "85,000",
            "avg_upi_credit": "0",
            "monthly_credits": [
                {"month": "Apr", "bank_credit": "85,000", "upi_credit": "0"},
                {"month": "May", "bank_credit": "85,000", "upi_credit": "0"},
                {"month": "Jun", "bank_credit": "85,000", "upi_credit": "0"},
                {"month": "Jul", "bank_credit": "85,000", "upi_credit": "0"},
                {"month": "Aug", "bank_credit": "85,000", "upi_credit": "0"},
                {"month": "Sep", "bank_credit": "85,000", "upi_credit": "0"},
            ],
        },
        "top_suppliers": [],
        "top_buyers": [
            {
                "name": "Employer Tech Sol",
                "monthly": [
                    {"month": "Apr", "amount": "85,000"},
                    {"month": "May", "amount": "85,000"},
                    {"month": "Jun", "amount": "85,000"},
                    {"month": "Jul", "amount": "85,000"},
                    {"month": "Aug", "amount": "85,000"},
                    {"month": "Sep", "amount": "85,000"},
                ],
            },
        ],
        "red_flags": [
            {
                "code": "RF001",
                "type": "active_loan_count_mismatch",
                "bureau_count": 5,
                "bank_count": 3,
                "discrepancies": [
                    {
                        "lender": "ICICI",
                        "type": "Car Loan",
                        "emi": "7,000",
                        "outstanding": "3,20,000",
                        "issue": "not in bank statement",
                    },
                    {
                        "lender": "HDFC",
                        "type": "Credit Card",
                        "emi": "5,000",
                        "outstanding": "60,000",
                        "issue": "not in bank statement",
                    },
                ],
            },
            {
                "code": "RF002",
                "type": "FOIR_breach",
                "threshold": ">60%",
                "total_existing_emi": "44,500",
                "proposed_new_emi": "11,000",
                "total_obligation": "55,500",
                "income": "85,000",
                "emi_breakdown": [
                    {
                        "type": "Home Loan",
                        "lender": "SBI",
                        "emi": "24,000",
                        "outstanding": "25,00,000",
                        "closure_probability": "LOW",
                    },
                    {
                        "type": "Car Loan",
                        "lender": "ICICI",
                        "emi": "7,000",
                        "outstanding": "3,20,000",
                        "closure_probability": "MEDIUM",
                        "note": "subject to mismatch",
                    },
                    {
                        "type": "PL",
                        "lender": "Bajaj",
                        "emi": "6,000",
                        "outstanding": "1,50,000",
                        "closure_probability": "MEDIUM",
                    },
                    {
                        "type": "CC EMI",
                        "lender": "HDFC",
                        "emi": "5,000",
                        "outstanding": "60,000",
                        "closure_probability": "HIGH",
                        "note": "subject to mismatch",
                    },
                    {
                        "type": "Consumer Durable",
                        "lender": "Axis",
                        "emi": "2,500",
                        "outstanding": "25,000",
                        "closure_probability": "HIGH",
                    },
                ],
            },
        ],
    },

    # ── Scenario 3: Vikram Singh ─────────────────────────────────────────
    {
        "case_id": "DEMO003",
        "customer_name": "Vikram Singh",
        "profile_type": "SALARIED",
        "loan_type": "Personal Loan",
        "loan_amount": "5,00,000",
        "segment": "Salaried",
        "claimed_income": "10,00,000",
        "banking": {
            "avg_monthly_credit": "60,000",
            "avg_upi_credit": "0",
            "monthly_credits": [
                {"month": "May", "bank_credit": "65,000", "upi_credit": "0"},
                {"month": "Jun", "bank_credit": "60,000", "upi_credit": "0"},
                {"month": "Jul", "bank_credit": "55,000", "upi_credit": "0"},
                {"month": "Aug", "bank_credit": "50,000", "upi_credit": "0"},
                {"month": "Sep", "bank_credit": "45,000", "upi_credit": "0"},
                {"month": "Oct", "bank_credit": "40,000", "upi_credit": "0"},
            ],
        },
        "top_suppliers": [],
        "top_buyers": [
            {
                "name": "Employer Retail Corp",
                "monthly": [
                    {"month": "May", "amount": "65,000"},
                    {"month": "Jun", "amount": "60,000"},
                    {"month": "Jul", "amount": "55,000"},
                    {"month": "Aug", "amount": "50,000"},
                    {"month": "Sep", "amount": "45,000"},
                    {"month": "Oct", "amount": "40,000"},
                ],
            },
        ],
        "red_flags": [
            {
                "code": "RF001",
                "type": "aggressive_borrowing",
                "total_loans_in_6_months": 4,
                "loans_in_last_3_months": 2,
                "recent_loans": [
                    {"month": "Oct", "type": "Gold Loan", "lender": "Muthoot", "amount": "1,00,000"},
                    {"month": "Sep", "type": "PL", "lender": "Bajaj", "amount": "1,50,000"},
                    {"month": "Jul", "type": "CC", "lender": "ICICI", "amount": "1,00,000"},
                    {"month": "Jun", "type": "PL", "lender": "HDFC", "amount": "2,00,000"},
                ],
            },
            {
                "code": "RF002",
                "type": "recent_delinquency",
                "lender": "Bajaj",
                "loan_type": "PL",
                "delinquency_month": "Aug 2024",
                "max_dpd": 18,
                "status": "Cured",
                "outstanding": "10,000",
            },
            {
                "code": "RF003",
                "type": "declining_abb",
                "start_value": "65,000",
                "end_value": "40,000",
                "decline_pct": "38%",
                "period": "6 months",
            },
        ],
    },

    # ── Scenario 4: Prakash Reddy ────────────────────────────────────────
    {
        "case_id": "DEMO004",
        "customer_name": "Prakash Reddy",
        "profile_type": "Self-Employed",
        "loan_type": "Business Loan",
        "loan_amount": "7,00,000",
        "segment": "Grocery",
        "claimed_income": "10,00,000",
        "banking": {
            "avg_monthly_credit": "70,000",
            "avg_upi_credit": "14,667",
            "monthly_credits": [
                {"month": "Apr", "bank_credit": "1,45,000", "upi_credit": "30,000"},
                {"month": "May", "bank_credit": "1,32,000", "upi_credit": "28,000"},
                {"month": "Jun", "bank_credit": "98,000", "upi_credit": "20,000"},
                {"month": "Jul", "bank_credit": "45,000", "upi_credit": "10,000"},
                {"month": "Aug", "bank_credit": "0", "upi_credit": "0"},
                {"month": "Sep", "bank_credit": "0", "upi_credit": "0"},
            ],
        },
        "top_suppliers": [
            {
                "name": "Distributor X",
                "monthly": [
                    {"month": "Apr", "amount": "80,000"},
                    {"month": "May", "amount": "75,000"},
                    {"month": "Jun", "amount": "50,000"},
                    {"month": "Jul", "amount": "20,000"},
                    {"month": "Aug", "amount": "0"},
                    {"month": "Sep", "amount": "0"},
                ],
            },
        ],
        "top_buyers": [
            {
                "name": "SK Builders",
                "monthly": [
                    {"month": "Apr", "amount": "40,000"},
                    {"month": "May", "amount": "40,000"},
                    {"month": "Jun", "amount": "40,000"},
                    {"month": "Jul", "amount": "40,000"},
                    {"month": "Aug", "amount": "0"},
                    {"month": "Sep", "amount": "0"},
                ],
            },
        ],
        "red_flags": [
            {
                "code": "RF001",
                "type": "business_income_stopped",
                "zero_income_months": ["Aug", "Sep"],
                "decline_pattern": "1,45,000 to 0",
            },
        ],
    },

    # ── Scenario 5: Priya Sharma ─────────────────────────────────────────
    {
        "case_id": "DEMO005",
        "customer_name": "Priya Sharma",
        "profile_type": "Self-Employed",
        "loan_type": "Personal Loan",
        "loan_amount": "8,00,000",
        "segment": "Consulting",
        "claimed_income": "10,00,000",
        "banking": {
            "avg_monthly_credit": "90,000",
            "avg_upi_credit": "90,000",
            "monthly_credits": [
                {"month": "Jun", "bank_credit": "88,000", "upi_credit": "88,000"},
                {"month": "Jul", "bank_credit": "92,000", "upi_credit": "92,000"},
                {"month": "Aug", "bank_credit": "85,000", "upi_credit": "85,000"},
                {"month": "Sep", "bank_credit": "95,000", "upi_credit": "95,000"},
                {"month": "Oct", "bank_credit": "80,000", "upi_credit": "80,000"},
                {"month": "Nov", "bank_credit": "1,00,000", "upi_credit": "1,00,000"},
            ],
        },
        "top_suppliers": [],
        "top_buyers": [
            {
                "name": "Client Tech A",
                "monthly": [
                    {"month": "Jun", "amount": "40,000"},
                    {"month": "Jul", "amount": "40,000"},
                    {"month": "Aug", "amount": "40,000"},
                    {"month": "Sep", "amount": "40,000"},
                    {"month": "Oct", "amount": "40,000"},
                    {"month": "Nov", "amount": "40,000"},
                ],
            },
        ],
        "red_flags": [
            {
                "code": "RF001",
                "type": "high_loan_velocity",
                "total_loans_in_6_months": 7,
                "loans_in_last_3_months": 4,
                "recent_loans": [
                    {"month": "Nov", "type": "PL", "lender": "Capital Float", "amount": "15,000"},
                    {"month": "Oct", "type": "PL", "lender": "Amazon Pay", "amount": "5,000"},
                    {"month": "Oct", "type": "PL", "lender": "KreditBee", "amount": "50,000"},
                    {"month": "Sep", "type": "PL", "lender": "SBI Card", "amount": "75,000"},
                    {"month": "Aug", "type": "BL", "lender": "LendingKart", "amount": "2,00,000"},
                    {"month": "Jul", "type": "PL", "lender": "Bajaj Finserv", "amount": "25,000"},
                    {"month": "Jun", "type": "PL", "lender": "Navi", "amount": "40,000"},
                ],
            },
            {
                "code": "RF002",
                "type": "historical_delinquency",
                "lender": "SBI Card",
                "loan_type": "PL",
                "delinquency_month": "Sep 2024",
                "max_dpd": 25,
                "status": "Cured",
                "outstanding": "12,500",
            },
        ],
    },
]


def _parse_amount(val):
    """Convert an Indian-format amount string to a float for display purposes."""
    if isinstance(val, (int, float)):
        return float(val)
    return float(str(val).replace(",", ""))


def _avg_supplier_or_buyer(entity):
    """Return average monthly amount for a supplier/buyer entry."""
    amounts = [_parse_amount(m["amount"]) for m in entity["monthly"]]
    non_zero = [a for a in amounts if a > 0]
    if not non_zero:
        return 0
    return sum(non_zero) / len(non_zero)


def _trend_description(monthly_credits):
    """Describe the 6-month credit trend."""
    values = [_parse_amount(m["bank_credit"]) for m in monthly_credits]
    if all(v == 0 for v in values):
        return "Zero throughout"
    if len(values) < 2:
        return "Insufficient data"
    first_nonzero = next((v for v in values if v > 0), values[0])
    last = values[-1]
    if first_nonzero == 0:
        return "Started at zero"
    change_pct = ((last - first_nonzero) / first_nonzero) * 100
    if last == 0:
        return "Declined to zero"
    elif change_pct < -15:
        return f"Declining ({change_pct:+.0f}%)"
    elif change_pct > 15:
        return f"Growing ({change_pct:+.0f}%)"
    else:
        return "Stable"


def _format_inr(val):
    """Format a number as INR-style string (e.g. 19,00,000)."""
    if isinstance(val, str):
        val = _parse_amount(val)
    val = int(val)
    if val < 0:
        return "-" + _format_inr(-val)
    s = str(val)
    if len(s) <= 3:
        return s
    last3 = s[-3:]
    rest = s[:-3]
    parts = []
    while rest:
        parts.append(rest[-2:] if len(rest) >= 2 else rest)
        rest = rest[:-2]
    return ",".join(reversed(parts)) + "," + last3


def get_summary(scenario):
    """
    Return a standardized English summary of the borrower profile.

    Parameters
    ----------
    scenario : dict
        One of the dictionaries from the SCENARIOS list.

    Returns
    -------
    str
        Multi-line formatted summary.
    """
    lines = []

    # ── Applicant ────────────────────────────────────────────────────────
    lines.append("=== Applicant ===")
    lines.append(f"  Name     : {scenario['customer_name']}")
    lines.append(f"  Type     : {scenario['profile_type']}")
    lines.append(f"  Segment  : {scenario['segment']}")
    lines.append("")

    # ── Loan Request ─────────────────────────────────────────────────────
    lines.append("=== Loan Request ===")
    lines.append(f"  Type   : {scenario['loan_type']}")
    lines.append(f"  Amount : INR {scenario['loan_amount']}")
    lines.append("")

    # ── Banking Summary ──────────────────────────────────────────────────
    banking = scenario["banking"]
    mc = banking["monthly_credits"]
    trend = _trend_description(mc)
    lines.append("=== Banking Summary ===")
    lines.append(f"  Avg Monthly Credit : INR {banking['avg_monthly_credit']}")
    lines.append(f"  Avg UPI Credit     : INR {banking['avg_upi_credit']}")
    lines.append(f"  6-Month Trend      : {trend}")
    lines.append("")

    # ── Top Suppliers ────────────────────────────────────────────────────
    if scenario.get("top_suppliers"):
        lines.append("=== Top Suppliers ===")
        for s in scenario["top_suppliers"]:
            avg = _avg_supplier_or_buyer(s)
            lines.append(f"  {s['name']} -- avg monthly payment: INR {_format_inr(avg)}")
        lines.append("")

    # ── Top Buyers ───────────────────────────────────────────────────────
    if scenario.get("top_buyers"):
        lines.append("=== Top Buyers ===")
        for b in scenario["top_buyers"]:
            avg = _avg_supplier_or_buyer(b)
            lines.append(f"  {b['name']} -- avg monthly payment: INR {_format_inr(avg)}")
        lines.append("")

    # ── Existing Loans ───────────────────────────────────────────────────
    emi_items = []
    for rf in scenario.get("red_flags", []):
        if "emi_breakdown" in rf:
            emi_items.extend(rf["emi_breakdown"])
    if emi_items:
        lines.append("=== Existing Loans ===")
        for loan in emi_items:
            closure = ""
            if "closure_probability" in loan:
                closure = f"  [Closure: {loan['closure_probability']}]"
            note = ""
            if "note" in loan:
                note = f"  ({loan['note']})"
            lines.append(
                f"  {loan['type']} / {loan['lender']} -- "
                f"EMI: INR {loan['emi']}, Outstanding: INR {loan['outstanding']}"
                f"{closure}{note}"
            )
        lines.append("")

    # ── Red Flags ────────────────────────────────────────────────────────
    lines.append("=== Red Flags ===")
    for rf in scenario.get("red_flags", []):
        code = rf["code"]
        rf_type = rf["type"]

        if rf_type == "FOIR_ratio":
            lines.append(
                f"  [{code}] FOIR Ratio -- Total obligation: INR {rf['total_obligation']} "
                f"vs income: INR {rf['total_income']} "
                f"(existing EMI: INR {rf['total_existing_emi']}, "
                f"proposed EMI: INR {rf['proposed_new_emi']})"
            )

        elif rf_type == "unsecured_pct_portfolio":
            lines.append(
                f"  [{code}] Unsecured Portfolio Percentage: {rf['value']}"
            )

        elif rf_type == "active_loan_count_mismatch":
            lines.append(
                f"  [{code}] Active Loan Count Mismatch -- "
                f"Bureau: {rf['bureau_count']}, Bank statement: {rf['bank_count']}"
            )
            for d in rf.get("discrepancies", []):
                lines.append(
                    f"    - {d['lender']} {d['type']} (EMI: INR {d['emi']}, "
                    f"outstanding: INR {d['outstanding']}) -- {d['issue']}"
                )

        elif rf_type == "FOIR_breach":
            lines.append(
                f"  [{code}] FOIR Breach {rf['threshold']} -- "
                f"Total obligation: INR {rf['total_obligation']} "
                f"vs income: INR {rf['income']} "
                f"(existing EMI: INR {rf['total_existing_emi']}, "
                f"proposed EMI: INR {rf['proposed_new_emi']})"
            )

        elif rf_type == "aggressive_borrowing":
            lines.append(
                f"  [{code}] Aggressive Borrowing -- "
                f"{rf['total_loans_in_6_months']} loans in 6 months, "
                f"{rf['loans_in_last_3_months']} in last 3 months"
            )
            for loan in rf.get("recent_loans", []):
                lines.append(
                    f"    - {loan['month']}: {loan['type']} from {loan['lender']} "
                    f"(INR {loan['amount']})"
                )

        elif rf_type == "high_loan_velocity":
            lines.append(
                f"  [{code}] High Loan Velocity -- "
                f"{rf['total_loans_in_6_months']} loans in 6 months, "
                f"{rf['loans_in_last_3_months']} in last 3 months"
            )
            for loan in rf.get("recent_loans", []):
                lines.append(
                    f"    - {loan['month']}: {loan['type']} from {loan['lender']} "
                    f"(INR {loan['amount']})"
                )

        elif rf_type in ("recent_delinquency", "historical_delinquency"):
            label = "Recent Delinquency" if rf_type == "recent_delinquency" else "Historical Delinquency"
            lines.append(
                f"  [{code}] {label} -- {rf['lender']} {rf['loan_type']}, "
                f"month: {rf['delinquency_month']}, max DPD: {rf['max_dpd']}, "
                f"status: {rf['status']}, outstanding: INR {rf['outstanding']}"
            )

        elif rf_type == "declining_abb":
            lines.append(
                f"  [{code}] Declining ABB -- "
                f"from INR {rf['start_value']} to INR {rf['end_value']} "
                f"({rf['decline_pct']} decline over {rf['period']})"
            )

        elif rf_type == "business_income_stopped":
            lines.append(
                f"  [{code}] Business Income Stopped -- "
                f"zero income in {', '.join(rf['zero_income_months'])}, "
                f"decline pattern: INR {rf['decline_pattern']}"
            )

        else:
            lines.append(f"  [{code}] {rf_type}: {rf}")

    return "\n".join(lines)


# ── Quick self-test when run directly ────────────────────────────────────
if __name__ == "__main__":
    for sc in SCENARIOS:
        print(get_summary(sc))
        print("\n" + "=" * 60 + "\n")
