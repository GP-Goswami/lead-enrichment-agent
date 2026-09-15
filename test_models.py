import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://integrate.api.nvidia.com/v1"
)

models = [m.id for m in client.models.list().data]

working = []
for m in models:
    try:
        res = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print(f"SUCCESS MODEL: {m}")
        working.append(m)
        if len(working) >= 3:
            break
    except Exception as e:
        pass

print("ALL WORKING MODELS FOUND:", working)
with open("working_models.txt", "w") as f:
    f.write("\n".join(working))
