select
    zone_id,
    zone_name,
    borough,
    zone_geom
from {{ source('taxi_raw', 'zones') }}