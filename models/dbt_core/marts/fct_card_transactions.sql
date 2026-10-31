with cards as (
    -- Fixed: Re-routed reference lineage directly into your active staging layers
    select * from {{ ref('stg_card_transactions') }}
),

matches as (
    select * from {{ ref('int_card_expense_matches') }}
)

select
    c.card_transaction_key,
    c.source_system,
    c.source_period,
    c.raw_transaction_id,
    c.employee_id,
    c.merchant_name,
    c.original_amount,
    c.original_currency,
    coalesce(m.match_status, 'unmatched') as match_status,
    coalesce(m.match_rationale, 'No cross-system match evaluation found.') as match_rationale,
    m.expense_transaction_key as matched_expense_transaction_key,
    c.transaction_date,
    c.posting_date,
    c.accounting_period
from cards c
left join matches m 
    on c.card_transaction_key = m.card_transaction_key
