"""On-disk cache for model replies, so repeated test runs cost nothing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DEFAULT_CACHE_DIR = Path(".skilltest_cache")


class CacheMiss(Exception):
    """Raised in replay mode when a reply was never recorded."""


def make_key(model: str, prompt: str, temperature: float, run_index: int = 0) -> str:
    """Fingerprint one model request. Same inputs -> same key, always."""
    payload = json.dumps(
        {"model": model, "prompt": prompt, "temperature": temperature, "run": run_index},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Cache:
    """Stores one JSON file per model request in `directory`."""

    def __init__(self, directory: str | Path = DEFAULT_CACHE_DIR, enabled: bool = True):
        self.directory = Path(directory)
        self.enabled = enabled

    def _path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def get(self, key: str) -> str | None:
        """Return the saved reply, or None if there isn't one."""
        if not self.enabled:
            return None
        path = self._path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))["reply"]

    def set(self, key: str, reply: str, *, model: str, prompt: str) -> None:
        """Save a reply. The model and prompt are stored too, for humans reading the file."""
        if not self.enabled:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        record = {"model": model, "prompt": prompt, "reply": reply}
        self._path(key).write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )