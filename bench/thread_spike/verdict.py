"""Wire shapes and the pure predicates that judge a spike row (kernel-free).

The row's verdict is decided here, in the parent, never in the kernel child: a child that has
just built a wrong solid is the last place to trust with saying so. Everything is plain data in,
plain data out, so `tests/test_bench.py` pins every rule without a kernel and without a clock.

Nothing here prints a plausible number where none was measured (L02): a failed, timed-out or
dead row carries `None` in every measurement field, the default `Volume()` is a reference
column and never an input to a verdict, and a mesh that was not checked is never a pass.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from typing import Literal, NoReturn, TypedDict

from bench.thread_spike.maths import (
    CONTROL_OFFSET_PITCHES,
    DIAGNOSTIC_CLEARANCES,
    FRONTIER_MAX_TURNS,
    K_CANDIDATES,
    MATCHED_POSES,
    PAIR_CLEARANCES,
    PITCH,
    closed_volume,
    frontier_turns,
    interference_area,
    lengths,
    section_area,
    standard_max,
    turns_of,
)

# Relative tolerance of the precise volume against the closed form. The research maximum was
# 7.6e-6 over 576 sewn rows (R10) and the naive construction's defect is about 0.76, so 1e-4
# neither flaps nor hides a 1e-3 defect. Fixed before any data (D-09); never tuned toward a pass.
T_PASS = 1e-4

# Four times the 30 s INTERIM build-plus-mesh budget, so an over-budget row is measured rather
# than killed (RESEARCH Pattern 3). A protocol input.
ROW_TIMEOUT_S = 120.0
# The L19 gzip table compresses one fine STL 5 + 30 times at each of three levels, level 9
# included, and the largest fine STL is 164 MB (RESEARCH Pitfall 6): minutes, not seconds, so a
# row that asks for the table gets this deadline instead. A protocol input, like the row one.
GZIP_TABLE_TIMEOUT_S = 900.0

# The pure-Python STL check costs about 3 us per triangle (1.3 s for 605 450, 9.4 s for 3 203
# 406) and gigabytes of objects above this many triangles (in-process peak 2.98 GB after a 3.2 M
# triangle mesh and its check against 2.26 GB for the mesh alone, RESEARCH Pitfalls 5 and 6), so
# a mesh above it is not checked, and the report counts every skipped check.
FINE_CHECK_CEILING = 1_000_000

# The INTERIM budgets of Phase 1 D-01 (SCREW_BUILD_TIMEOUT 30 s and SCREW_EXPORT_CACHE_MB 64):
# a row is over budget past either, and over budget caps a size, it is never an escape (D-10).
# Phase 7 re-measures both. Seconds compare as floats, bytes as integers.
BUDGET_S = 30.0
BUDGET_BYTES = 64 * 1024 * 1024
# The shipped gate is derived from data by a rule fixed before any data: GATE_FACTOR times the
# chosen estimator's largest error, rounded up to one significant figure. The two estimators
# tie when the larger error is within ESTIMATOR_TIE times the smaller, and the cheaper wins
# (RESEARCH Protocol Inputs, D-20). Nobody tunes either number toward a pass.
GATE_FACTOR = 10
ESTIMATOR_TIE = 2.0

RowClass = Literal["ok", "silent_wrong", "failure", "timeout", "worker_died"]
Outcome = Literal["built", "failure", "timeout", "worker_died"]
Preset = tuple[str, float, float]
# One level of L19's gzip table: (level, output bytes, single-threaded median ms, 10-concurrent
# wall median ms). A tuple like `Preset`, so a record equals its parse.
GzipEntry = tuple[int, int, float, float]


class RowRequest(TypedDict):
    """One row to build: the wire shape of a request line. `presets` are
    (name, linear deflection mm, angular deflection rad)."""

    kind: str
    size: str
    d: float
    pitch: float
    turns: float
    length: float
    left_hand: bool
    k: int
    clearance: float
    presets: list[Preset]
    step: bool
    gzip_on: list[str]
    check_ceiling: int
    want_gzip_table: bool


class MeshRecord(TypedDict):
    """One mesh of a row. The five check fields are `None` when the check was not run
    (`checked` False): a skipped check is counted visibly, never reported as a pass. The two
    gzip fields are `None` unless the request named this preset in `gzip_on`."""

    preset: str
    tolerance: float
    angular: float
    triangles: int
    bytes: int
    mesh_s: float
    gzip1_bytes: int | None
    gzip1_s: float | None
    checked: bool
    check_s: float | None
    watertight: bool | None
    open_edges: int | None
    stl_volume: float | None
    surface_area: float | None


class RowRecord(RowRequest):
    """The request echoed plus what happened. Every measurement is `None` unless `outcome` is
    "built"; `error` is set exactly when it is not. The STEP fields are set exactly when the
    request asked for STEP and the row was built. `trim_s` is the seconds the tip trim took,
    set exactly on a built `trim` row (D-08). The last three exist only from a fresh `--once`
    child: `peak_rss_bytes` is that child's peak after its one mesh and gzip and before any STL
    check (a persistent worker's high-water mark is never a row's memory), and `gzip_table` and
    `gzip_selected` are L19's table on the row's STL and the level its rule picks, set exactly
    when the request asked for them."""

    outcome: Outcome
    error: str | None
    solids: int | None
    is_valid: bool | None
    precise_volume: float | None
    default_volume: float | None
    build_s: float | None
    volume_s: float | None
    meshes: list[MeshRecord] | None
    step_bytes: int | None
    step_s: float | None
    trim_s: float | None
    peak_rss_bytes: int | None
    gzip_table: list[GzipEntry] | None
    gzip_selected: int | None


_REQUEST_KEYS = ("kind", "size", "d", "pitch", "turns", "length", "left_hand", "k",
                 "clearance", "presets", "step", "gzip_on", "check_ceiling", "want_gzip_table")
_MEASURE_KEYS = ("solids", "is_valid", "precise_volume", "default_volume", "build_s",
                 "volume_s", "meshes")
_RECORD_KEYS = (*_REQUEST_KEYS, "outcome", "error", *_MEASURE_KEYS, "step_bytes", "step_s",
                "trim_s", "peak_rss_bytes", "gzip_table", "gzip_selected")
_MESH_KEYS = ("preset", "tolerance", "angular", "triangles", "bytes", "mesh_s", "gzip1_bytes",
              "gzip1_s", "checked", "check_s", "watertight", "open_edges", "stl_volume",
              "surface_area")
# What a campaign JSONL row carries beyond the record: the run's own verdict on it, kept for a
# reader's convenience and never trusted by `verdict`, which recomputes every one of them.
_RESULT_KEYS = ("closed_volume", "rel_err", "class", "reasons", "over_budget")


def _refuse(message: str) -> NoReturn:
    """Every refusal at this boundary is one exception type, a ValueError naming the key."""
    raise ValueError(message)


def _load_object(line: str, what: str) -> dict[str, object]:
    try:
        value: object = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{what} is not JSON: {exc}") from exc
    if not isinstance(value, dict):
        _refuse(f"{what} is not a JSON object")
    return value


def _exact_keys(obj: dict[str, object], expected: tuple[str, ...], what: str) -> None:
    for key in obj:
        if key not in expected:
            raise ValueError(f"{what} has an unknown key {key!r}")
    for key in expected:
        if key not in obj:
            raise ValueError(f"{what} is missing the key {key!r}")


def _str(obj: dict[str, object], key: str) -> str:
    value = obj[key]
    if not isinstance(value, str):
        _refuse(f"{key!r} must be a string, got {value!r}")
    return value


def _num(obj: dict[str, object], key: str) -> float:
    value = obj[key]
    # `json.loads` accepts NaN and Infinity; a NaN volume would compare as "not outside the
    # tolerance" and read as a pass, so a non-finite number is refused at the boundary (L02).
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        _refuse(f"{key!r} must be a finite number, got {value!r}")
    return float(value)


def _int(obj: dict[str, object], key: str) -> int:
    value = obj[key]
    if isinstance(value, bool) or not isinstance(value, int):
        _refuse(f"{key!r} must be an integer, got {value!r}")
    return value


def _bool(obj: dict[str, object], key: str) -> bool:
    value = obj[key]
    if not isinstance(value, bool):
        _refuse(f"{key!r} must be true or false, got {value!r}")
    return value


def _outcome(obj: dict[str, object]) -> Outcome:
    value = _str(obj, "outcome")
    if value == "built":
        return "built"
    if value == "failure":
        return "failure"
    if value == "timeout":
        return "timeout"
    if value == "worker_died":
        return "worker_died"
    raise ValueError(f"'outcome' must be built, failure, timeout or worker_died, got {value!r}")


def _optional[T](get: Callable[[dict[str, object], str], T], obj: dict[str, object],
                 key: str) -> T | None:
    return None if obj[key] is None else get(obj, key)


def _presets(obj: dict[str, object]) -> list[Preset]:
    value = obj["presets"]
    if not isinstance(value, list):
        _refuse(f"'presets' must be a list, got {value!r}")
    presets: list[Preset] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 3:
            raise ValueError(f"'presets' items are [name, tolerance, angular], got {item!r}")
        entry: dict[str, object] = dict(zip(("name", "tolerance", "angular"), item, strict=True))
        presets.append((_str(entry, "name"), _num(entry, "tolerance"), _num(entry, "angular")))
    return presets


def _strings(obj: dict[str, object], key: str) -> list[str]:
    value = obj[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        _refuse(f"{key!r} must be a list of strings, got {value!r}")
    return [item for item in value if isinstance(item, str)]


def _gzip_table(obj: dict[str, object]) -> list[GzipEntry] | None:
    value = obj["gzip_table"]
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        _refuse(f"'gzip_table' must be a non-empty list or null, got {value!r}")
    table: list[GzipEntry] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 4:
            raise ValueError("'gzip_table' items are [level, out_bytes, single_ms, "
                             f"concurrent_ms], got {item!r}")
        entry: dict[str, object] = dict(zip(
            ("level", "out_bytes", "single_ms", "concurrent_ms"), item, strict=True))
        table.append((_int(entry, "level"), _int(entry, "out_bytes"),
                      _num(entry, "single_ms"), _num(entry, "concurrent_ms")))
    return table


def _request_fields(obj: dict[str, object]) -> RowRequest:
    return {
        "kind": _str(obj, "kind"),
        "size": _str(obj, "size"),
        "d": _num(obj, "d"),
        "pitch": _num(obj, "pitch"),
        "turns": _num(obj, "turns"),
        "length": _num(obj, "length"),
        "left_hand": _bool(obj, "left_hand"),
        "k": _int(obj, "k"),
        "clearance": _num(obj, "clearance"),
        "presets": _presets(obj),
        "step": _bool(obj, "step"),
        "gzip_on": _strings(obj, "gzip_on"),
        "check_ceiling": _int(obj, "check_ceiling"),
        "want_gzip_table": _bool(obj, "want_gzip_table"),
    }


def parse_request(line: str) -> RowRequest:
    """A request line as a `RowRequest`. JSON only (never pickle or eval); the key set must be
    exactly the expected one, and a refusal names the offending key."""
    obj = _load_object(line, "request")
    _exact_keys(obj, _REQUEST_KEYS, "request")
    return _request_fields(obj)


def _mesh(item: object) -> MeshRecord:
    if not isinstance(item, dict):
        _refuse(f"'meshes' items must be objects, got {item!r}")
    _exact_keys(item, _MESH_KEYS, "mesh")
    checked = _bool(item, "checked")
    check_s = _optional(_num, item, "check_s")
    watertight = _optional(_bool, item, "watertight")
    open_edges = _optional(_int, item, "open_edges")
    stl_volume = _optional(_num, item, "stl_volume")
    surface_area = _optional(_num, item, "surface_area")
    present = (check_s is not None, watertight is not None, open_edges is not None,
               stl_volume is not None, surface_area is not None)
    if checked != all(present) or (not checked and any(present)):
        raise ValueError("mesh: the check fields are set exactly when 'checked' is true")
    gzip1_bytes = _optional(_int, item, "gzip1_bytes")
    gzip1_s = _optional(_num, item, "gzip1_s")
    if (gzip1_bytes is None) != (gzip1_s is None):
        raise ValueError("mesh: 'gzip1_bytes' and 'gzip1_s' are set together or not at all")
    return {
        "preset": _str(item, "preset"),
        "tolerance": _num(item, "tolerance"),
        "angular": _num(item, "angular"),
        "triangles": _int(item, "triangles"),
        "bytes": _int(item, "bytes"),
        "mesh_s": _num(item, "mesh_s"),
        "gzip1_bytes": gzip1_bytes,
        "gzip1_s": gzip1_s,
        "checked": checked,
        "check_s": check_s,
        "watertight": watertight,
        "open_edges": open_edges,
        "stl_volume": stl_volume,
        "surface_area": surface_area,
    }


def parse_record(line: str) -> RowRecord:
    """A record line as a `RowRecord`, with the same refusals as `parse_request` plus: a built
    row carries every measurement and no error, and any other outcome carries none and an
    error saying why."""
    obj = _load_object(line, "record")
    _exact_keys(obj, _RECORD_KEYS, "record")
    return _record_from(obj)


def parse_result_row(line: str) -> RowRecord:
    """A campaign JSONL row line as the `RowRecord` inside it: the run's own verdict keys must
    be present, are dropped, and nothing else is trusted from them."""
    obj = _load_object(line, "result row")
    _exact_keys(obj, (*_RECORD_KEYS, *_RESULT_KEYS), "result row")
    return _record_from({key: value for key, value in obj.items() if key not in _RESULT_KEYS})


def _record_from(obj: dict[str, object]) -> RowRecord:
    outcome = _outcome(obj)
    error = _optional(_str, obj, "error")
    solids = _optional(_int, obj, "solids")
    is_valid = _optional(_bool, obj, "is_valid")
    precise = _optional(_num, obj, "precise_volume")
    default = _optional(_num, obj, "default_volume")
    build_s = _optional(_num, obj, "build_s")
    volume_s = _optional(_num, obj, "volume_s")
    raw_meshes = obj["meshes"]
    if raw_meshes is not None and not isinstance(raw_meshes, list):
        _refuse(f"'meshes' must be a list or null, got {raw_meshes!r}")
    meshes = None if raw_meshes is None else [_mesh(item) for item in raw_meshes]
    step_bytes = _optional(_int, obj, "step_bytes")
    step_s = _optional(_num, obj, "step_s")
    trim_s = _optional(_num, obj, "trim_s")
    peak_rss = _optional(_int, obj, "peak_rss_bytes")
    gzip_table = _gzip_table(obj)
    gzip_selected = _optional(_int, obj, "gzip_selected")
    request = _request_fields(obj)
    measured = (solids, is_valid, precise, default, build_s, volume_s, meshes)
    if outcome == "built":
        for key, value in zip(_MEASURE_KEYS, measured, strict=True):
            if value is None:
                raise ValueError(f"a built record must carry {key!r}")
        if error is not None:
            raise ValueError("a built record must not carry an 'error'")
        if (step_bytes is None) != (step_s is None) or request["step"] != (step_bytes is not None):
            raise ValueError("a built record carries 'step_bytes' and 'step_s' exactly when "
                             "its request asked for STEP")
        if (trim_s is not None) != (request["kind"] == "trim"):
            raise ValueError("a built record carries 'trim_s' exactly when its kind is 'trim'")
        if peak_rss is not None and request["kind"] != "rod":
            raise ValueError("only a rod row carries 'peak_rss_bytes'")
        if (gzip_table is None) != (gzip_selected is None):
            raise ValueError("'gzip_table' and 'gzip_selected' are set together or not at all")
        if (gzip_table is not None) != request["want_gzip_table"]:
            raise ValueError("a built record carries 'gzip_table' exactly when its request "
                             "asked for one")
    else:
        for key, value in zip(_MEASURE_KEYS, measured, strict=True):
            if value is not None:
                raise ValueError(f"a {outcome} record must not carry {key!r}")
        if not error:
            raise ValueError(f"a {outcome} record must carry an 'error'")
        if step_bytes is not None or step_s is not None:
            raise ValueError(f"a {outcome} record must not carry a STEP measurement")
        if trim_s is not None:
            raise ValueError(f"a {outcome} record must not carry 'trim_s'")
        if peak_rss is not None or gzip_table is not None or gzip_selected is not None:
            raise ValueError(f"a {outcome} record must not carry a memory or gzip measurement")
    return {
        **request,
        "outcome": outcome,
        "error": error,
        "solids": solids,
        "is_valid": is_valid,
        "precise_volume": precise,
        "default_volume": default,
        "build_s": build_s,
        "volume_s": volume_s,
        "meshes": meshes,
        "step_bytes": step_bytes,
        "step_s": step_s,
        "trim_s": trim_s,
        "peak_rss_bytes": peak_rss,
        "gzip_table": gzip_table,
        "gzip_selected": gzip_selected,
    }


def failed_record(request: RowRequest, outcome: Outcome, error: str) -> RowRecord:
    """The request echoed with an outcome that is not a measurement, and `None` everywhere a
    number would be: a failure is never printed as a zero (L02)."""
    return {
        **request,
        "outcome": outcome,
        "error": error,
        "solids": None,
        "is_valid": None,
        "precise_volume": None,
        "default_volume": None,
        "build_s": None,
        "volume_s": None,
        "meshes": None,
        "step_bytes": None,
        "step_s": None,
        "trim_s": None,
        "peak_rss_bytes": None,
        "gzip_table": None,
        "gzip_selected": None,
    }


class HeaderRecord(TypedDict):
    """The first JSONL line of a campaign run: who ran what, on which protocol, behind which
    quiet readings. `readings` are (UTC time, 1-minute load) pairs; `k` is `None` for the K
    sweep, which has none, and `k_source` says where every other run's K came from."""

    run_id: str
    block: str
    head: str
    protocol_blob: str
    protocol_commit: str
    decisive: bool
    readings: list[tuple[str, float]]
    k: int | None
    k_source: str


