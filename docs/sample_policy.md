# Sample Expense and Corporate Card Policies (Synthetic)

All policies and data in this project are fictional. A flag indicates an item
for review; it is not proof of misconduct, fraud, or financial loss.

## Receipt requirement

- **Rule:** A receipt is required when an expense transaction’s USD-equivalent
  amount is greater than $75.00.
- **Evaluation:** Use the transaction-date FX rate. The threshold is strictly
  greater than $75.00.
- **Unavailable:** If FX is missing or the receipt indicator is unknown, report
  the evaluation as unavailable.
- **Flag:** `EXP_MISSING_RECEIPT`

## Submission window

- **Rule:** Flag an expense transaction submitted more than 30 calendar days
  after its transaction date.
- **Calculation:** `submission_date - transaction_date`.
- **Unavailable:** If either date is missing, report the evaluation as
  unavailable.
- **Flag:** `EXP_LATE_SUBMISSION`

## Category thresholds

Flag a transaction when its USD-equivalent amount is strictly greater than the
configured threshold.

| Category | Threshold (USD) |
| -------- | --------------- |
| Meals & Entertainment | $150.00 |
| Lodging/Hotel | $400.00 |
| Airfare | $1,000.00 |

Use the transaction-date FX rate. If the category has no configured threshold
or FX is unavailable, report the evaluation as unavailable.

- **Flag:** `EXP_EXCEEDS_THRESHOLD`

## Potential duplicates

- **Rule:** Flag expense transactions that share employee ID, normalized
  merchant, transaction date, original amount, and currency.
- **Interpretation:** These are potential duplicates for review. Do not delete
  or exclude them from spend totals solely because they match.
- **Flag:** `EXP_POTENTIAL_DUPLICATE`

## Cost center

- **Rule:** Flag an expense transaction if its cost center is missing or does
  not match the synthetic cost-center reference data.
- **Flag:** `EXP_INVALID_COST_CENTER`

## Card-to-expense matching

Match card transactions to expense transactions using the documented matching
criteria and date tolerance. Classify records as matched, unmatched, or
ambiguous. Do not force ambiguous matches. Matching supports reconciliation
only; matched card and expense amounts must not both be counted in expense
spend.
