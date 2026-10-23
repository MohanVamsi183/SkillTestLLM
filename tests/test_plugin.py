import pytest

# A tiny test file that the inner pytest run will execute; it prints the settings it sees.
SHOW_SETTINGS = """
from skilltest.config import settings

def test_show():
    print(f"MODEL={settings.model} JUDGE={settings.judge} "
          f"REPLAY={settings.replay} CACHE={settings.use_cache}")
"""


@pytest.fixture
def run(pytester):
    """Run pytest in a separate process inside a temporary project folder."""
    pytester.makepyfile(SHOW_SETTINGS)

    def _run(*args):
        return pytester.runpytest_subprocess("-s", *args)

    return _run


def test_defaults_without_config(run):
    result = run()
    result.stdout.fnmatch_lines(["*MODEL=ollama/qwen2.5:3b*REPLAY=False CACHE=True*"])


def test_pyproject_sets_model(pytester, run):
    pytester.makepyprojecttoml('[tool.skilltest]\nmodel = "mock/from-file"\n')
    result = run()
    result.stdout.fnmatch_lines(["*MODEL=mock/from-file*"])


def test_cli_flag_overrides_pyproject(pytester, run):
    pytester.makepyprojecttoml('[tool.skilltest]\nmodel = "mock/from-file"\n')
    result = run("--skilltest-model", "mock/from-cli")
    result.stdout.fnmatch_lines(["*MODEL=mock/from-cli*"])


def test_replay_flag_and_header(run):
    result = run("--replay")
    result.stdout.fnmatch_lines(["*mode=replay*", "*REPLAY=True*"])


def test_replay_with_no_cache_is_rejected(run):
    result = run("--replay", "--no-cache")
    assert result.ret != 0
    result.stderr.fnmatch_lines(["*can't be combined with --no-cache*"])