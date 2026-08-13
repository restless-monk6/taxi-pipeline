from google.cloud import bigquery
import urllib.request

# --- Settings ---
PROJECT_ID = "taxi-pipeline-503821"
DATASET = "taxi_raw"
TABLE = "yellow_tripdata"
MONTH = "2024-01"  # the month of data we're pulling

# --- 1. EXTRACT: download one month of taxi data ---
url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{MONTH}.parquet"
local_file = f"yellow_tripdata_{MONTH}.parquet"

print(f"Downloading {url} ...")
urllib.request.urlretrieve(url, local_file)
print("Download complete.")

# --- 2. LOAD: push the file into BigQuery ---
client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    write_disposition="WRITE_TRUNCATE",  # replace the table each run
)

print(f"Loading into {table_id} ...")
with open(local_file, "rb") as f:
    load_job = client.load_table_from_file(f, table_id, job_config=job_config)

load_job.result()  # wait for it to finish

table = client.get_table(table_id)
print(f"Done. Loaded {table.num_rows:,} rows into {table_id}.")