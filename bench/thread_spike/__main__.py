"""The spike's command line (kernel-free parent): `python -m bench.thread_spike <command>`.

`check-protocol` refuses (exit 2) until the pre-registered protocol is on `origin/main`: no
campaign run may start before that (SC1, D-16, D-19).

`smoke` builds one M6 right-hand 5-turn rod in a worker subprocess, checks it against the
closed form and prints a Markdown report. It is not a campaign run: no run id, never recorded in
`bench/RESULTS.md`, and its JSONL goes to a temporary directory. Not part of `make verify`.

`run <block> --run-id ID` runs one campaign block (ksweep, grid, frontier, ladder, controls,
trim, rss, pair, container) behind the
guard and the quiet gate, streaming one JSONL record per row under `bench/results/thread-spike/`
and printing the Markdown report. A run is never overwritten or retried in place, and K comes
only from a K-sweep run's own record through the pre-registered rule: there is no way to type
one. `smoke --block NAME` runs the same block code on a small subset and records nothing.

The rss block runs one fresh `--once` child per row, the only place a peak RSS exists, and
takes `--frontier-from` for the terminal rows of the frontier walk. The container block runs the
locked construction over the full grid in the production image under linux/amd64 through the
same worker protocol, validity, solid count and volume only, never decisive (emulated timings).

The pair block is question 3: per size and hand, a nut against a rod piece read at three matched
screw-motion poses and three half-pitch controls, each reading judged by `verdict.cell_verdict`
against the kernel-free closed form (D-11 to D-14). `smoke --pair` reads one cell and prints its
six readings.

The controls block runs its ruled-surface rows in a second worker whose PYTHONPATH adds the
scratch directory named by SCREW_SPIKE_CQW, and refuses (exit 2) when the package is not
importable there: the reference package is never on the default worker's path (D-06).

`campaign --run-id PREFIX` is the whole spike as one guarded command: every block in protocol
order as run id PREFIX-<block>, K taken from PREFIX-ksweep by the rule, then the verdict over
PREFIX-*; a block that refuses to start or crashes is logged in PREFIX-campaign.md and the rest
still run.

The parent never imports the kernel (an import-linter contract keeps it so): the kernel versions
are read from package metadata, and every build happens in the child.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import itertools
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from importlib import metadata
from pathlib import Path
from typing import IO, Literal

from bench import machine_facts
from bench.quiet import QUIET_CAP_S, QuietResult, Reading, read_now, wait_quiet
from bench.thread_spike.maths import (
    CONTROL_OFFSET_PITCHES,
    DIAGNOSTIC_CLEARANCES,
    FRONTIER_MAX_TURNS,
    INTERIM_PRESETS,
    K_CANDIDATES,
    MATCHED_POSES,
    NUT_HEIGHT,
    PAIR_CLEARANCES,
    PAIR_REFERENCE_SIZES,
    PITCH,
    RULED_MODULE,
    SAMPLE_SIZES,
    SIZES,
    TIP_CHAMFER_DEG,
    VOID_CLEARANCE,
    closed_volume,
    depth_presets,
    frontier_turns,
    lengths,
    standard_max,
    turns_of,
)
from bench.thread_spike.runner import (
    CONTAINER_IMAGE,
    Worker,
    container_argv,
    docker_kill,
    run_once,
)
from bench.thread_spike.verdict import (
    EMPTY_MM3,
    FINE_CHECK_CEILING,
    GZIP_TABLE_TIMEOUT_S,
    PAIR_BAND,
    PAIR_TIMEOUT_S,
    PROTOCOL_PATH,
    ROW_TIMEOUT_S,
    SECONDS_NOT_ESTABLISHED,
    GuardResult,
    HeaderRecord,
    PairReading,
    PairRecord,
    PairRequest,
    Preset,
    RowClass,
    RowRecord,
    RowRequest,
    block_gaps,
    bytes_over,
    cache_bytes,
    cell_verdict,
    classify_record,
    classify_row,
    closed_control,
    closed_of,
    escape_rows,
    excluded_clearances,
    fine_mesh,
    frontier_stop,
    k_scores,
    known_bad_inputs,
    mixed_hand_violated,
    over_budget,
    pair_gaps,
    parse_header,
    parse_pair_result_row,
    parse_result_row,
    pass_bar,
    protocol_guard,
    relative_error,
    request_seconds,
    row_class,
    row_label,
    seconds_over,
    select_estimator,
    select_k,
    sensitivity_ok,
    size_falsifiable,
    skipped_checks,
    turn_caps,
    variant_rules,
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
        "check_ceiling": FINE_CHECK_CEILING, "want_gzip_table": False,
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
    # A trimmed tip has no closed form, so a relative error against the untrimmed rod's would
    # read as an accuracy figure it is not (D-08).
    judged = record["kind"] != "trim"
    cells = [
        record["size"], "left" if record["left_hand"] else "right", f"{record['turns']:g}",
        str(record["k"]), record["kind"], row_class,
        "n/a" if solids is None else str(solids),
        "n/a" if valid is None else ("yes" if valid else "no"),
        _signed(record["precise_volume"], closed) if judged else "n/a",
        _signed(record["default_volume"], closed) if judged else "n/a",
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


Via = Literal["worker", "reference", "container", "fresh"]


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

    def __init__(self, worker: Worker, decisive: bool, sink: IO[str] | None, *,
                 reference: Worker | None = None, container: Worker | None = None,
                 fresh: Callable[[RowRequest, float], RowRecord] = run_once,
                 frontier_rows: list[RowRecord] | None = None) -> None:
        self._worker = worker
        self.reference = reference
        self.container = container
        self._fresh = fresh
        self.frontier_rows = frontier_rows
        self.decisive = decisive
        self._sink = sink
        self.rows: list[Measured] = []
        self.pairs: list[PairRecord] = []
        self.stops: list[str] = []
        self.notes: list[str] = []

    def measure(self, request: RowRequest, via: Via = "worker") -> Measured:
        if via == "fresh":
            # A row asking for the gzip table gets its own, longer deadline (verdict.py).
            record = self._fresh(request, GZIP_TABLE_TIMEOUT_S if request["want_gzip_table"]
                                 else ROW_TIMEOUT_S)
        else:
            worker = {"worker": self._worker, "reference": self.reference,
                      "container": self.container}[via]
            if worker is None:
                raise ValueError(f"this campaign has no {via} worker")
            record = worker.run(request, ROW_TIMEOUT_S)
        closed = closed_of(record)
        row_class, reasons = classify_record(record)
        measured = Measured(record, row_class, reasons, over_budget(record, self.decisive),
                            closed)
        self.rows.append(measured)
        if self._sink is not None:
            precise = record["precise_volume"]
            judged = record["kind"] != "trim"  # no closed form exists for a trimmed tip
            line = {**record, "closed_volume": closed,
                    "rel_err": (relative_error(precise, closed)
                                if precise is not None and judged else None),
                    "class": row_class, "reasons": list(reasons),
                    "over_budget": list(measured.over)}
            self._sink.write(json.dumps(line) + "\n")
            self._sink.flush()
        return measured

    def measure_pair(self, request: PairRequest) -> PairRecord:
        """One pair cell through the default worker under its own deadline, kept for the report
        and streamed to the JSONL with the verdict this run drew from it (never trusted later:
        `verdict` recomputes it)."""
        record = self._worker.run_pair(request, PAIR_TIMEOUT_S)
        self.pairs.append(record)
        if self._sink is not None:
            verdict, reasons = cell_verdict(record)
            line = {**record, "verdict": verdict, "reasons": list(reasons),
                    "closed_control": closed_control(record)}
            self._sink.write(json.dumps(line) + "\n")
            self._sink.flush()
        return record

    def set_sink(self, sink: IO[str] | None) -> None:
        self._sink = sink

    def close(self) -> None:
        for worker in (self._worker, self.reference, self.container):
            if worker is not None:
                worker.close()


# INTERIM presets in the order the report reads them: preview first, then fine.
_INTERIM: list[Preset] = [(name, tol, ang) for name, (tol, ang) in INTERIM_PRESETS.items()]


def _request(kind: str, size: str, length: Fraction, left_hand: bool, k: int, *,
             presets: list[Preset] | None = None, step: bool = False,
             gzip_on: list[str] | None = None, want_gzip_table: bool = False) -> RowRequest:
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
        "want_gzip_table": want_gzip_table,
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


# The comparison rows' standard turn counts of the one-pipe twist: the research walked it up to
# 250 turns, where inverted solids appeared at 160-171 (STACK, measured).
ONE_PIPE_TURNS = (100, 160, 200, 250)
CQW_ENV = "SCREW_SPIKE_CQW"
PACKAGE_NOT_IMPORTABLE = "ruled: skipped, package not importable"


def _block_controls(c: Campaign, k: int, smoke: bool) -> None:
    """D-06's comparison on the sample sizes, right hand: the negative control (naive sweep +
    fuse) at 10 turns, 10 mm, 20 mm and the standard max; the one-pipe twist at the standard
    max and at 100, 160, 200 and 250 turns; the ruled-surface reference at 10 turns and the
    standard max, in the reference worker only. A smoke run is M6 at 10 turns, and says so when
    the reference package is missing instead of refusing. `k` is carried into the request, where
    none of these constructions reads it."""
    for size in ("M6",) if smoke else SAMPLE_SIZES:
        d, pitch = PITCH[size]
        top = standard_max(d)
        if smoke:
            naive_at, pipe_at, ruled_at = [10 * pitch], [10 * pitch], [10 * pitch]
        else:
            naive_at = sorted({10 * pitch, Fraction(10), Fraction(20), top})
            pipe_at = sorted({top, *(Fraction(t) * pitch for t in ONE_PIPE_TURNS)})
            ruled_at = sorted({10 * pitch, top})
        for length in naive_at:
            c.measure(_request("naive", size, length, False, k))
        for length in pipe_at:
            c.measure(_request("one_pipe", size, length, False, k))
        for length in ruled_at:
            if c.reference is None:
                if PACKAGE_NOT_IMPORTABLE not in c.notes:
                    c.notes.append(PACKAGE_NOT_IMPORTABLE)
                continue
            c.measure(_request("ruled", size, length, False, k), via="reference")


def _block_trim(c: Campaign, k: int, smoke: bool) -> None:
    """One tip-chamfer-trim row per size and hand at the standard max (D-08): the full rod row
    trimmed, with preview and fine meshes, gzip-1 on the fine one and STEP, so the request
    cost is build + trim + the slower export. A smoke run is M6 at 20 mm."""
    for size in ("M6",) if smoke else SIZES:
        d, _ = PITCH[size]
        length = Fraction(20) if smoke else standard_max(d)
        for left in _hands(smoke):
            c.measure(_request("trim", size, length, left, k, presets=_INTERIM, step=True,
                               gzip_on=["fine"]))


def _frontier_terminals(rows: list[RowRecord]) -> list[tuple[str, bool, int]]:
    """The last measured turn count per (size, hand) of a frontier run's rod rows, in size order
    and right hand first: where each walk ended, whether on a failure or on 250 turns."""
    last: dict[tuple[str, bool], float] = {}
    for r in rows:
        if r["kind"] == "rod":
            key = (r["size"], r["left_hand"])
            last[key] = max(last.get(key, 0.0), r["turns"])
    terminals: list[tuple[str, bool, int]] = []
    for (size, left), turns in sorted(last.items(), key=lambda kv: (SIZES.index(kv[0][0]),
                                                                    kv[0][1])):
        if turns != int(turns):
            raise ValueError(f"frontier terminal {turns!r} turns of {size} is not a whole turn")
        terminals.append((size, left, int(turns)))
    return terminals


def _block_rss(c: Campaign, k: int, smoke: bool) -> None:
    """Peak RSS from fresh children only (RESEARCH Pitfall 5): one `--once` child per row. Per
    size and hand at the standard max, one at INTERIM fine and one at INTERIM preview, then each
    frontier walk's terminal row at fine (rows from `--frontier-from`). The right-hand fine
    standard-max child also runs L19's gzip table. A smoke run is one M6 right-hand 10-turn
    fine child, which asks for the table so that the path runs end to end."""
    fine = _INTERIM[1]
    if smoke:
        _, pitch = PITCH["M6"]
        c.measure(_request("rod", "M6", 10 * pitch, False, k, presets=[fine], gzip_on=["fine"],
                           want_gzip_table=True), via="fresh")
        return
    if c.frontier_rows is None:
        raise ValueError("the rss block needs the rows of a frontier run (--frontier-from)")
    for size in SIZES:
        d, _ = PITCH[size]
        for left in (False, True):
            for preset in _INTERIM:
                c.measure(_request("rod", size, standard_max(d), left, k, presets=[preset],
                                   gzip_on=[preset[0]],
                                   want_gzip_table=not left and preset[0] == "fine"),
                          via="fresh")
    for size, left, turns in _frontier_terminals(c.frontier_rows):
        _, pitch = PITCH[size]
        c.measure(_request("rod", size, Fraction(turns) * pitch, left, k, presets=[fine],
                           gzip_on=["fine"]), via="fresh")


def _block_container(c: Campaign, k: int, smoke: bool) -> None:
    """The locked construction over the full D-03 grid, both hands, rod and void, in the
    production image under linux/amd64 (D-05): validity, solid count and volume only, so the rod
    takes no presets and no STEP. A smoke run is M6 at 5 turns, right hand."""
    for size in ("M6",) if smoke else SIZES:
        d, pitch = PITCH[size]
        for length in [5 * pitch] if smoke else lengths(d, pitch):
            for left in _hands(smoke):
                c.measure(_request("rod", size, length, left, k), via="container")
                c.measure(_request("void", size, length, left, k), via="container")


_MATCHED = tuple((theta, 0.0) for theta in MATCHED_POSES)
_CONTROLS = tuple((theta, CONTROL_OFFSET_PITCHES) for theta in MATCHED_POSES)


def _pair_request(size: str, rod_left: bool, nut_left: bool, clearance: float, k: int,
                  poses: tuple[tuple[float, float], ...]) -> PairRequest:
    d, pitch = PITCH[size]
    return {"size": size, "d": float(d), "pitch": float(pitch), "m": NUT_HEIGHT[size],
            "clearance": clearance, "rod_left_hand": rod_left, "nut_left_hand": nut_left,
            "k": k, "poses": list(poses)}


def _block_pair(c: Campaign, k: int, smoke: bool) -> None:
    """Question 3 at the locked K (D-11 to D-14). Per size, both same-hand pairs at every
    diagnostic and proof clearance, read at the three matched poses and the three half-pitch
    controls; the mixed pair (right-hand rod, left-hand nut) at every proof clearance, matched
    poses only; then the two K values other than the locked one on the reference sizes, right
    hand, proof clearances (reference rows, not verdict inputs, Pitfall 8). A smoke run is one M6
    right-hand cell at c = 0.10."""
    if smoke:
        c.measure_pair(_pair_request("M6", False, False, 0.10, k, _MATCHED + _CONTROLS))
        return
    for size in SIZES:
        for left in (False, True):
            for clearance in (*DIAGNOSTIC_CLEARANCES, *PAIR_CLEARANCES):
                c.measure_pair(_pair_request(size, left, left, clearance, k,
                                             _MATCHED + _CONTROLS))
        for clearance in PAIR_CLEARANCES:
            c.measure_pair(_pair_request(size, False, True, clearance, k, _MATCHED))
    for size in PAIR_REFERENCE_SIZES:
        for other in (x for x in K_CANDIDATES if x != k):
            for clearance in PAIR_CLEARANCES:
                c.measure_pair(_pair_request(size, False, False, clearance, other,
                                             _MATCHED + _CONTROLS))


BLOCKS: dict[str, Callable[[Campaign, int, bool], None]] = {
    "ksweep": _block_ksweep, "grid": _block_grid, "frontier": _block_frontier,
    "ladder": _block_ladder, "controls": _block_controls, "trim": _block_trim,
    "rss": _block_rss, "pair": _block_pair, "container": _block_container,
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
        if record["kind"] != "trim":  # no closed form exists for a trimmed tip (D-08)
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


def report(header: list[str], measured: list[Measured], stops: list[str], end: Reading,
           extra: Sequence[str] = ()) -> str:
    """The run's Markdown: header lines, the per-size aggregate, then every non-ok row and every
    over-budget row on its own line with its reasons, the frontier stops, the block's own
    sections (`extra`), and the end reading labelled as including this run's own load."""
    lines = [*header, *([""] if header else []), *aggregate_table(measured), ""]
    for m in measured:
        if m.row_class != "ok":
            lines.append(f"- {row_label(m.record)}: {m.row_class}: {'; '.join(m.reasons)}")
        if m.over:
            lines.append(f"- {row_label(m.record)}: {'; '.join(m.over)}")
    lines.extend(f"- frontier {stop}" for stop in stops)
    if extra:
        lines.extend([*([] if lines[-1] == "" else [""]), *extra, ""])
    lines.append(_reading_line(end, " (includes this run's own load)"))
    return "\n".join(lines)


