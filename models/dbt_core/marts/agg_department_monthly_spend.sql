with expense_facts as (
    select * from {{ ref('fct_expense_transactions') }}
),

budgets as (
    -- Fixed: Switched file location link reference to match standard reference source layout
    select * from {{ ref('stg_monthly_budgets') }}
),

department_actuals as (
    select
        accounting_period,
        department_name,
        expense_category,
        sum(case when is_fx_available = true then amount_usd else 0 end) as actual_spend_usd
    from expense_facts
    group by 1, 2, 3
),

joined_spend as (
    select
        coalesce(a.accounting_period, b.accounting_period) as accounting_period,
        coalesce(a.department_name, b.department_name) as department_name,
        coalesce(a.expense_category, b.expense_category) as expense_category,
        coalesce(a.actual_spend_usd, 0) as actual_spend_usd,
        cast(b.budget_usd as decimal(18, 2)) as budget_usd
    from department_actuals a
    full outer join budgets b
        on a.accounting_period = b.accounting_period
        and a.department_name = b.department_name
        and a.expense_category = b.expense_category
)

select
    accounting_period,
    department_name,
    expense_category,
    actual_spend_usd,
    budget_usd,
    
    case 
        when budget_usd is null or budget_usd = 0 then null
        else cast(actual_spend_usd - budget_usd as decimal(18, 2))
    end as budget_variance,

    case 
        when budget_usd is null or budget_usd = 0 then null
        else cast((actual_spend_usd - budget_usd) / budget_usd as decimal(18, 4))
    end as budget_variance_percentage
from joined_spend
