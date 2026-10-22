"""Shared settings. Defaults live here; the pytest plugin overrides them from CLI flags."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from skilltest.cache import DEFAULT_CACHE_DIR, Cache


@dataclass
class Settings:
    model: str = "ollama/qwen2.5:3b"            # model that runs skills
    judge: str = "groq/openai/gpt-oss-120b"     # model used by assert_judge (Day 1, later)
    fallbacks: list[str] = field(default_factory=list)
    temperature: float = 0.7    # > 0 so repeated runs can differ, like real usage
    cache_dir: Path = DEFAULT_CACHE_DIR
    use_cache: bool = True
    replay: bool = False

    def make_cache(self) -> Cache:
        return Cache(self.cache_dir, enabled=self.use_cache)


settings = Settings()  # one shared instance used by the whole package