select * from {{ source('raw_data', 'expense_reports') }}