_CONSTRUCTIONS = {
    "naive": "naive sweep + fuse (negative control)",
    "one_pipe": "one-pipe twist",
    "ruled": "ruled-surface reference",
}


def _ratio(value: float | None, closed: float) -> str:
    return "n/a" if value is None else f"{value / closed:.6f}"


def _by_size(record: RowRecord) -> tuple[int, bool, float]:
    return SIZES.index(record["size"]), record["left_hand"], record["length"]


def controls_section(rows: list[RowRecord]) -> list[str]:
    """D-06's comparison: every comparison row with its class and its volume as a ratio to the
    closed form, then the known-bad inputs THRD-04's positive-control test needs, with their
    exact parameters. A negative control that reads ok is said so loudly: it did not control."""
    mine = [r for r in rows if r["kind"] in _CONSTRUCTIONS]
    if not mine:
        return ["controls: not recorded"]
    lines = ["| Construction | Size | Length mm | Turns | Class | Solids | Valid | "
             "Precise ratio | Default ratio |", "|---|---|---|---|---|---|---|---|---|"]
    for kind in _CONSTRUCTIONS:
        for r in sorted((r for r in mine if r["kind"] == kind), key=_by_size):
            closed = closed_of(r)
            solids, valid = r["solids"], r["is_valid"]
            lines.append(
                f"| {_CONSTRUCTIONS[kind]} | {r['size']} | {r['length']:g} | {r['turns']:g} | "
                f"{row_class(r)} | {'n/a' if solids is None else solids} | "
                f"{'n/a' if valid is None else ('yes' if valid else 'no')} | "
                f"{_ratio(r['precise_volume'], closed)} | "
                f"{_ratio(r['default_volume'], closed)} |")
    lines += ["", "Known-bad inputs for THRD-04 (naive rows with 1 solid, isValid True and a "
              "precise ratio below 0.5):"]
    bad = known_bad_inputs(mine)
    for r in bad:
        ratio = _ratio(r["precise_volume"], closed_of(r))
        lines.append(f"- naive_sweep_fuse(d={r['d']!r}, pitch={r['pitch']!r}, "
                     f"length={r['length']!r}): precise ratio {ratio}")
    if not bad:
        lines.append("- none recorded")
    lines += [f"- NEGATIVE CONTROL READ OK: {row_label(r)} -- the control did not control"
              for r in mine if r["kind"] == "naive" and row_class(r) == "ok"]
    lines += ["", "The ruled-surface profile is not identical to the pinned profile, so its "
              "ratio to this closed form is not an accuracy claim."]
    return lines


