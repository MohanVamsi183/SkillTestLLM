import pytest

from skilltest.cache import Cache, CacheMiss, make_key
from skilltest.models import call_model, clear_mock_replies, set_mock_reply


@pytest.fixture(autouse=True)
def reset_mocks():
    clear_mock_replies()
    yield
    clear_mock_replies()


@pytest.fixture
def cache(tmp_path):
    """A fresh cache in a temporary folder that pytest deletes afterwards."""
    return Cache(tmp_path / "cache")


def test_same_inputs_give_same_key():
    assert make_key("m", "p", 0.0) == make_key("m", "p", 0.0)


def test_different_run_index_gives_different_key():
    assert make_key("m", "p", 0.0, run_index=0) != make_key("m", "p", 0.0, run_index=1)


def test_set_then_get_returns_reply(cache):
    cache.set("abc", "hello", model="m", prompt="p")
    assert cache.get("abc") == "hello"


def test_missing_key_returns_none(cache):
    assert cache.get("never-saved") is None


def test_disabled_cache_never_stores(tmp_path):
    cache = Cache(tmp_path / "cache", enabled=False)
    cache.set("abc", "hello", model="m", prompt="p")
    assert cache.get("abc") is None


def test_second_call_is_served_from_cache(cache):
    set_mock_reply("hi", "first answer")
    assert call_model("hi", "mock/x", cache=cache) == "first answer"

    # The "model" would now answer differently, but the cached reply wins.
    set_mock_reply("hi", "second answer")
    assert call_model("hi", "mock/x", cache=cache) == "first answer"


def test_replay_raises_when_nothing_recorded(cache):
    with pytest.raises(CacheMiss):
        call_model("hi", "mock/x", cache=cache, replay=True)


def test_replay_works_after_recording(cache):
    set_mock_reply("hi", "recorded")
    call_model("hi", "mock/x", cache=cache)             # record
    clear_mock_replies()
    assert call_model("hi", "mock/x", cache=cache, replay=True) == "recorded"