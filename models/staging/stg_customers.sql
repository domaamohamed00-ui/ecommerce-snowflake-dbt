with source as (
    select * from {{ source('raw', 'CUSTOMERS') }}
),

renamed as (
    select
        cast(customer_id as integer) as customer_id,
        trim(customer_name) as customer_name,
        lower(trim(email)) as email,
        trim(city) as city,
        cast(signup_date as date) as signup_date
    from source
    where customer_id is not null
)

select * from renamed