_HEADER_KEYS = ("run_id", "block", "head", "protocol_blob", "protocol_commit", "decisive",
                "readings", "k", "k_source")


def parse_header(line: str) -> HeaderRecord:
    """A header line as a `HeaderRecord`, with the same refusals as `parse_record`."""
    obj = _load_object(line, "header")
    _exact_keys(obj, _HEADER_KEYS, "header")
    value = obj["readings"]
    if not isinstance(value, list):
        _refuse(f"'readings' must be a list, got {value!r}")
    readings: list[tuple[str, float]] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(f"'readings' items are [utc, load1], got {item!r}")
        entry: dict[str, object] = dict(zip(("utc", "load1"), item, strict=True))
        readings.append((_str(entry, "utc"), _num(entry, "load1")))
    return {
        "run_id": _str(obj, "run_id"),
        "block": _str(obj, "block"),
        "head": _str(obj, "head"),
        "protocol_blob": _str(obj, "protocol_blob"),
        "protocol_commit": _str(obj, "protocol_commit"),
        "decisive": _bool(obj, "decisive"),
        "readings": readings,
        "k": _optional(_int, obj, "k"),
        "k_source": _str(obj, "k_source"),
    }


def relative_error(measured: float, closed: float) -> float:
    """Signed: measured / closed - 1. An inverted solid reads about -2, which sign keeps."""
    return measured / closed - 1.0


