import pytest

from skilltest import run_skill
from skilltest.config import settings
from skilltest.models import clear_mock_replies, set_mock_reply
from skilltest.skill import SkillError, render


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    """Use a mock model and a temporary cache so tests never touch the network."""
    monkeypatch.setattr(settings, "model", "mock/test")
    monkeypatch.setattr(settings, "cache_dir", tmp_path / "cache")
    clear_mock_replies()
    yield
    clear_mock_replies()


@pytest.fixture
def skill_file(tmp_path):
    path = tmp_path / "support_reply.md"
    path.write_text(
        'Reply as JSON like {"reply": "...", "tone": "..."}.\n'
        "Company: {company}\n"
        "Customer message: {input}\n",
        encoding="utf-8",
    )
    return path


def test_render_fills_input():
    assert render("Say: {input}", {"input": "hi"}) == "Say: hi"


def test_render_leaves_json_braces_alone():
    template = 'Return {"reply": "x"} for {input}'
    assert render(template, {"input": "hi"}) == 'Return {"reply": "x"} for hi'


def test_render_leaves_unknown_placeholders_alone():
    assert render("{input} and {other}", {"input": "a"}) == "a and {other}"


def test_run_skill_sends_rendered_prompt_to_model(skill_file):
    # The mock only answers if the prompt contains the filled-in message.
    set_mock_reply("Customer message: Where is my order?", '{"reply": "On its way", "tone": "calm"}')
    out = run_skill(skill_file, input="Where is my order?", company="Acme")
    assert out == '{"reply": "On its way", "tone": "calm"}'


def test_run_skill_fills_extra_variables(skill_file):
    set_mock_reply("Company: Acme", "saw the company")
    assert run_skill(skill_file, input="hi", company="Acme") == "saw the company"


def test_missing_skill_file_raises(tmp_path):
    with pytest.raises(SkillError):
        run_skill(tmp_path / "nope.md", input="hi")