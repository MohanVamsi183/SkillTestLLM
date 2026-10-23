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