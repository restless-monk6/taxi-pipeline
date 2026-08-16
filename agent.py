import os
import subprocess
import chromadb
from google import genai
from google.genai import types

# --- Tool 1: governed metrics via the semantic layer ---
def query_metrics(metrics: str, group_by: str = "", order_by: str = "", limit: int = 0) -> str:
    """Query governed metrics from the dbt/MetricFlow semantic layer.

    Args:
        metrics: comma-separated, from: total_trips, total_revenue, total_fares,
            total_tip_amount, avg_fare, avg_tip_pct
        group_by: comma-separated, from: metric_time__month, metric_time__day,
            trip__payment_type, trip__pickup_hour, pickup_zone__zone_name,
            pickup_zone__borough, pickup_zone__nightlife_tier
        order_by: optional column to sort by, prefix with - for descending,
            e.g. -total_trips
        limit: optional max rows
    """
    out_csv = os.path.abspath("agent_mf_result.csv")
    if os.path.exists(out_csv):
        os.remove(out_csv)
    cmd = ["mf", "query", "--metrics", metrics, "--csv", out_csv]
    if group_by:
        cmd += ["--group-by", group_by]
    if order_by:
        cmd += ["--order", order_by]
    if limit:
        cmd += ["--limit", str(limit)]
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace",
                            cwd="taxi_dbt", env=env)
    if os.path.exists(out_csv):
        with open(out_csv) as f:
            return f.read()[:6000]
    return f"Query failed. stderr: {result.stderr[-1500:]}"

# --- Tool 2: zone character via the vector DB ---
chroma = chromadb.PersistentClient(path="chroma")
zones = chroma.get_or_create_collection("zones")

def search_zones(query: str, n_results: int = 8) -> str:
    """Search NYC taxi-zone profiles (venues, character, activity) by meaning.

    Args:
        query: natural-language description of what to find
        n_results: how many zone profiles to return
    """
    res = zones.query(query_texts=[query], n_results=n_results)
    return "\n\n".join(res["documents"][0])

# --- The agent ---
gclient = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM = """You are a data analyst for NYC yellow taxi data. You have two tools:
- query_metrics: exact numbers, rankings, and time trends from a governed
  semantic layer. ALWAYS use this for counts, revenue, tips, averages,
  comparisons over time, or 'most/least' questions.
- search_zones: descriptive profiles of taxi zones (venues, character).
  Use this for 'what is X like' or vibe-based questions.
Never invent numbers. If a tool errors, say so and show what you tried.
Data covers roughly the last 12 months of trips."""

chat = gclient.chats.create(
    model="gemini-flash-latest",
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM,
        tools=[query_metrics, search_zones],
    ),
)

print("NYC Taxi Agent (type 'quit' to exit)")
while True:
    q = input("\nYou: ").strip()
    if not q:
        continue
    if q.lower() in ("quit", "exit"):
        break
    try:
        reply = chat.send_message(q)
        print("\nAgent:", reply.text)
    except Exception as e:
        print("\n[error]", e)
        print("(Usually transient — ask again in a moment, or type 'quit'.)")