def classify_row(record: RowRecord, closed_volume: float) -> tuple[RowClass, tuple[str, ...]]:
    """The row's class and the reasons for it, against the kernel-free closed form.

    A failure, a timeout and a dead worker pass through with their error. A built row is
    `silent_wrong` when it has not exactly one solid, is not valid, misses the closed form by
    more than `T_PASS` (sign included), or has a checked mesh that is not watertight, has a
    signed volume <= 0 or misses the closed form by more than deflection x surface area (an
    inscribed mesh is a deflection-limited estimate, RESEARCH Pattern 7). No reasons: `ok`.
    """
    outcome = record["outcome"]
    if outcome != "built":
        return outcome, (record["error"] or outcome,)
    solids = record["solids"]
    is_valid = record["is_valid"]
    precise = record["precise_volume"]
    if solids is None or is_valid is None or precise is None:
        raise ValueError("a built record must carry solids, is_valid and precise_volume")
    reasons: list[str] = []
    if solids != 1:
        reasons.append(f"solids={solids}")
    if not is_valid:
        reasons.append("isValid False")
    error = relative_error(precise, closed_volume)
    if abs(error) > T_PASS:
        reasons.append(f"precise rel err {error:+.3e} outside +/-1e-4")
    for mesh in record["meshes"] or []:
        if not mesh["checked"]:
            continue
        watertight, open_edges = mesh["watertight"], mesh["open_edges"]
        stl_volume, area = mesh["stl_volume"], mesh["surface_area"]
        if watertight is None or open_edges is None or stl_volume is None or area is None:
            raise ValueError("a checked mesh must carry its check fields")
        name = mesh["preset"]
        if not watertight:
            reasons.append(f"{name}: STL not watertight ({open_edges} open edges)")
        if stl_volume <= 0:
            reasons.append(f"{name}: STL signed volume {stl_volume:+.3e} <= 0")
        elif abs(stl_volume - closed_volume) > mesh["tolerance"] * area:
            reasons.append(f"{name}: STL volume {stl_volume:.4f} misses the closed form "
                           f"{closed_volume:.4f} by more than deflection x area")
    return ("silent_wrong" if reasons else "ok"), tuple(reasons)


def classify_trim(record: RowRecord) -> tuple[RowClass, tuple[str, ...]]:
    """A tip-trim row's class on what can be judged: exactly one solid, `isValid()`, and a
    preview mesh that, when checked, is watertight with a positive signed volume. No closed form
    exists for a trimmed tip, so the volume is never compared to one (D-08): this is cost
    evidence, and the class never enters `pass_bar`."""
    outcome = record["outcome"]
    if outcome != "built":
        return outcome, (record["error"] or outcome,)
    reasons: list[str] = []
    if record["solids"] != 1:
        reasons.append(f"solids={record['solids']}")
    if not record["is_valid"]:
        reasons.append("isValid False")
    for mesh in record["meshes"] or []:
        if mesh["preset"] != "preview" or not mesh["checked"]:
            continue
        if not mesh["watertight"]:
            reasons.append(f"preview: STL not watertight ({mesh['open_edges']} open edges)")
        volume = mesh["stl_volume"]
        if volume is None or volume <= 0:
            reasons.append(f"preview: STL signed volume {volume!r} <= 0")
    return ("silent_wrong" if reasons else "ok"), tuple(reasons)


def classify_record(record: RowRecord) -> tuple[RowClass, tuple[str, ...]]:
    """The class and reasons of any row, by its kind: a trim row on `classify_trim`, every other
    row against its own closed form."""
    if record["kind"] == "trim":
        return classify_trim(record)
    return classify_row(record, closed_volume(record["d"], record["pitch"], record["length"],
                                              record["clearance"]))


PROTOCOL_PATH = ".planning/phases/02-thread-spike/02-SPIKE.md"
RESULTS_HEADING = "## Results"


def before_results(text: str) -> str | None:
    """The text up to, excluding, the first line that is exactly `## Results`; `None` when no
    line is. Split on newlines only: `splitlines` also breaks on form feeds and Unicode line
    separators, which would move the boundary of a file that carries one. A heading that merely
    starts with the words (`## Results and more`) is not the boundary."""
    offset = 0
    for line in text.split("\n"):
        if line == RESULTS_HEADING:
            return text[:offset]
        offset += len(line) + 1
    return None


@dataclass(frozen=True)
class GuardResult:
    held: bool
    reasons: tuple[str, ...]


def protocol_guard(local_text: str | None, main_text: str | None, *, fetched: bool,
                   landed_is_ancestor: bool) -> GuardResult:
    """Whether the pre-registered protocol is on `origin/main`, as a pure predicate over what
    git said (the caller reads git; this decides). Every failed check is named, not only the
    first.

    Each check exists because SC1 is a property of main's history, not of a file. The refs must
    have been fetched, or "on origin/main" is a guess. The text before `## Results` must equal
    origin/main's own blob: `make pr.land` squashes, so the PR 1 branch commits are absent from
    main and only origin/main's blob is the proof. And origin/main's commit of the protocol must
    be an ancestor of HEAD, or the branch was cut before the squash and its run would post-date
    nothing (RESEARCH Pattern 6, Pitfall 10). Text after `## Results` may differ freely: PR 2
    writes the Results and the Verdict there.
    """
    reasons: list[str] = []
    if not fetched:
        reasons.append("origin/main was not fetched, so what it holds is not known to be current")
    if local_text is None:
        reasons.append("the protocol file is missing from the working tree")
    if main_text is None:
        reasons.append("origin/main has no protocol file: the protocol PR has not landed")
    local_head = None if local_text is None else before_results(local_text)
    main_head = None if main_text is None else before_results(main_text)
    if local_text is not None and local_head is None:
        reasons.append(f"the working tree's protocol has no '{RESULTS_HEADING}' line")
    if main_text is not None and main_head is None:
        reasons.append(f"origin/main's protocol has no '{RESULTS_HEADING}' line")
    if local_head is not None and main_head is not None and local_head != main_head:
        reasons.append(f"the protocol text before '{RESULTS_HEADING}' differs from origin/main's")
    if not landed_is_ancestor:
        reasons.append("origin/main's protocol commit is not an ancestor of HEAD "
                       "(a branch cut before the squash?)")
    return GuardResult(held=not reasons, reasons=tuple(reasons))


# The rules below judge rod campaign rows. Each was written before any data existed and states
# so: a rule that could be tuned after the fact proves nothing (D-17).


def closed_of(record: RowRecord) -> float:
    """The closed form of this row's own section and length, kernel-free."""
    return closed_volume(record["d"], record["pitch"], record["length"], record["clearance"])


def row_class(record: RowRecord) -> RowClass:
    """The row's class recomputed from the raw record: a stored class is never trusted."""
    return classify_record(record)[0]


def row_label(record: RowRecord) -> str:
    hand = "left" if record["left_hand"] else "right"
    return f"{record['size']} {hand} L={record['length']:g} {record['kind']}"


