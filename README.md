# skilltest

Unit testing for LLM prompts and skills, built on pytest.

skilltest lets you treat a prompt file like code: load it, fill in its variables, run it against any LLM, and check the result in an ordinary pytest test. Model replies are cached on disk, so re-running a test suite costs nothing, and a replay mode lets tests run with no network access and no API keys.

The whole project runs on free models: local models through Ollama and free-tier cloud models through Groq.

## Why

Prompts and skill files (reusable instruction files for an LLM) break in quiet ways. Someone edits one line, a model gets upgraded, or a user sends an input nobody expected, and the output changes without any error. Code has unit tests to catch this. Prompts usually have nothing.

skilltest brings the familiar pytest workflow to prompts:

- Write tests as plain pytest functions.
- Run the same prompt against local and cloud models with one line changed.
- Fall back to another model automatically when one fails or hits a rate limit.
- Cache every reply so repeated runs are instant and free.
- Replay recorded replies so tests are reproducible and can run offline.

## Features

**Skill files with safe templating.** A skill is a Markdown file containing a prompt with `{placeholders}`. `run_skill()` fills only the placeholders you pass in and leaves every other brace untouched, so prompts can safely contain JSON examples such as `{"reply": "...", "tone": "..."}`. Python's built-in `str.format()` would crash on those.