def trim_section(rows: list[RowRecord]) -> list[str]:
    """D-08's cost evidence: per size and hand at the standard max, the trim seconds and the
    request cost build + trim + the slower export. Never a pass-bar input."""
    mine = sorted((r for r in rows if r["kind"] == "trim"), key=_by_size)
    if not mine:
        return ["trim: not recorded"]
    lines = ["| Size | Hand | Length mm | Class | Trim s | Request s (build + trim + slower "
             "export) | Fine triangles | STEP bytes |", "|---|---|---|---|---|---|---|---|"]
    for r in mine:
        fine = fine_mesh(r)
        seconds, trim_s, step = request_seconds(r), r["trim_s"], r["step_bytes"]
        lines.append(
            f"| {r['size']} | {'left' if r['left_hand'] else 'right'} | {r['length']:g} | "
            f"{row_class(r)} | {'n/a' if trim_s is None else format(trim_s, '.2f')} | "
            f"{'n/a' if seconds is None else format(seconds, '.2f')} | "
            f"{'n/a' if fine is None else fine['triangles']} | "
            f"{'n/a' if step is None else step} |")
    lines += ["", f"The cone angle is {TIP_CHAMFER_DEG:g} degrees from the end face at the "
              "minor radius, UNVERIFIED (ISO 4753 is unread): these rows are cost evidence "
              "for Phase 4, not geometry truth, and never enter the pass bar."]
    return lines


_MIB = 1024 * 1024


def rss_section(rows: list[RowRecord]) -> list[str]:
    """Peak RSS per row, every figure labelled as a fresh child's, then L19's gzip table and the
    level its rule selects for each row that asked for one. A row with no figure prints `n/a`
    and its class: a failed child has no memory to report (L02)."""
    mine = [r for r in rows if r["kind"] == "rod"]
    if not mine:
        return ["rss: not recorded"]
    lines = ["| Size | Hand | Preset | Turns | Length mm | Row | Peak RSS | Class |",
             "|---|---|---|---|---|---|---|---|"]
    for r in sorted(mine, key=_by_size):
        peak = r["peak_rss_bytes"]
        d = PITCH[r["size"]][0]
        top = float(standard_max(d))
        where = ("standard max" if r["length"] == top
                 else "frontier terminal" if r["length"] > top else "below standard max")
        figure = ("n/a" if peak is None
                  else f"{peak / _MIB:.1f} MiB (fresh child, this row only)")
        lines.append(f"| {r['size']} | {'left' if r['left_hand'] else 'right'} | "
                     f"{', '.join(name for name, _, _ in r['presets'])} | {r['turns']:g} | "
                     f"{r['length']:g} | {where} | {figure} | {row_class(r)} |")
    tabled = [r for r in sorted(mine, key=_by_size) if r["gzip_table"] is not None]
    if tabled:
        lines += ["", "L19 gzip table (levels 1, 6 and 9 on the row's own STL, fresh child):", "",
                  "| Size | Level | Output bytes | Single-threaded median ms | "
                  "10-concurrent wall median ms |", "|---|---|---|---|---|"]
        for r in tabled:
            for level, out_bytes, single_ms, concurrent_ms in r["gzip_table"] or []:
                lines.append(f"| {r['size']} | {level} | {out_bytes} | {single_ms:.1f} | "
                             f"{concurrent_ms:.1f} |")
        lines.append("")
        lines += [f"- {r['size']}: selected gzip level {r['gzip_selected']} "
                  "(spur L19's rule, `select_gzip_level`)" for r in tabled]
    return lines


def container_section(rows: list[RowRecord]) -> list[str]:
    """The container pass in two lines: how many rows ran and in which classes, and that the
    timings in them are not a measurement of anything but the emulator (D-05)."""
    if not rows:
        return ["container: not recorded"]
    counts = Counter(row_class(r) for r in rows)
    classes = ", ".join(f"{name} {counts[name]}" for name in (
        "ok", "silent_wrong", "failure", "timeout", "worker_died"))
    return [f"{len(rows)} rows in `{CONTAINER_IMAGE}` under linux/amd64: {classes}.",
            "Every timing in this run is emulation: validity, solid count and volume are the "
            "measurement, and a timing here feeds no bound (D-05)."]


_HANDS = ("right", "left")
_PAIR_HEAD = ("| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | "
              "Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | "
              "Cell verdict |")
_PAIR_RULE = "|---|---|---|---|---|---|---|"


def _hand_of(cell: PairRecord) -> str:
    return "left" if cell["rod_left_hand"] else "right"


def _same_hand_cells(cells: list[PairRecord], size: str, hand: str, k: int) -> list[PairRecord]:
    return sorted((c for c in cells if c["size"] == size and c["k"] == k
                   and c["rod_left_hand"] == c["nut_left_hand"] and _hand_of(c) == hand),
                  key=lambda c: c["clearance"])


def _vols(readings: list[PairReading]) -> str:
    return "/".join("n/a" if r["volume"] is None else f"{r['volume']:.6g}" for r in readings)


def _solids(readings: list[PairReading]) -> str:
    return "/".join("n/a" if r["solids"] is None else str(r["solids"]) for r in readings)


def _diagnostics(cell: PairRecord) -> str:
    readings = cell["readings"]
    if not readings:
        return "n/a"
    errors = sum(1 for r in readings if r["diag_errors"])
    warnings = sum(1 for r in readings if r["diag_warnings"])
    return f"errors {errors} of {len(readings)}, warnings {warnings} of {len(readings)}"


def _pair_row(cell: PairRecord) -> str:
    matched = [r for r in cell["readings"] if r["offset_pitches"] == 0.0]
    controls = [r for r in cell["readings"] if r["offset_pitches"] != 0.0]
    verdict, _ = cell_verdict(cell)
    shown = "n/a" if cell["outcome"] != "built" else f"{closed_control(cell):.6g}"
    cells = [f"{cell['clearance']:g}", _vols(matched) or "n/a", _vols(controls) or "n/a", shown,
             f"{_solids(matched) or 'n/a'} ; {_solids(controls) or 'n/a'}", _diagnostics(cell),
             verdict if cell["outcome"] == "built" else f"{verdict} ({cell['outcome']})"]
    return "| " + " | ".join(cells) + " |"


def _pair_reasons(cell: PairRecord) -> str | None:
    verdict, reasons = cell_verdict(cell)
    if verdict == "proven":
        return None
    return (f"- {cell['size']} {_hand_of(cell)} c={cell['clearance']:g}: {verdict}: "
            f"{'; '.join(reasons) or 'no reason recorded'}")


