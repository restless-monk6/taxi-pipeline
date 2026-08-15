from google.cloud import bigquery

PROJECT_ID = "taxi-pipeline-503821"
DATASET = "taxi_raw"
TABLE = "fsq_venues"
LOCAL = "nyc_venues.parquet"

client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

parquet_options = bigquery.ParquetOptions()
parquet_options.enable_list_inference = True

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    write_disposition="WRITE_TRUNCATE",
    parquet_options=parquet_options,
)

with open(LOCAL, "rb") as f:
    client.load_table_from_file(f, table_id, job_config=job_config).result()

table = client.get_table(table_id)
print(f"Loaded {table.num_rows:,} venues into {table_id}.")