def fine_mesh(record: RowRecord) -> MeshRecord | None:
    for mesh in record["meshes"] or []:
        if mesh["preset"] == "fine":
            return mesh
    return None


def request_seconds(record: RowRecord) -> float | None:
    """What one cold request costs: build plus the slower of the fine STL and the STEP export,
    the shape of `bench.build_time`'s "build + slower export", plus the tip trim on a trim row
    (D-08). `None` when any part is missing, never a partial sum (L02)."""
    fine = fine_mesh(record)
    build_s, step_s, trim_s = record["build_s"], record["step_s"], record["trim_s"]
    if fine is None or build_s is None or step_s is None:
        return None
    if record["kind"] == "trim":
        if trim_s is None:
            return None
        build_s += trim_s
    return build_s + max(fine["mesh_s"], step_s)


def cache_bytes(record: RowRecord) -> int | None:
    """Fine STL raw plus its gzip-1: the two encodings the export cache holds (D-10)."""
    fine = fine_mesh(record)
    if fine is None or fine["gzip1_bytes"] is None:
        return None
    return fine["bytes"] + fine["gzip1_bytes"]


def bytes_over(record: RowRecord) -> bool:
    """Over the 64 MiB cache budget. Integers, so exactly 64 MiB is inside and a byte more is
    over; it needs no quiet host, so it holds on any run."""
    total = cache_bytes(record)
    return total is not None and total > BUDGET_BYTES


def seconds_over(record: RowRecord) -> bool:
    """Over the 30 s budget by the clock, or killed by the row timeout (4 x the budget). Only a
    decisive run may say so (`over_budget`): a load-slowed row is not a slow construction."""
    if record["outcome"] == "timeout":
        return True
    seconds = request_seconds(record)
    return seconds is not None and seconds > BUDGET_S


SECONDS_NOT_ESTABLISHED = "seconds not established (non-decisive gate)"


def over_budget(record: RowRecord, decisive: bool) -> tuple[str, ...]:
    """Why this row is over budget (D-10), one reason per budget. Over budget caps a size; it
    is never an escape. The bytes clause holds on any run. The seconds clause is a timing claim:
    on a non-decisive gate it reads `SECONDS_NOT_ESTABLISHED` and never "over" (owner ruling R4).
    Fixed before any data."""
    reasons: list[str] = []
    total = cache_bytes(record)
    if total is not None and total > BUDGET_BYTES:
        reasons.append(f"over budget: fine raw + gzip-1 {total} bytes > {BUDGET_BYTES}")
    if seconds_over(record):
        seconds = request_seconds(record)
        if not decisive:
            reasons.append(SECONDS_NOT_ESTABLISHED)
        elif seconds is None:
            reasons.append(f"over budget: timeout, no record within {ROW_TIMEOUT_S:g} s")
        else:
            reasons.append(f"over budget: build + slower export {seconds!r} s > {BUDGET_S:g} s")
    return tuple(reasons)


def frontier_stop(rod: RowRecord, void: RowRecord, rod_class: RowClass, void_class: RowClass,
                  decisive: bool) -> str | None:
    """Why the walk up the frontier stops after this step, or `None` to take the next one
    (D-04): the rod or the void is not ok, naming which and its class; or, on a decisive gate
    only, build + fine mesh exceeded 30 s. A non-decisive run never stops on the clock, because
    a loaded host proves nothing about the construction (owner ruling R4). Written before any
    data."""
    where = f"at {rod['turns']:g} turns"
    if rod_class != "ok":
        return f"rod {rod_class} {where}"
    if void_class != "ok":
        return f"void {void_class} at {void['turns']:g} turns"
    fine, build_s = fine_mesh(rod), rod["build_s"]
    if decisive and fine is not None and build_s is not None:
        seconds = build_s + fine["mesh_s"]
        if seconds > BUDGET_S:
            return f"build + fine mesh {seconds:.2f} s > {BUDGET_S:g} s {where}"
    return None


def _at_standard_max(record: RowRecord) -> bool:
    return record["length"] == float(standard_max(PITCH[record["size"]][0]))


def _in_standard_range(record: RowRecord) -> bool:
    return record["length"] <= float(standard_max(PITCH[record["size"]][0]))


@dataclass(frozen=True)
class KScore:
    """One K's line of the K rule's table. `triangles` and `step_bytes` are summed over its
    standard-max rod rows and are `None` unless the K qualifies (rows and every one ok)."""

    k: int
    rows: int
    non_ok: int
    triangles: int | None
    step_bytes: int | None


def k_scores(rows: list[RowRecord]) -> list[KScore]:
    """Each candidate K that has rows, with its counts and, when it qualifies (every row ok: no
    failure, no silent_wrong, every precise error inside T_PASS, at the standard max and at 250
    turns, both hands), its triangle and STEP totals at the standard max. A standard-max rod row
    with no fine mesh or STEP cannot be scored and is refused."""
    scores: list[KScore] = []
    for k in K_CANDIDATES:
        mine = [r for r in rows if r["k"] == k]
        if not mine:
            continue
        non_ok = sum(1 for r in mine if row_class(r) != "ok")
        if non_ok:
            scores.append(KScore(k, len(mine), non_ok, None, None))
            continue
        top = [r for r in mine if r["kind"] == "rod" and _at_standard_max(r)]
        if not top:
            raise ValueError(f"K = {k} has no standard-max rod row to score")
        triangles = step_bytes = 0
        for r in top:
            fine, step = fine_mesh(r), r["step_bytes"]
            if fine is None or step is None:
                raise ValueError(f"{row_label(r)} at K = {k} has no fine mesh or no STEP, "
                                 "so it cannot be scored")
            triangles += fine["triangles"]
            step_bytes += step
        scores.append(KScore(k, len(mine), 0, triangles, step_bytes))
    return scores


def select_k(rows: list[RowRecord]) -> int | None:
    """The segment length K the grid is locked to (D-07), from the K sweep's rows: among the Ks
    that qualify (`k_scores`), the fewest fine triangles summed over the standard-max rod rows,
    then fewer STEP bytes, then the smaller K. `None` when none qualifies. Written before any
    data; nobody tunes it toward a pass."""
    best: tuple[int, int, int] | None = None
    for score in k_scores(rows):
        if score.triangles is None or score.step_bytes is None:
            continue
        key = (score.triangles, score.step_bytes, score.k)
        if best is None or key < best:
            best = key
    return None if best is None else best[2]


def gate_tolerance(max_abs_err: float) -> float:
    """The shipped gate's tolerance: GATE_FACTOR times the estimator's largest error on passing
    rows, rounded up to one significant figure (7.6e-6 gives 8e-5, 1e-5 gives 1e-4). Decimal
    arithmetic on the printed value so 1e-5 times 10 does not round up on float noise. Written
    before any data (D-09, D-20)."""
    if not math.isfinite(max_abs_err) or max_abs_err <= 0:
        raise ValueError(f"no gate can be derived from a max abs error of {max_abs_err!r}")
    scaled = Decimal(repr(max_abs_err)) * GATE_FACTOR
    step = Decimal(1).scaleb(scaled.adjusted())
    return float((scaled / step).to_integral_value(rounding=ROUND_CEILING) * step)


def select_estimator(rows: list[RowRecord]) -> tuple[str, float, float]:
    """The volume estimator to ship (D-20): `precise` (`BRepGProp`, eps 1e-6) or `stl` (the
    preview mesh's signed volume), compared over the ok rod rows that have a checked preview
    mesh by the largest absolute error against the closed form. When the larger error is within
    ESTIMATOR_TIE times the smaller the two tie and the cheaper by median seconds wins (then the
    smaller error); otherwise the smaller error wins. Returns the name, its largest error and
    `gate_tolerance` of it. The default `Volume()` is a reference column and not a candidate.
    Written before any data."""
    precise_errs: list[float] = []
    stl_errs: list[float] = []
    precise_s: list[float] = []
    stl_s: list[float] = []
    for r in rows:
        precise, volume_s = r["precise_volume"], r["volume_s"]
        previews = [m for m in r["meshes"] or [] if m["preset"] == "preview" and m["checked"]]
        if r["kind"] != "rod" or row_class(r) != "ok" or not previews:
            continue
        preview = previews[0]
        stl, check_s = preview["stl_volume"], preview["check_s"]
        if precise is None or volume_s is None or stl is None or check_s is None:
            raise ValueError(f"{row_label(r)} is ok and checked but carries no volume")
        closed = closed_of(r)
        precise_errs.append(abs(relative_error(precise, closed)))
        stl_errs.append(abs(relative_error(stl, closed)))
        precise_s.append(volume_s)
        stl_s.append(preview["mesh_s"] + check_s)
    if not precise_errs:
        raise ValueError("no ok rod row with a checked preview mesh to compare the estimators on")
    candidates = [("precise", max(precise_errs), statistics.median(precise_s)),
                  ("stl", max(stl_errs), statistics.median(stl_s))]
    smaller, larger = sorted(candidates, key=lambda c: c[1])
    if larger[1] <= ESTIMATOR_TIE * smaller[1]:
        name, err, _ = min(candidates, key=lambda c: (c[2], c[1]))
    else:
        name, err, _ = smaller
    return name, err, gate_tolerance(err)


