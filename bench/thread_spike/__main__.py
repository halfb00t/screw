"""The spike's command line (kernel-free parent): `python -m bench.thread_spike <command>`.

`check-protocol` refuses (exit 2) until the pre-registered protocol is on `origin/main`: no
campaign run may start before that (SC1, D-16, D-19).

`smoke` builds one M6 right-hand 5-turn rod in a worker subprocess, checks it against the
closed form and prints a Markdown report. It is not a campaign run: no run id, never recorded in
`bench/RESULTS.md`, and its JSONL goes to a temporary directory. Not part of `make verify`.

`run <block> --run-id ID` runs one campaign block (ksweep, grid, frontier, ladder) behind the
guard and the quiet gate, streaming one JSONL record per row under `bench/results/thread-spike/`
and printing the Markdown report. A run is never overwritten or retried in place, and K comes
only from a K-sweep run's own record through the pre-registered rule: there is no way to type
one. `smoke --block NAME` runs the same block code on a small subset and records nothing.

The parent never imports the kernel (an import-linter contract keeps it so): the kernel versions
are read from package metadata, and every build happens in the child.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from importlib import metadata
from pathlib import Path
from typing import IO

from bench import machine_facts
from bench.quiet import QUIET_CAP_S, QuietResult, Reading, read_now, wait_quiet
from bench.thread_spike.maths import (
    FRONTIER_MAX_TURNS,
    INTERIM_PRESETS,
    K_CANDIDATES,
    PITCH,
    SAMPLE_SIZES,
    SIZES,
    VOID_CLEARANCE,
    closed_volume,
    depth_presets,
    frontier_turns,
    lengths,
    standard_max,
    turns_of,
)
from bench.thread_spike.runner import Worker
from bench.thread_spike.verdict import (
    FINE_CHECK_CEILING,
    PROTOCOL_PATH,
    ROW_TIMEOUT_S,
    GuardResult,
    HeaderRecord,
    Preset,
    RowClass,
    RowRecord,
    RowRequest,
    cache_bytes,
    classify_row,
    closed_of,
    fine_mesh,
    frontier_stop,
    over_budget,
    parse_header,
    parse_result_row,
    protocol_guard,
    relative_error,
    request_seconds,
    row_label,
    select_k,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

# A run id names files under bench/, so it is fixed to this shape (T-02-08): no path separator,
# no dot, no upper case, at most 64 characters.
RUN_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
RESULTS_DIR = _REPO_ROOT / "bench" / "results" / "thread-spike"
# The research reference value, used when no K qualifies under the rule so the frontier and
# budget data still exist for a roadmap revision (D-07, D-10).
DEFAULT_K = 5
NO_K_SOURCE = "no K qualified under the rule (escape clause); 5 is the research reference value"
SMOKE_SIZES = ("M2", "M6")


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


_ROW_HEAD = ("| Size | Hand | Turns | K | Kind | Class | Solids | Valid | Precise rel err | "
             "Default rel err | Build s | Preview triangles | Watertight |")
_ROW_RULE = "|---|---|---|---|---|---|---|---|---|---|---|---|---|"


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
    print("## Thread spike smoke")
    print()
    for line in _environment_lines():
        print(line)
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

    print(_ROW_HEAD)
    print(_ROW_RULE)
    print(_table_row(record, row_class, closed))
    print()
    for reason in reasons:
        print(f"- {reason}")
    print(_reading_line(read_now(), " (includes this run's own load)"))
    print()
    print("**SMOKE** -- not a campaign run: no run id, never recorded in bench/RESULTS.md.")
    print(f"JSONL: `{jsonl}`")
    return 0 if row_class == "ok" else 1


@dataclass(frozen=True)
class Measured:
    """One row as run: the record, the class and reasons recomputed from it, the over-budget
    reasons (D-10) and the closed form it was judged against."""

    record: RowRecord
    row_class: RowClass
    reasons: tuple[str, ...]
    over: tuple[str, ...]
    closed: float


class Campaign:
    """One block's rows: runs each through the worker, judges it, streams it to the JSONL (one
    line per row, flushed as written, so a run that dies keeps what it measured) and keeps it for
    the report. `decisive` is the quiet gate's verdict: every timing-derived claim reads
    "not established" without it (owner ruling R4)."""

    def __init__(self, worker: Worker, decisive: bool, sink: IO[str] | None) -> None:
        self._worker = worker
        self.decisive = decisive
        self._sink = sink
        self.rows: list[Measured] = []
        self.stops: list[str] = []

    def measure(self, request: RowRequest) -> Measured:
        record = self._worker.run(request, ROW_TIMEOUT_S)
        closed = closed_of(record)
        row_class, reasons = classify_row(record, closed)
        measured = Measured(record, row_class, reasons, over_budget(record, self.decisive),
                            closed)
        self.rows.append(measured)
        if self._sink is not None:
            precise = record["precise_volume"]
            line = {**record, "closed_volume": closed,
                    "rel_err": None if precise is None else relative_error(precise, closed),
                    "class": row_class, "reasons": list(reasons),
                    "over_budget": list(measured.over)}
            self._sink.write(json.dumps(line) + "\n")
            self._sink.flush()
        return measured


# INTERIM presets in the order the report reads them: preview first, then fine.
_INTERIM: list[Preset] = [(name, tol, ang) for name, (tol, ang) in INTERIM_PRESETS.items()]


def _request(kind: str, size: str, length: Fraction, left_hand: bool, k: int, *,
             presets: list[Preset] | None = None, step: bool = False,
             gzip_on: list[str] | None = None) -> RowRequest:
    """One row request from exact fractions. The builder gets `float(length / pitch)`, never a
    float division of floats, so an integer-turn row is built with its exact integer (Pitfall
    1). A void is the cutter at `VOID_CLEARANCE`; a rod has none."""
    d, pitch = PITCH[size]
    return {
        "kind": kind, "size": size, "d": float(d), "pitch": float(pitch),
        "turns": float(turns_of(length, pitch)), "length": float(length),
        "left_hand": left_hand, "k": k,
        "clearance": VOID_CLEARANCE if kind == "void" else 0.0,
        "presets": [] if presets is None else presets, "step": step,
        "gzip_on": [] if gzip_on is None else gzip_on, "check_ceiling": FINE_CHECK_CEILING,
    }


def _rod(size: str, length: Fraction, left_hand: bool, k: int) -> RowRequest:
    """The full rod row: preview and fine meshes, STEP, gzip-1 on the fine STL (D-08, D-10)."""
    return _request("rod", size, length, left_hand, k, presets=_INTERIM, step=True,
                    gzip_on=["fine"])


def _void(size: str, length: Fraction, left_hand: bool, k: int) -> RowRequest:
    return _request("void", size, length, left_hand, k)


def _smoke_sizes(sizes: tuple[str, ...], smoke: bool) -> tuple[str, ...]:
    return SMOKE_SIZES if smoke else sizes


def _hands(smoke: bool) -> tuple[bool, ...]:
    return (False,) if smoke else (False, True)


def _block_ksweep(c: Campaign, k: int, smoke: bool) -> None:
    """K in {3, 5, 10} on the sample sizes, both hands: at the standard max the full rod and the
    void, at 250 turns the rod with the preview mesh only and the void (D-07). `k` is unused:
    the sweep is what picks it. A smoke run is K = 5 only, at 20 turns, with no far void."""
    del k
    for size in _smoke_sizes(SAMPLE_SIZES, smoke):
        d, pitch = PITCH[size]
        near = 20 * pitch if smoke else standard_max(d)
        far = 20 * pitch if smoke else FRONTIER_MAX_TURNS * pitch
        for k_value in (5,) if smoke else K_CANDIDATES:
            for left in _hands(smoke):
                c.measure(_rod(size, near, left, k_value))
                c.measure(_void(size, near, left, k_value))
                c.measure(_request("rod", size, far, left, k_value, presets=_INTERIM[:1]))
                if not smoke:
                    c.measure(_void(size, far, left, k_value))


def _block_grid(c: Campaign, k: int, smoke: bool) -> None:
    """Every size, every D-03 length, both hands, at the locked K: the rod and the void.
    A smoke run is the longest length of at most 20 turns, right hand only."""
    for size in _smoke_sizes(SIZES, smoke):
        d, pitch = PITCH[size]
        grid = lengths(d, pitch)
        if smoke:
            grid = [max(x for x in grid if turns_of(x, pitch) <= 20)]
        for length in grid:
            for left in _hands(smoke):
                c.measure(_rod(size, length, left, k))
                c.measure(_void(size, length, left, k))


def _block_frontier(c: Campaign, k: int, smoke: bool) -> None:
    """Per size and hand, walk the frontier upward from the first step above the standard max,
    rod and void at each, until `frontier_stop` says stop (D-04); one line per walk says why it
    ended. A smoke run is M2's first step only."""
    for size in ("M2",) if smoke else SIZES:
        d, pitch = PITCH[size]
        steps = frontier_turns(d, pitch)[:1] if smoke else frontier_turns(d, pitch)
        for left in _hands(smoke):
            hand = "left" if left else "right"
            stop: str | None = None
            last = 0
            for turns in steps:
                length = turns * pitch
                rod = c.measure(_rod(size, length, left, k))
                void = c.measure(_void(size, length, left, k))
                last = turns
                stop = frontier_stop(rod.record, void.record, rod.row_class, void.row_class,
                                     c.decisive)
                if stop is not None:
                    break
            outcome = f"stop: {stop}" if stop else f"no stop up to {steps[-1]} turns"
            c.stops.append(f"{size} {hand}: {outcome}; last measured {last} turns")


