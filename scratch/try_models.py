from dotenv import load_dotenv
import litellm

load_dotenv()  # reads GROQ_API_KEY from .env into the environment

MODELS = [
    "ollama/qwen2.5:3b",           # local, free, unlimited
    "groq/openai/gpt-oss-20b",     # cloud, fast
    "groq/openai/gpt-oss-120b",    # cloud, strongest (our judge)
]

for model in MODELS:
    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Say hi in exactly 5 words."}],
            temperature=0,
        )
        print(f"{model} -> {response.choices[0].message.content}")
    except Exception as error:
        print(f"{model} FAILED: {type(error).__name__}: {error}")