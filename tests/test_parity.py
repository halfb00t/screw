"""D-10: the web form, the HTTP API and the CLI expose exactly the registered model's fields.

One module, parametrised over `KINDS`, so a kind registered in any later phase is covered
the moment it is registered, with no edit here. Every comparison is against
`KINDS[kind].model_fields` -- never against a list a consumer keeps of its own, which would
drift together with the thing it is meant to check (01-RESEARCH.md Pitfall 2).

This module must stay in `make verify`. It holds no browser (L01): the UI is checked by
reading `app.js` and `style.css` as text, and `_field_literals` is shown to catch what it
claims to catch before it is trusted to find nothing.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import cast

import pytest
from conftest import REQUIRED_VALUES
from fastapi.testclient import TestClient
from pydantic import Field
from pydantic_core import PydanticUndefined

from screw import cli
from screw.app import STATIC, app, build_backend
from screw.calc import STANDING_WARNING, derive, download_name
from screw.calc.presets import expand
from screw.params import DEFAULT_KIND, KINDS, BoltParams, FastenerParams
from screw.solid import Format, Quality, export

client = TestClient(app)

# `params=` is typed by starlette as exactly this union (Pitfall 1).
Params = dict[str, str | int | float | bool | None]
# A repeated key needs the list-of-pairs form, which is invariant in its element type.
Pairs = list[tuple[str, str | int | float | bool | None]]

APP_JS = (STATIC / "app.js").read_text()
STYLE_CSS = (STATIC / "style.css").read_text()
FOREIGN = "zz_not_a_field"

# The flags of each command that are not generated from a model field, in the order `--help`
# lists them. `--preset` is the one flag of `info` and `export` that is not generated from a
# model field (D-11): the preset is metadata of one command, expanded into fields before the
# model is built, and the model routes of the API take no such key (D-09).
HAND_WRITTEN: dict[str, list[str]] = {
    "info": ["--preset"], "export": ["--output", "--format", "--quality", "--preset"]}


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


# The info row as the planner measured it (04-17-PLAN.md, G-04-5): exact declarations, so a
# revert to the one-line row, a clip or a deleted rule fails the gate. Property -> value.
INFO_ROW_RULES: dict[str, dict[str, str]] = {
    "#dims div": {
        "display": "flex", "flex-wrap": "wrap", "justify-content": "space-between",
        "gap": ".75rem", "padding": ".15rem 0", "border-bottom": "1px dashed var(--line)"},
    "#dims dt": {"color": "var(--muted)", "flex": "1 1 50%"},
    "#dims dd": {
        "margin": "0 0 0 auto", "font-variant-numeric": "tabular-nums",
        "overflow-wrap": "anywhere"},
    "#dims dl": {
        "display": "grid", "grid-template-columns": "repeat(auto-fill, minmax(12.5rem, 1fr))",
        "gap": ".15rem 1.5rem", "margin": "0"},
}
CLIPS = ("overflow", "overflow-x", "text-overflow")


def _css_rules(css: str) -> list[tuple[str, dict[str, str]]]:
    """Every brace-free rule of `css` as (squashed selector, declarations), comments dropped.

    The inner rules of an `@media` block are found the same way: the pattern needs a body with
    no brace in it, so the block's own opening brace never starts a match.
    """
    bare = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    rules: list[tuple[str, dict[str, str]]] = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", bare):
        declarations: dict[str, str] = {}
        for declaration in body.split(";"):
            if ":" in declaration:
                prop, value = declaration.split(":", 1)
                declarations[prop.strip()] = _squash(value)
        rules.append((_squash(selector), declarations))
    return rules


def _css_declarations(css: str, selector: str) -> dict[str, str]:
    """The declarations `selector` ends up with, a later rule overriding an earlier one."""
    merged: dict[str, str] = {}
    for found, declarations in _css_rules(css):
        if found == selector:
            merged.update(declarations)
    return merged


def _info_row_problems(css: str) -> list[str]:
    """What differs from the pinned info row; the four selectors are never read from `css`."""
    problems = [s for s, want in INFO_ROW_RULES.items() if _css_declarations(css, s) != want]
    dims = [(s, d) for s, d in _css_rules(css) if "#dims" in s]
    if any(value == "nowrap" for _, d in dims for value in d.values()):
        problems.append("nowrap")
    if any(prop in CLIPS for _, d in dims for prop in d):
        problems.append("clip")
    return problems


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_required_fields_are_exactly_the_ones_the_samples_name(kind: str) -> None:
    # A positive rule (P6): a field is required only when `REQUIRED_VALUES` names it, and every
    # other field carries a default, so a planted required field fails here instead of silently
    # breaking every `model()` call and "default document" assumption in the suite.
    fields = KINDS[kind].model_fields
    required = {name for name, field in fields.items() if field.is_required()}
    assert required == set(REQUIRED_VALUES.get(kind, {}))
    assert all(field.default is not PydanticUndefined
               for name, field in fields.items() if name not in required)


def test_a_planted_required_field_fails_the_required_field_rule() -> None:
    # The teeth of the rule above: a model with one more required field than the samples name.
    class Planted(FastenerParams):
        kind = "planted"
        extra_required: float = Field(...)

    required = {name for name, field in Planted.model_fields.items() if field.is_required()}
    assert required == {"extra_required"}
    assert required != set(REQUIRED_VALUES.get("planted", {}))


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
    # The required values ride along: a request missing one reports that first, and this test is
    # about the foreign key being named.
    query: Params = {FOREIGN: 1, **REQUIRED_VALUES.get(kind, {})}
    for path in (f"/api/{kind}/info", f"/api/{kind}/model.stl"):
        res = client.get(path, params=query)
        assert res.status_code == 422, path
        assert res.json()["detail"][0]["loc"] == ["query", FOREIGN], path


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_cli_flags_are_the_model(kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    fields = _expected_flags(kind)
    # A positive rule (D-11): the whole flag list is the hand-written flags then the model's
    # fields, so a stray flag fails here instead of being filtered out.
    for command, hand_written in HAND_WRITTEN.items():
        assert _cli_flags(kind, command, capsys) == ["--help", *hand_written, *fields]


# `screw pair` has no hand-written flag at all (no --preset: a preset is metadata of info and
# export, D-09) and is offered only for kinds whose model declares a clearance, so it is judged
# apart from HAND_WRITTEN, whose commands exist for every kind.
PAIR_KINDS = [kind for kind, model in KINDS.items() if "clearance" in model.model_fields]


def test_the_pair_command_is_offered_for_nut_only() -> None:
    assert PAIR_KINDS == ["nut"]


@pytest.mark.parametrize("kind", PAIR_KINDS)
def test_the_pair_flags_are_the_model_and_nothing_else(
        kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert _cli_flags(kind, "pair", capsys) == ["--help", *_expected_flags(kind)]


def test_a_stray_flag_makes_the_pair_flag_comparison_fail(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    real = cli._add_args

    def plant(ap: argparse.ArgumentParser, kind: str, model: type[FastenerParams]) -> None:
        real(ap, kind, model)
        ap.add_argument("--stray", default=None)

    monkeypatch.setattr(cli, "_add_args", plant)
    flags = _cli_flags("nut", "pair", capsys)
    assert "--stray" in flags
    assert flags != ["--help", *_expected_flags("nut")]


def test_a_stray_flag_makes_the_flag_comparison_fail(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # The teeth of the positive rule above: plant one option outside the generated group.
    real = cli._add_args

    def plant(ap: argparse.ArgumentParser, kind: str, model: type[FastenerParams]) -> None:
        real(ap, kind, model)
        ap.add_argument("--stray", default=None)

    monkeypatch.setattr(cli, "_add_args", plant)
    flags = _cli_flags("bolt", "info", capsys)
    assert "--stray" in flags
    assert flags != ["--help", *HAND_WRITTEN["info"], *_expected_flags("bolt")]


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_cli_and_the_api_print_the_same_preset_catalogue(
        kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    # D-10, FRNT-05: one document, so every registered kind has one and both front ends agree.
    # Compared as parsed JSON (key order and numbers included) after one real UTF-8 round trip.
    api = client.get("/api/presets", params={"kind": kind})
    assert api.status_code == 200, kind
    cli.main(["presets", kind])
    printed = capsys.readouterr().out.encode("utf-8")
    assert json.loads(printed) == json.loads(api.content)
    assert list(json.loads(printed)) == list(json.loads(api.content))
    assert json.loads(printed)["kind"] == kind
    assert json.loads(printed)["rows"], kind


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
    # A required field has no default to move off, so its value comes from the samples and every
    # case carries it: a request without it is refused, not an info document.
    required: Params = {**REQUIRED_VALUES.get(kind, {})}
    cases: list[Params] = [{**required}]
    for name, field in model.model_fields.items():
        if name in required:
            continue
        if isinstance(field.default, bool):
            cases.append({**required, name: not field.default})
        elif isinstance(field.default, float):
            cases.append({**required, name: field.default * 1.5})
    for name, value in REQUIRED_VALUES.get(kind, {}).items():
        cases.append({**required, name: value * 1.5})
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
        # The literal too, so rewording the constant fails here and not only in test_calc (D-04).
        assert api_doc["warnings"][0] == (
            "ends modelled per L15: bolt tip chamfer, under-head fillet on an ISO 4014 plain "
            "shank, nut lead-in countersinks and face chamfers; nominal, not toleranced; "
            "not a product build")


def test_the_limits_heading_is_the_same_ascii_string_on_the_cli_and_the_api(
        capsys: pytest.CaptureFixture[str]) -> None:
    # INFO-02: byte for byte, semicolon and spaces included, on an exact ISO 262 size of each kind.
    heading = "limits for a bought part; this model is nominal and not toleranced"
    for kind, extra in (("bolt", []), ("nut", ["--clearance", "0.1"])):
        cli.main(["info", kind, *extra])
        cli_groups = {r["group"] for r in json.loads(capsys.readouterr().out)["rows"]}
        api = client.get(f"/api/{kind}/info", params={"clearance": 0.1} if extra else {})
        assert heading in cli_groups
        assert heading in {r["group"] for r in api.json()["rows"]}


def test_the_downloads_of_iso_4017_m8_x_70_are_one_sentence_on_the_cli_the_api_and_export(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # G-04-3, FRNT-05: the document, the model route and `screw export` read one rule, so the
    # entry the document refuses is the 422 the route answers and the line export prints.
    row = expand("bolt", "iso4017:M8x70")
    assert row is not None
    fields: Params = {**row}
    cli.main(["info", "bolt", "--preset", "iso4017:M8x70"])
    cli_downloads = json.loads(capsys.readouterr().out)["downloads"]
    api_downloads = client.get("/api/bolt/info", params=fields).json()["downloads"]
    assert cli_downloads == api_downloads
    (refused,) = [e for e in api_downloads if e["refusal"] is not None]
    assert (refused["format"], refused["quality"]) == ("stl", "fine")
    assert refused["refusal"].startswith("thread_length and length: ")

    route = client.get("/api/bolt/model.stl", params=fields)   # quality defaults to fine
    assert route.status_code == 422
    (detail,) = route.json()["detail"]
    assert (detail["type"], detail["msg"]) == ("fine_stl_cap", refused["refusal"])

    out = tmp_path / "x.stl"
    with pytest.raises(SystemExit) as stop:
        cli.main(["export", "bolt", "--preset", "iso4017:M8x70", "-o", str(out)])
    assert stop.value.code == 2
    assert capsys.readouterr().err == f"error: {refused['refusal']}\n"
    assert not out.exists()


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_no_flag_is_a_value_and_agrees_with_the_omitted_default(
        kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    # `--no-x` is a real value (False), not "not given", and agrees with the omitted default.
    required = [word for name, value in REQUIRED_VALUES.get(kind, {}).items()
                for word in (_flag(name), repr(value))]
    cli.main(["info", kind, *required])
    default_doc = capsys.readouterr().out
    cli.main(["info", kind, *required, "--no-left-hand"])
    assert capsys.readouterr().out == default_doc


@pytest.mark.parametrize("kind", list(KINDS))
def test_every_row_key_is_unread_by_name_in_the_ui(
        kind: str, part_of: Callable[[str], FastenerParams]) -> None:
    keys = [row.key for row in derive(part_of(kind)).rows]
    assert keys, "derive() produced no rows to check"
    assert _field_literals(APP_JS, keys) == []


def test_the_row_keys_of_an_iso_4014_match_are_unread_by_name_in_the_ui() -> None:
    # An ISO 4014 match adds b, lg_max and ls_min to the default document's keys (D-17).
    m10x80 = KINDS["bolt"].model_validate(
        {"d": 10, "pitch": 1.5, "length": 80, "s": 16, "k": 6.4, "thread_length": 26})
    keys = [row.key for row in derive(m10x80).rows]
    assert {"b", "lg_max", "ls_min"} <= set(keys)
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
#
# Plan 03-05 replaced three `.value` spellings with the helper forms (rule 29 names the same
# list): a checkbox's `.value` is the constant "on", so a control is read and written only
# through read() and write(), and the boolean branch of buildForm is what builds one (D-09).
PINNED_STATEMENTS = [
    "fetch('api/kinds')",
    "for (const [name, prop] of Object.entries(schema.properties)) {",
    "fields.set(name, { input, wrap, title });",
    "for (const [name, { input }] of fields) write(input, h.get(name) ?? defaults[name]);",
    "q.set(name, value)",
    "const kind = h.get('kind') ?? kinds.default;",
    "if (currentKind !== kinds.default) hashQ.set('kind', currentKind);",
    "for (const row of info.rows) {",
    "Number(value) !== Number(defaults[name])",
    "prop.type === 'boolean'",
    "input.type = 'checkbox'",
    "String(input.checked)",
    "input.checked = String(v) === 'true'",
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


@pytest.mark.parametrize("kind", list(KINDS))
def test_the_form_has_a_fieldset_per_group_in_first_seen_order(kind: str) -> None:
    # Rule 1: one fieldset per group in first-seen order, so `left_hand` (declared between
    # pitch and length) opens a `Thread` fieldset after `Size` and `length` stays in `Size`; the
    # bolt's `s` and `k` open a `Head` fieldset last (04-03); the nut's `s` and `m` open `Nut`
    # and its `clearance` opens `Pair` (05-04).
    properties = client.get("/api/schema", params={"kind": kind}).json()["properties"]
    groups = list(dict.fromkeys(prop["group"] for prop in properties.values()))
    assert groups == {"bolt": ["Size", "Thread", "Head"],
                      "nut": ["Size", "Thread", "Nut", "Pair"]}[kind]
    assert properties["left_hand"]["type"] == "boolean"
    assert properties["left_hand"]["default"] is False


def test_the_ui_refuses_a_link_it_cannot_honour() -> None:
    # D-10 (01-UI-SPEC rule 10): a repeated, foreign or unreadable hash key is refused like an
    # unknown kind -- same clearing, a message naming it, nothing builds -- never dropped,
    # defaulted or rewritten away. Source assertions, since no browser is in the gate (L01).
    source = _squash(APP_JS)
    repeated = _squash(
        "if (seen.has(k)) return refuseLink(`The link names \"${k}\" more than once.`);")
    for statement in (
        repeated,
        _squash("k !== 'kind' && !fields.has(k)"),
        _squash("given !== 'true' && given !== 'false'"),
        _squash("given !== null && read(input) === ''"),
        _squash("`Unreadable value for \"${name}\": \"${given}\".`"),
    ):
        assert statement in source, statement
    assert "Unknown field " in APP_JS
    assert "Unknown fields " in APP_JS
    # `#d=` names a field with an empty value; the API answers `?d=` with a 422, so the page may
    # not exempt it and open the default part (WR-01).
    assert "given !== ''" not in source
    # The repeat check runs first: `#kind=bolt&kind=x` must be refused, not read as bolt.
    kind_lookup = _squash("const kind = h.get('kind') ?? kinds.default;")
    assert source.index(repeated) < source.index(kind_lookup)
    # One helper serves the unknown kind and the three new cases, and it clears everything.
    helper = re.search(r"function refuseLink\(message\) \{(.*?)\n\}", APP_JS, re.DOTALL)
    assert helper is not None
    for statement in ("clearForm();", "clearPicker();", "currentKind = null;",
                      "kindSelect.selectedIndex = -1;", "$('#dims').replaceChildren();",
                      "setDownloads(null);"):
        assert statement in helper.group(1), statement
    assert APP_JS.count("refuseLink(") >= 5  # the definition and the four refusals


def test_the_ui_keeps_the_warnings_of_the_mesh_on_screen() -> None:
    # D-11 (01-UI-SPEC rules 15 and 24): the warning is the honest label on the part the user
    # is still looking at, so it outlives a failed update and a refused link. Warnings belong
    # to a mesh, not to the last info fetch: that document may describe a part whose STL then
    # failed, so it only becomes the mesh's warnings where the mesh is replaced.
    source = _squash(APP_JS)
    assert "pendingWarnings = info.warnings ?? [];" in source
    assert source.count("meshWarnings = pendingWarnings") == 1
    show = re.search(r"function showModel\(buffer\) \{(.*?)\n\}", APP_JS, re.DOTALL)
    assert show is not None
    assert "meshWarnings = pendingWarnings;" in show.group(1)
    assert source.count("mesh ? meshWarnings : []") >= 3
    # Every call that shows an error names the warnings with it; the startup failure has no
    # mesh and is the only one that shows none.
    bare = [line for line in APP_JS.splitlines()
            if "showMessages(" in line and "function showMessages" not in line
            and "meshWarnings" not in line and "pendingWarnings" not in line]
    assert len(bare) == 1
    assert "Could not load the part kinds and schema" in bare[0]


def test_the_ui_prints_the_numbers_as_sent_under_the_designation_and_the_groups() -> None:
    # D-19, D-17 (01-UI-SPEC rules 22 and 23): the page writes `String(row.value)` and rounds
    # nowhere, so a valid 0.0004 reads 0.0004 and not `0 mm`; the heading is the server's
    # designation and each group heading the server's `group`, in first-seen order.
    source = _squash(APP_JS)
    assert "String(row.value)" in source
    for rounding in ("toFixed", "toPrecision", "toLocaleString", "Intl.NumberFormat"):
        assert rounding not in APP_JS, rounding
    assert "fmt(" not in APP_JS  # the retired rounding helper
    assert "info.designation" in APP_JS
    assert "row.group" in APP_JS
    assert "for (const row of info.rows) {" in source


def test_an_info_row_drops_a_long_value_whole_under_its_label_instead_of_into_the_next_cell(
) -> None:
    # G-04-5: ISO 4017 M8 x 70's `15.011106998930268 mm` ran 55 px into `Head height` when the
    # row kept its value on the label's line. Full precision is by design (L02, D-19), so the
    # row gives, never the number: it wraps, the label keeps half of it and a value that does
    # not fit beside it drops whole under it. No browser runs in the gate (L01), so the
    # stylesheet is read as text and the measurement lives in 04-17-PLAN.md.
    assert _info_row_problems(STYLE_CSS) == []
    # The plain space before the unit is the first break the value's last-resort guard takes.
    assert "${String(row.value)} ${row.unit}" in APP_JS


def test_the_info_row_check_has_teeth() -> None:
    dl = ("#dims dl { display: grid;"
          " grid-template-columns: repeat(auto-fill, minmax(12.5rem, 1fr));"
          " gap: .15rem 1.5rem; margin: 0; }\n")
    row = ("#dims div { display: flex; justify-content: space-between; gap: .75rem;"
           " padding: .15rem 0; border-bottom: 1px dashed var(--line); }\n")
    dt = "#dims dt { color: var(--muted); }\n"
    plan_01_04 = dl + row + dt + (
        "#dims dd { margin: 0; font-variant-numeric: tabular-nums; white-space: nowrap; }\n")
    found = _info_row_problems(plan_01_04)
    assert {"#dims div", "#dims dt", "#dims dd", "nowrap"} <= set(found)
    # Debug V4: wrapping text inside the one-line row split `14.38 mm` as `14.3 / 8 mm`.
    v4 = dl + row + dt + ("#dims dd { margin: 0; font-variant-numeric: tabular-nums;"
                          " white-space: normal; overflow-wrap: anywhere; }\n")
    assert "#dims div" in _info_row_problems(v4)
    ellipsis = "#dims dd { overflow: hidden; text-overflow: ellipsis; }"
    clipped = _info_row_problems(STYLE_CSS + ellipsis)
    assert {"#dims dd", "clip"} <= set(clipped)
    # A deleted rule is reported, not skipped.
    cut = re.sub(r"#dims dt \{[^}]*\}", "", STYLE_CSS)
    assert cut != STYLE_CSS
    assert "#dims dt" in _info_row_problems(cut)
    # Comments cannot satisfy or fail the pin.
    assert _info_row_problems("/* #dims dd { white-space: nowrap; } */" + STYLE_CSS) == []


def test_the_ui_keeps_the_notes_of_the_mesh_on_screen_like_its_warnings() -> None:
    # D-20 (01-UI-SPEC rules 15 and 24): a note describes the part like a warning does, so it
    # is copied to the mesh where the mesh is replaced and shown beside every error.
    source = _squash(APP_JS)
    assert "pendingNotes = info.notes ?? [];" in source
    assert source.count("meshNotes = pendingNotes") == 1
    show = re.search(r"function showModel\(buffer\) \{(.*?)\n\}", APP_JS, re.DOTALL)
    assert show is not None
    assert "meshNotes = pendingNotes;" in show.group(1)
    assert source.count("mesh ? meshNotes : []") >= 3
    # Wherever the warnings of the mesh are named the notes are named with them.
    for line in APP_JS.splitlines():
        if "mesh ? meshWarnings : []" in line:
            assert "mesh ? meshNotes : []" in line, line


def _function_body(name: str) -> str:
    found = re.search(rf"function {name}\([^)]*\) \{{(.*?)\n\}}", APP_JS, re.DOTALL)
    assert found is not None, name
    return found.group(1)


def test_the_ui_builds_its_picker_from_the_catalogue_and_writes_fields_only() -> None:
    # D-12, D-10 (01-UI-SPEC picker rules): the three selects come from /api/presets with no
    # field name, a pick writes the row's fields through write() and builds at once.
    source = _squash(APP_JS)
    assert "api/presets?kind=" in APP_JS
    assert "catalogue.axes" in APP_JS
    assert "entry.picker" in APP_JS
    assert "Object.entries(entry.fields)" in APP_JS
    assert "write(fields.get(name).input, value)" in source
    pick = _function_body("pick")
    assert "update()" in pick
    # Only the select values and the picked row are read, never a literal for a field.
    assert _field_literals(APP_JS, list(KINDS["bolt"].model_fields)) == []


def test_the_badge_composes_from_the_status_and_the_display_and_the_basis_stays_in_the_page(
) -> None:
    # D-09, TABL-06: `matches X`, `custom, based on X`, `custom`; the preset id never enters a
    # link, a query or a request, and the basis is cleared by navigate().
    assert "`matches ${preset.display}`" in APP_JS
    assert "`custom, based on ${presetBasis.display}`" in APP_JS
    assert "'custom'" in APP_JS
    assert "preset.status" in APP_JS
    # Every key read off a preset member of the info document: the badge uses the first two, the
    # id only finds the catalogue row for the selects.
    assert set(re.findall(r"\bpreset\.(\w+)", APP_JS)) == {"status", "display", "id"}
    for name in ("partQuery", "writeHash"):
        assert "presetBasis" not in _function_body(name), name
    assert "presetBasis = null;" in _function_body("navigate")
    # No request URL is built from the basis or a row id: the only fetches are the ones below.
    assert re.findall(r"fetch\(`([^`]*)`", APP_JS) == [
        "api/schema?kind=${encodeURIComponent(kind)}",
        "api/presets?kind=${encodeURIComponent(kind)}",
        "api/${currentKind}/info?${q}",
        "api/${currentKind}/model.stl?${stlQ}",
    ]
    assert "location.hash" not in _function_body("pick")


def test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly() -> None:
    # G-05-1, D-12, D-09, L02: a nut with its clearance empty answers every info request with a
    # 422 that carries no preset, and blank selects after that undid every pick. With no info
    # document the selects show the first catalogue row the form holds exactly (the rule and
    # the order of calc.presets.match), else blank; the badge stays empty (it reads a document).
    row_of_fields = _squash(_function_body("rowOfFields"))
    assert "catalogue.rows.find((row) => Object.entries(row.fields).every(" in row_of_fields
    assert "read(fields.get(name).input)" in row_of_fields
    assert "!== ''" in row_of_fields  # an empty control is no value: Number('') is 0
    assert "Number(held) === value" in row_of_fields  # exact, as the server compares
    assert "Math." not in row_of_fields  # no tolerance, no nearest row
    show_match = _squash(_function_body("showMatch"))
    assert "preset === null ? rowOfFields() : undefined" in show_match
    assert "if (preset === null) badge.textContent = '';" in show_match
    # The definition and the one call: nothing else reaches the match.
    assert APP_JS.count("rowOfFields()") == 2
    # Every failure still goes through showMatch(null).
    assert "showMatch(null);" in _function_body("update")
    # The match never reaches the link (D-09).
    for name in ("partQuery", "writeHash"):
        assert "rowOfFields" not in _function_body(name), name


def test_the_ui_builds_nodes_from_text_only() -> None:
    assert "textContent" in APP_JS
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML"):
        assert sink not in APP_JS, sink


def test_the_ui_builds_both_download_links_from_the_info_document_and_names_no_quality() -> None:
    # G-04-3, D-10, D-09, L02: the page links, per format, the first download the server does not
    # refuse, in the server's order, and holds no format name, no quality preference and no
    # warning text of its own. The state never enters the shareable link. Source assertions (L01).
    assert "setDownloads(q, info.downloads)" in _function_body("update")
    assert "downloadLinks" in APP_JS
    assert set(re.findall(r"\binfo\.(\w+)", APP_JS)) == {
        "designation", "rows", "warnings", "notes", "preset", "downloads", "counterpart"}
    assert set(re.findall(r"\bdownload\.(\w+)", APP_JS)) == {"format", "quality", "refusal"}
    body = _function_body("setDownloads")
    assert "qs.set('quality', download.quality)" in body
    assert "title" in body
    assert "`${label} (${download.quality})`" in APP_JS
    # The only quality the page names is the preview mesh it fetches; no format, no other
    # quality, no spelling of the cap or of the warning.
    assert len(re.findall(r"""(['"`])preview\1""", APP_JS)) == 1
    for word in ("fine", "stl", "step"):
        assert re.findall(rf"""(['"`]){word}\1""", APP_JS) == [], word
    assert APP_JS.count("info.warnings") == 1   # the pendingWarnings line, nothing matches a text
    assert "fine_stl_cap" not in APP_JS
    assert "fine STL" not in APP_JS
    for name in ("partQuery", "writeHash"):
        assert "quality" not in _function_body(name), name
        assert "download" not in _function_body(name), name


def _download_labels() -> dict[str, str]:
    """The static label of each `id="dl-<format>"` anchor of index.html, by format."""
    html = (STATIC / "index.html").read_text()
    return dict(re.findall(r'<a id="dl-(\w+)"[^>]*>([^<]*)</a>', html))


def _links_by_rule_17(labels: dict[str, str], downloads: list[dict[str, str | None]]
                      ) -> dict[str, str]:
    """Rule 17 of 01-UI-SPEC.md as the page applies it: per format the first entry whose refusal
    is null, labelled `<static label> (<quality>)` only when an earlier entry of that format was
    refused. A format with no served entry has no link."""
    links: dict[str, str] = {}
    refused: set[str] = set()
    for entry in downloads:
        fmt = str(entry["format"])
        if fmt in links:
            continue
        if entry["refusal"] is not None:
            refused.add(fmt)
            continue
        links[fmt] = labels[fmt] + (f" ({entry['quality']})" if fmt in refused else "")
    return links


def test_the_download_labels_are_static_and_the_refused_fine_stl_reads_download_stl_preview(
) -> None:
    # G-04-3: index.html holds one anchor per format the model route serves, with the static
    # labels; the page composes the quality after the label and holds no label of its own.
    route = client.get("/openapi.json").json()["paths"]["/api/bolt/model.{fmt}"]["get"]
    (fmt_param,) = [p for p in route["parameters"] if p["name"] == "fmt"]
    labels = _download_labels()
    assert set(labels) == set(fmt_param["schema"]["enum"])
    assert labels == {"stl": "Download STL", "step": "Download STEP"}

    row = expand("bolt", "iso4017:M8x70")
    assert row is not None
    fields: Params = {**row}
    capped = client.get("/api/bolt/info", params=fields).json()["downloads"]
    assert _links_by_rule_17(labels, capped) == {
        "stl": "Download STL (preview)", "step": "Download STEP"}
    served = client.get("/api/bolt/info").json()["downloads"]
    assert _links_by_rule_17(labels, served) == labels
    # A format whose every entry is refused has no link: the page keeps it disabled.
    assert _links_by_rule_17(labels, [{**e, "refusal": "x"} for e in capped
                                      if e["format"] == "stl"]) == {}


def _repeat_argvs(kind: str, name: str) -> list[list[str]]:
    """Every way to give one field's flag twice (the CLI keeps the last silently, D-12)."""
    flag = _flag(name)
    if _is_bool(kind, name):
        no = "--no-" + name.replace("_", "-")
        return [[flag, no], [flag, flag], [no, no]]
    return [[flag, "5", flag, "6"]]


def _duplicate(name: str) -> dict[str, object]:
    return {"loc": ["query", name], "type": "duplicate", "msg": f"{name} was given more than once."}


@pytest.mark.parametrize("kind", list(KINDS))
def test_a_repeated_parameter_is_refused_naming_it(
        kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    # API side (D-12): the repeat is refused before the query model judges either value, on
    # every route of the kind, and the 422 names the key.
    for name in KINDS[kind].model_fields:
        twice: Pairs = ([(name, "true"), (name, "false")] if _is_bool(kind, name)
                        else [(name, "5"), (name, "6")])
        for path in (f"/api/{kind}/info", f"/api/{kind}/model.stl"):
            res = client.get(path, params=twice)
            assert res.status_code == 422, (path, name)
            assert res.json()["detail"] == [_duplicate(name)], (path, name)
    # CLI side: the same refusal, exit 2 naming the flag.
    for name in KINDS[kind].model_fields:
        for given in _repeat_argvs(kind, name):
            with pytest.raises(SystemExit) as stop:
                cli.main(["info", kind, *given])
            assert stop.value.code == 2, given
            assert _flag(name) in capsys.readouterr().err, given
    # export's own options are refused the same way.
    for given in (["--quality", "fine", "--quality", "preview"],
                  ["--format", "stl", "--format", "step"],
                  ["--preset", "iso4017:M6x20", "--preset", "iso4017:M6x25"],
                  ["-o", "a.stl", "-o", "b.stl"]):
        with pytest.raises(SystemExit) as stop:
            cli.main(["export", kind, "-o", "x.stl", *given])
        assert stop.value.code == 2, given
        assert given[0] in capsys.readouterr().err, given


def test_a_thread_length_conflict_is_the_same_words_on_the_api_and_the_cli(
        capsys: pytest.CaptureFixture[str]) -> None:
    """D-25, FRNT-05: one rule, so the 422 `msg` and the CLI `error:` line are the same text."""
    for length, thread_length in ((10, 30), (10, 10.00001), (0.5, 0.75)):
        res = client.get("/api/bolt/info", params={"length": length,
                                                   "thread_length": thread_length})
        assert res.status_code == 422, (length, thread_length)
        [detail] = res.json()["detail"]
        assert detail["type"] == "thread_length_conflict"
        with pytest.raises(SystemExit) as stop:
            cli.main(["info", "bolt", "--length", str(length),
                      "--thread-length", str(thread_length)])
        assert stop.value.code == 2
        assert capsys.readouterr().err == f"error: {detail['msg']}\n"


@pytest.mark.parametrize(("kind", "other", "params"), [
    ("bolt", "nut", {}), ("bolt", "nut", {"d": 6.5}),
    ("nut", "bolt", {"clearance": 0.1}), ("nut", "bolt", {"clearance": 0.1, "d": 6.5})])
def test_the_cli_and_the_api_print_the_same_counterpart(
        kind: str, other: str, params: Params, capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["info", kind, *[a for k, v in params.items() for a in (_flag(k), repr(v))]])
    cli_doc = json.loads(capsys.readouterr().out)
    api_doc = client.get(f"/api/{kind}/info", params=params).json()
    assert cli_doc["counterpart"] == api_doc["counterpart"]
    assert cli_doc["counterpart"]["kind"] == other
    assert cli_doc["warnings"] == api_doc["warnings"]
    assert "clearance" not in cli_doc["counterpart"]["fields"]


def test_the_ui_reads_the_counterpart_by_kind_and_fields_only_and_names_no_kind() -> None:
    # D-01, D-02, T-05-22: the link is composed from `info.counterpart` alone, as text in a hash
    # fragment (never innerHTML), and the page quotes no kind, field or label of its own.
    assert set(re.findall(r"\bcounterpart\.(\w+)", APP_JS)) == {"kind", "fields"}
    body = _function_body("showCounterpart")
    assert "new URLSearchParams({ kind: counterpart.kind, ...counterpart.fields })" in body
    assert "counterpartLink.href = `#${q}`;" in body
    assert "`Matching ${counterpart.kind}`" in body
    assert "counterpartLink.hidden = counterpart === null;" in body
    assert "showCounterpart(info.counterpart ?? null);" in _function_body("renderInfo")
    # A failed update and a refused link take the link away with the panel it belongs to.
    assert "showCounterpart(null);" in _function_body("refuseLink")
    assert "showCounterpart(null);" in _function_body("update")
    for kind_name in KINDS:
        assert re.findall(rf"""(['"`]){kind_name}\1""", APP_JS) == [], kind_name
    html = (STATIC / "index.html").read_text()
    assert re.search(r'<p id="badge"[^>]*></p>\s*<a id="counterpart" hidden></a>', html)


def test_a_field_with_no_default_is_written_empty_never_as_the_word_undefined() -> None:
    # RESEARCH P9b: the nut's clearance has no default, so `defaults[name]` is undefined.
    assert "else input.value = v ?? '';" in _function_body("write")
    assert "input.value = v;" not in APP_JS


def test_a_kind_change_drops_the_old_mesh_and_what_described_it() -> None:
    # R10, T-05-23 (05-OWNER-READS.md): a nut with no clearance typed builds nothing, so the old
    # bolt mesh, its warnings and its notes must not stay on screen under "last valid part".
    nav = _squash(_function_body("navigate"))
    assert nav.index("dropMesh();") < nav.index("await buildForm(kind)")
    assert nav.index("if (kind !== currentKind) {") < nav.index("dropMesh();")
    drop = _function_body("dropMesh")
    for statement in ("scene.remove(mesh, edges);", "mesh = null;", "edges = null;",
                      "meshWarnings = [];", "meshNotes = [];", "pendingWarnings = [];",
                      "pendingNotes = [];", "fitted = false;"):
        assert statement in drop, statement
    assert APP_JS.count("dropMesh()") == 2  # the definition and the one call on a kind change


def test_every_row_key_of_the_nut_and_pair_documents_is_unread_by_name_in_the_ui() -> None:
    # Plans 05-04 to 05-09 added these keys; `m` and `clearance` are fields too (05-10).
    exact = KINDS["nut"].model_validate({**REQUIRED_VALUES["nut"]})
    m18 = KINDS["nut"].model_validate(
        {**REQUIRED_VALUES["nut"], "d": 18.0, "pitch": 2.5, "s": 27.0, "m": 15.8})
    keys = {row.key for p in (exact, m18) for row in derive(p).rows}
    assert {"pitch_diameter", "minor_diameter", "m_max", "mw_min", "D1_min", "D2_max",
            "flank_gap", "axial_play", "nut_pitch_diameter", "engagement_turns"} <= keys
    assert _field_literals(APP_JS, [*keys, "m", "clearance"]) == []


def test_download_name_marks_only_the_preview_stl() -> None:
    # D-22, R9: the coarse mesh says so in its name; the fine STL and the STEP (which has no
    # tessellation) keep the plain slug.
    slug = BoltParams().slug()
    assert download_name(BoltParams(), "stl", "preview") == f"{slug}_preview.stl"
    assert download_name(BoltParams(), "stl", "fine") == f"{slug}.stl"
    assert download_name(BoltParams(), "step", "preview") == f"{slug}.step"
    assert download_name(BoltParams(), "step", "fine") == f"{slug}.step"


@pytest.mark.parametrize("kind", sorted(KINDS))
@pytest.mark.parametrize(("fmt", "quality"), [
    ("stl", "preview"), ("stl", "fine"), ("step", "preview"), ("step", "fine")])
def test_the_api_header_and_the_cli_name_a_download_alike(
        kind: str, fmt: str, quality: str, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    # FRNT-05 parity for the file name: `-o <directory>` writes the name the Content-Disposition
    # header carries. The CLI side is stubbed (its bytes are not under test, and the API side has
    # just built the same part), so the check costs one build per cell, not two.
    values = REQUIRED_VALUES.get(kind, {})
    r = client.get(f"/api/{kind}/model.{fmt}", params={**values, "quality": quality})
    assert r.status_code == 200
    header = re.fullmatch(r'attachment; filename="([^"]*)"', r.headers["content-disposition"])
    assert header, r.headers["content-disposition"]

    def stub(*_: object) -> bytes:
        return b"x"

    monkeypatch.setattr("screw.solid.export", stub)
    flags = [item for k, v in values.items() for item in (_flag(k), str(v))]
    cli.main(["export", kind, "-o", str(tmp_path), "--format", fmt, "--quality", quality, *flags])
    assert [f.name for f in tmp_path.iterdir()] == [header.group(1)]
