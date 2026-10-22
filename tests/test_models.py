import pytest

from skilltest.models import (
    DEFAULT_MOCK_REPLY,
    ModelError,
    call_model,
    clear_mock_replies,
    set_mock_reply,
)


@pytest.fixture(autouse=True)
def reset_mocks():
    """Start every test with no canned replies."""
    clear_mock_replies()
    yield
    clear_mock_replies()


def test_mock_returns_default_reply():
    assert call_model("anything", "mock/basic") == DEFAULT_MOCK_REPLY


def test_mock_returns_canned_reply_when_prompt_matches():
    set_mock_reply("refund", '{"reply": "Sure", "tone": "polite"}')
    reply = call_model("I want a refund please", "mock/basic")
    assert reply == '{"reply": "Sure", "tone": "polite"}'


def test_fallback_used_when_first_model_fails():
    reply = call_model("hi", "mock/fail", fallbacks=["mock/backup"])
    assert reply == DEFAULT_MOCK_REPLY


def test_raises_model_error_when_all_models_fail():
    with pytest.raises(ModelError) as error:
        call_model("hi", "mock/fail", fallbacks=["mock/fail"])
    assert "All models failed" in str(error.value)