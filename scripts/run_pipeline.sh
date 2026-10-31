#!/bin/bash

# Exit immediately if any command exits with a non-zero status
set -e

# Automatically find the absolute path of the project's root folder
# (one level up from where this script sits inside scripts/)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting Expense & Corporate Card Analytics Pipeline..."

# 1. Generate the deterministic data
echo "Step 1: Re-generating mock source data..."
python3 "$REPO_ROOT/mock_generator/generate_data.py"

# 2. Run dbt build
echo "Step 2: Executing dbt builds and testing models..."
# Temporarily jump into repo root so dbt reads dbt_project.yml and local profiles cleanly
cd "$REPO_ROOT"
dbt build --target dev --profiles-dir .

# 3. Export data to the automated Excel workbook
echo "Step 3: Exporting analytical marts to Excel workbook..."
python3 "$REPO_ROOT/scripts/export_to_excel.py"

echo "🎉 Pipeline run completed successfully!"
