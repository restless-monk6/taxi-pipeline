import os
import duckdb
from huggingface_hub import hf_hub_download

TOKEN = os.environ["HF_TOKEN"]
RELEASE = "release/dt=2026-08-11/places/parquet"
N_FILES = 100
OUT_DIR = "nyc_slices"
os.makedirs(OUT_DIR, exist_ok=True)

con = duckdb.connect()

KEEP = """fsq_place_id, name, latitude, longitude, address, locality,
          region, postcode, date_refreshed, date_closed,
          fsq_category_ids, fsq_category_labels"""

# NYC bounding box
LAT = "latitude BETWEEN 40.49 AND 40.92"
LON = "longitude BETWEEN -74.27 AND -73.68"

for i in range(N_FILES):
    out_file = f"{OUT_DIR}/nyc_{i:06d}.parquet"
    if os.path.exists(out_file):
        print(f"file {i}: already processed, skipping")
        continue
    fname = f"{RELEASE}/places_{i:06d}.parquet"
    print(f"file {i}: downloading ...")
    local = hf_hub_download(repo_id="foursquare/fsq-os-places", repo_type="dataset",
                            filename=fname, token=TOKEN, local_dir=".")
    con.sql(f"""
        COPY (
            SELECT {KEEP}
            FROM read_parquet('{fname}')
            WHERE {LAT} AND {LON}
              AND date_closed IS NULL
        ) TO '{out_file}' (FORMAT PARQUET)
    """)
    os.remove(local)
    print(f"file {i}: done")

print(con.sql(f"SELECT COUNT(*) AS nyc_venues FROM read_parquet('{OUT_DIR}/*.parquet')"))
con.sql(f"COPY (SELECT * FROM read_parquet('{OUT_DIR}/*.parquet')) TO 'nyc_venues.parquet' (FORMAT PARQUET)")
print("wrote nyc_venues.parquet")