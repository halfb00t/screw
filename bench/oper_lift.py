"""A reading one step past a guard, with that guard lifted and no other (07 R3, D-08).

The walls the sweep confirms are at the validator's own caps: 250 turns (`MAX_TURNS`) and 1e5 mm
(the `le` of every length field), as the sweep found them. The confirmation reads the next step
past each,
which `KINDS[kind].model_validate` refuses (`turn_cap`, `less_than_equal`), so without a lift the
point could never reach the kernel and the confirmation would only confirm the validator. A point
names the one guard it lifts and the new limit; every other validator runs as written, and the
production classes are not touched: `max_mm` builds a subclass, `max_turns` restores the module
constant before it returns.

`registered` is the other half (07 D-08, L20): the point files are pre-registered (R30) and
`bench.oper_sets` drops the parts the model refuses, so once the model's walls moved to the
measured ones a file generated against the model would change with every wall. `registered`
validates under the guards the sweep was registered under (250 turns, 1e5 mm on every length
field, a root radius above 0, no fine-pitch wall), so a point file and the derived sets depend
on the records and on this module, never on the production constants those records set.

Kernel-free, like `screw.params`. Not imported by `bench.oper`, which stays standard-library only.
"""

from __future__ import annotations

import copy
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from fractions import Fraction

from annotated_types import Le

from screw.calc import thread
from screw.params import KINDS, FastenerParams

LIFTS = ("max_turns", "max_mm")

# The guards of the registration, before any wall was measured (L11 for the turns, F1 for the
# millimetres, L12 for the root). Frozen here on purpose: they are what the point files were
# generated under, not what the product accepts now.
REGISTERED_TURNS = 250
REGISTERED_MM = 1e5
ABOVE_ZERO = 5e-324  # `root >= ABOVE_ZERO` is `root > 0` for a float
# No fine-pitch wall (07 R31): above every d / pitch two admitted floats can make, d at most 1e5
# over a pitch of at least 5e-324 being about 2e328.
UNWALLED = Fraction(10) ** 400


def _with_field_bound(model: type[FastenerParams], bound: float) -> type[FastenerParams]:
    """`model` with the `le` bound of every field that has one replaced by `bound`. A subclass:
    its validators are the base's, so `head_too_small` and the rest still run."""
    annotations: dict[str, object] = {}
    namespace: dict[str, object] = {"__module__": __name__, "__annotations__": annotations}
    for name, info in model.model_fields.items():
        if any(isinstance(item, Le) for item in info.metadata):
            lifted = copy.copy(info)
            lifted.metadata = [Le(bound) if isinstance(item, Le) else item
                               for item in info.metadata]
            annotations[name] = info.annotation
            namespace[name] = lifted
    # `type(...)` and not `pydantic.create_model`: mypy cannot match a ** dict to create_model's
    # overloads without an explicit Any, which this repo does not write (L04).
    subclass = type(f"Lifted{model.__name__}", (model,), namespace)
    if not issubclass(subclass, model):
        raise TypeError(f"{subclass!r} is not a subclass of {model!r}")
    return subclass


@contextmanager
def _turn_cap(turns: int) -> Iterator[None]:
    """`MAX_TURNS` at `turns` for the validation inside the block. The turn-cap validators read
    the module constant at call time, so the guard is exactly this one number."""
    module = vars(thread)
    saved = module["MAX_TURNS"]
    module["MAX_TURNS"] = turns
    try:
        yield
    finally:
        module["MAX_TURNS"] = saved


@contextmanager
def _root_floor(floor: float) -> Iterator[None]:
    """`MIN_ROOT_RADIUS_MM` at `floor` for the validation inside the block, like `_turn_cap`."""
    module = vars(thread)
    saved = module["MIN_ROOT_RADIUS_MM"]
    module["MIN_ROOT_RADIUS_MM"] = floor
    try:
        yield
    finally:
        module["MIN_ROOT_RADIUS_MM"] = saved


@contextmanager
def _no_pitch_wall() -> Iterator[None]:
    """Neither kind's fine-pitch wall for the validation inside the block, like `_turn_cap`: the
    refusal reads both constants at call time."""
    module = vars(thread)
    saved = {name: module[name] for name in ("MAX_BOLT_D_PER_PITCH", "MAX_NUT_D_PER_PITCH")}
    module.update(dict.fromkeys(saved, UNWALLED))
    try:
        yield
    finally:
        module.update(saved)


def drawn(kind: str, params: Mapping[str, object]) -> FastenerParams:
    """The validated parameters of `kind` under the production model less the fine-pitch wall:
    the model every set drawn from runner records before 07 R31 was drawn under. Those sets are
    checked under it and never drawn again (ruling G36), so the guard moves none of them and no
    value derived from their readings. Raises `pydantic.ValidationError` as `model_validate`."""
    with _no_pitch_wall():
        return KINDS[kind].model_validate(dict(params))


def _check(lift: Mapping[str, float] | None) -> None:
    if lift and (len(lift) != 1 or next(iter(lift)) not in LIFTS):
        raise ValueError(f"a lift names exactly one of {list(LIFTS)}, not {dict(lift)}")


def registered(kind: str, params: Mapping[str, float | bool],
               lift: Mapping[str, float] | None = None) -> FastenerParams:
    """The validated parameters of `kind` under the guards of the registration, with the one
    guard `lift` names lifted to the limit it gives, as in `validate`. Raises
    `pydantic.ValidationError` for what those guards refuse."""
    _check(lift)
    limits = {"max_turns": float(REGISTERED_TURNS), "max_mm": REGISTERED_MM, **(lift or {})}
    model = _with_field_bound(KINDS[kind], limits["max_mm"])
    with _turn_cap(int(limits["max_turns"])), _root_floor(ABOVE_ZERO), _no_pitch_wall():
        return model.model_validate(params)


def validate(kind: str, params: Mapping[str, float | bool],
             lift: Mapping[str, float] | None = None) -> FastenerParams:
    """The validated parameters of `kind`, with the one guard `lift` names lifted to the limit it
    gives (`{"max_turns": 260}` or `{"max_mm": 1e6}`). No lift is plain `model_validate`.
    Raises `pydantic.ValidationError` for what the model still refuses and `ValueError` for a
    lift that is not exactly one known guard."""
    model = KINDS[kind]
    if not lift:
        return model.model_validate(params)
    _check(lift)
    ((guard, limit),) = lift.items()
    if guard == "max_mm":
        return _with_field_bound(model, limit).model_validate(params)
    with _turn_cap(int(limit)):
        return model.model_validate(params)
