from skilltest import run_skill

for model in ["ollama/qwen2.5:3b", "groq/openai/gpt-oss-20b"]:
    out = run_skill(
        "examples/demo_skills/support_reply.md",
        input="I bought this 10 days ago and it broke. I want my money back.",
        company="Acme",
        model=model,
    )
    print(f"--- {model} ---\n{out}\n")