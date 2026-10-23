"""Rule-based assertions for model output. Every failure shows the reason and the output."""

from __future__ import annotations

import json
import re

PREVIEW_LIMIT = 500  # characters of model output shown in a failure message

_CODE_FENCE = re.compile(r"\s*```(?:json)?\s*(.*?)\s*```\s*", re.DOTALL)


class SkillAssertionError(AssertionError):
    """A failed skilltest check. Subclasses AssertionError so pytest reports it as a test failure."""

    def __init__(self, check: str, reason: str, output: str):
        self.check = check
        self.reason = reason
        self.output = output
        super().__init__(f"{check}: {reason}\n--- model output ---\n{_preview(output)}")


def _preview(text: str) -> str:
    if len(text) <= PREVIEW_LIMIT:
        return text
    return text[:PREVIEW_LIMIT] + f"... [{len(text) - PREVIEW_LIMIT} more characters]"


def assert_json(
    output: str,
    keys: list[str] | None = None,
    *,
    exact: bool = False,
    allow_code_fence: bool = False,
):
    """Check that `output` is valid JSON and return the parsed value.

    keys:             keys that must be present (requires a JSON object)
    exact:            also fail if the object has keys beyond `keys`
    allow_code_fence: accept output wrapped in ```json ... ``` fences
    """
    __tracebackhide__ = True  # make pytest point at the user's test line, not this function

    text = output
    if allow_code_fence:
        match = _CODE_FENCE.fullmatch(output)
        if match:
            text = match.group(1)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise SkillAssertionError(
            "assert_json",
            f"not valid JSON ({error.msg} at line {error.lineno}, column {error.colno})",
            output,
        ) from None

    if keys is not None:
        if not isinstance(data, dict):
            raise SkillAssertionError(
                "assert_json", f"expected a JSON object, got {type(data).__name__}", output
            )
        missing = [key for key in keys if key not in data]
        if missing:
            raise SkillAssertionError("assert_json", f"missing keys: {missing}", output)
        if exact:
            extra = sorted(set(data) - set(keys))
            if extra:
                raise SkillAssertionError("assert_json", f"unexpected extra keys: {extra}", output)

    return data


def assert_contains(output: str, text: str, *, case_sensitive: bool = False) -> None:
    """Check that `output` contains `text` (case-insensitive by default)."""
    __tracebackhide__ = True
    haystack, needle = (output, text) if case_sensitive else (output.lower(), text.lower())
    if needle not in haystack:
        raise SkillAssertionError("assert_contains", f"expected to find {text!r}", output)


def assert_not_contains(output: str, text: str, *, case_sensitive: bool = False) -> None:
    """Check that `output` does not contain `text` (case-insensitive by default)."""
    __tracebackhide__ = True
    haystack, needle = (output, text) if case_sensitive else (output.lower(), text.lower())
    if needle in haystack:
        raise SkillAssertionError("assert_not_contains", f"found forbidden text {text!r}", output)


def assert_regex(output: str, pattern: str, *, flags: int = 0) -> re.Match:
    """Check that `pattern` matches somewhere in `output`; return the match."""
    __tracebackhide__ = True
    match = re.search(pattern, output, flags)
    if match is None:
        raise SkillAssertionError("assert_regex", f"no match for pattern {pattern!r}", output)
    return match


def assert_max_words(output: str, limit: int) -> None:
    """Check that `output` has at most `limit` words."""
    __tracebackhide__ = True
    count = len(output.split())
    if count > limit:
        raise SkillAssertionError("assert_max_words", f"{count} words, limit is {limit}", output)