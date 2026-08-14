from google.cloud import bigquery
import urllib.request
import os

# --- Settings ---
PROJECT_ID = "taxi-pipeline-503821"
DATASET = "taxi_raw"
TABLE = "yellow_tripdata"
MONTHS = [f"2024-{m:02d}" for m in range(1, 13)]  # all of 2024

client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

# --- Which months are already loaded? (makes re-runs safe) ---
def loaded_months():
    try:
        q = f"""select distinct format_timestamp('%Y-%m', tpep_pickup_datetime) as m
                from `{table_id}`"""
        return {row.m for row in client.query(q).result()}
    except Exception:
        return set()  # table doesn't exist yet

already = loaded_months()
print(f"Already loaded: {sorted(already) or 'nothing'}")

# --- Load config: append + daily partitioning on pickup time ---
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    write_disposition="WRITE_APPEND",
    time_partitioning=bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="tpep_pickup_datetime",
    ),
)

for month in MONTHS:
    if month in already:
        print(f"{month}: already loaded, skipping")
        continue
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet"
    local_file = f"yellow_tripdata_{month}.parquet"
    if not os.path.exists(local_file):
        print(f"{month}: downloading ...")
        urllib.request.urlretrieve(url, local_file)
    print(f"{month}: loading ...")
    with open(local_file, "rb") as f:
        client.load_table_from_file(f, table_id, job_config=job_config).result()
    print(f"{month}: done")

table = client.get_table(table_id)
print(f"Table now holds {table.num_rows:,} rows.")