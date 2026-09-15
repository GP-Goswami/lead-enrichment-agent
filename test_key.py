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

print("Testing first 30 model IDs from NVIDIA catalog:")
for m in models[:30]:
    try:
        res = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print(f"✅ WORKING MODEL FOUND: {m}")
        with open("working_model.txt", "w") as f:
            f.write(m)
        break
    except Exception as e:
        err_str = str(e)
        if "410" in err_str:
            print(f"❌ 410 Gone: {m}")
        elif "404" in err_str:
            print(f"❌ 404 Not Found/No Permission: {m}")
        else:
            print(f"❌ Other Error ({m}): {err_str[:60]}")
