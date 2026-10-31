select * from {{ source('raw_data', 'monthly_budgets') }}
