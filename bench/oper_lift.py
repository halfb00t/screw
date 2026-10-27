"""A reading one step past a guard, with that guard lifted and no other (07 R3, D-08).

The walls the sweep confirms are at the validator's own caps: 250 turns (`MAX_TURNS`) and 1e5 mm
(`INTERIM_MAX_MM`, the `le` of every length field). The confirmation reads the next step past each,
which `KINDS[kind].model_validate` refuses (`turn_cap`, `less_than_equal`), so without a lift the
point could never reach the kernel and the confirmation would only confirm the validator. A point
names the one guard it lifts and the new limit; every other validator runs as written, and the
production classes are not touched: `max_mm` builds a subclass, `max_turns` restores the module
constant before it returns.

Kernel-free, like `screw.params`. Not imported by `bench.oper`, which stays standard-library only.
"""

from __future__ import annotations

import copy
from collections.abc import Iterator, Mapping
from contextlib import contextmanager

from annotated_types import Le

from screw.calc import thread
from screw.params import KINDS, FastenerParams

LIFTS = ("max_turns", "max_mm")


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


def validate(kind: str, params: Mapping[str, float | bool],
             lift: Mapping[str, float] | None = None) -> FastenerParams:
    """The validated parameters of `kind`, with the one guard `lift` names lifted to the limit it
    gives (`{"max_turns": 260}` or `{"max_mm": 1e6}`). No lift is plain `model_validate`.
    Raises `pydantic.ValidationError` for what the model still refuses and `ValueError` for a
    lift that is not exactly one known guard."""
    model = KINDS[kind]
    if not lift:
        return model.model_validate(params)
    if len(lift) != 1 or next(iter(lift)) not in LIFTS:
        raise ValueError(f"a lift names exactly one of {list(LIFTS)}, not {dict(lift)}")
    ((guard, limit),) = lift.items()
    if guard == "max_mm":
        return _with_field_bound(model, limit).model_validate(params)
    with _turn_cap(int(limit)):
        return model.model_validate(params)
