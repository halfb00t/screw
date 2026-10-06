"""The spike's command line (kernel-free parent): `python -m bench.thread_spike <command>`.

`check-protocol` refuses (exit 2) until the pre-registered protocol is on `origin/main`: no
campaign run may start before that (SC1, D-16, D-19).

`smoke` builds one M6 right-hand 5-turn rod in a worker subprocess, checks it against the
closed form and prints a Markdown report. It is not a campaign run: no run id, never recorded in
`bench/RESULTS.md`, and its JSONL goes to a temporary directory. Not part of `make verify`.

The parent never imports the kernel (an import-linter contract keeps it so): the kernel versions
are read from package metadata, and every build happens in the child.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from bench import machine_facts
from bench.quiet import Reading, read_now, wait_quiet
from bench.thread_spike.maths import INTERIM_PRESETS, closed_volume
from bench.thread_spike.runner import Worker
from bench.thread_spike.verdict import (
    FINE_CHECK_CEILING,
    PROTOCOL_PATH,
    ROW_TIMEOUT_S,
    GuardResult,
    RowRecord,
    RowRequest,
    classify_row,
    protocol_guard,
    relative_error,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    """One git call: list argv, no shell, the return code read by the caller (T-02-06)."""
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False,
                          cwd=_REPO_ROOT)


@dataclass(frozen=True)
class GuardFacts:
    """The guard's verdict and the facts a run header prints beside it."""

    result: GuardResult
    main_blob: str
    main_commit: str
    head: str


def read_guard(fetch: bool) -> GuardFacts:
    """Read git and ask `verdict.protocol_guard`. Without `fetch` nothing is fetched, so the
    guard reports `origin/main was not fetched` among its reasons: what the local ref holds
    might be stale."""
    fetched = fetch and _git("fetch", "origin", "main").returncode == 0
    path = _REPO_ROOT / PROTOCOL_PATH
    local_text = path.read_text() if path.exists() else None
    shown = _git("show", f"origin/main:{PROTOCOL_PATH}")
    main_text = shown.stdout if shown.returncode == 0 else None
    # The last commit on origin/main that touched the protocol: after a squash this is main's
    # own commit, not the PR branch's, and it is what HEAD must contain.
    commit = _git("log", "-1", "--format=%H", "origin/main", "--", PROTOCOL_PATH)
    main_commit = commit.stdout.strip() if commit.returncode == 0 else ""
    is_ancestor = bool(main_commit) and _git(
        "merge-base", "--is-ancestor", main_commit, "HEAD").returncode == 0
    blob = _git("rev-parse", f"origin/main:{PROTOCOL_PATH}")
    head = _git("rev-parse", "HEAD")
    return GuardFacts(
        protocol_guard(local_text, main_text, fetched=fetched, landed_is_ancestor=is_ancestor),
        blob.stdout.strip() if blob.returncode == 0 else "none",
        main_commit or "none",
        head.stdout.strip() if head.returncode == 0 else "unknown",
    )


def check_protocol() -> int:
    """Fetch, ask the guard. Held: exit 0 with the facts. Refused: every reason on stderr, exit
    2 (the shape of `bench.export_cost.find_set`). No flag skips it."""
    facts = read_guard(fetch=True)
    if not facts.result.held:
        print("protocol guard: refused -- " + "; ".join(facts.result.reasons), file=sys.stderr)
        return 2
    print("protocol guard: held")
    print(f"- origin/main protocol blob: `{facts.main_blob}`")
    print(f"- origin/main protocol commit: `{facts.main_commit}`")
    print(f"- HEAD: `{facts.head}`")
    return 0


def _reading_line(reading: Reading, note: str = "") -> str:
    return f"- load1 {reading.load1:.2f} read {reading.utc}{note}"


def _head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _smoke_request() -> RowRequest:
    tolerance, angular = INTERIM_PRESETS["preview"]
    return {
        "kind": "rod", "size": "M6", "d": 6.0, "pitch": 1.0, "turns": 5.0, "length": 5.0,
        "left_hand": False, "k": 5, "clearance": 0.0,
        "presets": [("preview", tolerance, angular)], "step": False, "gzip_on": [],
        "check_ceiling": FINE_CHECK_CEILING,
    }


