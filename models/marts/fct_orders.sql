with orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

joined as (
    select
        o.order_id,
        o.customer_id,
        o.product_id,
        o.order_date,
        o.order_status,
        o.quantity,
        p.price,
        (o.quantity * p.price) as total_amount
    from orders o
    left join products p on o.product_id = p.product_id
)

select * from joined
