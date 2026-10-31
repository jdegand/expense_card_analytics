import os
import duckdb
import pandas as pd

DB_PATH = "spend_analytics.duckdb"
OUTPUT_PATH = "reports/monthly_reporting_workbook.xlsx"

def export_marts_to_excel():
    print(f"Connecting to database at {DB_PATH}...")
    con = duckdb.connect(database=DB_PATH, read_only=True)
    
    # Define the tables you want to export from your analytical layer
    tables_to_export = {
        "Department Spend": "main_marts.agg_department_monthly_spend",
        "Expense Transactions": "main_marts.fct_expense_transactions",
        "Audit Exceptions": "main_marts.fct_expense_audit_flags",
        "Card Reconciliation": "main_marts.fct_card_transactions"
    }
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Use pandas ExcelWriter with openpyxl engine
    with pd.ExcelWriter(OUTPUT_PATH, engine='openpyxl') as writer:
        for sheet_name, table_name in tables_to_export.items():
            print(f"Extracting {table_name} into sheet '{sheet_name}'...")
            
            # Query the table directly out of duckdb
            df = con.execute(f"select * from {table_name}").df()
            
            # --- FIX: Safe way to find and strip timezones in modern Pandas ---
            for col in df.columns:
                if isinstance(df[col].dtype, pd.DatetimeTZDtype):
                    df[col] = df[col].dt.tz_localize(None)
            
            # Write to excel
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Optional: Add basic formatting access
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            worksheet.sheet_view.showGridLines = True
            
    print(f"🎉 Success! Reporting workbook exported to {OUTPUT_PATH}")
    con.close()

if __name__ == "__main__":
    export_marts_to_excel()
