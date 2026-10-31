with expenses as (
    select * from {{ ref('stg_expense_transactions') }}
),

fx_rates as (
    select * from {{ ref('stg_fx_rates') }}
),

matched_rates as (
    select
        e.expense_transaction_key,
        f.usd_per_currency_unit as exchange_rate,
        row_number() over (
            partition by e.expense_transaction_key 
            order by f.effective_date desc
        ) as rn
    from expenses e
    left join fx_rates f
        on e.original_currency = f.currency_code
        and f.effective_date <= e.transaction_date
    where e.original_currency != 'USD'
),

deduplicated_rates as (
    select expense_transaction_key, exchange_rate 
    from matched_rates 
    where rn = 1
)

select
    e.*,
    case 
        when e.original_currency = 'USD' then 1.0000
        else r.exchange_rate 
    end as fx_rate,

    case 
        when e.original_currency = 'USD' then e.original_amount
        when r.exchange_rate is not null then cast(e.original_amount * r.exchange_rate as decimal(18, 2))
        else null
    end as amount_usd,

    case 
        when e.original_currency != 'USD' and r.exchange_rate is null then false 
        else true 
    end as is_fx_available

from expenses e
left join deduplicated_rates r 
    on e.expense_transaction_key = r.expense_transaction_key
