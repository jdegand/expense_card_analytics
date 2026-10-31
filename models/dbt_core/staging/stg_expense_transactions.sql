with source as (
    select * from {{ source('raw_data', 'expense_transactions') }}
),

expense_lines as (
    select
        cast(source_system as varchar) as source_system,
        cast(source_period as varchar) as source_period,
        cast(raw_transaction_id as varchar) as raw_transaction_id,
        
        cast(
            coalesce(source_system, '') || '_' || 
            coalesce(source_period, '') || '_' || 
            coalesce(raw_transaction_id, '') 
        as varchar) as expense_transaction_key,

        cast(employee_id as varchar) as employee_id,
        cast(cost_center_id as varchar) as cost_center_id,
        cast(report_id as varchar) as report_id,

        trim(merchant_name) as merchant_name,
        trim(expense_category) as expense_category,
        
        cast(receipt_indicator as boolean) as receipt_indicator,

        cast(original_amount as decimal(18, 2)) as original_amount,
        trim(upper(original_currency)) as original_currency,

        cast(transaction_date as date) as transaction_date,
        cast(posting_date as date) as posting_date,
        cast(accounting_period as varchar) as accounting_period
    from source
)

select * from expense_lines
