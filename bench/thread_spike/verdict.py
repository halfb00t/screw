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
from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from typing import Literal, NoReturn, TypedDict

from bench.thread_spike.maths import (
    FRONTIER_MAX_TURNS,
    K_CANDIDATES,
    PITCH,
    closed_volume,
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
    set exactly on a built `trim` row (D-08)."""

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


_REQUEST_KEYS = ("kind", "size", "d", "pitch", "turns", "length", "left_hand", "k",
                 "clearance", "presets", "step", "gzip_on", "check_ceiling")
_MEASURE_KEYS = ("solids", "is_valid", "precise_volume", "default_volume", "build_s",
                 "volume_s", "meshes")
_RECORD_KEYS = (*_REQUEST_KEYS, "outcome", "error", *_MEASURE_KEYS, "step_bytes", "step_s",
                "trim_s")
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
