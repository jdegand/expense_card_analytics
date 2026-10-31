# Data Dictionary

This dictionary covers the expense and corporate-card analytics MVP. Travel and
fleet are future extensions and are not included in the current models.

## Key convention

For transaction sources, retain `source_system`, `source_period`, and
`raw_transaction_id` in staging. Define the source business grain, then derive
a deterministic key from all three components:

`source_system + source_period + raw_transaction_id`

A hash may be used as a surrogate key; it does not replace the business-grain
definition. Use natural keys for employees and cost centers.

## `fct_expense_transactions`

- **Grain:** One row per expense line.
- **Key:** Deterministic source-derived expense transaction key.

Includes source identifiers, report and employee references, cost center,
merchant, category, transaction and posting dates, accounting period, original
amount and currency, FX rate, USD amount, receipt indicator, and FX availability.
Enriches expense lines with report submission date, employee, and cost-center
information.

## `fct_expense_audit_flags`

- **Grain:** One row per expense transaction per triggered policy rule.
- **Key:** Composite of expense transaction key and rule ID.

Includes the transaction key, rule ID, and human-readable review reason.

## `fct_card_transactions`

- **Grain:** One row per card charge.
- **Key:** Deterministic source-derived card transaction key.

Includes source identifiers, transaction details, original amount and currency,
FX rate, USD amount, FX availability, and card-to-expense match status.

## `int_card_expense_matches`

- **Grain:** One row per card-to-expense matching result, as defined by the
  documented matching approach.
- **Key:** Document the key used for each match result.

Includes match status (`matched`, `unmatched`, or `ambiguous`) and match
rationale. Do not force ambiguous matches or double-count matched card and
expense records in spend totals.

## `agg_department_monthly_spend`

- **Grain:** One row per accounting period, department, and category.
- **Key:** Composite of accounting period, department, and category.
- **Budget rule:** Join budgets only at this same grain. Do not repeat a
  higher-level budget across lower-grain rows.

Includes eligible USD expense actuals, budget, budget variance, and budget
variance percentage. Variance fields are unavailable when the required budget
is missing or zero.

## Reference tables

- `expense_reports`: One row per submitted expense report.
- `employees`: One row per employee; use the employee natural key.
- `cost_centers`: One row per valid cost center; use the cost-center natural
  key.
- `monthly_budgets`: One row per accounting period, department, and category.
- `fx_rates`: One row per currency and effective date.
