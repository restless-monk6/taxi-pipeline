# taxi_dbt

The dbt project for the NYC taxi pipeline. See the [repo root README](../README.md)
for prerequisites, BigQuery setup, and how to load the raw data this project reads
from.

## Commands

Run these from this directory:

```powershell
dbt run     # build stg_yellow_tripdata (view) and daily_trip_metrics (table)
dbt test    # assert trip_date is unique and non-null
dbt build   # both, in dependency order
```

## Sources and models

| Resource | Type | Notes |
| --- | --- | --- |
| `taxi_raw.yellow_tripdata` | source | Landed by `../load_taxi.py`. One month at a time. |
| `stg_yellow_tripdata` | view | Renames columns to snake_case, filters negative fares and distances. |
| `daily_trip_metrics` | table | One row per pickup date: trip count, avg distance, avg fare, total revenue. |

Models build into the `taxi` dataset; the source lives in `taxi_raw`.
