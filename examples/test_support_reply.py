from pathlib import Path

from skilltest import assert_contains, assert_json, assert_max_words, assert_not_contains, run_skill

SKILL = Path(__file__).parent / "demo_skills" / "support_reply.md"


def test_refund_reply_is_valid_json_with_two_keys():
    out = run_skill(
        SKILL,
        input="I bought this 10 days ago and it broke. I want my money back.",
        company="Acme",
    )
    data = assert_json(out, keys=["reply", "tone"], exact=True)
    assert_max_words(data["tone"], 1)


def test_reply_mentions_30_days():
    out = run_skill(SKILL, input="Can I still return this? I bought it 3 weeks ago.", company="Acme")
    assert_contains(out, "30")


def test_reply_does_not_sound_robotic():
    out = run_skill(SKILL, input="Where is my order?", company="Acme")
    assert_not_contains(out, "as an ai")