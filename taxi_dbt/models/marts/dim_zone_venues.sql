{{ config(materialized='table') }}

with venue_zones as (
    select
        z.zone_id,
        z.zone_name,
        z.borough,
        v.venue_id,
        v.category_labels
    from {{ ref('stg_venues') }} v
    join {{ ref('stg_zones') }} z
      on st_within(v.venue_point, z.zone_geom)
)

select
    zone_id,
    zone_name,
    borough,
    count(*) as total_venues,
    countif(exists(select 1 from unnest(category_labels) l
                   where l like 'Dining and Drinking%'))                    as dining_venues,
    countif(exists(select 1 from unnest(category_labels) l
                   where l like 'Dining and Drinking > Bar%'))              as bar_venues,
    countif(exists(select 1 from unnest(category_labels) l
                   where l like 'Business and Professional Services > Office%')) as office_venues,
    countif(exists(select 1 from unnest(category_labels) l
                   where l like 'Retail%'))                                 as retail_venues,
    countif(exists(select 1 from unnest(category_labels) l
                   where l like 'Travel and Transportation > Lodging%'))    as lodging_venues,
    countif(exists(select 1 from unnest(category_labels) l
                   where l like 'Arts and Entertainment%'))                 as entertainment_venues
from venue_zones
group by zone_id, zone_name, borough