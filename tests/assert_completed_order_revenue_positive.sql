select
    order_id,
    total_amount
from {{ ref('fct_orders') }}
where order_status = 'completed'
  and total_amount <= 0