def _signed(value: float | None, closed: float) -> str:
    return "n/a" if value is None else f"{relative_error(value, closed):+.3e}"


def _table_row(record: RowRecord, row_class: str, closed: float) -> str:
    """One Markdown row. A cell with no measurement behind it prints `n/a`, never a zero."""
    meshes = [m for m in record["meshes"] or [] if m["preset"] == "preview"]
    triangles = str(meshes[0]["triangles"]) if meshes else "n/a"
    if not meshes:
        watertight = "n/a"
    elif not meshes[0]["checked"]:
        watertight = "not checked"  # a skipped check is never reported as a pass
    else:
        watertight = "yes" if meshes[0]["watertight"] else "no"
    solids = record["solids"]
    valid = record["is_valid"]
    build_s = record["build_s"]
    cells = [
        record["size"], "left" if record["left_hand"] else "right", f"{record['turns']:g}",
        str(record["k"]), record["kind"], row_class,
        "n/a" if solids is None else str(solids),
        "n/a" if valid is None else ("yes" if valid else "no"),
        _signed(record["precise_volume"], closed), _signed(record["default_volume"], closed),
        "n/a" if build_s is None else f"{build_s:.2f}", triangles, watertight,
    ]
    return "| " + " | ".join(cells) + " |"


def smoke() -> int:
    """One rod row end to end. Exit 0 only when the row classifies ok."""
    quiet = wait_quiet(cap=0.0)  # one reading; non-decisive by construction
    versions = ", ".join(f"{dist} {metadata.version(dist)}"
                         for dist in ("cadquery", "cadquery-ocp"))
    print("## Thread spike smoke")
    print()
    print(f"- Machine: {machine_facts()}")
    print(f"- Python: {platform.python_version()}")
    print(f"- Kernel: {versions}")
    print(f"- HEAD: `{_head()}`")
    for reading in quiet.readings:
        print(_reading_line(reading, " (at start)"))
    print("- Quiet gate: smoke: quiet gate not waited")
    guard = read_guard(fetch=False).result
    state = "held" if guard.held else "refused -- " + "; ".join(guard.reasons)
    print(f"- Protocol guard (informational in smoke (not fetched); never enforced here): {state}")
    print()

    request = _smoke_request()
    closed = closed_volume(request["d"], request["pitch"], request["length"],
                           request["clearance"])
    worker = Worker()
    try:
        record = worker.run(request, ROW_TIMEOUT_S)
    finally:
        worker.close()
    row_class, reasons = classify_row(record, closed)

    out_dir = Path(tempfile.mkdtemp(prefix="screw-spike-smoke-"))
    jsonl = out_dir / "smoke.jsonl"
    jsonl.write_text(json.dumps({**record, "closed_volume": closed, "class": row_class,
                                 "reasons": list(reasons)}) + "\n")

    print("| Size | Hand | Turns | K | Kind | Class | Solids | Valid | Precise rel err | "
          "Default rel err | Build s | Preview triangles | Watertight |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    print(_table_row(record, row_class, closed))
    print()
    for reason in reasons:
        print(f"- {reason}")
    print(_reading_line(read_now(), " (includes this run's own load)"))
    print()
    print("**SMOKE** -- not a campaign run: no run id, never recorded in bench/RESULTS.md.")
    print(f"JSONL: `{jsonl}`")
    return 0 if row_class == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.thread_spike",
        description="The thread spike (Phase 2): a pre-registered measurement campaign.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "smoke", help="build one M6 right-hand 5-turn rod end to end; not a campaign run")
    commands.add_parser(
        "check-protocol", help="exit 2 unless the protocol is on origin/main (the run guard)")
    args = parser.parse_args(argv)
    return check_protocol() if args.command == "check-protocol" else smoke()


if __name__ == "__main__":
    sys.exit(main())
