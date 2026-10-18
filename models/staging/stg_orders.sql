with source as (
    select * from {{ source('raw', 'ORDERS') }}
),

deduped as (
    select
        *,
        row_number() over (partition by order_id order by order_date desc) as rn
    from source
),

renamed as (
    select
        cast(order_id as integer) as order_id,
        cast(customer_id as integer) as customer_id,
        cast(product_id as integer) as product_id,
        cast(quantity as integer) as quantity,
        cast(order_date as date) as order_date,
        trim(status) as order_status
    from deduped
    where rn = 1
)

select * from renamed
