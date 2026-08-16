import os
import chromadb
from google import genai

gclient = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
chroma = chromadb.PersistentClient(path="chroma")
zones = chroma.get_or_create_collection("zones")

print("Chat with your NYC zone data (type 'quit' to exit)")
while True:
    q = input("\nYou: ").strip()
    if not q:
        continue
    if q.lower() in ("quit", "exit"):
        break

    res = zones.query(query_texts=[q], n_results=6)
    context = "\n\n".join(res["documents"][0])

    prompt = f"""You are an assistant answering questions about New York City
neighborhoods, using taxi-zone profiles derived from real warehouse data.

Answer the question using ONLY the context below. If the context doesn't
contain what's needed, say so plainly — do not guess. Mention zone names
when relevant.

Context:
{context}

Question: {q}"""

    reply = gclient.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
    )
    print("\nAssistant:", reply.text)