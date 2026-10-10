"""D-10: the web form, the HTTP API and the CLI expose exactly the registered model's fields.

One module, parametrised over `KINDS`, so a kind registered in any later phase is covered
the moment it is registered, with no edit here. Every comparison is against
`KINDS[kind].model_fields` -- never against a list a consumer keeps of its own, which would
drift together with the thing it is meant to check (01-RESEARCH.md Pitfall 2).

This module must stay in `make verify`. It holds no browser (L01): the UI is checked by
reading `app.js` as text, and `_field_literals` is shown to catch what it claims to catch
before it is trusted to find nothing.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import cast

import pytest
from fastapi.testclient import TestClient

from screw import cli
from screw.app import STATIC, app, build_backend
from screw.calc import STANDING_WARNING, derive
from screw.params import DEFAULT_KIND, KINDS, FastenerParams
from screw.solid import Format, Quality, export

client = TestClient(app)

# `params=` is typed by starlette as exactly this union (Pitfall 1).
Params = dict[str, str | int | float | bool | None]

APP_JS = (STATIC / "app.js").read_text()
FOREIGN = "zz_not_a_field"


async def _inline_backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
    return export(p, cast(Format, fmt), cast(Quality, quality))


@pytest.fixture(autouse=True, scope="module")
def _inline_build_backend() -> Iterator[None]:
    """Build in process, so the model-route checks never need a pool (as tests/test_api.py)."""
    app.dependency_overrides[build_backend] = lambda: _inline_backend
    yield
    app.dependency_overrides.pop(build_backend, None)


def _flag(name: str) -> str:
    return "--" + name.replace("_", "-")


def _is_bool(kind: str, name: str) -> bool:
    return KINDS[kind].model_fields[name].annotation is bool


def _expected_flags(kind: str) -> list[str]:
    """The flags the model's fields generate: a boolean field is a pair, `--x` then `--no-x`."""
    flags: list[str] = []
    for name in KINDS[kind].model_fields:
        flags.append(_flag(name))
        if _is_bool(kind, name):
            flags.append("--no-" + name.replace("_", "-"))
    return flags


def _cli_flags(kind: str, command: str, capsys: pytest.CaptureFixture[str]) -> list[str]:
    """Every long flag `<command> <kind> --help` lists, in the order it lists them.

    The whole help, not only the kind's own group: a hand-written flag added to the kind's
    parser outside the generated group would otherwise sit in the plain `options:` section
    and go unseen (found by planting one, 01-05 Task 2).
    """
    with pytest.raises(SystemExit) as stop:
        cli.main([command, kind, "--help"])
    assert stop.value.code == 0
    lines = capsys.readouterr().out.splitlines()
    assert f"{kind} parameters (defaults in brackets):" in lines
    # An option line is two spaces, the invocation, then (after two or more spaces) its help
    # text; reading only the invocation keeps a `--word` inside help prose out of the list.
    flags: list[str] = []
    for line in lines:
        if m := re.match(r"^ {2}(-\S.*?)(?: {2,}|$)", line):
            flags += re.findall(r"--[a-z0-9-]+", m.group(1))
    return flags


def _field_literals(source: str, names: list[str]) -> list[str]:
    """The names `source` reads as a quoted literal or as a property of a parameter holder.

    A bare `\\.name` match would flag `box.getSize(new Vector3()).length()` for the field
    `length` (01-RESEARCH.md F3), so a property read counts only on the receivers that carry
    parameters: info, prop, values, h, q, defaults and properties.
    """
    receivers = r"(?:info|prop|values|h|q|defaults|properties)"
    found: set[str] = set()
    for name in names:
        n = re.escape(name)
        quoted = rf"""(['"`]){n}\1"""
        read = rf"\b{receivers}\s*\.\s*{n}\b"
        subscript = rf"""\b{receivers}\s*\[\s*['"`]{n}['"`]\s*\]"""
        if any(re.search(p, source) for p in (quoted, read, subscript)):
            found.add(name)
    return sorted(found)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def test_the_registry_is_not_empty_and_holds_the_default() -> None:
    # First, so an empty registry fails here instead of passing every parametrised test
    # below with nothing to iterate (Pitfall 2).
    assert len(KINDS) >= 1
    assert DEFAULT_KIND in KINDS
    body = client.get("/api/kinds").json()
    assert body["default"] == DEFAULT_KIND
    assert body["kinds"] == list(KINDS)


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_api_schema_is_the_model(kind: str) -> None:
    properties = client.get("/api/schema", params={"kind": kind}).json()["properties"]
    assert list(properties) == list(KINDS[kind].model_fields)
    for name, prop in properties.items():
        for key in ("title", "group", "unit"):
            assert key in prop, f"{kind}.{name} has no {key} in its schema"