def pair_escapes(cells: list[PairRecord], locked_k: int, sizes: Sequence[str]) -> tuple[str, ...]:
    """The escape clause of D-14 over the locked-K cells of `sizes`: a size is not falsifiable
    unless both hands have a proven proof-clearance cell, and a size whose mixed-hand pair did not
    read violated at every matched pose (or has no mixed cell) fails the rule that a mixed pair
    must read violated. A size with no cell at all is both."""
    reasons: list[str] = []
    for size in sizes:
        mine = [c for c in cells if c["size"] == size and c["k"] == locked_k]
        weak = [hand for hand in _HANDS
                if not size_falsifiable(_same_hand_cells(cells, size, hand, locked_k))]
        if weak:
            reasons.append(f"pair: not falsifiable for size {size} ({', '.join(weak)} hand)")
        if not mixed_hand_violated(mine):
            reasons.append(f"pair: size {size}: the mixed-hand pair did not read violated at "
                           "every matched pose")
    return tuple(reasons)


def _yes(flag: bool) -> str:
    return "yes" if flag else "NO"


def pair_section(cells: list[PairRecord], locked_k: int) -> list[str]:
    """Question 3 for the sizes recorded: per (size, hand) one row per clearance with every
    volume read, the control's closed form and the cell verdict; then falsifiability, the
    excluded clearances, the mixed-hand line and the sensitivity line per size; the reference K
    rows; and the variant rules, which are computed from the same readings and never change the
    verdict (owner ruling R1)."""
    if not cells:
        return ["pair: not recorded"]
    sizes = [size for size in SIZES if any(c["size"] == size for c in cells)]
    locked = [c for c in cells if c["k"] == locked_k]
    lines = [f"Locked K = {locked_k}; every cell below is read at it. A cell is proven only if "
             f"all 3 matched poses read empty (<= {EMPTY_MM3:g} mm3) and all 3 "
             f"controls read within {PAIR_BAND:g} of the closed form (D-12, D-14).", ""]
    for size in sizes:
        for hand in _HANDS:
            of_hand = _same_hand_cells(cells, size, hand, locked_k)
            if not of_hand:
                continue
            lines += [f"#### {size} {hand} hand (m = {NUT_HEIGHT[size]:g} mm, UNVERIFIED)", "",
                      _PAIR_HEAD, _PAIR_RULE, *(_pair_row(c) for c in of_hand), ""]
            lines += [r for r in (_pair_reasons(c) for c in of_hand) if r is not None]
            lines.append("")
    lines += ["#### Falsifiability (D-14)", ""]
    for size in sizes:
        weak = [hand for hand in _HANDS
                if not size_falsifiable(_same_hand_cells(cells, size, hand, locked_k))]
        lines.append(f"- not falsifiable for size {size} ({', '.join(weak)} hand): the escape "
                     "clause fires" if weak else f"- {size}: falsifiable on both hands")
        for hand in _HANDS:
            of_hand = _same_hand_cells(cells, size, hand, locked_k)
            if of_hand:
                dropped = excluded_clearances(of_hand)
                lines.append(f"- {size} {hand}: excluded clearances "
                             f"{', '.join(f'{c:g}' for c in dropped) or 'none'}")
        mixed = [c for c in locked if c["size"] == size and c["rod_left_hand"]
                 != c["nut_left_hand"]]
        lines.append(f"- {size}: mixed-hand pair read violated at every matched pose: "
                     f"{_yes(mixed_hand_violated(mixed))} ({len(mixed)} mixed cells)")
        for hand in _HANDS:
            twin = [c for c in _same_hand_cells(cells, size, hand, locked_k)
                    if c["clearance"] == DIAGNOSTIC_CLEARANCES[1]]
            if twin:
                lines.append(f"- {size} {hand}: sensitivity (c = {DIAGNOSTIC_CLEARANCES[1]:g}) "
                             f"{'ok' if sensitivity_ok(twin[0]) else 'NOT ok'}")
    reference = [c for c in cells if c["k"] != locked_k]
    lines += ["", "#### Reference K (reported, not verdict inputs)", ""]
    if reference:
        lines += ["| Size | K | " + " | ".join(f"c = {c:g}" for c in PAIR_CLEARANCES) + " |",
                  "|---|---|" + "---|" * len(PAIR_CLEARANCES)]
        for size in sizes:
            for k in sorted({c["k"] for c in reference if c["size"] == size}):
                verdicts = {c["clearance"]: cell_verdict(c)[0] for c in reference
                            if c["size"] == size and c["k"] == k}
                lines.append(f"| {size} | {k} | " + " | ".join(
                    verdicts.get(c, "n/a") for c in PAIR_CLEARANCES) + " |")
    else:
        lines.append("none recorded")
    rules = variant_rules(locked)
    names = list(rules)
    keys = list(dict.fromkeys(key for table in rules.values() for key in table))
    lines += ["", "#### Variant rules (reported, never the verdict)", "",
              "Computed from the same recorded readings. The D-14 column is the verdict; the "
              "others are for Phase 5's revision and never feed it (owner ruling R1).", ""]
    if keys:
        proof = {f"{c['size']} {_hand_of(c)} c={c['clearance']:g} K={c['k']}": c for c in locked
                 if c["rod_left_hand"] == c["nut_left_hand"]}
        lines += ["| Cell | D-14 verdict | " + " | ".join(names) + " |",
                  "|---|---|" + "---|" * len(names)]
        lines += [f"| {key} | {cell_verdict(proof[key])[0]} | "
                  + " | ".join(_yes(rules[name][key]) for name in names) + " |" for key in keys]
    else:
        lines.append("no proof cell recorded")
    return lines


def pair_report(header: list[str], cells: list[PairRecord], locked_k: int, end: Reading) -> str:
    """The pair run's Markdown: header lines, the pair section, the end reading labelled as
    including this run's own load. An empty run raises: an empty report reads as a pass."""
    if not cells:
        raise ValueError("the pair block produced no cells -- an empty report must be refused")
    return "\n".join([*header, "", *pair_section(cells, locked_k), "",
                      _reading_line(end, " (includes this run's own load)")])


# What each block adds to its report beyond the per-size aggregate: a title and the lines, as a
# function of the rows alone, so a run's report and the verdict over its JSONL print the same.
SECTIONS: dict[str, tuple[str, Callable[[list[RowRecord]], list[str]]]] = {
    "controls": ("### Controls (D-06)", controls_section),
    "trim": ("### Tip trim cost (D-08)", trim_section),
    "rss": ("### Peak RSS and the L19 gzip table", rss_section),
    "container": ("### Container validity (D-05)", container_section),
}


def _block_extra(block: str, campaign: Campaign) -> list[str]:
    section = SECTIONS.get(block)
    lines = [f"- {note}" for note in campaign.notes]
    if section is not None:
        title, build = section
        lines += [*([""] if lines else []), title, "", *build([m.record for m in campaign.rows])]
    return lines


def _controls_behave(rows: list[Measured]) -> bool:
    """The comparison rows' smoke expectation: the negative control is wrong on purpose and
    must not read ok, the one-pipe row must, and the reference row must build (its profile
    differs from the pinned one, so its class says nothing)."""
    for m in rows:
        kind = m.record["kind"]
        if (kind == "naive" and m.row_class == "ok") or (
                kind == "one_pipe" and m.row_class != "ok") or (
                kind == "ruled" and m.record["outcome"] != "built"):
            return False
    return True


# A block's smoke exit is 0 only when its rows came out as that block expects; the default is
# every row ok.
SMOKE_EXPECTS: dict[str, Callable[[list[Measured]], bool]] = {"controls": _controls_behave}


def _smoke_passes(block: str, rows: list[Measured]) -> bool:
    expects = SMOKE_EXPECTS.get(block)
    return all(m.row_class == "ok" for m in rows) if expects is None else expects(rows)


def _reference_env(environ: Mapping[str, str]) -> tuple[dict[str, str] | None, str]:
    """The environment of the reference worker (PYTHONPATH adding the scratch directory named
    by SCREW_SPIKE_CQW) and why it could not be built, checked by importing the package in a
    throw-away child: this parent never imports the reference package or the kernel (T-02-11)."""
    scratch = environ.get(CQW_ENV)
    if not scratch:
        return None, (f"{CQW_ENV} is not set: the ruled-surface reference needs the scratch "
                      "directory its package was installed into (D-06)")
    path = os.pathsep.join(p for p in (scratch, environ.get("PYTHONPATH")) if p)
    child = {**environ, "PYTHONPATH": path}
    probe = subprocess.run([sys.executable, "-c", f"import {RULED_MODULE}"], env=child,
                           cwd=_REPO_ROOT, capture_output=True, text=True, check=False)
    if probe.returncode != 0:
        last = (probe.stderr.strip().splitlines() or ["no error text"])[-1]
        return None, f"{RULED_MODULE} is not importable from {CQW_ENV}={scratch}: {last}"
    return child, ""


