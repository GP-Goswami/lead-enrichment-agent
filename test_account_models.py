import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv('NVIDIA_API_KEY'), base_url='https://integrate.api.nvidia.com/v1')

models = [m.id for m in client.models.list().data]

print(f"Testing all {len(models)} models for account permissions...")
working_models = []

for m in models:
    try:
        res = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print(f"FOUND WORKING MODEL: {m}")
        working_models.append(m)
    except Exception as e:
        err = str(e)
        if "404" not in err and "410" not in err:
            print(f"Model {m} error: {err[:80]}")

print("\n=== SUMMARY OF WORKING MODELS ===")
print(working_models)
with open("working_models_list.txt", "w") as f:
    f.write("\n".join(working_models))
