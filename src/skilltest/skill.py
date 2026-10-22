"""Load a skill (a Markdown prompt template), fill in its variables, and run it."""

from __future__ import annotations

import re
from pathlib import Path

from skilltest.config import settings
from skilltest.models import call_model

# Matches {name} where name is letters, digits or underscores.
_PLACEHOLDER = re.compile(r"\{(\w+)\}")


class SkillError(Exception):
    """Raised when a skill file can't be loaded."""


def load_skill(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        raise SkillError(f"Skill file not found: {path}")
    return path.read_text(encoding="utf-8")


def render(template: str, variables: dict[str, object]) -> str:
    """Replace {name} placeholders found in `variables`. Leave every other brace alone."""

    def substitute(match: re.Match) -> str:
        name = match.group(1)
        return str(variables[name]) if name in variables else match.group(0)

    return _PLACEHOLDER.sub(substitute, template)


def run_skill(
    path: str | Path,
    input: str = "",
    *,
    model: str | None = None,
    run_index: int = 0,
    **variables: object,
) -> str:
    """Run the skill at `path` with `input` (and any extra variables); return the reply."""
    prompt = render(load_skill(path), {"input": input, **variables})
    return call_model(
        prompt,
        model or settings.model,
        fallbacks=settings.fallbacks,
        temperature=settings.temperature,
        cache=settings.make_cache(),
        run_index=run_index,
        replay=settings.replay,
    )