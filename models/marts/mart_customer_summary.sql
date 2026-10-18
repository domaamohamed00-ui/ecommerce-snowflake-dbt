with fct as (
    select * from {{ ref('fct_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

summary as (
    select
        c.customer_id,
        c.customer_name,
        c.email,
        c.city,
        count(f.order_id) as total_orders,
        coalesce(sum(case when f.order_status = 'completed' then f.total_amount else 0 end), 0) as total_spent
    from customers c
    left join fct f on c.customer_id = f.customer_id
    group by 1, 2, 3, 4
)

select * from summary
