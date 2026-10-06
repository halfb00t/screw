"""Tests for `scripts.skip_tokens`'s `find_skip_tokens` and its commit-msg hook entry.

Run as `.venv/bin/python -m pytest tests/test_skip_tokens.py -q` **from the repository
root** -- the `-m` form puts the repo root on `sys.path`, which is what makes `import
scripts` resolve at all: `scripts` is not installed into the venv (it is not listed in
`pyproject.toml`'s `[tool.hatch.build.targets.wheel] packages`), and there is no
`tests/__init__.py` or `conftest.py` anywhere in this repo to do it another way. A bare
`.venv/bin/pytest` would not find `scripts` (the same constraint `tests/test_bench.py`
documents for `bench`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.skip_tokens import find_skip_tokens, main

REPO_ROOT = Path(__file__).resolve().parents[1]

# The six tokens D-02 lists, each alone in a one-line subject.
TOKEN_SUBJECTS = [
    "docs: update readme [skip ci]",
    "docs: update readme [ci skip]",
    "docs: update readme [no ci]",
    "docs: update readme [skip actions]",
    "docs: update readme [actions skip]",
    "docs: update readme\n\nskip-checks: true",
]


@pytest.mark.parametrize("message", TOKEN_SUBJECTS)
def test_each_token_form_alone_in_a_one_line_subject_is_found(message: str) -> None:
    """Every one of the six tokens GitHub Actions honours (D-02) is found on its own."""
    assert find_skip_tokens(message) != []


def test_all_upper_case_bracketed_form_is_found() -> None:
    """GitHub's own matching case is unstated (RESEARCH A1); the hook over-matches on
    purpose -- an all-caps bracket form is still found."""
    assert find_skip_tokens("fix: bug [SKIP CI]") != []


def test_mixed_case_bracketed_form_is_found() -> None:
    assert find_skip_tokens("fix: bug [Skip Ci]") != []


def test_trailer_written_in_upper_case_is_found() -> None:
    assert find_skip_tokens("fix: bug\n\nSKIP-CHECKS: TRUE") != []


def test_trailer_with_no_space_after_colon_is_found() -> None:
    assert find_skip_tokens("fix: bug\n\nskip-checks:true") != []


def test_token_in_a_later_paragraph_of_the_body_is_found() -> None:
    """The `6fce500` shape: a clean subject, a token mentioned in prose two paragraphs
    down, saying it was left out on purpose -- and it still skipped CI."""
    message = (
        "docs(04): note on CI behaviour\n\n"
        "This commit changes nothing about the pipeline.\n\n"
        "No [ci skip] on purpose -- this one should run.\n"
    )
    assert find_skip_tokens(message) != []


def test_token_as_the_first_text_of_the_message_is_found() -> None:
    assert find_skip_tokens("[skip ci] fix: bug") != []


def test_token_ending_the_message_with_no_trailing_newline_is_found() -> None:
    assert find_skip_tokens("fix: bug body text [skip ci]") != []


def test_clean_multi_paragraph_message_gives_no_tokens() -> None:
    message = (
        "feat(05): add the merge gate\n\n"
        "Refuses a skip token at commit time.\n\n"
        "Also fixes a typo in the docs.\n"
    )
    assert find_skip_tokens(message) == []


def test_empty_message_gives_no_tokens() -> None:
    assert find_skip_tokens("") == []


def test_bracketed_words_joined_by_a_hyphen_is_a_near_miss() -> None:
    """GitHub does not honour `[skip-ci]` (hyphen, no space) -- the hook must not
    over-match past what D-02 actually lists."""
    assert find_skip_tokens("fix: bug [skip-ci]") == []


def test_two_words_without_brackets_is_a_near_miss() -> None:
    assert find_skip_tokens("fix: bug, skip ci for this one") == []


def test_find_skip_tokens_searches_the_whole_text_it_is_given() -> None:
    """Neither caller cuts (D-02): the hook hands `find_skip_tokens` the whole buffer git
    gives it, and `make pr.land` hands it the whole PR title and body -- one pattern, so
    the two checks cannot drift apart."""
    message = (
        "A normal PR description.\n"
        "\n"
        "# ------------------------ >8 ------------------------\n"
        "[skip ci]\n"
    )
    assert find_skip_tokens(message) == ["[skip ci]"]


@pytest.mark.parametrize("git_editor", ["vi", None, ":"])
def test_hook_refuses_a_token_below_a_git_cut_line_whatever_git_editor_says(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    git_editor: str | None,
) -> None:
    """D-02: a cut line typed by hand is byte-identical to git's own, and `GIT_EDITOR`
    only says whether an editor ran, not whether `-v` was given -- so the hook trusts no
    cut line at all, in any commit mode (the debt record's probe table)."""
    if git_editor is None:
        monkeypatch.delenv("GIT_EDITOR", raising=False)
    else:
        monkeypatch.setenv("GIT_EDITOR", git_editor)
    message = (
        "safe subject\n\n"
        "# ------------------------ >8 ------------------------\n"
        "[skip ci]\n"
    )
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text(message, encoding="utf-8")
    assert main([str(path)]) == 1
    assert "line 4: '[skip ci]'" in capsys.readouterr().out


def test_hook_refuses_a_token_in_the_appended_commit_v_diff_and_says_to_commit_without_v(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """D-02's accepted cost and D-03's way out: a `git commit -v` whose appended staged
    diff names a token is refused too -- the hook reads the whole buffer git hands it,
    diff included -- and the refusal tells a `-v` author to commit without it."""
    monkeypatch.setenv("GIT_EDITOR", "vi")
    message = (
        "docs: a subject\n\n"
        "# ------------------------ >8 ------------------------\n"
        "# Do not modify or remove the line above.\n"
        "# Everything below it will be ignored.\n"
        "diff --git a/f b/f\n"
        "+a line naming [skip ci] inside the diff\n"
    )
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text(message, encoding="utf-8")
    assert main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "line 7: '[skip ci]'" in out
    assert "commit without -v" in out


def test_hook_names_a_token_above_and_below_a_cut_line_on_both_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Pins the hook's entry (`main`), the one caller that applies the cut, in an
    editor session (`GIT_EDITOR=vi`)."""
    monkeypatch.setenv("GIT_EDITOR", "vi")
    message = (
        "docs: add the skip-token doc [skip ci]\n"
        "# ------------------------ >8 ------------------------\n"
        "diff --git a/f b/f\n"
        "+another [skip ci] mention inside the diff\n"
    )
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text(message, encoding="utf-8")
    assert main([str(path)]) == 1
    out = capsys.readouterr().out
    assert out.count("'[skip ci]'") == 2
    assert "line 1: '[skip ci]'" in out
    assert "line 4: '[skip ci]'" in out


# --- the hook entry, run as a subprocess (T-05-01: the message is read from a file and
# matched with `re`, never interpolated into a shell) ----------------------------------


def _run_hook(message_file: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scripts.skip_tokens", str(message_file)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_hook_entry_exits_1_with_the_token_named_for_a_token_message(tmp_path: Path) -> None:
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text("fix: bug [skip ci]\n", encoding="utf-8")
    result = _run_hook(msg_file)
    assert result.returncode == 1
    assert "[skip ci]" in result.stdout
    assert "line 1" in result.stdout


def test_hook_entry_exits_0_for_a_clean_message(tmp_path: Path) -> None:
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text("fix: a clean commit\n", encoding="utf-8")
    result = _run_hook(msg_file)
    assert result.returncode == 0


def test_hook_entry_handles_invalid_utf8_with_a_token_without_crashing(tmp_path: Path) -> None:
    """Encoding edge: the message file is decoded with `errors="replace"`, so invalid
    UTF-8 bytes are still checked -- never a traceback -- and a token in that file is
    still refused."""
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_bytes(b"fix: bug \xff\xfe [skip ci]\n")
    result = _run_hook(msg_file)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


def test_hook_entry_handles_invalid_utf8_without_a_token(tmp_path: Path) -> None:
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_bytes(b"fix: a clean commit \xff\xfe\n")
    result = _run_hook(msg_file)
    assert result.returncode == 0
    assert "Traceback" not in result.stderr
