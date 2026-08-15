select
    VendorID as vendor_id,
    tpep_pickup_datetime as pickup_at,
    tpep_dropoff_datetime as dropoff_at,
	PULocationID as pickup_zone_id,
    DOLocationID as dropoff_zone_id,
    payment_type,
    passenger_count,
    trip_distance,
    fare_amount,
    tip_amount,
    total_amount
from {{ source('taxi_raw', 'yellow_tripdata') }}
where fare_amount >= 0
  and trip_distance >= 0
  and tpep_pickup_datetime >= timestamp(date_trunc(date_sub(current_date(), interval 12 month), month))
  and tpep_pickup_datetime < timestamp(date_trunc(current_date(), month))
  and tpep_dropoff_datetime >= tpep_pickup_datetime