def _grid_rows(rows: list[RowRecord]) -> list[RowRecord]:
    """Only a rod or a void row is a verdict input. The negative control, the one-pipe and
    ruled-surface comparison rows and the tip-trim rows are evidence beside the verdict, and the
    naive control is wrong on purpose: it must never be able to fail a bar."""
    return [r for r in rows if r["kind"] in ("rod", "void")]


def pass_bar(rows: list[RowRecord], decisive: bool,
             ) -> tuple[Literal["held", "failed", "not established"], tuple[str, ...]]:
    """The pre-registered pass bar over the allowed grid (D-09), both hands, rod and void: any
    silent_wrong, failure or worker_died row fails it, naming the row. A timeout is an
    over-budget cap on a decisive gate (D-10) and leaves the bar held; on a non-decisive gate the
    row's validity is unknown, so the bar is not established, which is not an escape either
    (owner ruling R4). A failure outranks a timeout. Written before any data."""
    failed: list[str] = []
    timed_out: list[str] = []
    for r in _grid_rows(rows):
        cls = row_class(r)
        if cls in ("silent_wrong", "failure", "worker_died"):
            failed.append(f"{row_label(r)}: {cls}")
        elif cls == "timeout":
            timed_out.append(f"{row_label(r)}: timeout")
    if failed:
        return "failed", tuple(failed)
    if timed_out and not decisive:
        return "not established", tuple(timed_out)
    return "held", ()


def skipped_checks(rows: list[RowRecord]) -> tuple[int, int]:
    """(meshes whose STL check was skipped, meshes) over the pass-bar rows (rods and voids). A
    skipped check leaves the row's class alone (`classify_row`) but is counted wherever the pass
    bar is printed, so a held bar never reads as a claim about meshes nobody checked."""
    meshes = [mesh for r in _grid_rows(rows) for mesh in r["meshes"] or []]
    return sum(1 for mesh in meshes if not mesh["checked"]), len(meshes)


@dataclass(frozen=True)
class TurnCap:
    """One size's caps (D-04, D-10), each with the reason it is what it is.

    `construction_turns`: the last ok frontier turn count before the stop, `None` when no cap can
    be claimed (no record, an incomplete walk, a timeout stop on a non-decisive gate).
    `bytes_cap_length` (mm) and `bytes_cap_turns`: the largest grid length below the first
    over-budget row, `None` when no row is over and 0.0 when even the shortest is.
    `seconds_cap_length` follows the same rule but only from a decisive run; `seconds_established`
    says whether it could be claimed at all."""

    size: str
    construction_turns: float | None
    stop_reason: str
    bytes_cap_length: float | None
    bytes_cap_turns: float | None
    seconds_cap_length: float | None
    seconds_established: bool


def _hand_cap(size: str, hand: str, rows: list[RowRecord], decisive: bool,
              ) -> tuple[float | None, str]:
    """One hand's frontier walk: step through the recorded turn counts in order and stop where
    `frontier_stop` says. Its cap is the last ok step, or the standard max when the very first
    step stopped (that length is already in the grid)."""
    d, pitch = PITCH[size]
    standard_turns = float(turns_of(standard_max(d), pitch))
    steps: dict[float, dict[str, RowRecord]] = {}
    for r in rows:
        steps.setdefault(r["turns"], {})[r["kind"]] = r
    last_ok: float | None = None
    for turns in sorted(steps):
        rod, void = steps[turns].get("rod"), steps[turns].get("void")
        if rod is None or void is None:
            raise ValueError(f"frontier step {turns:g} of {size} {hand} lacks its rod or void row")
        classes = (row_class(rod), row_class(void))
        stop = frontier_stop(rod, void, classes[0], classes[1], decisive)
        if stop is None:
            last_ok = turns
            continue
        if "timeout" in classes and not decisive:
            return None, f"{hand}: {stop}; a timeout on a non-decisive gate is not established"
        return (standard_turns if last_ok is None else last_ok), f"{hand}: {stop}"
    assert last_ok is not None  # the caller passes at least one row
    if last_ok != FRONTIER_MAX_TURNS:
        return None, f"{hand}: frontier walk incomplete, last measured {last_ok:g} turns"
    return float(FRONTIER_MAX_TURNS), f"{hand}: no stop up to {FRONTIER_MAX_TURNS} turns"


def _construction_cap(size: str, rows: list[RowRecord], decisive: bool,
                      ) -> tuple[float | None, str]:
    """The smaller of the two hands' caps, with the limiting hand's reason."""
    if not rows:
        return None, "no frontier record"
    caps: list[tuple[float, str]] = []
    for hand, left in (("right", False), ("left", True)):
        mine = [r for r in rows if r["left_hand"] == left]
        if not mine:
            return None, f"no frontier record for the {hand} hand"
        cap, reason = _hand_cap(size, hand, mine, decisive)
        if cap is None:
            return None, reason
        caps.append((cap, reason))
    return min(caps)


def _length_cap(rows: list[RowRecord], over: Callable[[RowRecord], bool]) -> float | None:
    """The largest length below the first (shortest) row `over` budget, across both hands:
    `None` when no row is over, 0.0 when no length is below the first that is."""
    over_lengths = [r["length"] for r in rows if over(r)]
    if not over_lengths:
        return None
    first = min(over_lengths)
    return max((r["length"] for r in rows if r["length"] < first), default=0.0)


def turn_caps(grid_rows: list[RowRecord], frontier_rows: list[RowRecord],
              decisive: bool) -> dict[str, TurnCap]:
    """Per size: the construction cap from the frontier walk (D-04), the bytes cap from the grid
    (always established, integers) and the seconds cap from the grid (only when `decisive`,
    D-10). The smaller of them is Phase 3's cap-and-warn input; this returns all three with
    their reasons rather than hiding which one binds. Sizes with no rows are absent: the
    caller reports them missing. Written before any data."""
    caps: dict[str, TurnCap] = {}
    for size, (_, pitch) in PITCH.items():
        grid = [r for r in grid_rows if r["size"] == size and r["kind"] == "rod"]
        frontier = [r for r in frontier_rows if r["size"] == size]
        if not grid and not frontier:
            continue
        construction, reason = _construction_cap(size, frontier, decisive)
        by_bytes = _length_cap(grid, bytes_over)
        by_seconds = _length_cap(grid, seconds_over) if decisive else None
        caps[size] = TurnCap(
            size, construction, reason, by_bytes,
            None if by_bytes is None else by_bytes / float(pitch), by_seconds, decisive)
    return caps


def escape_rows(rows: list[RowRecord]) -> tuple[str, ...]:
    """The rows that fire the escape clause (D-10): a failure, worker_died or silent_wrong row,
    rod or void, either hand, inside the standard range (length at most min(10 d, 200 mm)).
    Beyond it a failure is a frontier stop, and a timeout is a cap (`pass_bar`), not an escape.
    Written before any data."""
    reasons: list[str] = []
    for r in _grid_rows(rows):
        cls = row_class(r)
        if cls in ("silent_wrong", "failure", "worker_died") and _in_standard_range(r):
            reasons.append(f"{row_label(r)}: {cls}")
    return tuple(reasons)


def known_bad_inputs(rows: list[RowRecord]) -> list[RowRecord]:
    """The naive construction's rows that pass every check short of the volume: exactly one
    solid, `isValid()` True, and a precise volume below half the closed form. These are the
    known-bad inputs THRD-04's positive-control test needs in Phase 3 (D-06): a shape a
    validity-only gate waves through. A failure row carries no volume and is not one."""
    bad: list[RowRecord] = []
    for r in rows:
        precise = r["precise_volume"]
        if (r["kind"] == "naive" and r["outcome"] == "built" and r["solids"] == 1
                and r["is_valid"] is True and precise is not None
                and precise / closed_of(r) < 0.5):
            bad.append(r)
    return bad


# --- Completeness: a block is read only when its record is the pre-registered row set ---

RowKey = tuple[str, str, bool, int, float]  # kind, size, left hand, K, length in mm
_SHOWN = 4


def _label(key: RowKey) -> str:
    kind, size, left, k, length = key
    return f"{size} {'left' if left else 'right'} L={length:.10g} {kind} K={k}"


def _some(items: Sequence[str]) -> str:
    more = len(items) - _SHOWN
    return "; ".join(items[:_SHOWN]) + (f"; and {more} more" if more > 0 else "")