def _block_ladder(c: Campaign, k: int, smoke: bool) -> None:
    """The mesh ladder (D-20): right hand, at 10 turns and at the standard max, every INTERIM
    preset and every depth preset, gzip-1 on each, the check under the ceiling. A smoke run is
    10 and 20 turns on two sizes."""
    for size in _smoke_sizes(SAMPLE_SIZES, smoke):
        d, pitch = PITCH[size]
        presets = [*_INTERIM, *depth_presets(float(pitch))]
        for length in (10 * pitch, 20 * pitch if smoke else standard_max(d)):
            c.measure(_request("rod", size, length, False, k, presets=presets,
                               gzip_on=[name for name, _, _ in presets]))


BLOCKS: dict[str, Callable[[Campaign, int, bool], None]] = {
    "ksweep": _block_ksweep, "grid": _block_grid, "frontier": _block_frontier,
    "ladder": _block_ladder,
}


def _peak(values: list[float]) -> str:
    """The signed value of greatest magnitude, so a -2 from an inverted solid is not hidden
    behind a +1e-6; `n/a` for none."""
    return f"{max(values, key=abs):+.3e}" if values else "n/a"


def _max_of(values: Sequence[float], fmt: str) -> str:
    return format(max(values), fmt) if values else "n/a"


_AGGREGATE_HEAD = (
    "| Size | Rows | ok | silent_wrong | failure | timeout | worker_died | "
    "Max precise rel err | Max default rel err | Max fine triangles | Max fine bytes | "
    "Max raw + gzip-1 bytes | Max build + slower export s | Max STEP bytes | Checks skipped |")


