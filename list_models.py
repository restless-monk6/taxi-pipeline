import os
from google import genai

gclient = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for m in gclient.models.list():
    print(m.name)