**One function for any model.** `call_model()` wraps [LiteLLM](https://docs.litellm.ai/), so the same code calls a local Ollama model, Groq, Gemini, OpenAI, Anthropic and many others. Only the model name changes.

**Fallback chain.** Give a list of fallback models. If the first model fails for any reason (rate limit, outage, wrong name), skilltest tries the next one and only raises an error after every model has failed, listing each failure.

**Disk cache.** Every reply is saved as a JSON file named by a SHA-256 fingerprint of the model, prompt, temperature and run number. The same request is served from disk the next time. Changing even one character of the prompt produces a new fingerprint and a fresh model call.

**Replay mode.** With replay switched on, skilltest never calls a model. It serves recorded replies only and fails with a clear message if a reply was never recorded. This makes test runs deterministic and lets CI run without API keys.

**Mock models.** Any model name starting with `mock/` returns canned replies instantly with no network access. skilltest's own test suite uses these, which keeps it fast and deterministic.

## Quickstart

### Requirements

- Python 3.11 or newer
- [Ollama](https://ollama.com) for free local models (optional but recommended)
- A free [Groq](https://console.groq.com) API key for cloud models (optional)

### Install

```bash
git clone https://github.com/MohanVamsi183/SkillTestLLM.git
cd SkillTestLLM
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install the package in editable mode:

```bash
pip install -e .
```

Pull a small local model:

```bash
ollama pull qwen2.5:3b
```

### API keys

Create a file named `.env` in the project root. It is listed in `.gitignore` and is never committed.

```text
GROQ_API_KEY=your_key_here
```

Model availability differs between Groq accounts. To see which models your key can use, call `https://api.groq.com/openai/v1/models` with your key.

## Usage

### 1. Write a skill

`examples/demo_skills/support_reply.md`:

```markdown
You are a customer support agent for {company}.
Refunds are allowed within 30 days of purchase.

Reply to the customer message below. Respond with ONLY a JSON object with
exactly two keys: "reply" (your message to the customer) and "tone"
(one word describing your tone). No other text.

Customer message: {input}
```

### 2. Run it

```python
from skilltest import run_skill

out = run_skill(
    "examples/demo_skills/support_reply.md",
    input="I bought this 10 days ago and it broke. I want my money back.",
    company="Acme",
)
print(out)
```

Example output from `qwen2.5:3b`:

```json
{
  "reply": "Hello, I'm sorry to hear about your issue. Refunds are typically allowed within 30 days of purchase. Since you bought it 10 days ago, we can process your refund. Please provide us with the order details so we can proceed. Thanks for your patience.",
  "tone": "apologetic"
}
```

To try a different model for one call, pass `model=`:

```python
out = run_skill(
    "examples/demo_skills/support_reply.md",
    input="Can I still return this?",
    company="Acme",
    model="groq/openai/gpt-oss-20b",
)
```

### 3. Test it with pytest

```python
import json
from pathlib import Path

from skilltest import run_skill

SKILL = Path(__file__).parent / "demo_skills" / "support_reply.md"


def test_refund_reply_is_valid_json_with_two_keys():
    out = run_skill(
        SKILL,
        input="I bought this 10 days ago and it broke. I want my money back.",
        company="Acme",
    )
    data = json.loads(out)
    assert set(data) == {"reply", "tone"}


def test_reply_mentions_30_days():
    out = run_skill(SKILL, input="Can I still return this? I bought it 3 weeks ago.", company="Acme")
    assert "30" in out
```

### 4. Configure

Settings live in one shared object. Change them in a `conftest.py` to apply them to every test:

```python
from skilltest.config import settings

settings.model = "groq/openai/gpt-oss-20b"   # model that runs skills
settings.fallbacks = ["ollama/qwen2.5:3b"]   # tried in order if the main model fails
settings.temperature = 0.7                   # above 0 so repeated runs can differ
settings.use_cache = True                    # save and reuse replies
settings.replay = False                      # True = recorded replies only, no model calls
```

| Setting | Default | Meaning |
| --- | --- | --- |
| `model` | `ollama/qwen2.5:3b` | Model that runs skills |
| `judge` | `groq/openai/gpt-oss-120b` | Model reserved for LLM-as-judge checks |
| `fallbacks` | `[]` | Models to try in order if the main model fails |
| `temperature` | `0.7` | Sampling temperature for skill runs |
| `cache_dir` | `.skilltest_cache` | Folder for saved replies |
| `use_cache` | `True` | Save and reuse replies |
| `replay` | `False` | Serve recorded replies only |

### 5. Call a model directly

The lower-level model layer can be used on its own:

```python
from skilltest.cache import Cache
from skilltest.models import call_model

reply = call_model(
    "Name one planet.",
    "groq/openai/gpt-oss-20b",
    fallbacks=["ollama/qwen2.5:3b"],
    cache=Cache(),
)
```

Measured on the author's machine, the first call took 8.91 seconds (including the one-time library import and the API call) and the cached second call took 0.01 seconds.

## Running the tests

```bash
pytest -v
```

The suite has 19 tests covering the model layer, fallbacks, the cache, replay mode, templating and skill loading. It uses mock models only, so it needs no network access or API keys and finishes in under a second.

## Project structure

```text
SkillTestLLM/
├── pyproject.toml            package metadata and pytest plugin entry point
├── src/skilltest/
│   ├── __init__.py           public API: run_skill
│   ├── plugin.py             pytest plugin hooks
│   ├── config.py             shared settings
│   ├── models.py             LiteLLM wrapper, fallback chain, mock models
│   ├── cache.py              on-disk reply cache and replay support
│   └── skill.py              skill loading, safe templating, run_skill
├── tests/                    tests for skilltest itself (mock models only)
├── examples/demo_skills/     example skill files
└── .skilltest_cache/         recorded model replies
```

## Design decisions

**Lazy import of LiteLLM.** LiteLLM takes several seconds to import. It is imported inside the function that calls a real model, so code paths that only use mock models or the cache never load it. This cut the test suite from 7.28 seconds to 0.23 seconds.

**Cache keyed by the requested model.** The cache key uses the model you asked for, not the fallback that answered, so the next run finds the reply whichever model produced it. The saved file still records which model actually answered.

**Safe templating instead of `str.format()`.** Only placeholders that you pass are replaced. Any other text in braces, including JSON examples and unknown placeholders, is left exactly as written.

**Replay never reaches the network.** `call_model()` checks the cache first, then stops if replay is on, and only then calls a model. This order guarantees that replay mode cannot make a network request.

## Roadmap

- [x] Package skeleton registered as a pytest plugin
- [x] Model layer with fallback chain and mock models
- [x] Disk cache and replay mode
- [x] Skill files with safe templating and `run_skill()`
- [ ] Command-line flags (`--skilltest-model`, `--replay`, `--no-cache`) and `[tool.skilltest]` config in `pyproject.toml`
- [ ] Assertion helpers: `assert_json`, `assert_contains`, `assert_regex`, `assert_max_words`
- [ ] LLM-as-judge assertion with structured pass/fail verdicts
- [ ] Repeated runs with a pass-rate threshold for non-deterministic outputs
- [ ] Snapshot drift detection using sentence embeddings
- [ ] Automatic edge-case inputs: empty, very long, multilingual, prompt injection
- [ ] GitHub Actions CI that runs in replay mode with no API keys
- [ ] Publish to PyPI

## Tech stack

Python 3.11+, pytest, LiteLLM, Ollama, Groq API, python-dotenv

## Acknowledgements

Based on the "Unit Testing LLM Skills" research idea in [gpsaggese/gpsaggese.github.io](https://github.com/gpsaggese/gpsaggese.github.io/tree/master/research/ideas).

## License

MIT
