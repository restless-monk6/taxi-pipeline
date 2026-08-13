select
    VendorID as vendor_id,
    tpep_pickup_datetime as pickup_at,
    tpep_dropoff_datetime as dropoff_at,
    passenger_count,
    trip_distance,
    fare_amount,
    tip_amount,
    total_amount
from {{ source('taxi_raw', 'yellow_tripdata') }}
where fare_amount >= 0
  and trip_distance >= 0