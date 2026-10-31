with expenses as (
    select * from {{ ref('int_expense_fx_conversion') }}
),

cards as (
    -- Fixed: Pointed directly to your active staging file matching your directory structure
    select * from {{ ref('stg_card_transactions') }} 
),

potential_matches as (
    select
        c.card_transaction_key,
        e.expense_transaction_key,
        c.merchant_name as card_merchant,
        e.merchant_name as expense_merchant,
        
        count(e.expense_transaction_key) over(partition by c.card_transaction_key) as matches_for_this_card,
        count(c.card_transaction_key) over(partition by e.expense_transaction_key) as matches_for_this_expense

    from cards c
    full outer join expenses e
        on c.employee_id = e.employee_id
        and c.original_amount = e.original_amount
        and c.original_currency = e.original_currency
        and abs(date_diff('day', cast(c.transaction_date as date), cast(e.transaction_date as date))) <= 3
),

classified_matches as (
    select
        card_transaction_key,
        expense_transaction_key,
        
        case
            when card_transaction_key is null then 'unmatched'
            when expense_transaction_key is null then 'unmatched'
            when matches_for_this_card = 1 and matches_for_this_expense = 1 then 'matched'
            else 'ambiguous'
        end as match_status,

        case
            when card_transaction_key is null then 'Expense transaction has no corresponding corporate card charge.'
            when expense_transaction_key is null then 'Corporate card charge has no matching submitted expense entry.'
            when matches_for_this_card = 1 and matches_for_this_expense = 1 
                 and card_merchant = expense_merchant then 'Exact 1:1 deterministic pairing match.'
            when matches_for_this_card = 1 and matches_for_this_expense = 1 
                 and card_merchant != expense_merchant then 'Fuzzy date/amount match; merchant names differ.'
            else 'Multiple valid transaction candidate matches found within threshold window. Manual review required.'
        end as match_rationale

    from potential_matches
)

select * from classified_matches
