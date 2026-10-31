import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

def generate_mock_data(seed=42, output_dir="data/raw"):
    print(f"Initializing synthetic data generation with seed={seed}...")
    
    # 1. Setup seeded random generators for strict repeatability across environments
    rng = np.random.default_rng(seed)
    
    # Core Date Configurations (Inclusive of June 30, 2026)
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 6, 30)
    # Add +1 to include the upper boundary day in pool generation
    date_range_days = (end_date - start_date).days + 1
    
    # Target Volumetrics
    num_employees = 75
    num_cost_centers = 8
    num_expense_lines = 4000
    num_card_transactions = 3200
    
    # Target Anomaly Counts
    target_missing_receipts = 120
    target_late_reports = 60
    target_duplicate_pairs = 12
    target_invalid_cost_centers = 15
    target_ambiguous_matches = 15
    target_matched_cards = 2500
    
    # Ensure project directories exist safely using pathlib
    output_path = Path(output_dir)
    (output_path / "expenses").mkdir(parents=True, exist_ok=True)
    (output_path / "cards").mkdir(parents=True, exist_ok=True)
    (output_path / "reference").mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------
    # PHASE 1: GENERATE REFERENCE TABLES
    # ----------------------------------------------------
    print("Generating reference tables...")
    
    # Cost Centers
    departments = ["Sales", "Engineering", "HR", "Marketing", "Finance", "Operations", "Legal", "Product"]
    cost_centers = pd.DataFrame({
        "cost_center_id": [f"CC_{100 + i}" for i in range(num_cost_centers)],
        "department_name": departments
    })
    cost_centers.to_csv(output_path / "reference/cost_centers.csv", index=False)
    
    # Employees
    employees = pd.DataFrame({
        "employee_id": [f"EMP_{1000 + i}" for i in range(num_employees)],
        "employee_name": [f"Employee Name {i}" for i in range(num_employees)],
        "cost_center_id": rng.choice(cost_centers["cost_center_id"].values, size=num_employees)
    })
    employees.to_csv(output_path / "reference/employees.csv", index=False)
    
    # FX Rates (Daily for EUR, CAD, GBP; USD = 1.0000)
    currencies = ["EUR", "CAD", "GBP"]
    base_rates = {"EUR": 1.08, "CAD": 0.74, "GBP": 1.27}
    
    fx_records = []
    for day in range(date_range_days):
        current_date = start_date + timedelta(days=day)
        
        # FIXED: Corrected invalid if-statement and established explicit 3-day March blackout window
        if current_date.month == 3 and current_date.day in {10, 11, 12}:
            continue
            
        for curr in currencies:
            fluctuation = rng.uniform(-0.02, 0.02)
            fx_records.append({
                "currency_code": curr,
                "effective_date": current_date.strftime("%Y-%m-%d"),
                "usd_per_currency_unit": round(base_rates[curr] + fluctuation, 4)
            })
    fx_rates = pd.DataFrame(fx_records)
    fx_rates.to_csv(output_path / "reference/fx_rates.csv", index=False)

    # Budgets (Grain: Period, Department, Category)
    categories = ["Meals & Entertainment", "Lodging/Hotel", "Airfare"]
    budget_records = []
    for month in range(1, 7):
        period = f"2026-0{month}"
        for dept in departments:
            for cat in categories:
                budget_records.append({
                    "accounting_period": period,
                    "department_name": dept,
                    "expense_category": cat,
                    "budget_usd": round(float(rng.uniform(5000, 25000)), 2)
                })
    monthly_budgets = pd.DataFrame(budget_records)
    monthly_budgets.to_csv(output_path / "reference/monthly_budgets.csv", index=False)

    # ----------------------------------------------------
    # PHASE 2: TRANSACTION ENGINE BUILD (BASE DATA)
    # ----------------------------------------------------
    print("Generating structural transaction entries...")
    
    pool_emp_ids = rng.choice(employees["employee_id"].values, size=num_expense_lines)
    
    # IMPROVEMENT: Replaced slow iterative lookups with a vectorized pandas Index reindex mapping
    employee_to_cc = employees.set_index("employee_id")["cost_center_id"]
    pool_cc_ids = employee_to_cc.reindex(pool_emp_ids).to_numpy()
    
    merchants_pool = ["Delta Air", "Marriott Stay", "Uber Meals", "Amazon Business", "Local Bistro", "Staples Office"]
    pool_merchants = rng.choice(merchants_pool, size=num_expense_lines)
    
    # Vectorized Generation of Random Timestamps across the range (now includes June 30)
    pool_days_offset = rng.integers(0, date_range_days, size=num_expense_lines)
    pool_tx_dates = pd.Series([start_date + timedelta(days=int(d)) for d in pool_days_offset])
    
    # Establish distinct representations for source period vs accounting period
    expense_data = pd.DataFrame({
        "source_system": "EXPENSE_MGR",
        "source_period": pool_tx_dates.dt.strftime("%Y-%m"),
        "raw_transaction_id": [f"TXEXP_{200000 + i}" for i in range(num_expense_lines)],
        "report_id": [f"RPT_{10000 + (i // 2)}" for i in range(num_expense_lines)], 
        "employee_id": pool_emp_ids,
        "cost_center_id": pool_cc_ids,
        "merchant_name": pool_merchants,
        "expense_category": ["Airfare" if "Delta" in m else "Lodging/Hotel" if "Marriott" in m else "Meals & Entertainment" for m in pool_merchants],
        "receipt_indicator": "TRUE",
        "original_amount": np.round(rng.uniform(10.0, 500.0, size=num_expense_lines), 2),
        "original_currency": rng.choice(["USD", "EUR", "CAD", "GBP"], size=num_expense_lines, p=[0.7, 0.1, 0.1, 0.1]),
        "transaction_date": pool_tx_dates.dt.strftime("%Y-%m-%d"),
        "posting_date": (pool_tx_dates + pd.Timedelta(days=2)).dt.strftime("%Y-%m-%d"),
        "accounting_period": pool_tx_dates.dt.strftime("%Y-%m")
    })

    # ----------------------------------------------------
    # PHASE 3: CONTROLLING ANOMALIES & KPI TARGETS
    # ----------------------------------------------------
    print("Injecting precise anomaly populations...")

    # FIXED: Replaced brittle head filtering with explicit slice assignment to guarantee exact metric denominators
    # Anomaly A: Missing Receipts above $75 Threshold (Target: Exactly 120 items)
    expense_data.loc[0:target_missing_receipts - 1, "original_amount"] = np.round(rng.uniform(76.0, 300.0, size=target_missing_receipts), 2)
    expense_data.loc[0:target_missing_receipts - 1, "original_currency"] = "USD"
    expense_data.loc[0:target_missing_receipts - 1, "receipt_indicator"] = "FALSE"
    
    # Anomaly B: Category Threshold Breaches (Specific known index injection)
    # Airfare > $1000
    expense_data.loc[150, ["original_amount", "original_currency", "expense_category", "merchant_name"]] = [1250.00, "USD", "Airfare", "Delta Air"]
    # Meals > $150
    expense_data.loc[151, ["original_amount", "original_currency", "expense_category", "merchant_name"]] = [185.50, "USD", "Meals & Entertainment", "Local Bistro"]
    # Lodging > $400
    expense_data.loc[152, ["original_amount", "original_currency", "expense_category", "merchant_name"]] = [450.00, "USD", "Lodging/Hotel", "Marriott Stay"]

    # Anomaly C: Invalid Cost Centers (Target: Exactly 15 items)
    expense_data.loc[200:200 + target_invalid_cost_centers - 1, "cost_center_id"] = "CC_999"

    # FIXED: Forced specific transactions to hit March 10, ensuring the blackout FX anomaly resolves correctly
    # Anomaly D: Missing FX rates via March Blackout
    expense_data.loc[300:304, "transaction_date"] = "2026-03-10"
    expense_data.loc[300:304, "original_currency"] = "EUR"

    # FIXED: Collected all duplicate row structures into a list and executed a single pd.concat to maximize efficiency
    # Anomaly E: Potential Duplicates (Target: Exactly 12 identical twin pairs)
    duplicate_list = []
    for i in range(target_duplicate_pairs):
        target_idx = 400 + i
        duplicate_copy = expense_data.loc[target_idx].copy()
        # Generates a brand new transaction business key but maintains all matching properties
        duplicate_copy["raw_transaction_id"] = f"TXEXP_DUP_{i}"
        duplicate_list.append(duplicate_copy)
    
    if duplicate_list:
        expense_data = pd.concat([expense_data, pd.DataFrame(duplicate_list)], ignore_index=True)

    # DERIVED BUSINESS KEY FOR DATA DICTIONARY CONFORMITY
    expense_data["expense_transaction_key"] = expense_data["source_system"] + "_" + expense_data["source_period"] + "_" + expense_data["raw_transaction_id"]

    # ----------------------------------------------------
    # PHASE 4: PARENT EXPENSE REPORT MATRIX
    # ----------------------------------------------------
    print("Aggregating expense lines into parent reports...")
    
    # FIXED: Converted transaction string fields to true datetime types before grouping to eliminate fragile string-max behaviors
    expense_data["dt_temp"] = pd.to_datetime(expense_data["transaction_date"])
    report_group = expense_data.groupby("report_id")["dt_temp"].max().reset_index()
    
    # Establish base corporate turnaround time (vectorized addition of 2 to 10 days)
    report_group["submission_date"] = report_group["dt_temp"] + pd.to_timedelta(rng.integers(2, 11, size=len(report_group)), unit="D")
    
    # Anomaly F: Late Submitted Reports (> 30 days window) (Target: Exactly 60 reports)
    # FIXED: Dynamically capture the true size of the filtered subset to eliminate array mismatch bugs
    late_report_ids = report_group["report_id"].head(target_late_reports)
    mask = report_group["report_id"].isin(late_report_ids)
    
    report_group.loc[mask, "submission_date"] = \
        report_group.loc[mask, "dt_temp"] + pd.to_timedelta(rng.integers(35, 45, size=mask.sum()), unit="D")

    # Cast timestamp structures back to standardized ISO strings for file persistence
    report_group["submission_date"] = report_group["submission_date"].dt.strftime("%Y-%m-%d")
    unique_reports = report_group.drop(columns=["dt_temp"])
    expense_data.drop(columns=["dt_temp"], inplace=True)
    # FIXED: Corrected parenthesis location layout syntax errors
    expense_data.to_csv(output_path / "expenses/expense_transactions.csv", index=False)
    unique_reports.to_csv(output_path / "expenses/expense_reports.csv", index=False)
    # ----------------------------------------------------
    # PHASE 5: CREDIT CARD ENGINE & MATCH TOPOLOGY
    # ----------------------------------------------------
    print("Generating credit card stream and alignment match maps...")
    # FIXED: Isolated clean indices (starting at index 1000) for "Clean Matches" to separate policy failures from match metrics
    clean_expense_sample = expense_data.iloc[1000:1000 + target_matched_cards]
    # IMPROVEMENT: Replaced slow row-by-row iterrows() loops with explicit, high-performance vectorized dict mappings
    card_base = clean_expense_sample.copy()
    card_base["source_system"] = "AMEX_CORP"
    card_base["raw_transaction_id"] = [f"TXCARD_{i}" for i in range(target_matched_cards)]
    card_records = card_base[[
    "source_system", "source_period", "raw_transaction_id", "employee_id",
    "merchant_name", "original_amount", "original_currency", "transaction_date",
    "posting_date", "accounting_period"
    ]].to_dict(orient="records")
    # Generate Ambiguous Matches (Target: Exactly 15 entries with masked merchant metadata)
    ambig_expense_sample = expense_data.iloc[3600:3600 + target_ambiguous_matches]
    for idx, exp_row in ambig_expense_sample.iterrows():
        card_records.append({
        "source_system": "AMEX_CORP",
        "source_period": exp_row["source_period"],
        "raw_transaction_id": f"TXCARD_AMBIG_{idx}",
        "employee_id": exp_row["employee_id"],
        "merchant_name": "UNKNOWN MERCHANDISE CORP",
        "original_amount": exp_row["original_amount"],
        "original_currency": exp_row["original_currency"],
        "transaction_date": exp_row["transaction_date"],
        "posting_date": exp_row["posting_date"],
        "accounting_period": exp_row["accounting_period"]
        })

    # FIXED: Handled potential range errors by establishing an explicit remaining target cap
    current_card_count = len(card_records)
    remaining_unmatched_needed = max(0, num_card_transactions - current_card_count)
    # Generate standalone unmatched card pool
    random_days_offset = rng.integers(0, date_range_days, size=remaining_unmatched_needed)
    random_card_dates = pd.Series([start_date + timedelta(days=int(d)) for d in random_days_offset])
    
    for k in range(remaining_unmatched_needed):
        tx_dt = random_card_dates.iloc[k]
        card_records.append({
        "source_system": "AMEX_CORP",
        "source_period": tx_dt.strftime("%Y-%m"),
        "raw_transaction_id": f"TXCARD_UNMATCHED_{k}",
        "employee_id": rng.choice(employees["employee_id"].values),
        "merchant_name": "Standalone Card Vendor",
        "original_amount": round(float(rng.uniform(15.0, 200.0)), 2),
        "original_currency": "USD",
        "transaction_date": tx_dt.strftime("%Y-%m-%d"),
        "posting_date": (tx_dt + timedelta(days=2)).strftime("%Y-%m-%d"),
        "accounting_period": tx_dt.strftime("%Y-%m")
        })

    cards_df = pd.DataFrame(card_records)
    # DERIVED BUSINESS KEY FOR DATA DICTIONARY CONFORMITY
    cards_df["card_transaction_key"] = cards_df["source_system"] + "_" + cards_df["source_period"] + "_" + cards_df["raw_transaction_id"]
    # FIXED: Corrected parenthesis layout syntax error
    cards_df.to_csv(output_path / "cards/card_transactions.csv", index=False)
    # ----------------------------------------------------
    # DATA QUALITY ASSURANCE VALIDATION CHECKS
    # ----------------------------------------------------
    print("Executing final data assurance checks...")
    # FIXED: Corrected conditional check to evaluate strict greater-than (>) threshold assignment
    actual_missing_receipts = len(expense_data[(expense_data["original_amount"] > 75.0) & (expense_data["receipt_indicator"] == "FALSE")])
    actual_invalid_cc = len(expense_data[expense_data["cost_center_id"] == "CC_999"])
    actual_duplicates = len(expense_data[expense_data["raw_transaction_id"].str.contains("DUP")])
    # FIXED: Replaced standard print statements with structured runtime asset validation checks
    assert actual_missing_receipts >= target_missing_receipts, f"Data Quality Error: Missing receipt target mismatch ({actual_missing_receipts})"
    assert actual_invalid_cc == target_invalid_cost_centers, f"Data Quality Error: Invalid cost center count mismatch ({actual_invalid_cc})"
    assert actual_duplicates == target_duplicate_pairs, f"Data Quality Error: Duplicate pair injection failed ({actual_duplicates})"
    assert len(cards_df) == num_card_transactions, f"Data Quality Error: Card volume mismatch ({len(cards_df)})"
    print("\n" + "="*45)
    print("MOCK DATA GENERATION COMPLETE SUMMARY")
    print("="*45)
    print(f"Employees Seeded:            {len(employees)}")
    print(f"Cost Centers Seeded:         {len(cost_centers)}")
    print(f"Expense Lines Exported:      {len(expense_data)}")
    print(f"Expense Reports Exported:    {len(unique_reports)}")
    print(f"Card Charges Exported:       {len(cards_df)}")
    print(f"Budget Plan Records:         {len(monthly_budgets)}")
    print("-"*45)
    print(f"Verified Missing Receipts:   {actual_missing_receipts}")
    print(f"Verified Invalid Cost Ctrs:  {actual_invalid_cc}")
    print(f"Verified Duplicate Pairs:    {actual_duplicates}")
    print("="*45 + "\n")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic data for pipeline verification.")
    parser.add_argument("--seed", type=int, default=42, help="Random engine generation initializer integer.")
    parser.add_argument("--output_dir", type=str, default="data/raw", help="Target output folder structure.")
    args = parser.parse_args()
    generate_mock_data(seed=args.seed, output_dir=args.output_dir)
