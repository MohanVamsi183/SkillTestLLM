import os

import requests
from dotenv import load_dotenv

load_dotenv()

response = requests.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
    timeout=30,
)
print("Status:", response.status_code)

if response.ok:
    for model in sorted(m["id"] for m in response.json()["data"]):
        print(model)
else:
    print(response.text)