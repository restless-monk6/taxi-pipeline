select
    fsq_place_id as venue_id,
    name as venue_name,
    latitude,
    longitude,
    st_geogpoint(longitude, latitude) as venue_point,
    postcode,
    locality,
    fsq_category_labels as category_labels,
    split(fsq_category_labels[safe_offset(0)], ' > ')[safe_offset(0)] as primary_category
from {{ source('taxi_raw', 'fsq_venues') }}
where latitude is not null
  and longitude is not null
  and name is not null