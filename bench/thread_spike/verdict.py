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
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, NoReturn, TypedDict

# Relative tolerance of the precise volume against the closed form. The research maximum was
# 7.6e-6 over 576 sewn rows (R10) and the naive construction's defect is about 0.76, so 1e-4
# neither flaps nor hides a 1e-3 defect. Fixed before any data (D-09); never tuned toward a pass.
T_PASS = 1e-4

# Four times the 30 s INTERIM build-plus-mesh budget, so an over-budget row is measured rather
# than killed (RESEARCH Pattern 3). A protocol input.
ROW_TIMEOUT_S = 120.0

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


class MeshRecord(TypedDict):
    """One mesh of a row. The four check fields are `None` when the check was not run
    (`checked` False): a skipped check is counted visibly, never reported as a pass."""

    preset: str
    tolerance: float
    angular: float
    triangles: int
    bytes: int
    mesh_s: float
    checked: bool
    watertight: bool | None
    open_edges: int | None
    stl_volume: float | None
    surface_area: float | None


class RowRecord(RowRequest):
    """The request echoed plus what happened. Every measurement is `None` unless `outcome` is
    "built"; `error` is set exactly when it is not."""

    outcome: Outcome
    error: str | None
    solids: int | None
    is_valid: bool | None
    precise_volume: float | None
    default_volume: float | None
    build_s: float | None
    volume_s: float | None
    meshes: list[MeshRecord] | None


_REQUEST_KEYS = ("kind", "size", "d", "pitch", "turns", "length", "left_hand", "k",
                 "clearance", "presets")
_MEASURE_KEYS = ("solids", "is_valid", "precise_volume", "default_volume", "build_s",
                 "volume_s", "meshes")
_RECORD_KEYS = (*_REQUEST_KEYS, "outcome", "error", *_MEASURE_KEYS)
_MESH_KEYS = ("preset", "tolerance", "angular", "triangles", "bytes", "mesh_s", "checked",
              "watertight", "open_edges", "stl_volume", "surface_area")


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
    watertight = _optional(_bool, item, "watertight")
    open_edges = _optional(_int, item, "open_edges")
    stl_volume = _optional(_num, item, "stl_volume")
    surface_area = _optional(_num, item, "surface_area")
    present = (watertight is not None, open_edges is not None, stl_volume is not None,
               surface_area is not None)
    if checked != all(present) or (not checked and any(present)):
        raise ValueError("mesh: the check fields are set exactly when 'checked' is true")
    return {
        "preset": _str(item, "preset"),
        "tolerance": _num(item, "tolerance"),
        "angular": _num(item, "angular"),
        "triangles": _int(item, "triangles"),
        "bytes": _int(item, "bytes"),
        "mesh_s": _num(item, "mesh_s"),
        "checked": checked,
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
    measured = (solids, is_valid, precise, default, build_s, volume_s, meshes)
    if outcome == "built":
        for key, value in zip(_MEASURE_KEYS, measured, strict=True):
            if value is None:
                raise ValueError(f"a built record must carry {key!r}")
        if error is not None:
            raise ValueError("a built record must not carry an 'error'")
    else:
        for key, value in zip(_MEASURE_KEYS, measured, strict=True):
            if value is not None:
                raise ValueError(f"a {outcome} record must not carry {key!r}")
        if not error:
            raise ValueError(f"a {outcome} record must carry an 'error'")
    return {
        **_request_fields(obj),
        "outcome": outcome,
        "error": error,
        "solids": solids,
        "is_valid": is_valid,
        "precise_volume": precise,
        "default_volume": default,
        "build_s": build_s,
        "volume_s": volume_s,
        "meshes": meshes,
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


PROTOCOL_PATH = ".planning/phases/02-thread-spike/02-SPIKE.md"
RESULTS_HEADING = "## Results"


def before_results(text: str) -> str | None:
    return text


@dataclass(frozen=True)
class GuardResult:
    held: bool
    reasons: tuple[str, ...]


def protocol_guard(local_text: str | None, main_text: str | None, *, fetched: bool,
                   landed_is_ancestor: bool) -> GuardResult:
    _ = (local_text, main_text, fetched, landed_is_ancestor)
    return GuardResult(held=False, reasons=())
