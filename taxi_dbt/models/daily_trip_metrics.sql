{{ config(materialized='table') }}

select
    date(pickup_at) as trip_date,
    count(*) as total_trips,
    round(avg(trip_distance), 2) as avg_distance,
    round(avg(fare_amount), 2) as avg_fare,
    round(sum(total_amount), 2) as total_revenue
from {{ ref('stg_yellow_tripdata') }}
group by trip_date
order by trip_date