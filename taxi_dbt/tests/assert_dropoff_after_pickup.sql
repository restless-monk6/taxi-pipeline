{{ config(severity = 'warn') }}

select *
from {{ ref('stg_yellow_tripdata') }}
where dropoff_at < pickup_at