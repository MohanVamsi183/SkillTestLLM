"""pytest plugin: turn command-line flags and [tool.skilltest] config into skilltest settings."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from skilltest.cache import DEFAULT_CACHE_DIR
from skilltest.config import settings


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("skilltest", "LLM skill testing")
    group.addoption(
        "--skilltest-model",
        default=None,
        help="Model that runs skills, e.g. groq/openai/gpt-oss-20b",
    )
    group.addoption(
        "--skilltest-judge",
        default=None,
        help="Model used by assert_judge",
    )
    group.addoption(
        "--no-cache",
        action="store_true",
        help="Ignore saved replies and always call models live",
    )
    group.addoption(
        "--replay",
        action="store_true",
        help="Use saved replies only; fail if a reply was never recorded",
    )


def _read_pyproject(root: Path) -> dict:
    """Return the [tool.skilltest] table from pyproject.toml, or {} if there isn't one."""
    path = root / "pyproject.toml"
    if not path.exists():
        return {}
    with path.open("rb") as file:
        return tomllib.load(file).get("tool", {}).get("skilltest", {})


def pytest_configure(config: pytest.Config) -> None:
    file_cfg = _read_pyproject(config.rootpath)

    # Priority: command-line flag > pyproject.toml > built-in default
    settings.model = config.getoption("--skilltest-model") or file_cfg.get("model", settings.model)
    settings.judge = config.getoption("--skilltest-judge") or file_cfg.get("judge", settings.judge)
    settings.fallbacks = list(file_cfg.get("fallbacks", settings.fallbacks))
    settings.temperature = float(file_cfg.get("temperature", settings.temperature))
    settings.cache_dir = config.rootpath / file_cfg.get("cache_dir", str(DEFAULT_CACHE_DIR))
    settings.use_cache = not config.getoption("--no-cache")
    settings.replay = config.getoption("--replay")

    if settings.replay and not settings.use_cache:
        raise pytest.UsageError("--replay reads from the cache, so it can't be combined with --no-cache")


def pytest_report_header(config: pytest.Config) -> str:
    if settings.replay:
        mode = "replay (no model calls)"
    elif settings.use_cache:
        mode = "live + cache"
    else:
        mode = "live, no cache"
    return f"skilltest: model={settings.model} | judge={settings.judge} | mode={mode}"