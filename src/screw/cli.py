"""Command line: `screw serve`, `screw info <kind>`, `screw export <kind>`, `screw presets <kind>`,
`screw pair <kind>`.

Each kind's options are generated from its registered model, so they always match the API.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, cast, get_args, get_origin

from pydantic import ValidationError

from . import __version__, int_env
from .calc import explicit_conflict
from .params import KINDS, FastenerParams, NutParams
from .records import configure


# argparse keeps the last of two values for one option without a word, so `--d 5 --d 6` would
# build a d=6 part the command line also says is d=5 (D-12, L02: a direct conflict between two
# things the user asked for is refused, never guessed). A parameter is `None` until given, so
# "already set" is `is not None`; the same rule refuses the repeated query key on the API.
# `Sequence[object]`, not `Sequence[Any]`: L04 writes no `Any`, and the wider parameter type
# is still a valid override (mypy --strict with disallow_any_explicit).
def _refuse_repeat(action: argparse.Action, parser: argparse.ArgumentParser,
                   namespace: argparse.Namespace, option_string: str | None) -> None:
    if getattr(namespace, action.dest) is not None:
        parser.error(f"{'/'.join(action.option_strings)} was given more than once "
                     f"(again as {option_string})")


class _Once(argparse.Action):
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 values: str | Sequence[object] | None, option_string: str | None = None) -> None:
        _refuse_repeat(self, parser, namespace, option_string)
        setattr(namespace, self.dest, values)


class _OnceBool(argparse.BooleanOptionalAction):
    """`--x` / `--no-x`, each at most once between them: `--x --no-x` is a contradiction."""

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 values: str | Sequence[object] | None, option_string: str | None = None) -> None:
        _refuse_repeat(self, parser, namespace, option_string)
        super().__call__(parser, namespace, values, option_string)


def _add_args(ap: argparse.ArgumentParser, kind: str, model: type[FastenerParams]) -> None:
    g = ap.add_argument_group(f"{kind} parameters (defaults in brackets)")
    for name, field in model.model_fields.items():
        flag = "--" + name.replace("_", "-")
        shown = "required" if field.is_required() else field.default
        help_text = f"{field.description} [{shown}]".replace("%", "%%")
        # pydantic gives every declared field an annotation; this check exists only to narrow
        # `field.annotation`'s `type | None` to a real type for argparse's `type=`, not because
        # a field can actually lack one. Before the `is bool` test: mypy otherwise narrows the
        # else branch to `None` and calls the numeric branch unreachable.
        annotation = field.annotation
        assert annotation is not None
        if annotation is bool:
            # A flag that takes no value (`--left-hand` / `--no-left-hand`), never a bool-typed
            # one: bool("false") is True, which would build the hand the user did not ask for.
            g.add_argument(flag, dest=name, default=None, help=help_text, action=_OnceBool)
        elif get_origin(annotation) is Literal:
            g.add_argument(flag, dest=name, default=None, help=help_text, action=_Once,
                           choices=list(get_args(annotation)))
        else:
            g.add_argument(flag, dest=name, default=None, help=help_text, action=_Once,
                           metavar="V", type=annotation)


def _add_preset(ap: argparse.ArgumentParser) -> None:
    # The one flag of info and export that is not generated from a model field (D-11).
    ap.add_argument("--preset", default=None, action=_Once, metavar="ID",
                    help="fill the fields from an ISO preset (screw presets <kind> lists them); "
                         "flags given as well override it")


def _params(kind: str, ns: argparse.Namespace) -> FastenerParams:
    model = KINDS[kind]
    values = {k: v for k in model.model_fields if (v := getattr(ns, k)) is not None}
    if ns.preset is not None:
        # The preset is metadata of this one command (D-09): it is expanded into the mm fields
        # here and the model never sees it. The explicit flags are laid over the row, so a
        # field the user typed wins (L02), and the conflict rule below then judges the merged
        # values: `--preset iso4014:M10x80 --length 20` is a thread longer than its bolt.
        from .calc.presets import expand

        row = expand(kind, ns.preset)
        if row is None:
            print(f"error: preset: unknown id {ns.preset!r} for kind {kind}; "
                  f"list them with screw presets {kind}", file=sys.stderr)
            raise SystemExit(2)
        values = {**row, **values}
    # D-25: only the explicit flags are in `values`, so this is the request-boundary rule the API
    # applies to the raw query, and it is the kind's own rule, never the bolt's for every kind
    # (04-REVIEW WR-02). The model cannot tell an explicit value from its default.
    if (conflict := explicit_conflict(kind, values)) is not None:
        print(f"error: {conflict.msg}", file=sys.stderr)
        raise SystemExit(2)
    try:
        return model(**values)
    except ValidationError as exc:
        for err in exc.errors():
            where = ".".join(str(x) for x in err["loc"])
            msg = err["msg"].removeprefix("Value error, ")
            print(f"error: {where + ': ' if where else ''}{msg}", file=sys.stderr)
        raise SystemExit(2) from None


def cmd_serve(ns: argparse.Namespace) -> None:
    import uvicorn

    # The composition root: every production start is `screw serve`. configure() installs
    # the one stderr JSON handler for the SCREW_WORKERS=1 default; app.py's lifespan() calls
    # it again, idempotently, because this call alone would silently miss every record once
    # a deployer raises SCREW_WORKERS (see records.py's docstring).
    configure()
    # log_config=None: ported from spur, which verified it by reading the installed
    # uvicorn's Config.configure_logging(), whose entire body is gated behind
    # `if self.log_config is not None`. Passing None skips uvicorn's own dictConfig
    # entirely, and since no log_level is passed either, uvicorn never touches
    # `uvicorn.error`/`uvicorn.access`'s levels or handlers -- they keep propagate=True
    # and land on the one root handler above, so the whole stream shares one format.
    uvicorn.run("screw.app:app", host=ns.host, port=ns.port, workers=ns.workers,
                root_path=ns.root_path, proxy_headers=True, log_config=None)


def cmd_presets(ns: argparse.Namespace) -> None:
    from .calc.presets import catalogue_document

    print(catalogue_document(ns.kind).model_dump_json(indent=2))


def cmd_info(ns: argparse.Namespace) -> None:
    from .calc import derive

    print(derive(_params(ns.kind, ns)).model_dump_json(indent=2))


def cmd_export(ns: argparse.Namespace) -> None:
    out: Path = ns.output
    # A directory has no extension to read the format from, so it must be named (D-22, R9).
    if out.is_dir() and not ns.format:
        raise SystemExit("error: output is a directory: pass --format stl or --format step")
    fmt = ns.format or out.suffix.lower().lstrip(".").replace("stp", "step")
    if fmt not in ("stl", "step"):
        raise SystemExit("error: output must end in .stl or .step (or pass --format)")
    from .calc import derive, download_name, download_refusal

    p = _params(ns.kind, ns)
    # The same kernel-free rule the API's `_serve` applies (D-02, FRNT-05 parity). Exit 2 like
    # `_params`, the CLI analogue of the 422: a parameter choice is refused, nothing failed
    # to build (a BuildError below keeps exit 1; 03-RESEARCH Open Question 5).
    quality: str = ns.quality or "fine"
    refusal = download_refusal(p, fmt, quality)
    if refusal is not None:
        print(f"error: {refusal}", file=sys.stderr)
        raise SystemExit(2)
    # Imported after the extension check and the refusals, so a typo or a refused export
    # costs milliseconds, not the ~2 s it takes to load the CAD kernel.
    from .build_errors import BuildError
    from .solid import Format, Quality, export

    try:
        data = export(p, cast("Format", fmt), cast("Quality", quality))   # checked above
    except BuildError as exc:
        raise SystemExit(f"error: {exc}") from None
    # A directory gets the name the API's Content-Disposition carries; a file path the user typed
    # is written as given. Only the STL has a quality: the STEP has no tessellation to name.
    if out.is_dir():
        out = out / download_name(p, fmt, quality)
    out.write_bytes(data)
    detail = f", {quality}" if fmt == "stl" else ""
    print(f"wrote {out} ({len(data) / 1024:.0f} KiB{detail})", file=sys.stderr)
    for warning in derive(p).warnings:
        print(f"warning: {warning}", file=sys.stderr)


# Exit codes of `screw pair`: the verdict, readable by a script without parsing the JSON.
PAIR_EXIT = {"proven": 0, "violated": 1, "inconclusive": 2}


def cmd_pair(ns: argparse.Namespace) -> None:
    p = _params(ns.kind, ns)
    # The proof mates the nut with the nominal rod of its own d and pitch, a rod the nut's own
    # validator does not judge (it judges the void, which a positive clearance widens): refuse
    # here, before the kernel loads, as exit 2 like every other refused parameter.
    from .calc.thread import root_radius_refusal

    if (refusal := root_radius_refusal(p.d, p.pitch)) is not None:
        print(f"error: pair: the nominal rod {refusal}", file=sys.stderr)
        raise SystemExit(2)
    from .solid.pair import prove

    report = prove(cast("NutParams", p))    # `pair` is offered only for kinds with a clearance
    print(report.model_dump_json(indent=2))
    # The last statement, and never a plain return: the real boolean parks its operation for
    # the life of the process and a normal interpreter exit then dies in OpenCascade's teardown
    # with status 139 after the JSON is already out (RESEARCH F5, 3 of 3 runs). os._exit skips
    # the teardown, so the streams are flushed by hand first.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(PAIR_EXIT[report.verdict])


def main(argv: list[str] | None = None) -> None:
    env = os.environ.get
    # allow_abbrev=False on every parser, kind parsers included: with the default,
    # `screw info bolt --len 5` quietly binds --length, and a prefix choosing a field is a
    # parameter the user did not name (L02). `--m 5` is refused either way.
    ap = argparse.ArgumentParser(prog="screw", allow_abbrev=False,
                                 description="Parametric thread and fastener generator.")
    ap.add_argument("--version", action="version", version=f"screw {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("serve", help="run the web UI and API", allow_abbrev=False)
    s.add_argument("--host", default=env("SCREW_HOST", "127.0.0.1"))
    s.add_argument("--port", type=int, default=int_env("SCREW_PORT", 8000))
    # INTERIM (spur L17): one server process, because the build pool and the caches are
    # per process. Not measured for screw; Phase 7 re-sweeps it (OPER-02).
    s.add_argument("--workers", type=int, default=int_env("SCREW_WORKERS", 1))
    s.add_argument("--root-path", default=env("SCREW_ROOT_PATH", ""),
                   help="URL prefix when served behind a reverse proxy, e.g. /screw")
    s.set_defaults(func=cmd_serve)

    i = sub.add_parser("info", help="print derived dimensions as JSON", allow_abbrev=False)
    ik = i.add_subparsers(dest="kind", required=True)
    i.set_defaults(func=cmd_info)

    e = sub.add_parser("export", help="write an STL or STEP file", allow_abbrev=False)
    ek = e.add_subparsers(dest="kind", required=True)
    e.set_defaults(func=cmd_export)

    pr = sub.add_parser("presets", help="print a kind's ISO preset catalogue as JSON",
                        allow_abbrev=False)
    prk = pr.add_subparsers(dest="kind", required=True)
    pr.set_defaults(func=cmd_presets)

    pa = sub.add_parser("pair", help="prove with the kernel whether a nut mates its bolt; "
                                     "exit 0 proven, 1 violated, 2 inconclusive",
                        allow_abbrev=False)
    pak = pa.add_subparsers(dest="kind", required=True)
    pa.set_defaults(func=cmd_pair)

    for kind, model in KINDS.items():
        prk.add_parser(kind, allow_abbrev=False)

        if "clearance" in model.model_fields:    # the model decides which kinds have a pair
            kp = pak.add_parser(kind, allow_abbrev=False)
            kp.set_defaults(preset=None)    # no --preset: `_params` reads it, the command has none
            _add_args(kp, kind, model)

        kp = ik.add_parser(kind, allow_abbrev=False)
        _add_preset(kp)
        _add_args(kp, kind, model)

        kp = ek.add_parser(kind, allow_abbrev=False)
        kp.add_argument("-o", "--output", type=Path, required=True, action=_Once,
                        help="file.stl or file.step, or a directory (with --format)")
        kp.add_argument("--format", choices=["stl", "step"], action=_Once,
                        help="override the file extension")
        # default=None so a repeat is detectable; cmd_export reads `ns.quality or "fine"`.
        kp.add_argument("--quality", choices=["preview", "fine"], default=None, action=_Once,
                        help="STL tessellation [fine]")
        _add_preset(kp)
        _add_args(kp, kind, model)

    ns = ap.parse_args(argv)
    ns.func(ns)


if __name__ == "__main__":
    main()