def _aggregate_row(size: str, rows: list[Measured]) -> str:
    counts = Counter(m.row_class for m in rows)
    precise: list[float] = []
    default: list[float] = []
    triangles: list[int] = []
    fine_bytes: list[int] = []
    cached: list[int] = []
    seconds: list[float] = []
    step: list[int] = []
    skipped = 0
    for m in rows:
        record = m.record
        if record["precise_volume"] is not None:
            precise.append(relative_error(record["precise_volume"], m.closed))
        if record["default_volume"] is not None:
            default.append(relative_error(record["default_volume"], m.closed))
        fine = fine_mesh(record)
        if fine is not None:
            triangles.append(fine["triangles"])
            fine_bytes.append(fine["bytes"])
        total = cache_bytes(record)
        if total is not None:
            cached.append(total)
        taken = request_seconds(record)
        if taken is not None:
            seconds.append(taken)
        if record["step_bytes"] is not None:
            step.append(record["step_bytes"])
        skipped += sum(1 for mesh in record["meshes"] or [] if not mesh["checked"])
    cells = [
        size, str(len(rows)), *(str(counts[name]) for name in (
            "ok", "silent_wrong", "failure", "timeout", "worker_died")),
        _peak(precise), _peak(default), _max_of(triangles, "d"), _max_of(fine_bytes, "d"),
        _max_of(cached, "d"), _max_of(seconds, ".2f"), _max_of(step, "d"), str(skipped),
    ]
    return "| " + " | ".join(cells) + " |"


def aggregate_table(measured: list[Measured]) -> list[str]:
    """The per-size table: counts per class, the signed extremes of both volume errors, the
    largest sizes and costs, and the checks skipped over the ceiling (a skipped check is counted,
    never read as a pass). Sizes in numeric order. An empty block raises: an empty table reads
    as a pass."""
    if not measured:
        raise ValueError("the block produced no rows -- an empty table must be refused, "
                         "never printed as one that reads as a pass")
    lines = [_AGGREGATE_HEAD, "|" + "---|" * 15]
    for size in SIZES:
        rows = [m for m in measured if m.record["size"] == size]
        if rows:
            lines.append(_aggregate_row(size, rows))
    return lines


