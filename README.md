# NYC Taxi Pipeline

An ELT pipeline that pulls NYC TLC yellow taxi trip data into BigQuery and models it
with dbt.

```
TLC public parquet  ──load_taxi.py──▶  taxi_raw.yellow_tripdata   (raw landing table)
                                              │
                                              ▼  dbt
                                       stg_yellow_tripdata        (view — cleaned)
                                              │
                                              ▼
                                       daily_trip_metrics         (table — one row/day)
```

## Layout

| Path | What it is |
| --- | --- |
| `load_taxi.py` | Extract + load. Downloads one month of TLC parquet and loads it into BigQuery. |
| `taxi_dbt/` | The dbt project (profile `taxi_dbt`, models under `taxi_dbt/models/`). |
| `venv/` | Local virtualenv — not tracked. |

## Prerequisites

- Python 3.12
- A Google Cloud project with BigQuery enabled. This pipeline targets
  `taxi-pipeline-503821`.
- `gcloud` CLI, authenticated for application-default credentials:

  ```
  gcloud auth application-default login
  ```

  Both `load_taxi.py` and dbt authenticate this way — dbt's profile uses
  `method: oauth`, so there is no service-account key file to manage.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

dbt reads its connection from `~/.dbt/profiles.yml`. The profile it expects:

```yaml
taxi_dbt:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: taxi-pipeline-503821
      dataset: taxi
      threads: 4
      location: US
      maximum_bytes_billed: 10000000000
```

Note the two datasets: raw data lands in `taxi_raw`, and dbt builds its models into
`taxi`.

## Running the pipeline

**1. Load raw data.** From the repo root:

```powershell
python load_taxi.py
```

This downloads `yellow_tripdata_2024-01.parquet` (~50 MB) into the working directory
and loads it into `taxi_raw.yellow_tripdata`. The month is set by the `MONTH`
constant at the top of the script.

The load uses `WRITE_TRUNCATE`, so **each run replaces the whole table** rather than
appending. Changing `MONTH` and re-running gives you that month *instead of*, not in
addition to, what was there before.

**2. Build and test the models.** From `taxi_dbt/`:

```powershell
cd taxi_dbt
dbt run
dbt test
```

`dbt run` builds `stg_yellow_tripdata` as a view and `daily_trip_metrics` as a table.
`dbt test` asserts `trip_date` in `daily_trip_metrics` is unique and non-null.

## The models

**`stg_yellow_tripdata`** (view) — the cleaning layer. Renames TLC's mixed-case
columns to snake_case, selects the subset of columns the marts need, and drops rows
with a negative `fare_amount` or `trip_distance`.

**`daily_trip_metrics`** (table) — one row per calendar pickup date, with
`total_trips`, `avg_distance`, `avg_fare`, and `total_revenue`. Materialized as a
table since it's small and gets queried repeatedly.

## Known limitations

- **Single month only.** Both the loader's `WRITE_TRUNCATE` and the hardcoded `MONTH`
  constant mean the warehouse holds exactly one month at a time.
- **No partitioning or clustering** on the raw table, so every model run scans the
  full month.
- **Thin test coverage.** Only `daily_trip_metrics.trip_date` is tested; the staging
  model has no tests of its own.
