from datetime import date
from google.cloud import bigquery
import pyarrow.parquet as pq
import urllib.request
import urllib.error
import os

# --- Settings ---
PROJECT_ID = "taxi-pipeline-503821"
DATASET = "taxi_raw"
TABLE = "yellow_tripdata"
START_YEAR, START_MONTH = 2025, 1   # earliest history we ever want
RETENTION_MONTHS = 12               # rolling window: keep at most 1 years

# Only the columns we actually use downstream.
KEEP_COLUMNS = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "tip_amount",
    "total_amount",
]

def retention_cutoff():
    """First day of the oldest month we keep."""
    today = date.today()
    total = today.year * 12 + (today.month - 1) - RETENTION_MONTHS
    y, m = divmod(total, 12)
    return date(y, m + 1, 1)

def candidate_months():
    """From our start (or the retention cutoff, whichever is later) to now."""
    cut = retention_cutoff()
    y, m = max((START_YEAR, START_MONTH), (cut.year, cut.month))
    months = []
    today = date.today()
    while (y, m) <= (today.year, today.month):
        months.append(f"{y}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return months

client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

def loaded_months():
    try:
        q = f"""select format_timestamp('%Y-%m', tpep_pickup_datetime) as m
                from `{table_id}`
                group by m
                having count(*) >= 1000"""
        return {row.m for row in client.query(q).result()}
    except Exception:
        return set()

already = loaded_months()
print(f"Already loaded: {sorted(already) or 'nothing'}")

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    write_disposition="WRITE_APPEND",
    time_partitioning=bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="tpep_pickup_datetime",
    ),
)

for month in candidate_months():
    if month in already:
        print(f"{month}: already loaded, skipping")
        continue
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet"
    local_file = f"yellow_tripdata_{month}.parquet"
    slim_file = f"slim_{month}.parquet"
    if not os.path.exists(local_file):
        print(f"{month}: downloading ...")
        try:
            urllib.request.urlretrieve(url, local_file)
        except urllib.error.HTTPError:
            print(f"{month}: not published by TLC yet, skipping")
            continue
    print(f"{month}: trimming to {len(KEEP_COLUMNS)} columns ...")
    table_data = pq.read_table(local_file, columns=KEEP_COLUMNS)
    pq.write_table(table_data, slim_file)
    print(f"{month}: loading ...")
    with open(slim_file, "rb") as f:
        client.load_table_from_file(f, table_id, job_config=job_config).result()
    os.remove(slim_file)
    print(f"{month}: done")

# --- Rolling window: forget months past retention ---
cutoff = retention_cutoff()
print(f"Retention: deleting anything before {cutoff} ...")
client.query(
    f"DELETE FROM `{table_id}` WHERE tpep_pickup_datetime < '{cutoff}'"
).result()

table = client.get_table(table_id)
print(f"Table now holds {table.num_rows:,} rows.")