def _image_facts() -> tuple[str | None, str]:
    """`<id> <created>` of the production image, or `None` and why not: docker absent, or the
    image not built (`make image`). One list-argv call, no shell (T-02-12)."""
    try:
        done = subprocess.run(
            ["docker", "image", "inspect", CONTAINER_IMAGE, "--format", "{{.Id}} {{.Created}}"],
            capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None, "docker is not installed or not on PATH"
    if done.returncode != 0:
        return None, (f"image {CONTAINER_IMAGE} is not available ({done.stderr.strip()}): "
                      "run `make image` first")
    return done.stdout.strip(), ""


def _container_lines(image: str) -> list[str]:
    machine = platform.machine()
    where = (f"under emulation on {machine}" if machine.lower() in ("arm64", "aarch64")
             else f"on a {machine} host")
    return [f"- Image: `{CONTAINER_IMAGE}` {image}",
            f"- platform linux/amd64 {where}: timings feed no bound"]


def _container_worker() -> Worker:
    """The worker that runs inside the image. A timeout abandons its container, so each spawn
    takes a new name and `docker kill` stops the old one."""
    names = itertools.count()
    prefix = f"screw-spike-{os.getpid()}"
    return Worker(argv=lambda: container_argv(f"{prefix}-{next(names)}", _REPO_ROOT),
                  on_timeout=docker_kill)


def _make_campaign(block: str, decisive: bool, sink: IO[str] | None, *,
                   reference_env: dict[str, str] | None,
                   frontier_rows: list[RowRecord] | None) -> Campaign:
    """One block's campaign with the workers it needs. The container block is never decisive:
    emulated timings say nothing about the production host (D-05)."""
    return Campaign(
        Worker(), decisive and block != "container", sink,
        reference=None if reference_env is None else Worker(env=reference_env),
        container=_container_worker() if block == "container" else None,
        frontier_rows=frontier_rows)


def _frontier_rows(frontier_from: str, results_dir: Path) -> list[RowRecord]:
    """The rows of a recorded frontier run, for the rss block's terminal rows."""
    path = results_dir / f"{frontier_from}.jsonl"
    if not path.is_file():
        raise ValueError(f"frontier run {frontier_from!r} is not recorded under {results_dir}")
    lines = path.read_text().splitlines()
    if not lines or parse_header(lines[0])["block"] != "frontier":
        raise ValueError(f"run {frontier_from!r} is not a frontier run")
    return [parse_result_row(line) for line in lines[1:]]


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
              results_dir: Path = RESULTS_DIR, env: Mapping[str, str] | None = None,
              frontier_from: str | None = None) -> int:
    """One guarded campaign block. Refusals, all exit 2 with nothing written: a run id that is
    not `RUN_ID`; a run id already recorded (a run is never overwritten or retried in place); a
    `--k-from` missing, malformed or given to the K sweep; the protocol guard. Then: the quiet
    gate, the header as the first JSONL line, rows streamed, the end reading, the Markdown.
    The controls block also refuses, before the guard and with nothing written, when
    SCREW_SPIKE_CQW (read from `env`, default the process environment) does not name a
    directory the reference package imports from, and the container block when docker or the
    image is absent. The rss block requires `--frontier-from <frontier run id>` and no other
    block takes it."""
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
    elif (block == "rss") != (frontier_from is not None):
        problem = ("block 'rss' requires --frontier-from <frontier run id>" if block == "rss"
                   else f"only the rss block takes --frontier-from, not {block!r}")
    elif frontier_from is not None and not RUN_ID.fullmatch(frontier_from):
        problem = f"--frontier-from {frontier_from!r} is not a run id"
    if problem is not None:
        print(f"refused: {problem}", file=sys.stderr)
        return 2
    reference_env: dict[str, str] | None = None
    if block == "controls":
        reference_env, why = _reference_env(os.environ if env is None else env)
        if reference_env is None:
            print(f"refused: {why}", file=sys.stderr)
            return 2
    image: str | None = None
    if block == "container":
        image, why = _image_facts()
        if image is None:
            print(f"refused: {why}", file=sys.stderr)
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
    frontier_rows: list[RowRecord] | None = None
    if frontier_from is not None:
        try:
            frontier_rows = _frontier_rows(frontier_from, results_dir)
        except ValueError as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 2
    quiet = wait_quiet()  # the protocol's constants; no flag overrides them
    # Emulated timings prove nothing about the production host, so a container run is never
    # decisive whatever the host gate said (D-05); the gate's readings are still recorded.
    decisive = quiet.decisive and block != "container"
    results_dir.mkdir(parents=True, exist_ok=True)
    header: HeaderRecord = {
        "run_id": run_id, "block": block, "head": facts.head, "protocol_blob": facts.main_blob,
        "protocol_commit": facts.main_commit, "decisive": decisive,
        "readings": [(r.utc, r.load1) for r in quiet.readings], "k": k, "k_source": k_source,
    }
    try:
        sink = target.open("x", encoding="utf-8")  # exclusive: never overwrites
    except FileExistsError:
        print(f"refused: run id {run_id!r} already recorded; a run is never overwritten",
              file=sys.stderr)
        return 2
    campaign = _make_campaign(block, decisive, sink, reference_env=reference_env,
                              frontier_rows=frontier_rows)
    try:
        sink.write(json.dumps(header) + "\n")
        sink.flush()
        BLOCKS[block](campaign, DEFAULT_K if k is None else k, False)
    finally:
        campaign.close()
        sink.close()
    head_lines = [
        f"## Thread spike run {run_id}", "", *_environment_lines(),
        f"- Protocol blob: `{facts.main_blob}`", f"- Protocol commit: `{facts.main_commit}`",
        f"- Block: {block}", f"- K: {'swept' if k is None else k} ({k_source})",
        *(_reading_line(r) for r in quiet.readings),
        *(_container_lines(image) if image is not None else []),
        _release_line(quiet) if block != "container"
        else f"- release: container run, non-decisive by construction (gate read at "
             f"{quiet.readings[-1].utc})",
    ]
    if block == "pair":
        text = pair_report(head_lines, campaign.pairs, DEFAULT_K if k is None else k, read_now())
    else:
        text = report(head_lines, campaign.rows, campaign.stops, read_now(),
                      _block_extra(block, campaign))
    (results_dir / f"{run_id}.md").write_text(text + "\n")
    print(text)
    return 0


def smoke_block(block: str) -> int:
    """A block's code on a smoke subset (sizes M2 and M6, right hand, at most 6 rows, lengths of
    at most 20 turns; frontier: M2's first step; K = 5): no run id, output in a temporary
    directory, the guard informational and the quiet cap 0. Exit 0 only when every row is ok."""
    if block == "pair":
        return smoke_pair()
    image: str | None = None
    if block == "container":
        image, why = _image_facts()
        if image is None:
            print(f"refused: {why}", file=sys.stderr)
            return 2
    quiet = wait_quiet(cap=0.0)
    print(f"## Thread spike smoke: {block}")
    print()
    for line in _environment_lines():
        print(line)
    if image is not None:
        for line in _container_lines(image):
            print(line)
    for reading in quiet.readings:
        print(_reading_line(reading, " (at start)"))
    print("- Quiet gate: smoke: quiet gate not waited")
    guard = read_guard(fetch=False).result
    state = "held" if guard.held else "refused -- " + "; ".join(guard.reasons)
    print(f"- Protocol guard (informational in smoke (not fetched); never enforced here): {state}")
    print()
    out_dir = Path(tempfile.mkdtemp(prefix="screw-spike-smoke-"))
    reference_env = _reference_env(os.environ)[0] if block == "controls" else None
    campaign = _make_campaign(block, quiet.decisive, None, reference_env=reference_env,
                              frontier_rows=None)
    try:
        with (out_dir / "smoke.jsonl").open("w", encoding="utf-8") as sink:
            campaign.set_sink(sink)
            BLOCKS[block](campaign, DEFAULT_K, True)
    finally:
        campaign.close()
    print(_ROW_HEAD)
    print(_ROW_RULE)
    for m in campaign.rows:
        print(_table_row(m.record, m.row_class, m.closed))
    print()
    print(report([], campaign.rows, campaign.stops, read_now(), _block_extra(block, campaign)))
    print()
    print("**SMOKE** -- not a campaign run: no run id, never recorded in bench/RESULTS.md.")
    print(f"JSONL: `{out_dir / 'smoke.jsonl'}`")
    return 0 if _smoke_passes(block, campaign.rows) else 1