def expected_rows(block: str, k: int | None, *, sizes: Sequence[str],
                  sample_sizes: Sequence[str]) -> list[RowKey]:
    """The rows the Method table pre-registers for a block whose set is fixed in advance
    (`ksweep`, `grid`, `ladder`, `container`), as (kind, size, hand, K, length): the sizes x
    lengths x hands x kinds, one key per row. The frontier walk stops where it stops and is
    judged by `frontier_gaps`; the pair block's cells by `pair_gaps`. Nothing here is tuned: it
    is the table, written down once more so a record can be held against it."""
    keys: list[RowKey] = []
    if block == "ksweep":
        for size in sample_sizes:
            d, pitch = PITCH[size]
            for k_value in K_CANDIDATES:
                for left in (False, True):
                    for length in (standard_max(d), FRONTIER_MAX_TURNS * pitch):
                        keys += [("rod", size, left, k_value, float(length)),
                                 ("void", size, left, k_value, float(length))]
    elif block in ("grid", "container"):
        if k is None:
            raise ValueError(f"block {block} is judged at a K")
        for size in sizes:
            d, pitch = PITCH[size]
            for length in lengths(d, pitch):
                for left in (False, True):
                    keys += [("rod", size, left, k, float(length)),
                             ("void", size, left, k, float(length))]
    elif block == "ladder":
        if k is None:
            raise ValueError("block ladder is judged at a K")
        for size in sample_sizes:
            d, pitch = PITCH[size]
            keys += [("rod", size, False, k, float(length))
                     for length in (10 * pitch, standard_max(d))]
    else:
        raise ValueError(f"block {block} has no fixed row set")
    return keys


def _row_key(r: RowRecord) -> RowKey:
    return (r["kind"], r["size"], r["left_hand"], r["k"], r["length"])


def _counted_gaps(wanted: Counter[str], got: Counter[str], what: str) -> list[str]:
    """What a record lacks, adds or repeats against what was pre-registered, one line each. The
    keys are labels, which name a row or cell uniquely."""
    missing = sorted((wanted - got).elements())
    unexpected = sorted(label for label in got if label not in wanted)
    repeated = sorted(label for label in got if label in wanted and got[label] > wanted[label])
    gaps: list[str] = []
    if missing:
        gaps.append(f"{len(missing)} of {wanted.total()} pre-registered {what} missing: "
                    f"{_some(missing)}")
    if unexpected:
        gaps.append(f"{len(unexpected)} {what} not in the pre-registered set: {_some(unexpected)}")
    if repeated:
        gaps.append(f"{len(repeated)} {what} recorded more than once: {_some(repeated)}")
    return gaps


def frontier_gaps(rows: Sequence[RowRecord], k: int, decisive: bool, *,
                  sizes: Sequence[str]) -> list[str]:
    """How a frontier record falls short of the Method table: for every size and hand a walk of
    consecutive steps from the first one, a rod and a void at each exactly once and at the
    block's K, ending either at the last step (250 turns) or at a step `frontier_stop` ends, and
    with no step after a stop."""
    gaps: list[str] = []
    for size in sizes:
        d, pitch = PITCH[size]
        steps = frontier_turns(d, pitch)
        for left in (False, True):
            name = f"{size} {'left' if left else 'right'}"
            mine = [r for r in rows if r["size"] == size and r["left_hand"] == left]
            if not mine:
                gaps.append(f"{name}: no walk recorded")
                continue
            by_step: dict[float, list[RowRecord]] = {}
            for r in mine:
                by_step.setdefault(r["turns"], []).append(r)
            for turns in sorted(t for t in by_step if t not in steps):
                gaps.append(f"{name}: {turns:g} turns is not a pre-registered step")
            walked = [t for t in steps if t in by_step]
            if walked != steps[:len(walked)]:
                gaps.append(f"{name}: the steps are not consecutive from {steps[0]} turns")
            pairs = {t: {kind: [r for r in by_step[t] if r["kind"] == kind]
                         for kind in ("rod", "void")} for t in walked}
            for t, kinds in pairs.items():
                for kind, found in kinds.items():
                    if len(found) != 1:
                        gaps.append(f"{name}: step {t:g} has {len(found)} {kind} rows, not 1")
                if any(r["k"] != k for found in kinds.values() for r in found):
                    gaps.append(f"{name}: step {t:g} was not recorded at K = {k}")
            whole = [t for t in walked if all(len(f) == 1 for f in pairs[t].values())]
            for position, t in enumerate(whole):
                rod, void = pairs[t]["rod"][0], pairs[t]["void"][0]
                stop = frontier_stop(rod, void, row_class(rod), row_class(void), decisive)
                if stop is not None and position < len(whole) - 1:
                    gaps.append(f"{name}: a step follows the stop at {t:g} turns")
                elif stop is None and t == whole[-1] and t != steps[-1]:
                    gaps.append(f"{name}: the walk ends at {t:g} turns without a stop or "
                                f"reaching {steps[-1]}")
    return gaps


def block_gaps(block: str, header: HeaderRecord, rows: Sequence[RowRecord], *,
               sizes: Sequence[str], sample_sizes: Sequence[str]) -> list[str]:
    """How a recorded block falls short of its pre-registered row set, one line each; empty when
    it is complete. A block is read only when complete (the Method): a partial record, such as
    the JSONL of a run that crashed, is reported and not judged."""
    k = header["k"]
    if block != "ksweep" and k is None:
        return ["its header carries no K, so the rows it should hold cannot be named"]
    if block == "frontier":
        assert k is not None
        return frontier_gaps(rows, k, header["decisive"], sizes=sizes)
    wanted = Counter(map(_label, expected_rows(block, k, sizes=sizes, sample_sizes=sample_sizes)))
    return _counted_gaps(wanted, Counter(_label(_row_key(r)) for r in rows), "rows")


# --- Pair check (question 3, D-11 to D-14) ---

# Relative band of a control reading around the closed form: 100x the research's worst agreement
# of a non-empty reading (1e-5, RESEARCH R7), fixed before any data (D-14).
PAIR_BAND = 1e-3
# A pair reading is empty when it has 0 solids or abs(volume) <= this: the c = 0 garbage read
# -0.0000 in one solid (RESEARCH R4), which a plain `volume == 0` would call non-empty.
EMPTY_MM3 = 1e-6
# One pair cell is one request: a full M20 body took 16-121 s per boolean (STACK section C) and
# a cell is six of them, so the cell gets its own deadline.
PAIR_TIMEOUT_S = 600.0

ReadingOutcome = Literal["built", "failure"]
PairVerdict = Literal["proven", "violated", "inconclusive"]


class PairReading(TypedDict):
    """One pose's boolean. `offset_pitches` is 0 for a matched pose and `CONTROL_OFFSET_PITCHES`
    for a control. `outcome` is "failure" when the boolean raised, and then every measurement is
    `None`; the diagnostics are columns, never verdict inputs (they missed every false-empty in
    research, Pitfall 4)."""

    theta: float
    offset_pitches: float
    outcome: ReadingOutcome
    solids: int | None
    volume: float | None
    diag_errors: bool | None
    diag_warnings: bool | None
    seconds: float | None


class PairCell(TypedDict):
    """What names a pair cell: the rod of one hand against a nut of one hand at one clearance."""

    size: str
    d: float
    pitch: float
    m: float
    clearance: float
    rod_left_hand: bool
    nut_left_hand: bool
    k: int


class PairRequest(PairCell):
    """One cell to read: `poses` are (theta, offset in pitches), read in order."""

    poses: list[tuple[float, float]]


class PairRecord(PairCell):
    """The cell echoed plus what happened. A built cell has an `nut_volume` and no error; any
    other outcome has an error and no readings unless the worker itself reported them (a
    "failure" keeps the readings taken so far, the last of them the one that raised)."""

    outcome: Outcome
    error: str | None
    nut_volume: float | None
    readings: list[PairReading]


_PAIR_CELL_KEYS = ("size", "d", "pitch", "m", "clearance", "rod_left_hand", "nut_left_hand", "k")
_PAIR_REQUEST_KEYS = (*_PAIR_CELL_KEYS, "poses")
_PAIR_RECORD_KEYS = (*_PAIR_CELL_KEYS, "outcome", "error", "nut_volume", "readings")
_PAIR_READING_KEYS = ("theta", "offset_pitches", "outcome", "solids", "volume", "diag_errors",
                      "diag_warnings", "seconds")
# What a campaign JSONL pair row carries beyond the record: the run's own verdict on it, kept for a
# reader's convenience and never trusted by `verdict`, which recomputes it.
_PAIR_RESULT_KEYS = ("verdict", "reasons", "closed_control")


def _pair_cell_fields(obj: dict[str, object]) -> PairCell:
    return {
        "size": _str(obj, "size"),
        "d": _num(obj, "d"),
        "pitch": _num(obj, "pitch"),
        "m": _num(obj, "m"),
        "clearance": _num(obj, "clearance"),
        "rod_left_hand": _bool(obj, "rod_left_hand"),
        "nut_left_hand": _bool(obj, "nut_left_hand"),
        "k": _int(obj, "k"),
    }