def _query_names(path: str) -> list[str]:
    parameters = app.openapi()["paths"][path]["get"]["parameters"]
    return [p["name"] for p in parameters if p["in"] == "query"]


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_api_query_is_the_model(kind: str) -> None:
    fields = list(KINDS[kind].model_fields)
    assert _query_names(f"/api/{kind}/info") == fields
    # Sorted: the query model inherits `quality` from a mixin listed after the fields, so
    # OpenAPI lists it first. A query string has no order a user sees; the form and the
    # CLI flags do, and those are compared in order above and below.
    assert sorted(_query_names(f"/api/{kind}/model.{{fmt}}")) == sorted([*fields, "quality"])


@pytest.mark.parametrize("kind", list(KINDS))
def test_a_foreign_field_is_refused_on_every_route(kind: str) -> None:
    query: Params = {FOREIGN: 1}
    for path in (f"/api/{kind}/info", f"/api/{kind}/model.stl"):
        res = client.get(path, params=query)
        assert res.status_code == 422, path
        assert res.json()["detail"][0]["loc"] == ["query", FOREIGN], path


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_cli_flags_are_the_model(kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    fields = _expected_flags(kind)
    assert _cli_flags(kind, "info", capsys) == ["--help", *fields]
    # export's own three options come first; everything after them is the model.
    assert _cli_flags(kind, "export", capsys) == ["--help", "--output", "--format",
                                                  "--quality", *fields]


@pytest.mark.parametrize("kind", list(KINDS))
def test_a_foreign_or_abbreviated_flag_exits_2(kind: str,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    foreign = _flag(FOREIGN)
    with pytest.raises(SystemExit) as stop:
        cli.main(["info", kind, foreign, "1"])
    assert stop.value.code == 2
    assert foreign in capsys.readouterr().err

    # Exact equality, not prefix matching: `--len` must not quietly bind `--length` (L02).
    for name in KINDS[kind].model_fields:
        prefix = _flag(name)[:-1]
        with pytest.raises(SystemExit) as stop:
            cli.main(["info", kind, prefix, "1"])
        assert stop.value.code == 2, prefix
        capsys.readouterr()


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_cli_and_the_api_print_the_same_document(
        kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    model = KINDS[kind]
    cases: list[Params] = [{}]
    for name, field in model.model_fields.items():
        if isinstance(field.default, bool):
            cases.append({name: not field.default})
        elif isinstance(field.default, float):
            cases.append({name: field.default * 1.5})
    assert len(cases) > 1, "no float field to move off its default"

    def argv(values: Params) -> list[str]:
        out: list[str] = []
        for k, v in values.items():
            if isinstance(v, bool):
                # A boolean flag takes no value: `--x` or `--no-x`, never `--x false`.
                out.append(_flag(k) if v else "--no-" + k.replace("_", "-"))
            else:
                out += [_flag(k), repr(v)]
        return out

    for values in cases:
        cli.main(["info", kind, *argv(values)])
        cli_doc = json.loads(capsys.readouterr().out)
        api_doc = client.get(f"/api/{kind}/info", params=values).json()
        assert cli_doc == api_doc, values
        assert cli_doc["warnings"][0] == STANDING_WARNING
        assert api_doc["warnings"][0] == STANDING_WARNING


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_no_flag_is_a_value_and_agrees_with_the_omitted_default(
        kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    # `--no-x` is a real value (False), not "not given", and agrees with the omitted default.
    cli.main(["info", kind])
    default_doc = capsys.readouterr().out
    cli.main(["info", kind, "--no-left-hand"])
    assert capsys.readouterr().out == default_doc


@pytest.mark.parametrize("kind", list(KINDS))
def test_every_row_key_is_unread_by_name_in_the_ui(kind: str) -> None:
    keys = [row.key for row in derive(KINDS[kind]()).rows]
    assert keys, "derive() produced no rows to check"
    assert _field_literals(APP_JS, keys) == []


def test_the_literal_check_has_teeth() -> None:
    names = ["d", "pitch", "length"]
    assert _field_literals("const v = info.length;", names) == ["length"]
    assert _field_literals("defaults.pitch", names) == ["pitch"]
    assert _field_literals("q.get('d')", names) == ["d"]
    assert _field_literals('h.get("pitch")', names) == ["pitch"]
    assert _field_literals("props[`length`]", names) == ["length"]
    # F3's false positive: the three.js vector length is not the bolt's length field.
    assert _field_literals("box.getSize(new Vector3()).length()", names) == []
    assert _field_literals("const kind = h.get('kind') ?? kinds.default;", names) == []


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_ui_reads_no_field_by_name(kind: str) -> None:
    assert _field_literals(APP_JS, list(KINDS[kind].model_fields)) == []


# The statements plan 01-04 pinned for this test (01-UI-SPEC.md, Interaction Contract rule
# 29), whitespace aside. Each is a piece of the generic round trip: the form built from the
# schema, the hash read and written without a field name, the default kind taken from
# /api/kinds, the info panel built from whatever rows arrive. Rewording one is not a style
# edit: it means the page may have stopped being generic.
PINNED_STATEMENTS = [
    "fetch('api/kinds')",
    "for (const [name, prop] of Object.entries(schema.properties)) {",
    "fields.set(name, { input, wrap, title });",
    "for (const [name, { input }] of fields) input.value = h.get(name) ?? defaults[name];",
    "q.set(name, input.value)",
    "const kind = h.get('kind') ?? kinds.default;",
    "if (currentKind !== kinds.default) hashQ.set('kind', currentKind);",
    "for (const row of info.rows) {",
    "Number(input.value) !== Number(defaults[name])",
    # Not the whole handler: 01-04 shipped `() => navigate().catch(reportLoadError)` where
    # its plan quoted `navigate`; the property that matters is that the hash drives navigate().
    "window.addEventListener('hashchange'",
    "navigator.clipboard.writeText(location.href)",
]


def test_the_ui_round_trips_every_field_through_generic_code() -> None:
    source = _squash(APP_JS)
    for statement in PINNED_STATEMENTS:
        assert _squash(statement) in source, statement
    # The default comes from /api/kinds, never from where a kind sits in the list (D-09).
    assert "kinds.default" in source
    assert "kinds.kinds[0]" not in source


def test_the_ui_builds_nodes_from_text_only() -> None:
    assert "textContent" in APP_JS
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML"):
        assert sink not in APP_JS, sink


def _repeat_argvs(kind: str, name: str) -> list[list[str]]:
    """Every way to give one field's flag twice (the CLI keeps the last silently, D-12)."""
    flag = _flag(name)
    if _is_bool(kind, name):
        no = "--no-" + name.replace("_", "-")
        return [[flag, no], [flag, flag], [no, no]]
    return [[flag, "5", flag, "6"]]


@pytest.mark.parametrize("kind", list(KINDS))
def test_a_repeated_parameter_is_refused_naming_it(
        kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    for name in KINDS[kind].model_fields:
        for given in _repeat_argvs(kind, name):
            with pytest.raises(SystemExit) as stop:
                cli.main(["info", kind, *given])
            assert stop.value.code == 2, given
            assert _flag(name) in capsys.readouterr().err, given
    # export's own options are refused the same way.
    for given in (["--quality", "fine", "--quality", "preview"],
                  ["--format", "stl", "--format", "step"],
                  ["-o", "a.stl", "-o", "b.stl"]):
        with pytest.raises(SystemExit) as stop:
            cli.main(["export", kind, "-o", "x.stl", *given])
        assert stop.value.code == 2, given
        assert given[0] in capsys.readouterr().err, given
