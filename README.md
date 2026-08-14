# NYC Taxi Pipeline

An ELT pipeline that pulls NYC TLC yellow taxi trip data into BigQuery and models it
with dbt. Currently holds the full year 2024 (~40M trips) in a partitioned raw table,
with a validation suite guarding both the raw and cleaned layers.

```
TLC public parquet (12 months)  ──load_taxi.py──▶  taxi_raw.yellow_tripdata
                                                   (partitioned by pickup day)
                                                          │
                                                          ▼  dbt
                                                   stg_yellow_tripdata    (view — cleaned)
                                                          │
                                                          ▼
                                                   daily_trip_metrics     (table — one row/day)
```

## Layout

| Path | What it is |
| --- | --- |
| `load_taxi.py` | Extract + load. Downloads each month of 2024 TLC parquet and appends it into BigQuery. Idempotent: already-loaded months and already-downloaded files are skipped, so re-running is always safe. |
| `taxi_dbt/` | The dbt project (profile `taxi_dbt`). Models are organized by layer: `models/staging/` (views) and `models/marts/` (tables). |
| `taxi_dbt/tests/` | Singular data tests (SQL that returns bad rows). |
| `venv/` | Local virtualenv — not tracked. |

## Prerequisites

- Python 3.12
- A Google Cloud project with BigQuery enabled and **billing linked** (without
  billing, BigQuery sandbox tables expire after 60 days). This pipeline targets
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
cd taxi_dbt
dbt deps          # installs dbt_utils (used by the validation tests)
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
      maximum_bytes_billed: 10000000000   # hard cap: any query over 10 GB fails
```

Note the two datasets: raw data lands in `taxi_raw`, and dbt builds its models into
`taxi`.

## Running the pipeline

**1. Load raw data.** From the repo root:

```powershell
python load_taxi.py
```

Loops over all 12 months of 2024. For each month it checks whether that month is
already in the warehouse (skips if so), downloads the parquet if it isn't on disk,
and appends it with `WRITE_APPEND`. The raw table is day-partitioned on
`tpep_pickup_datetime`, so downstream queries scan only the days they touch.
BigQuery load jobs are free and don't consume query quota.

**2. Build and test the models.** From `taxi_dbt/`:

```powershell
dbt run
dbt test
```

`dbt run` builds the staging view and `daily_trip_metrics` (366 rows — one per day
of 2024). `dbt test` runs the 9-test validation suite.

## The models

**`stg_yellow_tripdata`** (view, `models/staging/`) — the cleaning layer. Renames
TLC's mixed-case columns to snake_case and filters out garbage the raw files are
known to contain:

- negative `fare_amount` or `trip_distance`
- pickups outside 2024 (stray rows in the monthly files claim dates years away)
- trips that end before they start (~1,500 such rows exist in the 2024 data)

**`daily_trip_metrics`** (table, `models/marts/`) — one row per calendar pickup
date, with `total_trips`, `avg_distance`, `avg_fare`, and `total_revenue`.

## Validation

Tests live at three layers, so bad data is caught as early as possible:

- **Source tests** (`models/staging/sources.yml`): raw trips must have pickup and
  dropoff timestamps and a `total_amount`.
- **Staging tests** (`models/schema.yml`): `pickup_at` not null;
  `fare_amount` and `trip_distance` within accepted ranges (`dbt_utils`) — proving
  the cleaning filters work on every run.
- **Mart tests**: `trip_date` unique and not null.
- **Singular test** (`tests/assert_dropoff_after_pickup.sql`): no trip may end
  before it starts.

## Roadmap

- **Airflow** (via Docker Compose): schedule load → run → test, with a weekly check
  that appends new TLC months as they're published.
- **Foursquare venue data**: bulk-load FSQ Open Source Places for NYC, join venues
  to taxi zones for enrichment.
- **Semantic layer** (MetricFlow): metrics defined once in YAML over the marts.
- **Vector DB + RAG**: ChromaDB over zone/venue profiles for descriptive questions.
- **AI agent**: tool-using agent that answers metric questions through the semantic
  layer and contextual questions through the vector DB.
