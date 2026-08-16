{{ config(materialized='table') }}

select
    pickup_zone_id as zone_id,
    count(*) as total_trips,
    round(avg(fare_amount), 2) as avg_fare,
    round(safe_divide(sum(tip_amount), sum(fare_amount)) * 100, 1) as avg_tip_pct,
    round(avg(trip_distance), 2) as avg_distance,
    countif(extract(hour from pickup_at) >= 22 or extract(hour from pickup_at) <= 4)
        as late_night_trips
from {{ ref('stg_yellow_tripdata') }}
group by zone_id