def _offset(value: float) -> float:
    """A pose is matched (offset 0) or a control (half a pitch): nothing else is pre-registered."""
    if value not in (0.0, CONTROL_OFFSET_PITCHES):
        raise ValueError(f"'offset_pitches' must be 0 or {CONTROL_OFFSET_PITCHES}, got {value!r}")
    return value


def parse_pair_request(line: str) -> PairRequest:
    """A pair request line as a `PairRequest`: JSON only, the key set exactly the expected one,
    every pose a [theta, offset] pair at a pre-registered offset."""
    obj = _load_object(line, "pair request")
    _exact_keys(obj, _PAIR_REQUEST_KEYS, "pair request")
    raw = obj["poses"]
    if not isinstance(raw, list):
        _refuse(f"'poses' must be a list, got {raw!r}")
    poses: list[tuple[float, float]] = []
    for item in raw:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(f"'poses' items are [theta, offset_pitches], got {item!r}")
        entry: dict[str, object] = dict(zip(("theta", "offset"), item, strict=True))
        poses.append((_num(entry, "theta"), _offset(_num(entry, "offset"))))
    return {**_pair_cell_fields(obj), "poses": poses}


def _pair_reading(item: object) -> PairReading:
    if not isinstance(item, dict):
        _refuse(f"'readings' items must be objects, got {item!r}")
    _exact_keys(item, _PAIR_READING_KEYS, "pair reading")
    outcome = _str(item, "outcome")
    solids = _optional(_int, item, "solids")
    volume = _optional(_num, item, "volume")
    diag_errors = _optional(_bool, item, "diag_errors")
    diag_warnings = _optional(_bool, item, "diag_warnings")
    seconds = _optional(_num, item, "seconds")
    measured = {"solids": solids, "volume": volume, "diag_errors": diag_errors,
                "diag_warnings": diag_warnings, "seconds": seconds}
    kind: ReadingOutcome
    if outcome == "built":
        kind = "built"
        for key, value in measured.items():
            if value is None:
                raise ValueError(f"a built reading must carry {key!r}")
    elif outcome == "failure":
        kind = "failure"
        for key, value in measured.items():
            if value is not None:
                raise ValueError(f"a failure reading must not carry {key!r}")
    else:
        raise ValueError(f"a reading's 'outcome' must be built or failure, got {outcome!r}")
    return {
        "theta": _num(item, "theta"),
        "offset_pitches": _offset(_num(item, "offset_pitches")),
        "outcome": kind,
        "solids": solids,
        "volume": volume,
        "diag_errors": diag_errors,
        "diag_warnings": diag_warnings,
        "seconds": seconds,
    }


def _pair_record_from(obj: dict[str, object]) -> PairRecord:
    outcome = _outcome(obj)
    error = _optional(_str, obj, "error")
    nut_volume = _optional(_num, obj, "nut_volume")
    raw = obj["readings"]
    if not isinstance(raw, list):
        _refuse(f"'readings' must be a list, got {raw!r}")
    readings = [_pair_reading(item) for item in raw]
    if outcome == "built":
        if error is not None:
            raise ValueError("a built pair record must not carry an 'error'")
        if nut_volume is None:
            raise ValueError("a built pair record must carry its 'nut_volume'")
        if not readings or any(r["outcome"] != "built" for r in readings):
            raise ValueError("a built pair record carries readings, every one of them built")
    else:
        if not error:
            raise ValueError(f"a {outcome} pair record must carry an 'error'")
        if outcome != "failure" and (readings or nut_volume is not None):
            raise ValueError(f"a {outcome} pair record carries no readings and no nut_volume: "
                             "the worker never answered")
    return {**_pair_cell_fields(obj), "outcome": outcome, "error": error,
            "nut_volume": nut_volume, "readings": readings}


def parse_pair_record(line: str) -> PairRecord:
    """A pair record line as a `PairRecord`, with the refusals of `parse_pair_request` plus: a
    built cell carries its nut volume, built readings and no error, and a cell that timed out or
    whose worker died carries an error and nothing measured."""
    obj = _load_object(line, "pair record")
    _exact_keys(obj, _PAIR_RECORD_KEYS, "pair record")
    return _pair_record_from(obj)


def parse_pair_result_row(line: str) -> PairRecord:
    """A campaign JSONL pair row as the `PairRecord` inside it: the run's own verdict keys must be
    present, are dropped, and nothing else is trusted from them."""
    obj = _load_object(line, "pair result row")
    _exact_keys(obj, (*_PAIR_RECORD_KEYS, *_PAIR_RESULT_KEYS), "pair result row")
    return _pair_record_from({k: v for k, v in obj.items() if k not in _PAIR_RESULT_KEYS})


def failed_pair_record(request: PairRequest, outcome: Outcome, error: str) -> PairRecord:
    """The request's cell echoed with an outcome that is not a measurement: no nut volume and no
    reading, never a zero (L02)."""
    return {
        "size": request["size"], "d": request["d"], "pitch": request["pitch"], "m": request["m"],
        "clearance": request["clearance"], "rod_left_hand": request["rod_left_hand"],
        "nut_left_hand": request["nut_left_hand"], "k": request["k"],
        "outcome": outcome, "error": error, "nut_volume": None, "readings": [],
    }


def closed_control(record: PairCell) -> float:
    """The closed-form volume in mm3 of the half-pitch control: engaged length times the
    interference area at phase pi. The band's centre for every control reading (D-14)."""
    return record["m"] * interference_area(record["d"], record["pitch"], record["clearance"],
                                           math.pi)


def _closed_matched(record: PairCell) -> float:
    return record["m"] * interference_area(record["d"], record["pitch"], record["clearance"], 0.0)


def _nut_body(record: PairCell) -> float:
    """pi d^2 m - A(c) m: the plain blank less the void thread through all of it (STACK § C:
    within 1.1e-6)."""
    d = record["d"]
    return (math.pi * d * d - section_area(d, record["pitch"], record["clearance"])) * record["m"]


def _is_empty(reading: PairReading) -> bool:
    volume = reading["volume"]
    return reading["solids"] == 0 or volume is None or abs(volume) <= EMPTY_MM3


def _off_by(reading: PairReading, closed: float) -> float:
    volume = reading["volume"]
    if volume is None:
        raise ValueError("a built reading must carry its volume")
    return abs(volume / closed - 1.0)


def _matched(record: PairRecord) -> list[PairReading]:
    return [r for r in record["readings"] if r["offset_pitches"] == 0.0]


def _controls(record: PairRecord) -> list[PairReading]:
    return [r for r in record["readings"] if r["offset_pitches"] == CONTROL_OFFSET_PITCHES]


def _is_mixed(record: PairCell) -> bool:
    return record["rod_left_hand"] != record["nut_left_hand"]


def _hand(record: PairCell) -> str:
    return "left" if record["rod_left_hand"] else "right"


def _poses_ok(readings: list[PairReading]) -> bool:
    return tuple(r["theta"] for r in readings) == MATCHED_POSES


def cell_verdict(record: PairRecord) -> tuple[PairVerdict, tuple[str, ...]]:
    """The pre-registered rule for one cell, and why (D-12, D-14; owner ruling R1 left D-14
    exactly as written).

    A cell that did not finish is inconclusive. A mixed-hand cell whose poses are exactly
    `MATCHED_POSES` and nothing else is `violated` when every matched pose reads non-empty, else
    inconclusive: an empty read at a pair that cannot thread proves nothing either way, and one
    reading at a pose chosen after the fact proves nothing at all. For a same-hand cell: c <= 0
    is inconclusive by definition (D-11); poses other than the pre-registered ones are refused;
    a nut body whose precise volume misses
    pi d^2 m - A(c) m by more than `T_PASS` is not believed (not even a violation); any matched
    pose non-empty is `violated`; otherwise `proven` only when every matched pose is empty AND
    every control is non-empty within `PAIR_BAND` of the closed form. Anything else is
    inconclusive, with every reason. The diagnostic columns are never read.
    """
    outcome = record["outcome"]
    if outcome != "built":
        return "inconclusive", (f"cell {outcome}: {record['error']}",)
    matched, controls = _matched(record), _controls(record)
    if _is_mixed(record):
        if controls or not _poses_ok(matched):
            return "inconclusive", ("the poses are not the pre-registered ones: a mixed-hand "
                                    "cell is read at the matched poses and nothing else (D-12)",)
        reads = [r for r in matched if not _is_empty(r)]
        if len(reads) == len(matched):
            return "violated", (f"mixed-hand pair: all {len(matched)} matched poses non-empty",)
        return "inconclusive", (f"mixed-hand pair: {len(matched) - len(reads)} of "
                                f"{len(matched)} matched poses empty",)
    clearance = record["clearance"]
    if clearance <= 0:
        return "inconclusive", (f"c = {clearance:g} mm: inconclusive by definition (D-11)",)
    if not (_poses_ok(matched) and _poses_ok(controls)):
        return "inconclusive", ("the poses are not the pre-registered ones: no verdict is "
                                "drawn from poses chosen after the fact (D-12)",)
    nut_volume = record["nut_volume"]
    if nut_volume is None:
        raise ValueError("a built pair record must carry its nut_volume")
    body = _nut_body(record)
    if abs(nut_volume / body - 1.0) > T_PASS:
        return "inconclusive", (f"the nut body is {nut_volume:.6g} mm3, not the closed form "
                                f"{body:.6g} mm3 within {T_PASS:g}: no reading is believed",)
    reads = [r for r in matched if not _is_empty(r)]
    if reads:
        return "violated", tuple(f"matched pose theta {r['theta']:+.4f} reads {r['volume']:.6g} mm3"
                                 for r in reads)
    closed = closed_control(record)
    if closed <= EMPTY_MM3:
        return "inconclusive", (f"control cannot fire by geometry: its closed form is "
                                f"{closed:.3g} mm3, at or below {EMPTY_MM3:g}",)
    reasons: list[str] = []
    for r in controls:
        if _is_empty(r):
            reasons.append(f"control at theta {r['theta']:+.4f} reads empty "
                           f"(closed form {closed:.6g} mm3)")
        elif _off_by(r, closed) > PAIR_BAND:
            reasons.append(f"control at theta {r['theta']:+.4f} reads {r['volume']:.6g} mm3, "
                           f"{_off_by(r, closed):.2e} off the closed form {closed:.6g} mm3: "
                           f"outside the band {PAIR_BAND:g}")
    return ("inconclusive", tuple(reasons)) if reasons else ("proven", ())


