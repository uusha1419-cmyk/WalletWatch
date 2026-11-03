import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

c = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=45000),  # 45 sec
)

print("Models with 'flash' in the name:")
for m in c.models.list():
    if "flash" in m.name:
        print(" ", m.name)

print()
for name in ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-2.5-flash-lite", "gemini-3.5-flash"):
    t = time.time()
    try:
        c.models.generate_content(model=name, contents="Say hello in one sentence")
        print(name, "OK", round(time.time() - t, 1), "sec")
    except Exception as e:
        print(name, "FAILED", round(time.time() - t, 1), "sec", str(e)[:200])