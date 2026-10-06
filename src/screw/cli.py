"""Command line: `screw serve`, `screw info <kind>`, `screw export <kind>`.

Each kind's options are generated from its registered model, so they always match the API.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Literal, cast, get_args, get_origin

from pydantic import ValidationError

from . import __version__, int_env
from .params import KINDS, FastenerParams
from .records import configure


def _add_args(ap: argparse.ArgumentParser, kind: str, model: type[FastenerParams]) -> None:
    g = ap.add_argument_group(f"{kind} parameters (defaults in brackets)")
    for name, field in model.model_fields.items():
        flag = "--" + name.replace("_", "-")
        help_text = f"{field.description} [{field.default}]".replace("%", "%%")
        if get_origin(field.annotation) is Literal:
            g.add_argument(flag, dest=name, default=None, help=help_text,
                           choices=list(get_args(field.annotation)))
        else:
            # pydantic gives every declared field an annotation; this check exists
            # only to narrow `field.annotation`'s `type | None` to a real type for
            # argparse's `type=`, not because a field can actually lack one.
            assert field.annotation is not None
            g.add_argument(flag, dest=name, default=None, help=help_text,
                           metavar="V", type=field.annotation)


def _params(kind: str, ns: argparse.Namespace) -> FastenerParams:
    model = KINDS[kind]
    values = {k: v for k in model.model_fields if (v := getattr(ns, k)) is not None}
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


def cmd_info(ns: argparse.Namespace) -> None:
    from .calc import derive

    print(derive(_params(ns.kind, ns)).model_dump_json(indent=2))


def cmd_export(ns: argparse.Namespace) -> None:
    out: Path = ns.output
    fmt = ns.format or out.suffix.lower().lstrip(".").replace("stp", "step")
    if fmt not in ("stl", "step"):
        raise SystemExit("error: output must end in .stl or .step (or pass --format)")
    # Imported after the extension check so a typo costs milliseconds, not the ~2 s it takes
    # to load the CAD kernel.
    from .build_errors import BuildError
    from .calc import derive
    from .solid import Format, export

    p = _params(ns.kind, ns)
    try:
        data = export(p, cast("Format", fmt), ns.quality)   # the check above is the proof
    except BuildError as exc:
        raise SystemExit(f"error: {exc}") from None
    out.write_bytes(data)
    print(f"wrote {out} ({len(data) / 1024:.0f} KiB)", file=sys.stderr)
    for warning in derive(p).warnings:
        print(f"warning: {warning}", file=sys.stderr)


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

    for kind, model in KINDS.items():
        kp = ik.add_parser(kind, allow_abbrev=False)
        _add_args(kp, kind, model)

        kp = ek.add_parser(kind, allow_abbrev=False)
        kp.add_argument("-o", "--output", type=Path, required=True, help="file.stl or file.step")
        kp.add_argument("--format", choices=["stl", "step"], help="override the file extension")
        kp.add_argument("--quality", choices=["preview", "fine"], default="fine",
                        help="STL tessellation [fine]")
        _add_args(kp, kind, model)

    ns = ap.parse_args(argv)
    ns.func(ns)


if __name__ == "__main__":
    main()