def smoke_pair() -> int:
    """One M6 right-hand pair cell at c = 0.10 and K = 5, its six readings and its verdict
    against the closed form: no run id, nothing recorded, the guard informational. Exit 0 when
    the cell ran, whatever the verdict (a false-empty control is a measured outcome, not a defect
    of the harness), 1 when it failed, timed out or its worker died."""
    quiet = wait_quiet(cap=0.0)
    print("## Thread spike smoke: pair")
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
    campaign = _make_campaign("pair", quiet.decisive, None, reference_env=None,
                              frontier_rows=None)
    try:
        BLOCKS["pair"](campaign, DEFAULT_K, True)
    finally:
        campaign.close()
    cell = campaign.pairs[0]
    if cell["outcome"] != "built":
        print(f"cell {cell['outcome']}: {cell['error']}")
    else:
        print("| Pose | theta | Solids | Volume mm3 | Seconds | Diagnostics (columns only) |")
        print("|---|---|---|---|---|---|")
        for r in cell["readings"]:
            pose = "matched" if r["offset_pitches"] == 0.0 else "control"
            print(f"| {pose} | {r['theta']:+.4f} | {r['solids']} | {r['volume']:.6g} | "
                  f"{r['seconds']:.1f} | errors {r['diag_errors']}, warnings "
                  f"{r['diag_warnings']} |")
        print()
        print(f"- control closed form: {closed_control(cell):.6g} mm3 "
              f"(m = {cell['m']:g}, c = {cell['clearance']:g})")
        verdict, reasons = cell_verdict(cell)
        print(f"- cell verdict: {verdict}")
        for reason in reasons:
            print(f"  - {reason}")
    print(_reading_line(read_now(), " (includes this run's own load)"))
    print()
    print("**SMOKE** -- not a campaign run: no run id, never recorded in bench/RESULTS.md.")
    return 0 if cell["outcome"] == "built" else 1


ROD_BLOCKS = ("ksweep", "grid", "frontier", "ladder")
# The runs a clean verdict needs: the four rod blocks, the container pass, whose rows count toward
# the pass bar and the escape clause because production runs in that image (D-05), and the pair
# block, whose falsifiability is question 3 and fires the escape clause by itself (D-14).
PASS_BLOCKS = (*ROD_BLOCKS, "pair", "container")
_NOT_ESTABLISHED = "not established"
_Runs = dict[str, tuple[HeaderRecord, list[RowRecord]]]
_PairRun = tuple[HeaderRecord, list[PairRecord]]


def _read_runs(prefix: str, results_dir: Path) -> tuple[_Runs, _PairRun | None]:
    """Every `<prefix>-*.jsonl` as (header, rows) by block, the pair run apart because its rows
    are cells. Two runs of one block under a prefix are ambiguous and refused: which one is the
    record?"""
    runs: _Runs = {}
    pair: _PairRun | None = None
    for path in sorted(results_dir.glob(f"{prefix}-*.jsonl")):
        lines = path.read_text().splitlines()
        if not lines:
            raise ValueError(f"{path.name} is empty")
        header = parse_header(lines[0])
        block = header["block"]
        taken = pair[0] if block == "pair" and pair is not None else (
            runs[block][0] if block in runs else None)
        if taken is not None:
            raise ValueError(f"two runs of block {block} under prefix {prefix!r}: "
                             f"{taken['run_id']!r} and {header['run_id']!r}")
        if block == "pair":
            pair = (header, [parse_pair_result_row(line) for line in lines[1:]])
        else:
            runs[block] = (header, [parse_result_row(line) for line in lines[1:]])
    return runs, pair


# The blocks whose record is held against the Method table's row set before it is read. The
# controls, trim and rss runs are evidence beside the verdict, no input to its outcome, and are
# not (they are still held to the locked K by `_unread_blocks`).
COMPLETE_BLOCKS = ("ksweep", "grid", "frontier", "ladder", "container")


def _incomplete_blocks(runs: _Runs, pair: _PairRun | None) -> dict[str, list[str]]:
    """Per verdict block, how its record falls short of the pre-registered row set (sizes x
    lengths or turns x hands x kinds, each row once, frontier walks ended); a block with nothing
    to report is complete and absent from the result."""
    gaps: dict[str, list[str]] = {}
    for block in COMPLETE_BLOCKS:
        if block in runs:
            header, rows = runs[block]
            found = block_gaps(block, header, rows, sizes=SIZES, sample_sizes=SAMPLE_SIZES)
            if found:
                gaps[block] = found
    if pair is not None:
        found = pair_gaps(pair[0], pair[1], sizes=SIZES, reference_sizes=PAIR_REFERENCE_SIZES)
        if found:
            gaps["pair"] = found
    return gaps


def _unread_blocks(runs: _Runs, pair: _PairRun | None) -> dict[str, list[str]]:
    """The blocks the verdict will not read, each with why. A block is unread when its
    record is incomplete (`_incomplete_blocks`) or when its header, or any row it holds, names
    another K than the one `select_k` takes from the sweep's own record (`DEFAULT_K` when none
    qualifies, as `run_block` does): K is never read from a header, so a run at a K the rule did
    not select cannot stand in for the locked construction. With no complete sweep there is
    nothing to check a K against, which is a missing block and not a licence to trust a
    header."""
    unread = _incomplete_blocks(runs, pair)
    if "ksweep" not in runs or "ksweep" in unread:
        return unread
    chosen = select_k(runs["ksweep"][1])
    locked = DEFAULT_K if chosen is None else chosen
    source = (f"selected by select_k from run `{runs['ksweep'][0]['run_id']}`"
              if chosen is not None else f"no K qualified, so the harness's {DEFAULT_K}")
    headers = {block: head for block, (head, _) in runs.items() if block != "ksweep"}
    if pair is not None:
        headers["pair"] = pair[0]
    for block, header in headers.items():
        if header["k"] != locked:
            unread.setdefault(block, []).append(
                f"run `{header['run_id']}` was recorded at K = {header['k']}, but the sweep's "
                f"locked K is {locked} ({source})")
    # A header vouches for nothing it did not build: every row must carry the locked K too. The
    # evidence runs are held to no row set, so this is the only place their rows' K is read.
    # The pair cells are not checked here: `pair_gaps` holds the locked cells at the header's K
    # and the reference cells at the two other K values, which the Method pre-registers.
    for block, (header, rows) in runs.items():
        others = sorted({r["k"] for r in rows} - {locked})
        if block != "ksweep" and others:
            count = sum(1 for r in rows if r["k"] != locked)
            unread.setdefault(block, []).append(
                f"run `{header['run_id']}` holds {count} rows recorded at K = "
                f"{', '.join(map(str, others))}, but the sweep's locked K is {locked} ({source})")
    return unread


def _recorded_non_ok(block: str, runs: _Runs, pair: _PairRun | None) -> list[str]:
    """Every row of an unread block whose class is not ok, with that class, and for the pair
    block every cell that did not finish, with its outcome. Not judged, never silent: a
    recorded failure in a block nobody could read is still named (L02)."""
    if block == "pair":
        cells = [] if pair is None else pair[1]
        return [f"recorded, not judged: {c['size']} {_hand_of(c)} rod, "
                f"{'left' if c['nut_left_hand'] else 'right'} nut c={c['clearance']:g} "
                f"K={c['k']}: {c['outcome']}" for c in cells if c["outcome"] != "built"]
    rows = runs[block][1] if block in runs else []
    return [f"recorded, not judged: {row_label(r)}: {cls}" for r in rows
            if (cls := row_class(r)) != "ok"]


# The verdict blocks the escape clause is drawn from: the grid's and the container's rows
# (`escape_rows`), the pair cells (`pair_escapes`) and the sweep (no K qualified). With one of
# them unread or missing, "not fired" would be a claim about rows nobody judged.
_ESCAPE_SOURCES = ("ksweep", "grid", "pair", "container")


def _first_over(rows: list[RowRecord], size: str, over: Callable[[RowRecord], bool]) -> str | None:
    """The shortest row of `size`, rod or void, over a budget, as its label, or `None`."""
    hits = [r for r in rows if r["size"] == size and r["kind"] in ("rod", "void") and over(r)]
    return row_label(min(hits, key=lambda r: r["length"])) if hits else None


def _k_section(runs: _Runs) -> list[str]:
    if "ksweep" not in runs:
        return ["K: not established (no ksweep run)"]
    header, rows = runs["ksweep"]
    k = select_k(rows)
    chosen = (f"selected K: {k} (select_k over run `{header['run_id']}`)" if k is not None
              else f"{NO_K_SOURCE}; no K was selected")
    lines = [chosen, "", "| K | Rows | Non-ok rows | Fine triangles at the standard max | "
             "STEP bytes at the standard max | Qualifies |", "|---|---|---|---|---|---|"]
    for score in k_scores(rows):
        qualifies = score.triangles is not None
        lines.append(f"| {score.k} | {score.rows} | {score.non_ok} | "
                     f"{'n/a' if score.triangles is None else score.triangles} | "
                     f"{'n/a' if score.step_bytes is None else score.step_bytes} | "
                     f"{'yes' if qualifies else 'no'} |")
    return lines


