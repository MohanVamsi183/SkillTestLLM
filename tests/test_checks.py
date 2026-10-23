import pytest

from skilltest import (
    SkillAssertionError,
    assert_contains,
    assert_json,
    assert_max_words,
    assert_not_contains,
    assert_regex,
)

GOOD_JSON = '{"reply": "Sure", "tone": "calm"}'
FENCED_JSON = '```json\n{"reply": "Sure", "tone": "calm"}\n```'


# --- assert_json -----------------------------------------------------------

def test_json_returns_parsed_data():
    assert assert_json(GOOD_JSON) == {"reply": "Sure", "tone": "calm"}


def test_json_rejects_invalid_json():
    with pytest.raises(SkillAssertionError, match="not valid JSON"):
        assert_json("Sure! Here you go")


def test_json_rejects_code_fence_by_default():
    with pytest.raises(SkillAssertionError, match="not valid JSON"):
        assert_json(FENCED_JSON)


def test_json_accepts_code_fence_when_allowed():
    assert assert_json(FENCED_JSON, allow_code_fence=True)["tone"] == "calm"


def test_json_reports_missing_keys():
    with pytest.raises(SkillAssertionError, match=r"missing keys: \['urgency'\]"):
        assert_json(GOOD_JSON, keys=["reply", "urgency"])


def test_json_exact_rejects_extra_keys():
    with pytest.raises(SkillAssertionError, match=r"unexpected extra keys: \['tone'\]"):
        assert_json(GOOD_JSON, keys=["reply"], exact=True)


def test_json_keys_require_an_object():
    with pytest.raises(SkillAssertionError, match="expected a JSON object, got list"):
        assert_json("[1, 2, 3]", keys=["reply"])


# --- text checks -----------------------------------------------------------

def test_contains_ignores_case_by_default():
    assert_contains("Refunds within 30 DAYS", "30 days")


def test_contains_case_sensitive_option():
    with pytest.raises(SkillAssertionError, match="expected to find"):
        assert_contains("30 DAYS", "30 days", case_sensitive=True)


def test_not_contains_fails_on_forbidden_text():
    with pytest.raises(SkillAssertionError, match="found forbidden text"):
        assert_not_contains("As an AI language model, I...", "as an ai")


def test_regex_returns_match():
    assert assert_regex("Order #48213 shipped", r"#(\d+)").group(1) == "48213"


def test_regex_fails_when_no_match():
    with pytest.raises(SkillAssertionError, match="no match for pattern"):
        assert_regex("no numbers here", r"\d+")


def test_max_words():
    assert_max_words("one two three", 3)
    with pytest.raises(SkillAssertionError, match="4 words, limit is 3"):
        assert_max_words("one two three four", 3)


# --- failure message -------------------------------------------------------

def test_failure_message_includes_model_output():
    with pytest.raises(SkillAssertionError) as error:
        assert_contains("the actual reply", "refund")
    assert "--- model output ---" in str(error.value)
    assert "the actual reply" in str(error.value)


def test_long_output_is_truncated_in_message():
    with pytest.raises(SkillAssertionError) as error:
        assert_contains("x" * 2000, "refund")
    assert "more characters" in str(error.value)