from skilltest.models import call_model

reply = call_model(
    "Say hi in 5 words.",
    "groq/this-model-does-not-exist",               # will fail
    fallbacks=["groq/openai/gpt-oss-20b", "ollama/qwen2.5:3b"],
)
print(reply)