import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv('NVIDIA_API_KEY'),
    base_url='https://integrate.api.nvidia.com/v1',
    timeout=10.0
)

models = [
    'deepseek-ai/deepseek-v4-flash-0731',
    'google/diffusiongemma-26b-a4b-it',
    'google/gemma-4-31b-it',
    '01-ai/yi-large',
    'adept/fuyu-8b',
    'databricks/dbrx-instruct'
]

fastest_model = None

for m in models:
    t0 = time.time()
    try:
        res = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
            timeout=8.0
        )
        t1 = time.time()
        print(f"SUCCESS: {m} responded in {t1-t0:.2f} seconds!")
        if not fastest_model:
            fastest_model = m
    except Exception as e:
        print(f"FAILED {m}: {str(e)[:70]}")

print(f"\nFASTEST WORKING MODEL: {fastest_model}")
