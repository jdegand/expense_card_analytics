with source as (
    select * from {{ source('raw_data', 'fx_rates') }}
),

exchange_rates as (
    select
        trim(upper(currency_code)) as currency_code,
        cast(effective_date as date) as effective_date,
        cast(usd_per_currency_unit as decimal(18, 4)) as usd_per_currency_unit
    from source
)

select * from exchange_rates