def report(header: list[str], measured: list[Measured], stops: list[str], end: Reading) -> str:
    """The run's Markdown: header lines, the per-size aggregate, then every non-ok row and every
    over-budget row on its own line with its reasons, the frontier stops, and the end reading
    labelled as including this run's own load."""
    lines = [*header, *([""] if header else []), *aggregate_table(measured), ""]
    for m in measured:
        if m.row_class != "ok":
            lines.append(f"- {row_label(m.record)}: {m.row_class}: {'; '.join(m.reasons)}")
        if m.over:
            lines.append(f"- {row_label(m.record)}: {'; '.join(m.over)}")
    lines.extend(f"- frontier {stop}" for stop in stops)
    lines.append(_reading_line(end, " (includes this run's own load)"))
    return "\n".join(lines)


def _environment_lines() -> list[str]:
    versions = ", ".join(f"{dist} {metadata.version(dist)}"
                         for dist in ("cadquery", "cadquery-ocp"))
    return [f"- Machine: {machine_facts()}", f"- Python: {platform.python_version()}",
            f"- Kernel: {versions}", f"- HEAD: `{_head()}`"]


def _release_line(quiet: QuietResult) -> str:
    if quiet.decisive:
        return f"- release: decisive at {quiet.readings[-1].utc}"
    return f"- release: non-decisive after {QUIET_CAP_S:g} s ({len(quiet.readings)} readings)"


def _locked_k(k_from: str, results_dir: Path) -> tuple[int, str]:
    """K from the K-sweep run's own record through `select_k`; there is no way to type one.
    `None` from the rule means K = 5, the research reference value, and says so."""
    path = results_dir / f"{k_from}.jsonl"
    if not path.is_file():
        raise ValueError(f"K-sweep run {k_from!r} is not recorded under {results_dir}")
    lines = path.read_text().splitlines()
    if not lines or parse_header(lines[0])["block"] != "ksweep":
        raise ValueError(f"run {k_from!r} is not a ksweep run")
    k = select_k([parse_result_row(line) for line in lines[1:]])
    if k is None:
        return DEFAULT_K, NO_K_SOURCE
    return k, f"selected by select_k from run {k_from}"


def run_block(block: str, run_id: str, k_from: str | None, *,
              results_dir: Path = RESULTS_DIR) -> int:
    """One guarded campaign block. Refusals, all exit 2 with nothing written: a run id that is
    not `RUN_ID`; a run id already recorded (a run is never overwritten or retried in place); a
    `--k-from` missing, malformed or given to the K sweep; the protocol guard. Then: the quiet
    gate, the header as the first JSONL line, rows streamed, the end reading, the Markdown."""
    target = results_dir / f"{run_id}.jsonl"
    problem = None
    if not RUN_ID.fullmatch(run_id):
        problem = f"run id {run_id!r} must fullmatch [a-z0-9][a-z0-9-]{{0,63}}"
    elif target.exists():
        problem = f"run id {run_id!r} already recorded; a run is never overwritten"
    elif (block == "ksweep") != (k_from is None):
        problem = ("the K sweep takes no --k-from; every other block requires one"
                   if block == "ksweep" else f"block {block!r} requires --k-from <ksweep run id>")
    elif k_from is not None and not RUN_ID.fullmatch(k_from):
        problem = f"--k-from {k_from!r} is not a run id"
    if problem is not None:
        print(f"refused: {problem}", file=sys.stderr)
        return 2
    facts = read_guard(fetch=True)
    if not facts.result.held:
        print("protocol guard: refused -- " + "; ".join(facts.result.reasons), file=sys.stderr)
        return 2
    k, k_source = None, f"swept over K in {', '.join(map(str, K_CANDIDATES))}"
    if k_from is not None:
        try:
            k, k_source = _locked_k(k_from, results_dir)
        except ValueError as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 2
    quiet = wait_quiet()  # the protocol's constants; no flag overrides them
    results_dir.mkdir(parents=True, exist_ok=True)
    header: HeaderRecord = {
        "run_id": run_id, "block": block, "head": facts.head, "protocol_blob": facts.main_blob,
        "protocol_commit": facts.main_commit, "decisive": quiet.decisive,
        "readings": [(r.utc, r.load1) for r in quiet.readings], "k": k, "k_source": k_source,
    }
    try:
        sink = target.open("x", encoding="utf-8")  # exclusive: never overwrites
    except FileExistsError:
        print(f"refused: run id {run_id!r} already recorded; a run is never overwritten",
              file=sys.stderr)
        return 2
    worker = Worker()
    try:
        sink.write(json.dumps(header) + "\n")
        sink.flush()
        campaign = Campaign(worker, quiet.decisive, sink)
        BLOCKS[block](campaign, DEFAULT_K if k is None else k, False)
    finally:
        worker.close()
        sink.close()
    head_lines = [
        f"## Thread spike run {run_id}", "", *_environment_lines(),
        f"- Protocol blob: `{facts.main_blob}`", f"- Protocol commit: `{facts.main_commit}`",
        f"- Block: {block}", f"- K: {'swept' if k is None else k} ({k_source})",
        *(_reading_line(r) for r in quiet.readings), _release_line(quiet),
    ]
    text = report(head_lines, campaign.rows, campaign.stops, read_now())
    (results_dir / f"{run_id}.md").write_text(text + "\n")
    print(text)
    return 0


