# Project Progress Log

A running record of how this pipeline was built, what it taught, and where it
ended up. Companion to the README (which describes *what is*; this describes
*how it got here*). Status: **the original vision is built and working.**

## The story

### Recovery — rebuilding after the reformat

Resumed on a freshly reformatted PC with only `D:\taxi-pipeline` surviving.
Rebuilt Python + venv, gcloud + ADC, Docker + WSL2, and the dbt profile.
Discovered the original data had lived in a deleted GCP project and that
BigQuery sandbox mode had expired the tables (no billing linked). Fixed with
billing + a $1 budget alert + `maximum_bytes_billed` caps.

> **Lesson:** code is the asset; data is replaceable. Free and permanent beats
> free and expiring.

### Structure (`3beb2bd`)

Cleaned the dbt scaffold; organized models into `staging/` (views, cleaning)
and `marts/` (tables, aggregation). Bronze = `taxi_raw`, silver = staging,
gold = marts.

### Validation (`6ac7449`)

Nine tests across source / staging / mart layers, including a custom test that
caught **1,558 trips ending before they started** on day one.

> **Lesson:** tests are the alarm system for a pipeline nobody watches.

### Scale (`f0e4301`)

Append loading, day-partitioned raw table, idempotent month-by-month loads,
date-sanity filters in staging.

> **Lessons:** partitioning keeps queries cheap; idempotency makes
> interruption boring; SQL runs FROM → WHERE → SELECT.

### Orchestration (`601a6ce`)

Airflow 3.3.1 via the official Docker Compose stack, customized through
`docker-compose.override.yml` (project mount, ADC credentials, pip packages).
DAG: `load_taxi_data >> dbt_run >> dbt_test`, Saturdays 8am ET, catchup off.
Debugged a missing mount, a skipped override, and a dbt cache shared between
Windows and the container (fixed with container-local `DBT_TARGET_PATH`).

> **Lessons:** the scheduler is the brain, the UI just a window; everything is
> code; separate caches when environments share a folder.

### The storage saga (`7fe6258`)

At 9.92 GB of a 10 GB free tier, one rewrite delivered four fixes: schema
drift handled (TLC added `cbd_congestion_fee` mid-2025), idempotency
garbage-proofed (months count only with ≥1000 rows), columns trimmed 19 → 11
via pyarrow, and a 12-month rolling retention window. Result: **3.42 GB,
flat forever.**

> **Lessons:** measure, don't guess; upstream changes without asking; load
> only what you use; let pipelines forget.

### Foursquare enrichment (`8365468`)

FSQ OS Places (100 files, 111M places, gated behind a HF token) streamed
through a download-filter-delete DuckDB loop into **711,138 open NYC venues**;
TLC zone polygons from BigQuery public data; spatial join
(`ST_WITHIN(venue_point, zone_geom)`) into `dim_zone_venues` — venue counts
by category for 260 zones. East Village: 429 bars, most in the city.

> **Lessons:** coarse filter early (bounding box), exact filter late
> (polygons); facts append, dimensions (snapshots) replace; secrets live in
> environment variables, never in code.

### Semantic layer (`689ab85`, `76d482f`)

MetricFlow over the marts: a `trips` semantic model (measures, time and hour
dimensions, `pickup_zone` entity) and a `zones` model (borough,
`nightlife_tier` derived from bar counts), joined through the shared entity.
Six governed metrics; `mf query` answers any metric × dimension combination
with generated SQL.

**Finding #1:** bar-heavy zones tip 14.6% vs 12.5% in quiet zones.

> **Lessons:** define metrics once, in YAML; ratio metrics beat averaged
> percentages; edit YAML → `dbt parse` → then query (mf reads the compiled
> manifest, not your files).

### AI layer (`dcc83b8`)

Three programs on top of the platform:

- `build_zone_vectors.py` — writes an English profile of each zone *from
  warehouse data* (venues, trip stats, honest derived tags like "one of the
  city's busiest nightlife districts"), embeds them into a persistent ChromaDB
  store.
- `chat_zones.py` — RAG chat: retrieve top profiles by meaning, Gemini answers
  from ONLY that context.
- `agent.py` — the capstone: a tool-using agent (Gemini free tier) with
  `query_metrics` (drives MetricFlow → governed SQL → BigQuery) and
  `search_zones` (vector similarity). Numbers only ever come from the
  semantic layer; descriptions from the vector store.

Debugged along the way: a deprecated model name (fixed with the
`gemini-flash-latest` alias), mf's console output breaking in pipes (fixed by
switching the tool contract to CSV files), and mf's success unicorn 🦄
crashing Windows' cp1252 pipes (fixed with `PYTHONUTF8=1`).

**Finding #2:** the biggest tippers ride at 4–7 PM (15.0–15.6%); the 3–6 AM
crowd tips worst (8.3%). Generosity follows the neighborhood, not the
nightlife: bar-heavy *zones* tip well, bar-closing *hours* don't.

> **Lessons:** RAG quality is document quality — turn numbers into words;
> retrieval is a shortlister, the LLM is the reader; vectors do similarity,
> semantic layers do math — an agent needs both; docstrings are the tool
> manual the model actually reads.

## Final architecture

```
TLC monthly parquet ──▶ dynamic idempotent loader (11 cols, 12-mo window) ─┐
FSQ OS Places ──▶ DuckDB NYC extract ──▶ venue snapshot loader ────────────┤
TLC zone polygons (BQ public data) ────────────────────────────────────────┤
                                                                           ▼
                              BigQuery: taxi_raw (bronze, ~3.4 GB)
                                              │  dbt (Airflow, Sat 8am ET)
                                              ▼
                   staging views (silver) ──▶ marts (gold):
                   daily_trip_metrics · dim_zone_venues · zone_trip_stats
                            │                                │
             MetricFlow semantic layer                 zone profiles
             (6 metrics, entity joins)                 → ChromaDB vectors
                            │                                │
                            └────────── agent.py ────────────┘
                              (Gemini + tools: governed numbers
                               + semantic search, zero hallucinated math)
```

All code at `github.com/restless-monk6/taxi-pipeline`. Total cloud cost: **$0**.

## Habits adopted

- The repo is the source of truth; every session ends with commit + push.
- Logs over vibes; read the traceback to the line.
- Idempotency everywhere; re-running is always safe.
- Measure before deciding; interrogate every filter until it makes sense.
- Secrets in environment variables; ignore-rule first, then `git rm --cached`.
- Edit → parse → query: compilers before runtimes.

## Roadmap

- [x] Rebuild environment after reformat
- [x] Revive pipeline; validation suite
- [x] Full-scale loading with partitioning, retention, column trimming
- [x] Airflow orchestration (weekly, self-catching-up)
- [x] Foursquare enrichment + spatial join
- [x] Semantic layer (MetricFlow)
- [x] Vector DB + RAG chat
- [x] AI agent over the semantic layer

### Ideas for later

- Streamlit chat UI over the agent
- Monthly venue-refresh DAG (needs HF token in Airflow via Connections)
- Tag rows with source-file month (kill phantom days for good)
- Custom Airflow image (replace `_PIP_ADDITIONAL_REQUIREMENTS`)
- More metrics: airport-trip share, congestion-fee analysis, weekday/weekend
