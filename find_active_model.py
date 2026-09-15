import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv('NVIDIA_API_KEY'), base_url='https://integrate.api.nvidia.com/v1')

models = [m.id for m in client.models.list().data]

active_model = None
for m in models:
    # Skip vision or guard or embed models
    if any(k in m for k in ['embed', 'guard', 'vlm', 'reward', 'rerank', 'safety', 'starcoder', 'deplot']):
        continue
    try:
        res = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        active_model = m
        print(f"FOUND: {m}")
        break
    except Exception as e:
        print(f"Failed {m}: {str(e)[:80]}")

if active_model:
    with open("active_model.txt", "w") as f:
        f.write(active_model)
