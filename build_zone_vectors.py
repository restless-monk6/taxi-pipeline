from google.cloud import bigquery
import chromadb

PROJECT_ID = "taxi-pipeline-503821"

client = bigquery.Client(project=PROJECT_ID)
rows = list(client.query("""
    select
        v.zone_id, v.zone_name, v.borough,
        v.total_venues, v.bar_venues, v.dining_venues, v.office_venues,
        v.retail_venues, v.lodging_venues, v.entertainment_venues,
        t.total_trips, t.avg_fare, t.avg_tip_pct, t.avg_distance, t.late_night_trips
    from taxi.dim_zone_venues v
    left join taxi.zone_trip_stats t on t.zone_id = v.zone_id
""").result())

chroma = chromadb.PersistentClient(path="chroma")
collection = chroma.get_or_create_collection("zones")

ids, docs, metas = [], [], []
for r in rows:
    doc = (
        f"{r.zone_name} is a taxi zone in {r.borough}. "
        f"It has {r.total_venues} venues: {r.bar_venues} bars, "
        f"{r.dining_venues} dining spots, {r.office_venues} offices, "
        f"{r.retail_venues} retail stores, {r.lodging_venues} hotels or lodging, "
        f"and {r.entertainment_venues} arts and entertainment venues. "
    )
    tags = []
    if r.bar_venues >= 150:
        tags.append("one of the city's busiest nightlife and bar districts")
    elif r.bar_venues >= 50:
        tags.append("an active nightlife scene")
    if r.office_venues >= 400:
        tags.append("a major office and business district")
    if r.lodging_venues >= 40:
        tags.append("a tourist and hotel hub")
    if r.entertainment_venues >= 150:
        tags.append("rich in arts and entertainment")
    if r.dining_venues >= 800:
        tags.append("a dining destination")
    if tags:
        doc += "It is known as " + ", ".join(tags) + ". "
    if r.total_trips:
        doc += (
            f"Over the last year it saw {r.total_trips:,} taxi pickups "
            f"({r.late_night_trips:,} late-night), with an average fare of "
            f"${r.avg_fare}, average tip of {r.avg_tip_pct}%, and average "
            f"trip distance of {r.avg_distance} miles."
        )
    else:
        doc += "It saw no meaningful taxi pickup activity in the last year."
    ids.append(str(r.zone_id))
    docs.append(doc)
    metas.append({"zone_name": r.zone_name, "borough": r.borough})

collection.upsert(ids=ids, documents=docs, metadatas=metas)
print(f"Embedded {len(ids)} zone profiles into ./chroma")

# --- retrieval test ---
q = "trendy nightlife neighborhood in Brooklyn with lots of bars"
res = collection.query(query_texts=[q], n_results=3)
print(f"\nQuery: {q}")
for doc in res["documents"][0]:
    print("-", doc[:160], "...")
    
    
res = collection.query(query_texts=[q], n_results=10)
for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
    print(round(dist, 3), meta["zone_name"], "-", meta["borough"])