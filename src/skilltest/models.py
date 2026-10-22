"""Model layer: one function to call any LLM, with fallbacks, caching and a mock for tests."""

from __future__ import annotations

from dotenv import load_dotenv

from skilltest.cache import Cache, CacheMiss, make_key

load_dotenv()  # read API keys from .env


class ModelError(Exception):
    """Raised when every model in the fallback chain fails."""


# ---------------------------------------------------------------------------
# Mock models: any model name starting with "mock/" never touches the network.
#   mock/<anything>  -> returns a canned reply
#   mock/fail        -> always raises (used to test fallbacks)
# ---------------------------------------------------------------------------
_MOCK_REPLIES: dict[str, str] = {}
DEFAULT_MOCK_REPLY = "mock reply"


def set_mock_reply(prompt_contains: str, reply: str) -> None:
    """Make mock models return `reply` whenever the prompt contains `prompt_contains`."""
    _MOCK_REPLIES[prompt_contains] = reply


def clear_mock_replies() -> None:
    """Forget all canned replies."""
    _MOCK_REPLIES.clear()


def _call_mock(prompt: str, model: str) -> str:
    if model == "mock/fail":
        raise RuntimeError("mock/fail always fails")
    for fragment, reply in _MOCK_REPLIES.items():
        if fragment in prompt:
            return reply
    return DEFAULT_MOCK_REPLY


def _call_one(prompt: str, model: str, temperature: float) -> str:
    """Call a single model and return its text reply."""
    if model.startswith("mock/"):
        return _call_mock(prompt, model)

    # Lazy import: litellm takes seconds to load, and mock-only runs never need it.
    import litellm

    litellm.suppress_debug_info = True
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def call_model(
    prompt: str,
    model: str,
    *,
    fallbacks: list[str] | tuple[str, ...] = (),
    temperature: float = 0.0,
    cache: Cache | None = None,
    run_index: int = 0,
    replay: bool = False,
) -> str:
    """Send `prompt` to `model`, trying each fallback in order if it fails.

    - cache:     if given, reuse a saved reply or save the new one
    - run_index: lets the same prompt be cached several times (for repeated runs)
    - replay:    never call a model; raise CacheMiss if no saved reply exists
    """
    key = make_key(model, prompt, temperature, run_index)

    if cache is not None:
        saved = cache.get(key)
        if saved is not None:
            return saved

    if replay:
        raise CacheMiss(
            f"No saved reply for model={model!r}, run {run_index}. "
            "Run once without --replay to record it."
        )

    errors: list[str] = []
    for candidate in [model, *fallbacks]:
        try:
            reply = _call_one(prompt, candidate, temperature)
        except Exception as error:  # rate limit, bad name, network, ...
            errors.append(f"{candidate}: {type(error).__name__}: {error}")
            continue
        if cache is not None:
            cache.set(key, reply, model=candidate, prompt=prompt)
        return reply

    raise ModelError("All models failed:\n" + "\n".join(errors))