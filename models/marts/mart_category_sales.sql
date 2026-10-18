with fct as (
    select * from {{ ref('fct_orders') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

category_summary as (
    select
        p.category,
        count(f.order_id) as total_orders,
        coalesce(sum(case when f.order_status= 'completed' then f.total_amount else 0 end), 0) as total_revenue
    from products p
    left join fct f on p.product_id = f.product_id
    group by 1
)

select * from category_summary
