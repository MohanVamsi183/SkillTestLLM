"""Model layer: one function to call any LLM, with fallbacks and a mock for tests."""

from __future__ import annotations

import litellm
from dotenv import load_dotenv

load_dotenv()                        # read API keys from .env
litellm.suppress_debug_info = True   # hide LiteLLM's "Give Feedback" banner


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
) -> str:
    """Send `prompt` to `model`; if it fails, try each fallback in order.

    Returns the first successful reply. Raises ModelError listing every
    failure if all models fail.
    """
    errors: list[str] = []
    for candidate in [model, *fallbacks]:
        try:
            return _call_one(prompt, candidate, temperature)
        except Exception as error:  # rate limit, bad name, network, ...
            errors.append(f"{candidate}: {type(error).__name__}: {error}")
    raise ModelError("All models failed:\n" + "\n".join(errors))