def _estimator_line(grid_rows: list[RowRecord], decisive: bool) -> tuple[str, bool]:
    """The estimator section's line and whether estimator and T_gate were both established. They
    are one outcome: `select_estimator` returns the winner and its gate together, or raises.
    `decisive` is the grid run's gate: a tie is broken by seconds only on a decisive one."""
    try:
        name, err, gate = select_estimator(grid_rows, decisive)
    except ValueError as exc:
        return (f"estimator and T_gate: {_NOT_ESTABLISHED} ({exc}); no clean pass without them",
                False)
    return f"estimator: {name}; max abs error {err:.3e}; T_gate {gate:g}", True


def _cap_cell(value: float | None, *, established: bool = True) -> str:
    if not established:
        return f"{_NOT_ESTABLISHED} (non-decisive gate)"
    return "no row over budget" if value is None else f"{value:g}"


def _run_of(runs: _Runs, block: str) -> tuple[HeaderRecord | None, list[RowRecord]]:
    """The block's header and rows, or `(None, [])` when that block was not recorded."""
    return runs.get(block, (None, []))


def _caps_section(runs: _Runs) -> list[str]:
    grid_header, grid = _run_of(runs, "grid")
    front_header, frontier = _run_of(runs, "frontier")
    # The construction cap is a frontier claim and the seconds cap a grid claim; each is judged
    # on its own run's gate, so they can differ (a decisive grid with a loose frontier).
    by_frontier = turn_caps(grid, frontier, front_header["decisive"] if front_header else False)
    by_grid = turn_caps(grid, [], grid_header["decisive"] if grid_header else False)
    if not by_frontier:
        return ["no rows to cap"]
    lines = ["| Size | Construction cap (turns) | Construction stop | Bytes cap (mm) | "
             "Bytes cap (turns) | Seconds cap (mm) |", "|---|---|---|---|---|---|"]
    for size, cap in by_frontier.items():
        seconds = by_grid.get(size)  # absent when the grid was not recorded or not read
        construction = (_NOT_ESTABLISHED if cap.construction_turns is None
                        else f"{cap.construction_turns:g}")
        seconds_cell = ("no grid record" if seconds is None
                        else _cap_cell(seconds.seconds_cap_length,
                                       established=seconds.seconds_established))
        lines.append(f"| {size} | {construction} | {cap.stop_reason} | "
                     f"{_cap_cell(cap.bytes_cap_length)} | {_cap_cell(cap.bytes_cap_turns)} | "
                     f"{seconds_cell} |")
    front_id = front_header["run_id"] if front_header else "none"
    grid_id = grid_header["run_id"] if grid_header else "none"
    lines.append("")
    lines.append(f"- construction cap from run `{front_id}`; "
                 f"bytes and seconds caps from run `{grid_id}`")
    for size in by_frontier:
        first = _first_over(grid, size, bytes_over)
        if first is not None:
            lines.append(f"- {size}: first row over the bytes budget: {first}")
        # A row over the clock is a timing claim: only a decisive grid may name it (R4).
        if grid_header is not None and not grid_header["decisive"]:
            lines.append(f"- {size}: first row over the seconds budget: {SECONDS_NOT_ESTABLISHED}")
        elif (first := _first_over(grid, size, seconds_over)) is not None:
            lines.append(f"- {size}: first row over the seconds budget: {first}")
    return lines


def _combined_bar(parts: list[tuple[str, tuple[str, ...]]]) -> tuple[str, tuple[str, ...]]:
    """The pass bar over several runs' rows: failed outranks not established outranks held, and
    every offending row of that status is named."""
    for status in ("failed", _NOT_ESTABLISHED):
        named = tuple(reason for part, reasons in parts if part == status for reason in reasons)
        if named:
            return status, named
    return "held", ()


def verdict_campaign(prefix: str, *, results_dir: Path = RESULTS_DIR) -> int:
    """Judge a recorded rod campaign: read every `<prefix>-*.jsonl`, recompute every row's class
    from its raw record (a stored class is never trusted: the file could be edited, T-02-09),
    and print K and the rule's table, the estimator and T_gate, the pass bar with every
    offending row, the escape clause, and the turn cap per size with where each came from.

    Exit 0 only when the pass bar held, no escape fired, all four rod blocks, the pair run and
    the container run were read, and the volume estimator and its T_gate were established;
    otherwise 1, "not established" and a missing block included: a partial campaign never reads
    as a pass (D-15, D-20). A block is read only when its record is complete against the
    pre-registered row set (`block_gaps`, `pair_gaps`) and was recorded at the K that `select_k`
    takes from the sweep's own record; any other is reported by block, with why, and not judged.
    2 for a prefix or a record it cannot read; a header that names no K is readable and is an
    unread block (exit 1), the pair run's included.
    The container rows count toward the pass bar and the escape clause beside the host grid's,
    pre-registered because production runs in that image (D-05), and are never decisive. The
    controls, trim and rss runs are evidence printed beside the verdict and never inputs to its
    outcome (pass bar, escape, caps, K, estimator), but they are read only at the locked K like
    every other run, so an evidence run at another K withholds the pass.
    Plan 02-05 extends it with the pair section."""
    if not RUN_ID.fullmatch(prefix):
        print(f"refused: prefix {prefix!r} must fullmatch [a-z0-9][a-z0-9-]{{0,63}}",
              file=sys.stderr)
        return 2
    try:
        runs, pair = _read_runs(prefix, results_dir)
        if not runs and pair is None:
            print(f"no runs recorded under prefix {prefix!r} in {results_dir}", file=sys.stderr)
            return 1
        # A block is read only when its record is the pre-registered row set (the Method), at the
        # K the sweep selected: a partial one, such as the JSONL of a run that crashed, or one at
        # another K, is reported and not judged.
        unread = _unread_blocks(runs, pair)
        for block in unread:
            unread[block] += _recorded_non_ok(block, runs, pair)
            runs.pop(block, None)
        if "pair" in unread:
            pair = None
        present = {*runs, *(("pair",) if pair is not None else ())}
        missing = [block for block in PASS_BLOCKS if block not in present and block not in unread]

        def absent(block: str) -> str:
            return f"{block} run not read" if block in unread else f"no {block} run"

        grid_header, grid = _run_of(runs, "grid")
        container_header, container = _run_of(runs, "container")
        grid_bar = (pass_bar(grid, grid_header["decisive"]) if grid_header is not None
                    else (_NOT_ESTABLISHED, (absent("grid"),)))
        # Emulated timings are never decisive, whatever a stored header says (D-05).
        container_bar = (pass_bar(container, False) if container_header is not None
                         else (_NOT_ESTABLISHED, (absent("container"),)))
        bar, offenders = _combined_bar([
            grid_bar, (container_bar[0], tuple(f"container {r}" for r in container_bar[1]))])
        pair_header, pair_cells = pair if pair is not None else (None, [])
        # The pair header's K is the sweep's whenever the sweep was read (`_unread_blocks`).
        locked_k = None if pair_header is None else pair_header["k"]
        # Judged for the sizes the campaign covered: the grid's, or all of them when it has none.
        covered = [s for s in SIZES if any(r["size"] == s for r in grid)] or list(SIZES)
        pair_escape = (() if locked_k is None
                       else pair_escapes(pair_cells, locked_k, covered))
        # D-07 / the protocol's escape clause: a sweep in which no K qualified leaves the
        # construction without a segment length the rule can defend, so it is an escape and
        # never a clean pass at the research's K = 5 (`run` still uses 5 to keep the data).
        no_k = (("K: no K qualified under the rule (every candidate has a non-ok row)",)
                if "ksweep" in runs and select_k(runs["ksweep"][1]) is None else ())
        escaped = (*escape_rows(grid), *(f"container {r}" for r in escape_rows(container)),
                   *pair_escape, *no_k)
        not_read = [block for block in _ESCAPE_SOURCES if block in unread]
        not_recorded = [block for block in _ESCAPE_SOURCES if block in missing]
        unjudged = "; ".join([*(["blocks not read: " + ", ".join(not_read)] if not_read else []),
                              *(["blocks missing: " + ", ".join(not_recorded)]
                                if not_recorded else [])])
        escape = ("FIRED" if escaped else f"{_NOT_ESTABLISHED} ({unjudged})" if unjudged
                  else "not fired")
        headers = {**{block: head for block, (head, _) in runs.items()},
                   **({"pair": pair_header} if pair_header is not None else {})}
        lines = [f"## Thread spike verdict: campaign {prefix}", ""]
        lines.append("- Blocks read: " + ", ".join(
            f"{block} (run `{headers[block]['run_id']}`, "
            f"{'decisive' if headers[block]['decisive'] else 'non-decisive'})"
            for block in dict.fromkeys((*PASS_BLOCKS, *SECTIONS)) if block in headers))
        if missing:
            lines.append("- Blocks missing: " + ", ".join(missing))
        if unread:
            lines.append("- Blocks not read: " + ", ".join(unread))
            lines += [f"  - {block}: {gap}" for block, gaps in unread.items() for gap in gaps]
        estimator_line, estimator_established = _estimator_line(
            grid, grid_header is not None and grid_header["decisive"])
        unchecked, meshes = skipped_checks([*grid, *container])
        lines += ["", "### K", "", *_k_section(runs), "", "### Volume estimator", "",
                  estimator_line, "", "### Pass bar", "", f"pass bar: {bar}",
                  *(f"- {reason}" for reason in offenders),
                  f"- mesh checks skipped: {unchecked} of {meshes} meshes unchecked (a skipped "
                  "check is not a pass for its mesh)", "", "### Escape clause", "",
                  f"escape clause: {escape}",
                  *(f"- {reason}" for reason in escaped), "", "### Turn caps", "",
                  *_caps_section(runs), ""]
        for block, (title, build) in SECTIONS.items():
            lines += [title, "", *build(_run_of(runs, block)[1]), ""]
        lines += ["### Pair check (D-11 to D-14)", "",
                  *(["pair: not read" if "pair" in unread else "pair: not recorded"]
                    if locked_k is None
                    else pair_section(pair_cells, locked_k)), ""]
    except ValueError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    clean = (bar == "held" and not escaped and not missing and not unread
             and estimator_established)
    lines.append("**Verdict:** " + ("pass bar held, no escape fired" if clean
                                    else "not a pass: see the sections above"))
    print("\n".join(lines))
    return 0 if clean else 1