def _same_hand(cells: list[PairRecord]) -> list[PairRecord]:
    return [c for c in cells if not _is_mixed(c)]


def size_falsifiable(cells: list[PairRecord]) -> bool:
    """True when some cell at a proof clearance (c >= 0.05) is proven (D-14). The cells are one
    size's, of one hand or both: the caller decides what "a size" spans."""
    return any(c["clearance"] >= min(PAIR_CLEARANCES) and cell_verdict(c)[0] == "proven"
               for c in _same_hand(cells))


def excluded_clearances(cells: list[PairRecord]) -> tuple[float, ...]:
    """The proof clearances at which some cell did not prove, ascending: the flaky (size, c)
    cells Phase 5 must leave out of its allowed clearances (D-14)."""
    return tuple(sorted({c["clearance"] for c in _same_hand(cells)
                         if c["clearance"] in PAIR_CLEARANCES and cell_verdict(c)[0] != "proven"}))


def mixed_hand_violated(cells: list[PairRecord]) -> bool:
    """True only when there is at least one mixed-hand cell and `cell_verdict` reads every one
    violated (D-14: a mixed-hand pair must read violated): it finished, it was read at exactly
    the pre-registered matched poses and every matched reading is non-empty. No cell, a cell
    that did not finish, an empty reading or a pose chosen after the fact is not a violation."""
    mixed = [c for c in cells if _is_mixed(c)]
    return bool(mixed) and all(cell_verdict(c)[0] == "violated" for c in mixed)


_SENSITIVITY = DIAGNOSTIC_CLEARANCES[1]


def sensitivity_ok(cell: PairRecord) -> bool:
    """D-11's sensitivity check: the c = -0.05 cell's matched readings are all non-empty and
    within `PAIR_BAND` of the closed form of a matched pose with interference."""
    if cell["outcome"] != "built" or cell["clearance"] != _SENSITIVITY:
        return False
    matched, closed = _matched(cell), _closed_matched(cell)
    return (_poses_ok(matched) and closed > EMPTY_MM3
            and all(not _is_empty(r) and _off_by(r, closed) <= PAIR_BAND for r in matched))


def _fires_in_band(readings: list[PairReading], closed: float) -> list[bool]:
    return [not _is_empty(r) and _off_by(r, closed) <= PAIR_BAND for r in readings]


def _key(cell: PairRecord) -> str:
    return f"{cell['size']} {_hand(cell)} c={cell['clearance']:g} K={cell['k']}"


def _two_of_three(cell: PairRecord) -> bool:
    """Matched poses all empty; at least two of three controls fire, each fired one in band."""
    closed = closed_control(cell)
    controls = _controls(cell)
    fired = [r for r in controls if not _is_empty(r)]
    return (closed > EMPTY_MM3 and all(_is_empty(r) for r in _matched(cell))
            and len(fired) >= 2 and all(_fires_in_band(fired, closed)))


def _seam_excluded(cell: PairRecord) -> bool:
    """The primary rule over the poses off the seam (theta != 0)."""
    closed = closed_control(cell)
    matched = [r for r in _matched(cell) if r["theta"] != 0.0]
    controls = [r for r in _controls(cell) if r["theta"] != 0.0]
    return (closed > EMPTY_MM3 and bool(controls) and all(_is_empty(r) for r in matched)
            and all(_fires_in_band(controls, closed)))


def _same_pose_control(cell: PairRecord, cells: list[PairRecord]) -> bool:
    """Matched poses all empty, and the same cell's c = -0.05 reading at each of those poses (the
    nut and rod of the same size, hands and K) non-empty within the band: the same-pose control."""
    twins = [c for c in cells if c["outcome"] == "built" and c["clearance"] == _SENSITIVITY
             and (c["size"], c["rod_left_hand"], c["nut_left_hand"], c["k"])
             == (cell["size"], cell["rod_left_hand"], cell["nut_left_hand"], cell["k"])]
    if not twins or not all(_is_empty(r) for r in _matched(cell)):
        return False
    closed = _closed_matched(twins[0])
    reference = _matched(twins[0])
    return (closed > EMPTY_MM3 and _poses_ok(reference)
            and all(_fires_in_band(reference, closed)))


def variant_rules(cells: list[PairRecord]) -> dict[str, dict[str, bool]]:
    """Variant pair rules computed from the same recorded readings, per same-hand proof cell, for
    Phase 5's revision: two of three controls firing in band; the seam pose (theta = 0) left out;
    the same-pose c = -0.05 reading as the control. Reported beside the verdict and never an
    input to `cell_verdict` (owner ruling R1: no one tunes a rule toward a pass)."""
    proof = [c for c in _same_hand(cells) if c["clearance"] in PAIR_CLEARANCES]
    built = [c for c in proof if c["outcome"] == "built"]
    names: dict[str, Callable[[PairRecord], bool]] = {
        "two of three controls fire in band": _two_of_three,
        "seam pose excluded": _seam_excluded,
        "same-pose c=-0.05 reading as the control": lambda c: _same_pose_control(c, cells),
    }
    return {name: {_key(c): c in built and rule(c) for c in proof} for name, rule in names.items()}


PairKey = tuple[str, bool, bool, float, int]  # size, rod hand, nut hand, clearance, K


def expected_cells(k: int, *, sizes: Sequence[str],
                   reference_sizes: Sequence[str]) -> list[PairKey]:
    """The cells the Method table pre-registers for the pair block at the locked K: per size both
    same-hand pairs at every diagnostic and proof clearance and the mixed pair at every proof
    clearance, then on the reference sizes the two other K values, right hand, proof
    clearances."""
    keys: list[PairKey] = []
    for size in sizes:
        for left in (False, True):
            keys += [(size, left, left, c, k) for c in (*DIAGNOSTIC_CLEARANCES, *PAIR_CLEARANCES)]
        keys += [(size, False, True, c, k) for c in PAIR_CLEARANCES]
    for size in reference_sizes:
        for other in (x for x in K_CANDIDATES if x != k):
            keys += [(size, False, False, c, other) for c in PAIR_CLEARANCES]
    return keys


def _cell_label(key: PairKey) -> str:
    size, rod_left, nut_left, clearance, k = key
    hands = ("left" if rod_left else "right") + ("" if rod_left == nut_left
                                                   else " rod, left nut" if nut_left
                                                   else " rod, right nut")
    return f"{size} {hands} c={clearance:g} K={k}"


def pair_gaps(header: HeaderRecord, cells: Sequence[PairRecord], *, sizes: Sequence[str],
              reference_sizes: Sequence[str]) -> list[str]:
    """How a recorded pair block falls short of its pre-registered cells, one line each; empty
    when complete. A cell that did not finish is a recorded outcome, not a gap."""
    k = header["k"]
    if k is None:
        return ["its header carries no K, so the cells it should hold cannot be named"]
    wanted = Counter(map(_cell_label, expected_cells(k, sizes=sizes,
                                                     reference_sizes=reference_sizes)))
    got = Counter(_cell_label((c["size"], c["rod_left_hand"], c["nut_left_hand"], c["clearance"],
                               c["k"])) for c in cells)
    return _counted_gaps(wanted, got, "cells")
