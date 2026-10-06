"""Reject a commit message carrying a GitHub Actions skip token (D-02).

GitHub Actions honours six tokens anywhere in a commit message and silently skips every
workflow run for that commit: `[skip ci]`, `[ci skip]`, `[no ci]`, `[skip actions]`,
`[actions skip]`, and the trailer `skip-checks: true`
(<https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/skipping-workflow-runs>).

Why a commit-time hook, and not only the squash-merge setting (D-03): GitHub applies the
token to a PR's *head* commit too, not only to a push -- a token-carrying ship note left
PR #2's head (`20b63e4`) with zero recorded checks, not a red run. And a literal mention
in *prose* is enough: Phase 4's note "No `[ci skip]` on purpose" (`6fce500`) was itself
skipped and needed the empty trigger commit `87d500e`. Blocking at commit time closes both
holes, for every tool that commits here -- human, `gsd-ship`, or anything else.

This module serves two callers: the `no-skip-token` commit-msg hook below (`main`), and,
from Plan 05-02, `make pr.land`'s check of the squash commit's subject and body. Both hand
`find_skip_tokens` the whole text they were given -- the hook the buffer git hands a
commit-msg hook, `make pr.land` the PR title and body -- one pattern, so the two checks
cannot drift apart (D-02). There is no cut, ever: a cut line typed by hand in an editor
session is byte-identical to git's own, and `GIT_EDITOR` only says whether an editor ran,
not whether `-v` was given, so no signal distinguishes the two
(docs/tech_debt/resolved/2026-09-25-commit-msg-hook-trusts-a-hand-typed-cut-line.md). The
accepted cost: a `git commit -v` whose appended staged diff names a token is refused too
(`git config --get commit.verbose` reads empty on this machine, 2026-09-25) -- the
refusal names the line and tells the author to commit without `-v` (D-03).

The match is deliberately broader than GitHub's own: case-insensitive, anywhere in the
message. GitHub's documentation does not state a case rule -- over-matching costs a
reworded commit message; under-matching costs a run-less commit on `main` (the actual
failure this phase responds to, `538d26f` and `bfc9110`).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

# The five bracketed phrases, exactly as GitHub writes them (a single space inside the
# brackets), plus the `skip-checks:` trailer with optional whitespace before `true` --
# matched as unanchored substrings, case-insensitive (D-02; see module docstring for why
# case-insensitive is the safe direction to over-match in).
SKIP_TOKEN = re.compile(
    r"\[(?:skip ci|ci skip|no ci|skip actions|actions skip)\]"
    r"|skip-checks:\s*true",
    re.IGNORECASE,
)


def find_skip_tokens(message: str) -> list[str]:
    """Every skip token in the whole of `message`, in order of appearance, as the matched
    text. Pure -- no I/O, so `pr.land` (Plan 05-02) can call it against a squash subject
    and body with no message-file round trip. Neither caller cuts: the hook (`main`,
    below) hands in the whole buffer git gives it, and `make pr.land` hands in the whole
    PR title and body (D-02)."""
    return [m.group(0) for m in SKIP_TOKEN.finditer(message)]


def main(argv: list[str] | None = None) -> int:
    """The commit-msg hook entry: `python -m scripts.skip_tokens MESSAGE_FILE`."""
    parser = argparse.ArgumentParser(
        prog="scripts.skip_tokens",
        description="Refuse a commit message carrying a GitHub Actions skip token.",
    )
    parser.add_argument("message_file", help="Path git hands a commit-msg hook")
    args = parser.parse_args(argv)

    # Replace, not raise: an invalid-UTF-8 byte in the message must still be checked --
    # refused if it carries a token, accepted if it does not -- never a traceback.
    raw = Path(args.message_file).read_text(encoding="utf-8", errors="replace")
    # No cut, ever (D-02): a cut line typed by hand in an editor session without `-v` is
    # byte-identical to git's own, and githooks(5)'s `GIT_EDITOR=:` signal only tells
    # this hook whether an editor ran, not whether `-v` was given -- there is no content
    # or environment signal left that tells the two apart
    # (docs/tech_debt/resolved/2026-09-25-commit-msg-hook-trusts-a-hand-typed-cut-line.md).
    # The one false positive this buys: a `git commit -v` whose appended staged diff
    # names a token is refused too -- the refusal below names the line and tells the
    # author to commit without `-v` (D-03).
    tokens = find_skip_tokens(raw)
    if not tokens:
        return 0

    print("make: this commit message carries a GitHub Actions skip token:")
    # Each token's 1-based line: walk `raw` with str.index from the end of the previous
    # match so an earlier occurrence of the same text is never mistaken for this one's
    # start (find_skip_tokens returns matches in order of appearance, non-overlapping).
    search_from = 0
    for token in tokens:
        pos = raw.index(token, search_from)
        line_no = raw.count("\n", 0, pos) + 1
        print(f"      line {line_no}: {token!r}")
        search_from = pos + len(token)
    print("      A skip token here silences CI on this commit, and on a PR head it")
    print("      leaves the PR with zero checks.")
    print('      Describe it in words instead ("a GitHub Actions skip token") -- do not')
    print("      write the literal token.")
    print(
        "      If a named line is in the diff `git commit -v` appends below the cut"
        " line, commit without -v -- this hook reads the whole message either way."
    )
    print(
        "      See docs/tech_debt/resolved/"
        "2026-09-25-ship-note-skip-token-leaks-into-squash-merge.md."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
