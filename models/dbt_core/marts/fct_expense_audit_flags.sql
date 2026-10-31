with expense_facts as (
    select * from {{ ref('fct_expense_transactions') }}
),

missing_receipts as (
    select
        expense_transaction_key,
        'EXP_MISSING_RECEIPT' as rule_id,
        'Receipt missing for charge strictly greater than $75.00 threshold.' as review_reason
    from expense_facts
    where receipt_indicator = false
      and amount_usd > 75.00
      and is_fx_available = true
),

late_submissions as (
    select
        expense_transaction_key,
        'EXP_LATE_SUBMISSION' as rule_id,
        'Expense report submitted ' || cast(date_diff('day', cast(transaction_date as date), cast(submission_date as date)) as varchar) || ' days after transaction date (violates 30-day window).' as review_reason
    from expense_facts
    where submission_date is not null
      and transaction_date is not null
      and date_diff('day', cast(transaction_date as date), cast(submission_date as date)) > 30
),

category_breaches as (
    select
        expense_transaction_key,
        'EXP_EXCEEDS_THRESHOLD' as rule_id,
        'Spend amount of $' || cast(amount_usd as varchar) || ' exceeds allowable limit for category: ' || expense_category || '.' as review_reason
    from expense_facts
    where is_fx_available = true
      and (
        (expense_category = 'Meals & Entertainment' and amount_usd > 150.00) or
        (expense_category = 'Lodging/Hotel' and amount_usd > 400.00) or
        (expense_category = 'Airfare' and amount_usd > 1000.00)
      )
),

potential_duplicates as (
    select
        expense_transaction_key,
        'EXP_POTENTIAL_DUPLICATE' as rule_id,
        'Identical transaction characteristics detected for employee ' || employee_id || ' (matching amount, date, and merchant).' as review_reason
    from (
        select
            expense_transaction_key,
            employee_id,
            count(*) over(
                partition by employee_id, merchant_name, transaction_date, original_amount, original_currency
            ) as identical_record_count
        from expense_facts
    )
    where identical_record_count > 1
),

invalid_cost_centers as (
    select
        expense_transaction_key,
        'EXP_INVALID_COST_CENTER' as rule_id,
        'Cost center identifier ' || coalesce(cost_center_id, 'NULL') || ' is missing or does not match reference organizational data.' as review_reason
    from expense_facts
    where cost_center_id is null 
       or cost_center_id = 'CC_999'
),

all_flags as (
    select * from missing_receipts
    union all
    select * from late_submissions
    union all
    select * from category_breaches
    union all
    select * from potential_duplicates
    union all
    select * from invalid_cost_centers
)

select
    cast(expense_transaction_key || '_' || rule_id as varchar) as expense_audit_flag_key,
    expense_transaction_key,
    rule_id,
    review_reason,
    current_timestamp as flagged_at
from all_flags
