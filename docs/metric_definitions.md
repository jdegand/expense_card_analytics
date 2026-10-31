# Metric Definitions

All monetary metrics are in USD unless stated otherwise. A metric is unavailable
when required inputs or its denominator are missing or zero. Do not replace
unavailable values with zero.

## Dates and reporting period

- **Transaction date:** Date the purchase occurred; used for FX lookup.
- **Posting date:** Date recorded by the financial system.
- **Accounting period:** Source-assigned month used for expense and budget
  reporting. This does not imply formal accrual accounting.
- **Submission date:** Report-level date used to calculate submission delay.

Keep these fields distinct and document the date basis used by each report.

## Expense spend

- **Formula:** Sum of eligible USD-converted expense transactions.
- **Inclusion:** Include valid amounts with an applicable FX rate. Report
  missing-FX records separately.
- **Grain:** Accounting period and selected reporting dimensions.
- **Limitation:** Do not add card transactions to expense spend.

## Budget variance

- **Variance:** `actual_spend_usd - budget_usd`.
- **Variance percentage:** `(actual_spend_usd - budget_usd) / budget_usd`.
- Compare actuals and budgets at the same accounting-period, department, and
  category grain. Variance percentage is unavailable when budget is missing or
  zero.

## Exception rate

- **Formula:** Distinct expense transactions with one or more policy flags
  divided by eligible expense transactions in the same period and population.
- A transaction with multiple flags counts once in the numerator.

## Exception dollars

- **Formula:** Sum the USD amounts of distinct flagged expense transactions.
- A transaction with multiple flags counts once. This is spend associated with
  items for review, not confirmed loss or savings.

## Receipt compliance rate

- **Formula:** Transactions above the $75 USD-equivalent threshold with a
  receipt divided by eligible transactions above that threshold.
- Evaluate only transactions with valid FX and a known receipt indicator.
  Report unavailable evaluations separately.

## Submission cycle time

- **Formula:** `submission_date - transaction_date`, in calendar days.
- Report only transactions with both dates. Report missing-date records
  separately.

## Card match rate

- **Formula:** Matched card transactions divided by eligible card transactions.
- Define the eligible population in the matching documentation. Report
  unmatched and ambiguous counts separately.
- Matching is for reconciliation and does not add card amounts to expense
  spend.
  