# The campaign's blocks in protocol order. K first: D-07 locks it before the grid reads it. `rss`
# after `frontier`: it measures the frontier's terminal rows. `container` last: it validates the
# construction the other blocks locked. `pair` reads the locked K too.
CAMPAIGN_BLOCKS = ("ksweep", "grid", "frontier", "ladder", "trim", "controls", "rss", "pair", "container")  # noqa: E501
# PREFIX-container is ten characters longer than PREFIX, and a run id is at most 64.
MAX_PREFIX = 50
# What a block reads from an earlier one: K from the K sweep, and the rss block's terminal rows
# from the frontier walk. A block whose input did not complete is skipped, because a K selected
# from half a sweep is not the sweep's K.
_NEEDS: dict[str, tuple[str, ...]] = {
    **{block: ("ksweep",) for block in CAMPAIGN_BLOCKS if block != "ksweep"},
    "rss": ("ksweep", "frontier"),
}


def _campaign_block(block: str, prefix: str, results_dir: Path,
                    env: Mapping[str, str] | None) -> tuple[bool, str]:
    """One block exactly as `run` would run it, as run id PREFIX-<block> with its own guard,
    gate, header and end reading. (Completed, the line for the campaign log.) A refusal to start
    (exit 2, nothing written) and a crash mid-way (the partial JSONL is kept, never re-run) are
    both logged and neither stops the campaign."""
    run_id = f"{prefix}-{block}"
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(stderr):
            code = run_block(block, run_id, None if block == "ksweep" else f"{prefix}-ksweep",
                             results_dir=results_dir, env=env,
                             frontier_from=f"{prefix}-frontier" if block == "rss" else None)
    except Exception as exc:  # a crashed block is one logged block, not a lost campaign
        return False, (f"- {block}: interrupted ({type(exc).__name__}: {exc}); its partial "
                       f"record `{run_id}.jsonl` is kept and is never re-run")
    reason = stderr.getvalue().strip()
    if code == 0:
        if reason:
            print(reason, file=sys.stderr)
        return True, f"- {block}: ran as `{run_id}`"
    return False, f"- {block}: refused to start (exit {code}): {reason or 'no reason given'}"


def run_campaign(prefix: str, *, results_dir: Path = RESULTS_DIR,
                 env: Mapping[str, str] | None = None) -> int:
    """The whole spike as one guarded command (D-15): every block of `CAMPAIGN_BLOCKS` in that
    order as run id PREFIX-<block>, K read from PREFIX-ksweep by `select_k` and never typed, then
    `verdict --campaign PREFIX`, whose output and the line "campaign finished" are printed and
    appended to PREFIX-campaign.md; the exit code is the verdict's.

    Refusals, all exit 2 with nothing written: a PREFIX that is not a run id or is longer than 50
    characters; any PREFIX-<block>.jsonl or PREFIX-campaign.md already there (a campaign never
    overwrites or resumes); the protocol guard, asked once up front (and again by every block).
    """
    problem = None
    log_path = results_dir / f"{prefix}-campaign.md"
    if not RUN_ID.fullmatch(prefix) or len(prefix) > MAX_PREFIX:
        problem = (f"prefix {prefix!r} must fullmatch [a-z0-9][a-z0-9-]{{0,63}} and be at most "
                   f"{MAX_PREFIX} characters, so PREFIX-container is a run id")
    else:
        taken = [f"{prefix}-{b}.jsonl" for b in CAMPAIGN_BLOCKS
                 if (results_dir / f"{prefix}-{b}.jsonl").exists()]
        if taken or log_path.exists():
            problem = (f"{', '.join(taken) or log_path.name} already recorded; a campaign never "
                       "overwrites or resumes a run")
    if problem is not None:
        print(f"refused: {problem}", file=sys.stderr)
        return 2
    facts = read_guard(fetch=True)
    if not facts.result.held:
        print("protocol guard: refused -- " + "; ".join(facts.result.reasons), file=sys.stderr)
        return 2
    results_dir.mkdir(parents=True, exist_ok=True)
    with log_path.open("x", encoding="utf-8") as log:
        def note(text: str) -> None:
            print(text)
            log.write(text + "\n")
            log.flush()

        note(f"## Thread spike campaign {prefix}")
        note("")
        completed: set[str] = set()
        for block in CAMPAIGN_BLOCKS:
            waiting = [b for b in _NEEDS.get(block, ()) if b not in completed]
            if waiting:
                note(f"- {block}: skipped, needs {', '.join(f'{prefix}-{b}' for b in waiting)}, "
                     "which did not complete")
                continue
            done, line = _campaign_block(block, prefix, results_dir, env)
            if done:
                completed.add(block)
            note(line)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = verdict_campaign(prefix, results_dir=results_dir)
        note("")
        if err.getvalue().strip():
            note(f"verdict: {err.getvalue().strip()}")
        if out.getvalue().strip():
            note(out.getvalue().rstrip("\n"))
        note("")
        note("campaign finished")
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bench.thread_spike",
        description="The thread spike (Phase 2): a pre-registered measurement campaign.")
    commands = parser.add_subparsers(dest="command", required=True)
    smoke_parser = commands.add_parser(
        "smoke", help="build one M6 right-hand 5-turn rod end to end; not a campaign run")
    smoke_modes = smoke_parser.add_mutually_exclusive_group()
    smoke_modes.add_argument(
        "--block", choices=tuple(BLOCKS),
        help="run this block's code on a small subset instead; records nothing")
    smoke_modes.add_argument(
        "--pair", action="store_true",
        help="one M6 right-hand pair cell at c = 0.10, K = 5: six readings and the cell verdict")
    commands.add_parser(
        "check-protocol", help="exit 2 unless the protocol is on origin/main (the run guard)")
    verdict_parser = commands.add_parser(
        "verdict", help="judge the recorded runs under a prefix; exit 0 only on a clean pass")
    verdict_parser.add_argument("--campaign", required=True, metavar="PREFIX",
                                help="read every bench/results/thread-spike/PREFIX-*.jsonl")
    run_parser = commands.add_parser(
        "run", help="one guarded campaign block, streamed to bench/results/thread-spike/")
    run_parser.add_argument("block", choices=tuple(BLOCKS))
    run_parser.add_argument("--run-id", required=True,
                            help="[a-z0-9][a-z0-9-]{0,63}; an id already recorded is refused")
    run_parser.add_argument("--k-from", default=None,
                            help="the ksweep run id whose record select_k reads; required by "
                                 "every block but ksweep")
    run_parser.add_argument("--frontier-from", default=None,
                            help="the frontier run id whose terminal rows the rss block "
                                 "measures; required by the rss block, refused by every other")
    campaign_parser = commands.add_parser(
        "campaign", help="every block in protocol order, then the verdict; exit 1 unless clean")
    campaign_parser.add_argument(
        "--run-id", required=True, metavar="PREFIX",
        help=f"at most {MAX_PREFIX} characters; the blocks are recorded as PREFIX-<block>")
    args = parser.parse_args(argv)
    if args.command == "check-protocol":
        return check_protocol()
    if args.command == "verdict":
        return verdict_campaign(args.campaign)
    if args.command == "campaign":
        return run_campaign(args.run_id)
    if args.command == "run":
        return run_block(args.block, args.run_id, args.k_from,
                         frontier_from=args.frontier_from)
    if args.pair:
        return smoke_pair()
    return smoke() if args.block is None else smoke_block(args.block)


if __name__ == "__main__":
    sys.exit(main())
