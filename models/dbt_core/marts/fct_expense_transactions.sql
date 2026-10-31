with expenses as (
    select * from {{ ref('int_expense_fx_conversion') }}
),

reports as (
    select * from {{ ref('stg_expense_reports') }}
),

employees as (
    select * from {{ ref('stg_employees') }}
),

cost_centers as (
    select * from {{ ref('stg_cost_centers') }}
)

select
    e.expense_transaction_key,
    e.source_system,
    e.source_period,
    e.raw_transaction_id,
    e.report_id,
    e.employee_id,
    e.cost_center_id,
    emp.employee_name,
    cc.department_name,
    e.merchant_name,
    e.expense_category,
    e.transaction_date,
    e.posting_date,
    r.submission_date,
    e.accounting_period,
    e.original_amount,
    e.original_currency,
    e.fx_rate,
    e.amount_usd,
    e.receipt_indicator,
    e.is_fx_available
from expenses e
left join reports r 
    on e.report_id = r.report_id
left join employees emp 
    on e.employee_id = emp.employee_id
left join cost_centers cc 
    on e.cost_center_id = cc.cost_center_id