def smoke_block(block: str) -> int:
    """A block's code on a smoke subset (sizes M2 and M6, right hand, at most 6 rows, lengths of
    at most 20 turns; frontier: M2's first step; K = 5): no run id, output in a temporary
    directory, the guard informational and the quiet cap 0. Exit 0 only when every row is ok."""
    quiet = wait_quiet(cap=0.0)
    print(f"## Thread spike smoke: {block}")
    print()
    for line in _environment_lines():
        print(line)
    for reading in quiet.readings:
        print(_reading_line(reading, " (at start)"))
    print("- Quiet gate: smoke: quiet gate not waited")
    guard = read_guard(fetch=False).result
    state = "held" if guard.held else "refused -- " + "; ".join(guard.reasons)
    print(f"- Protocol guard (informational in smoke (not fetched); never enforced here): {state}")
    print()
    out_dir = Path(tempfile.mkdtemp(prefix="screw-spike-smoke-"))
    worker = Worker()
    try:
        with (out_dir / "smoke.jsonl").open("w", encoding="utf-8") as sink:
            campaign = Campaign(worker, quiet.decisive, sink)
            BLOCKS[block](campaign, DEFAULT_K, True)
    finally:
        worker.close()
    print(_ROW_HEAD)
    print(_ROW_RULE)
    for m in campaign.rows:
        print(_table_row(m.record, m.row_class, m.closed))
    print()
    print(report([], campaign.rows, campaign.stops, read_now()))
    print()
    print("**SMOKE** -- not a campaign run: no run id, never recorded in bench/RESULTS.md.")
    print(f"JSONL: `{out_dir / 'smoke.jsonl'}`")
    return 0 if all(m.row_class == "ok" for m in campaign.rows) else 1


def verdict_campaign(prefix: str, *, results_dir: Path = RESULTS_DIR) -> int:  # noqa: ARG001
    return 99


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.thread_spike",
        description="The thread spike (Phase 2): a pre-registered measurement campaign.")
    commands = parser.add_subparsers(dest="command", required=True)
    smoke_parser = commands.add_parser(
        "smoke", help="build one M6 right-hand 5-turn rod end to end; not a campaign run")
    smoke_parser.add_argument(
        "--block", choices=tuple(BLOCKS),
        help="run this block's code on a small subset instead; records nothing")
    commands.add_parser(
        "check-protocol", help="exit 2 unless the protocol is on origin/main (the run guard)")
    run_parser = commands.add_parser(
        "run", help="one guarded campaign block, streamed to bench/results/thread-spike/")
    run_parser.add_argument("block", choices=tuple(BLOCKS))
    run_parser.add_argument("--run-id", required=True,
                            help="[a-z0-9][a-z0-9-]{0,63}; an id already recorded is refused")
    run_parser.add_argument("--k-from", default=None,
                            help="the ksweep run id whose record select_k reads; required by "
                                 "every block but ksweep")
    args = parser.parse_args(argv)
    if args.command == "check-protocol":
        return check_protocol()
    if args.command == "run":
        return run_block(args.block, args.run_id, args.k_from)
    return smoke() if args.block is None else smoke_block(args.block)


if __name__ == "__main__":
    sys.exit(main())
