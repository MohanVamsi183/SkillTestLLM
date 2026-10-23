import pytest

from skilltest import JudgeError, SkillAssertionError, assert_judge, judge
from skilltest.config import settings
from skilltest.models import clear_mock_replies, set_mock_reply

PASS = '{"pass": true, "reason": "Polite and mentions the refund window."}'
FAIL = '{"pass": false, "reason": "The reply is rude."}'


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    """Mock judge, a model that would fail if wrongly used, and a temporary cache."""
    monkeypatch.setattr(settings, "judge", "mock/judge")
    monkeypatch.setattr(settings, "model", "mock/fail")  # judging must NOT use this
    monkeypatch.setattr(settings, "fallbacks", [])
    monkeypatch.setattr(settings, "cache_dir", tmp_path / "cache")
    monkeypatch.setattr(settings, "replay", False)
    clear_mock_replies()
    yield
    clear_mock_replies()


def test_passing_verdict():
    set_mock_reply("CRITERION", PASS)
    verdict = assert_judge("Sure, happy to help!", "Is polite")
    assert verdict.passed
    assert "refund window" in verdict.reason


def test_failing_verdict_shows_reason_and_output():
    set_mock_reply("CRITERION", FAIL)
    with pytest.raises(SkillAssertionError) as error:
        assert_judge("Go away.", "Is polite")
    message = str(error.value)
    assert "criterion not met: 'Is polite'" in message
    assert "The reply is rude." in message
    assert "Go away." in message


def test_verdict_found_inside_extra_text():
    set_mock_reply("CRITERION", f"Here is my grade:\n```json\n{PASS}\n```\nDone.")
    assert judge("hi", "Is polite").passed


def test_criterion_and_output_are_in_judge_prompt():
    # The mock only answers if both pieces made it into the prompt.
    set_mock_reply("Mentions the 30-day policy", PASS)
    set_mock_reply("CRITERION", '{"pass": false, "reason": "criterion missing from prompt"}')
    assert judge("any output", "Mentions the 30-day policy").passed


def test_retries_once_after_unparseable_reply():
    set_mock_reply("could not be parsed", PASS)  # the retry prompt (checked first)
    set_mock_reply("CRITERION", "I think it is fine.")  # first reply: no JSON
    assert judge("hi", "Is polite").passed


def test_judge_error_after_two_bad_replies():
    set_mock_reply("CRITERION", "no json here at all")
    with pytest.raises(JudgeError, match="no valid verdict after a retry"):
        judge("hi", "Is polite")


def test_non_boolean_pass_is_rejected():
    set_mock_reply("CRITERION", '{"pass": "yes", "reason": "looks fine"}')
    with pytest.raises(JudgeError):
        judge("hi", "Is polite")