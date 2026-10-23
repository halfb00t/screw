import {
  Color, DirectionalLight, EdgesGeometry, GridHelper, HemisphereLight,
  LineBasicMaterial, LineSegments, Mesh, MeshStandardMaterial, PerspectiveCamera,
  Scene, Vector3, WebGLRenderer, OrbitControls, STLLoader,
} from './vendor/three.bundle.min.js';

const $ = (sel) => document.querySelector(sel);
const form = $('#params');
const kindSelect = $('#kind');
let kinds = { default: null, kinds: [] }; // the /api/kinds body
let currentKind = null; // the kind the last finished navigation loaded (form and picker); null while none is valid
const fields = new Map(); // name -> { input, wrap, title }
let defaults = {};
// The kind of the controls on screen, set with them and with defaults in buildForm. currentKind lags it
// for the whole catalogue fetch of a kind switch, and a value typed in that window was remembered under
// the old kind and reached the bolt's link (review WR-07, 2026-10-21, reproduced in a headless browser).
let formKind = null;
const picker = $('#picker');
const pickerLegend = picker.querySelector('legend');
const badge = $('#badge');
const counterpartLink = $('#counterpart');
const pickerSelects = []; // one select per catalogue axis, in axis order
let catalogue = null; // the /api/presets body for currentKind; null while there is no picker
let shownPreset = null; // the preset member of the newest info document, null after a failure
// The catalogue row the part last matched or was picked from, for the `custom, based on`
// badge. Page-session state only (D-09): navigate() clears it, and no request, hash or query
// ever reads it, so a link carries millimetres and never a preset.
let presetBasis = null;
// Per kind, the value last typed in this page into each field that has no default (none does since
// L17; the memory stays as the generic rule, R8), kept so the matching-part link can carry it
// (owner ruling 2026-10-21, L15 amendment, G-05-3). Typed means an input event: a link, Reset or a
// kind change never writes it, so the page never carries a number the user did not type (L02).
// Reset or a navigation that leaves the field holding another value forgets it (owner ruling
// 2026-10-21, WR-08). Page memory only, so a reload or a new tab forgets it. No request, hash or
// download ever reads it.
const lastTyped = new Map();
// Warnings belong to a mesh, not to the last info fetch (D-11). update() fetches info first,
// so by the time a model.stl request fails the newest info document describes the part that
// did not build while the mesh on screen is an older one. A rendered info document waits in
// pendingWarnings and becomes the mesh's warnings only where showModel replaces the mesh;
// every error shows meshWarnings below it, because the warning is the honest label on the
// part the user is still looking at (the standing warning, D-06). The notes (D-20) follow the
// same rule: they describe the part, so they stay with the mesh and not with the last fetch.
let pendingWarnings = [];
let meshWarnings = [];
let pendingNotes = [];
let meshNotes = [];

// Nothing here knows a field name, a row key or a kind's label: the form, the hash, the
// info panel and the download links are all read off what the API sends, so a new
// registered kind needs no edit in this file (D-10; tests/test_parity.py pins it).
// A checkbox's .value is the constant "on", so every read and write of a control goes through
// these two: a checkbox reads as 'true' or 'false' and is written from either, any other
// control by its value (D-09). The link then carries `left_hand=true` and nothing else.
// A field with no default has `undefined` for one: it is written as an empty control, never as the
// word "undefined" (RESEARCH P9b).
const read = (input) => (input.type === 'checkbox' ? String(input.checked) : input.value);
function write(input, v) {
  if (input.type === 'checkbox') input.checked = String(v) === 'true';
  else input.value = v ?? '';
}
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// ---------------------------------------------------------------- kinds and form

async function loadKinds() {
  const res = await fetch('api/kinds');
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  kinds = await res.json();
  kindSelect.replaceChildren(...kinds.kinds.map((k) => new Option(k, k)));
}

// A schema fetch an older navigation started must not rebuild the form after a newer one
// has asked for another kind (Pitfall 6). Every navigate() bumps this; buildForm() returns
// false, untouched DOM, when it was overtaken.
let formSeq = 0;

function clearForm() {
  form.replaceChildren();
  fields.clear();
  defaults = {};
  formKind = null;
}

function clearPicker() {
  picker.hidden = true;
  picker.replaceChildren(pickerLegend);
  pickerSelects.length = 0;
  catalogue = null;
  shownPreset = null;
  badge.textContent = '';
}

async function buildForm(kind) {
  const mine = formSeq;
  const res = await fetch(`api/schema?kind=${encodeURIComponent(kind)}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  const schema = await res.json();
  if (mine !== formSeq) return false;
  clearForm();
  formKind = kind;
  const groups = new Map();

  for (const [name, prop] of Object.entries(schema.properties)) {
    defaults[name] = prop.default;
    const group = prop.group ?? 'Other';
    if (!groups.has(group)) {
      const fs = document.createElement('fieldset');
      const legend = document.createElement('legend');
      legend.textContent = group;
      fs.append(legend);
      form.append(fs);
      groups.set(group, fs);
    }

    let input;
    if (prop.enum) {
      input = document.createElement('select');
      for (const v of prop.enum) input.add(new Option(v, v));
    } else if (prop.type === 'boolean') {
      input = document.createElement('input');
      input.type = 'checkbox';
    } else {
      input = document.createElement('input');
      input.type = 'number';
      input.inputMode = 'decimal';
      // HTML min is inclusive, so an exclusive bound must not set it: the browser would
      // accept the bound itself and the server would then refuse it. The 422 speaks for
      // exclusiveMinimum (Pitfall 5).
      if (prop.minimum !== undefined) input.min = prop.minimum;
      if (prop.maximum !== undefined) input.max = prop.maximum;
      input.step = prop.step ?? (prop.type === 'integer' ? 1 : 'any');
    }
    input.name = name;

    const wrap = document.createElement('label');
    wrap.className = 'field';
    wrap.title = prop.description ?? '';
    const title = prop.title ?? name;
    const nameEl = Object.assign(document.createElement('span'), { className: 'name', textContent: title });
    const unit = Object.assign(document.createElement('span'), { className: 'unit', textContent: prop.unit ?? '' });
    const control = Object.assign(document.createElement('span'), { className: 'control' });
    control.append(input, unit);
    wrap.append(nameEl, control);
    if (prop.description) {
      wrap.append(Object.assign(document.createElement('small'), { textContent: prop.description }));
    }
    groups.get(group).append(wrap);
    fields.set(name, { input, wrap, title });
  }
  return true;
}

// ---------------------------------------------------------------- preset picker

/** The values of select `i` offered once the selects before it hold `earlier`, in catalogue order. */
function offered(i, earlier) {
  const values = new Set();
  for (const entry of catalogue.rows) {
    if (earlier.every((v, j) => entry.picker[j] === v)) values.add(entry.picker[i]);
  }
  return [...values];
}

/** Fill the selects with `picks` (blank strings for none); a select with no choice before it is empty. */
function showPicks(picks) {
  pickerSelects.forEach((select, i) => {
    const earlier = picks.slice(0, i);
    const values = earlier.every((v) => v !== '') ? offered(i, earlier) : [];
    select.replaceChildren(new Option('', ''), ...values.map((v) => new Option(v, v)));
    select.value = picks[i];
  });
}

/**
 * The selects and the badge follow the fields (D-12, D-09): the matching catalogue row when the
 * newest info document says exact, blank selects when it says custom. When no document arrived
 * (the update failed) the selects show the row the fields hold exactly, else blank, and the badge
 * is empty, because it reads only a document. The badge text composes from preset.status and
 * preset.display alone; the id only finds the row.
 *
 * Measured, UAT 2026-10-21 test 1 (G-05-1): a nut with its clearance empty answers every info
 * request with a 422 that carries no preset. Blank selects after that failure undid every pick:
 * the first Standard wrote the smallest row (diameter 2, pitch 0.4, width 4, height 1.6) and went
 * blank with Size empty, so the next size could not be picked.
 */
function showMatch(preset) {
  if (catalogue === null) return;
  shownPreset = preset;
  const exact = preset !== null && preset.status === 'exact';
  const entry = exact
    ? catalogue.rows.find((row) => row.id === preset.id)
    : preset === null ? rowOfFields() : undefined;
  showPicks(entry ? entry.picker : pickerSelects.map(() => ''));
  // The last exact match is the basis, not only a pick: after Reset, or after an edit that lands
  // on another row, a later edit is "based on" the row the part really was (never a guess, D-09).
  if (exact) presetBasis = preset;
  if (preset === null) badge.textContent = '';
  else if (exact) badge.textContent = `matches ${preset.display}`;
  else badge.textContent = presetBasis ? `custom, based on ${presetBasis.display}` : 'custom';
}

// rowOfFields is the server's rule and order (calc.presets.match and match_nut: exact float
// equality, first row in catalogue order), so the page never names a row the server would not,
// and never a nearest one (L02). An empty control is no value: Number('') is 0 (rule 35).
/** The first catalogue row whose every field the form holds exactly, or undefined. */
function rowOfFields() {
  return catalogue.rows.find((row) => Object.entries(row.fields).every(([name, value]) => {
    // A row names a field the form lacks only when the catalogue is another kind's. navigate takes the
    // old catalogue off screen before a kind switch fetches the new form (review WR-09), so this is the
    // second line: a control that is not there does not hold the row and never throws (review IN-06).
    const control = fields.get(name);
    if (control === undefined) return false;
    const held = read(control.input);
    return held !== '' && Number(held) === value;
  }));
}

/**
 * A change in select `changed` resolves to one complete row: later selects holding a blank or a
 * value no longer offered take their first offered value, then every field the row defines is
 * written through write() and the part builds at once. Fields the row does not define (the
 * handedness) are left as they are (D-12). A change to blank is no pick: the selects go back to
 * what the fields match.
 */
function pick(changed) {
  const picks = pickerSelects.map((select) => select.value);
  if (picks[changed] === '') return showMatch(shownPreset);
  for (let i = changed + 1; i < picks.length; i++) {
    const values = offered(i, picks.slice(0, i));
    if (!values.includes(picks[i])) picks[i] = values[0];
  }
  const entry = catalogue.rows.find((row) => row.picker.every((v, i) => v === picks[i]));
  if (!entry) return showMatch(shownPreset);
  showPicks(picks);
  for (const [name, value] of Object.entries(entry.fields)) write(fields.get(name).input, value);
  presetBasis = entry;
  return update();
}

function buildPicker() {
  pickerSelects.length = 0;
  const labels = catalogue.axes.map((axis, i) => {
    const select = document.createElement('select');
    select.addEventListener('change', () => pick(i));
    pickerSelects.push(select);
    const control = Object.assign(document.createElement('span'), { className: 'control' });
    control.append(select);
    const label = Object.assign(document.createElement('label'), { className: 'field' });
    label.append(Object.assign(document.createElement('span'), { className: 'name', textContent: axis }), control);
    return label;
  });
  picker.replaceChildren(pickerLegend, ...labels);
  picker.hidden = false;
  showPicks(pickerSelects.map(() => ''));
}

// The catalogue is fetched once per kind change, after the form and under the same guard: a
// response an older navigation started must not build a picker for another kind (Pitfall 6).
async function loadPresets(kind) {
  const mine = formSeq;
  const res = await fetch(`api/presets?kind=${encodeURIComponent(kind)}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  const body = await res.json();
  if (mine !== formSeq) return false;
  catalogue = body;
  buildPicker();
  return true;
}

/**
 * A link the page cannot honour is refused whole, the same way for an unknown kind, a key
 * given twice, a key the kind does not define and a value its control cannot hold: the form,
 * the panel and the downloads go, nothing builds, and the message names what was wrong.
 * Opening any other part than the one the link names would be a silent change (L02, D-10);
 * the API answers the same input with a 422 and the CLI with exit 2.
 */
function refuseLink(message) {
  clearForm();
  clearPicker();
  currentKind = null;
  kindSelect.selectedIndex = -1;
  $('#dims').replaceChildren();
  showCounterpart(null);
  setDownloads(null);
  setStatus('');
  showMessages([message], mesh ? meshWarnings : [], mesh ? meshNotes : []);
}

/**
 * Startup, hashchange and the kind selector all land here: read the kind and the field
 * values off the hash, rebuild the form when the kind changed, then build the part.
 * An omitted kind= means the registry's default kind, for good: a link already shared
 * must never re-point (D-09).
 */
async function navigate() {
  clearTimeout(debounce);
  inflight?.abort();
  ++seq;
  const mine = ++formSeq;
  presetBasis = null;
  const h = new URLSearchParams(location.hash.slice(1));
  // First, before the kind lookup: get() would answer for the first of two values and the
  // link would open a part it does not name (`#kind=bolt&kind=x`). The API refuses a
  // repeated key the same way (D-12).
  const seen = new Set();
  for (const k of h.keys()) {
    if (seen.has(k)) return refuseLink(`The link names "${k}" more than once.`);
    seen.add(k);
  }
  const kind = h.get('kind') ?? kinds.default;

  if (!kinds.kinds.includes(kind)) {
    return refuseLink(`Unknown kind "${kind}". Known kinds: ${kinds.kinds.join(', ')}.`);
  }

  if (kind !== currentKind || kind !== formKind) {
    // The mesh on screen belongs to the other kind: it goes now, so it is never shown as the new
    // kind's last valid part while the new kind's schema and first info are still loading (R10,
    // T-05-23).
    // The form is also rebuilt when the form on screen is not the link's kind: Back before a kind
    // switch's catalogue loaded leaves the overtaken navigation's form on screen while currentKind
    // still names the kind the link asks for. Measured: a bolt built under the nut's controls, then
    // a silent page once update() waits for the form (owner choice 2026-10-21, plan 05-23).
    // The old kind's form and picker go with the mesh, before the new schema is fetched. Measured,
    // left live: a pick in the old picker wrote a bolt row's diameter and pitch into the nut's
    // controls once the nut's form arrived, then threw on a field the nut lacks (review WR-09,
    // 2026-10-21); during the schema fetch it ran the bolt's update, so the nut opened over a
    // rebuilt bolt as the last valid part (measured, plan 05-24). formKind stays null until the new
    // form is built, so update waits, and a navigation that overtakes this one rebuilds the kind it
    // names (the condition above).
    // The panel, the matching-part link, the downloads and the status describe the old part too, so
    // they go with it. Measured, left on screen: the bolt's rows, its Matching link and two live bolt
    // downloads stayed beside the blank form while the nut loaded, and for good when its schema fetch
    // failed (review WR-10, 2026-10-21); a failed bolt's status still claimed the last valid part over
    // the empty canvas (measured, plan 05-25).
    dropMesh();
    clearForm();
    clearPicker();
    $('#dims').replaceChildren();
    showCounterpart(null);
    setDownloads(null);
    setStatus('');
    try {
      if (!(await buildForm(kind))) return;
      if (!(await loadPresets(kind))) return;
    } catch (err) {
      // A navigation that overtook this one owns the page: refusing here wiped the bolt the user had
      // switched back to (measured, plan 05-25). Otherwise a form without its schema or its picker is
      // half a page, so the switch is refused whole, like a link the page cannot honour. That deselects
      // the selector, so picking the same kind again retries. Measured before: a failed schema fetch
      // left a blank form under a selector that read the new kind, and a select reports no change when
      // the option it shows is picked again (review WR-10, 2026-10-21).
      if (mine !== formSeq) return;
      return refuseLink(`Could not load the part: ${err.message}`);
    }
    currentKind = kind;
  }
  // `kind` is the only key that is not a field, and the only one the page writes besides them.
  const foreign = [...seen].filter((k) => k !== 'kind' && !fields.has(k));
  if (foreign.length > 0) {
    const names = foreign.map((k) => `"${k}"`).join(', ');
    const unknown = foreign.length === 1 ? `Unknown field ${names}` : `Unknown fields ${names}`;
    return refuseLink(`${unknown} for kind "${kind}". Known fields: ${[...fields.keys()].join(', ')}.`);
  }
  kindSelect.value = kind;
  for (const [name, { input }] of fields) write(input, h.get(name) ?? defaults[name]);
  for (const { input } of fields.values()) forgetUntyped(input);
  // A checkbox holds only true or false. Any other control hands back '' for a value it
  // cannot hold (a number input given "abc") or was given empty (`#d=`), and partQuery() would
  // skip it and open the default part under a link that named the field. The API answers `?d=`
  // with a 422, so a present key that reads back empty is refused, not exempted.
  for (const [name, { input }] of fields) {
    const given = h.get(name);
    const unreadable = input.type === 'checkbox'
      ? given !== null && given !== 'true' && given !== 'false'
      : given !== null && read(input) === '';
    if (unreadable) return refuseLink(`Unreadable value for "${name}": "${given}".`);
  }
  await update();
}

/** Query string with only the parameters that differ from the defaults. */
function partQuery() {
  const q = new URLSearchParams();
  for (const [name, { input }] of fields) {
    const value = read(input);
    if (value === '') continue;
    // 6.0 and 6 are the same default; a string compare would put the first in the link.
    // A checkbox compares as a string against 'false', so only a checked box is written.
    const changed = input.type === 'number'
      ? Number(value) !== Number(defaults[name])
      : value !== String(defaults[name]);
    if (changed) q.set(name, value);
  }
  return q;
}

function writeHash(q) {
  const hash = q.toString();
  history.replaceState(null, '', hash ? `#${hash}` : location.pathname + location.search);
}

// ---------------------------------------------------------------- messages

function showMessages(errors = [], warnings = [], notes = []) {
  const box = $('#messages');
  box.replaceChildren(
    ...errors.map((t) => Object.assign(document.createElement('p'), { className: 'error', textContent: t })),
    ...warnings.map((t) => Object.assign(document.createElement('p'), { className: 'warning', textContent: t })),
    ...notes.map((t) => Object.assign(document.createElement('p'), { className: 'note', textContent: t })),
  );
}

async function problems(res) {
  try {
    const body = await res.json();
    if (!Array.isArray(body.detail)) return [String(body.detail ?? res.statusText)];
    return body.detail.map((d) => {
      const msg = String(d.msg).replace(/^Value error, /, '');
      for (const name of [d.loc?.[1], ...(d.ctx?.fields ?? [])]) {
        fields.get(name)?.wrap.classList.add('invalid');
      }
      const field = fields.get(d.loc?.[1]);
      return field ? `${field.title}: ${msg}` : msg;
    });
  } catch {
    return [`${res.status} ${res.statusText}`];
  }
}

// The panel shows the designation, then one heading and list per distinct group in server
// order (the buildForm pattern), each value as the API sent it. Rounding here showed `0 mm`
// for a valid 0.0004 and 565.487 for 565.4866776461628 (tech debt 2026-10-06, D-19, L02).
function renderInfo(info) {
  const nodes = [];
  if (typeof info.designation === 'string') {
    nodes.push(Object.assign(document.createElement('h2'), { textContent: info.designation }));
  }
  const lists = new Map();
  for (const row of info.rows) {
    if (!lists.has(row.group)) {
      const list = document.createElement('dl');
      nodes.push(Object.assign(document.createElement('h3'), { textContent: row.group }), list);
      lists.set(row.group, list);
    }
    const line = document.createElement('div');
    line.append(
      Object.assign(document.createElement('dt'), { textContent: row.label }),
      Object.assign(document.createElement('dd'), { textContent: `${String(row.value)} ${row.unit}`.trim() }),
    );
    lists.get(row.group).append(line);
  }
  $('#dims').replaceChildren(...nodes);
  showCounterpart(info.counterpart ?? null);
  pendingWarnings = info.warnings ?? [];
  pendingNotes = info.notes ?? [];
  showMessages([], pendingWarnings, pendingNotes);
  showMatch(info.preset ?? null);
}

// The matching part is a link built from the document and the page's own typing: the kind and every
// field the server says carry over, as a hash the page already knows how to open. The server never
// names clearance (D-02), and rememberTyped skips any field with a default, which clearance has
// since L17, so lastTyped holds only fields without one (none today) and the generic rule adds
// them before the server's fields, which win. The nut therefore opens with its default clearance
// (L17), never one the user did not type. No kind, field or label is named here (L15 amendment
// 2026-10-21, G-05-3).
function showCounterpart(counterpart) {
  counterpartLink.hidden = counterpart === null;
  if (counterpart === null) return;
  const q = new URLSearchParams({ kind: counterpart.kind, ...lastTyped.get(counterpart.kind), ...counterpart.fields });
  counterpartLink.href = `#${q}`;
  counterpartLink.textContent = `Matching ${counterpart.kind}`;
}

// The page never links a download the server refuses (G-04-3, L02): the info document lists, per
// format and quality, whether the shared rule refuses it, in the server's order of preference, so
// each link is the first entry of its format that is not refused and the page names no format,
// no quality and no warning text of its own (D-10). When an earlier entry of that format was
// refused the label names the quality it falls back to and the title says why, because a coarser
// mesh must never pass for the one the user would have been refused (L02). The static label of
// each anchor is index.html's; a format with no served entry keeps it, disabled. Nothing here
// reaches the hash: partQuery and writeHash read the form only (D-09).
const downloadLinks = new Map(
  [...document.querySelectorAll('.downloads a')].map((a) => [a, a.textContent]),
);

function setDownloads(q, downloads = []) {
  for (const [a, label] of downloadLinks) {
    a.textContent = label;
    a.removeAttribute('href');
    a.removeAttribute('title');
    a.setAttribute('aria-disabled', 'true');
  }
  if (!q) return;
  const refusals = new Map(); // format -> the sentence that refused its first entry
  const linked = new Set();
  for (const download of downloads) {
    if (linked.has(download.format)) continue;
    if (download.refusal !== null) {
      if (!refusals.has(download.format)) refusals.set(download.format, download.refusal);
      continue;
    }
    const a = $(`#dl-${download.format}`);
    const qs = new URLSearchParams(q);
    qs.set('quality', download.quality);
    a.href = `api/${currentKind}/model.${download.format}?${qs}`;
    a.removeAttribute('aria-disabled');
    if (refusals.has(download.format)) {
      const label = downloadLinks.get(a);
      a.textContent = `${label} (${download.quality})`;
      a.title = refusals.get(download.format);
    }
    linked.add(download.format);
  }
}

const setStatus = (text) => { $('#status').textContent = text; };

// ---------------------------------------------------------------- update loop

let seq = 0;
let inflight = null;

// While a kind switch's catalogue fetch is in flight the form on screen is the new kind's and
// currentKind is still the old one. An update then would write the old kind's hash and send the new
// form's fields to the old kind's route. Measured: `#clearance=0.1` and `bolt/info?clearance=0.1`.
// navigate runs the update once the switch has loaded (review WR-07, owner choice (a), 2026-10-21).
// So the guard is the first statement below, with nothing before it that writes or requests.
async function update() {
  if (currentKind === null || formKind !== currentKind) return;
  const q = partQuery();
  // kind= is written only when it differs from the registry's default, so a link to the
  // default kind stays as short as the fields that differ (D-09).
  const hashQ = new URLSearchParams();
  if (currentKind !== kinds.default) hashQ.set('kind', currentKind);
  for (const [name, value] of q) hashQ.set(name, value);
  writeHash(hashQ);

  for (const { wrap } of fields.values()) wrap.classList.remove('invalid');
  setDownloads(null);
  inflight?.abort();
  const ctl = new AbortController();
  inflight = ctl;
  const mine = ++seq;
  setStatus('Building…');

  const fail = (errors) => {
    if (mine !== seq) return;
    showMessages(errors, mesh ? meshWarnings : [], mesh ? meshNotes : []);
    $('#dims').replaceChildren();
    showCounterpart(null);
    showMatch(null);
    setStatus(mesh ? 'Showing the last valid part' : '');
  };

  try {
    const infoRes = await fetch(`api/${currentKind}/info?${q}`, { signal: ctl.signal });
    if (!infoRes.ok) return fail(await problems(infoRes));
    const info = await infoRes.json();
    if (mine !== seq) return;
    renderInfo(info);

    const stlQ = new URLSearchParams(q);
    stlQ.set('quality', 'preview');
    const res = await fetch(`api/${currentKind}/model.stl?${stlQ}`, { signal: ctl.signal });
    if (!res.ok) return fail(await problems(res));
    const buf = await res.arrayBuffer();
    if (mine !== seq) return;
    showModel(buf);
    setDownloads(q, info.downloads);
    setStatus('');
  } catch (err) {
    if (err.name !== 'AbortError') fail([`Request failed: ${err.message}`]);
  }
}

let debounce;
const scheduleUpdate = () => {
  clearTimeout(debounce);
  // INTERIM (D-01): 350 ms carried from spur's app.js, a UI choice never measured for
  // screw. Phase 7 re-sweeps (OPER-02); tracked in
  // docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md.
  debounce = setTimeout(update, 350);
};

// ---------------------------------------------------------------- 3D view

const canvas = $('#canvas');
const renderer = new WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const scene = new Scene();
const camera = new PerspectiveCamera(35, 1, 0.1, 10000);
camera.up.set(0, 0, 1); // CAD convention: Z up
scene.add(camera);
scene.add(new HemisphereLight(0xffffff, 0x404850, 1.5));
const key = new DirectionalLight(0xffffff, 1.6); // follows the camera
key.position.set(0.6, 1, 0);
key.target.position.set(0, 0, -1);
camera.add(key, key.target);

const controls = new OrbitControls(camera, canvas);
const material = new MeshStandardMaterial({ metalness: 0.1, roughness: 0.55 });
const edgeMaterial = new LineBasicMaterial();
const loader = new STLLoader();
let mesh = null;
let edges = null;
let grid = null;
let box = null;
let fitted = false;

let frameQueued = false;
function render() {
  if (frameQueued) return;
  frameQueued = true;
  requestAnimationFrame(() => {
    frameQueued = false;
    renderer.render(scene, camera);
  });
}
controls.addEventListener('change', render);

function placeGrid() {
  if (grid) {
    scene.remove(grid);
    grid.geometry.dispose();
    grid.material.dispose();
    grid = null;
  }
  if (!box) return;
  const extent = Math.max(box.max.x - box.min.x, box.max.y - box.min.y) * 1.6;
  const step = [0.5, 1, 2, 5, 10, 20, 50, 100].find((s) => extent / s <= 24) ?? 200;
  const size = Math.ceil(extent / step) * step;
  const colour = css('--grid');
  grid = new GridHelper(size, Math.round(size / step), colour, colour);
  grid.rotation.x = Math.PI / 2; // GridHelper lies in XZ; we want XY
  grid.position.z = box.min.z - 0.01;
  scene.add(grid);
}

function applyTheme() {
  scene.background = new Color(css('--view-bg'));
  material.color.set(css('--mesh'));
  edgeMaterial.color.set(css('--edge'));
  placeGrid();
  render();
}

function fit() {
  if (!box) return;
  const centre = box.getCenter(new Vector3());
  const radius = box.getSize(new Vector3()).length() / 2;
  const dist = (radius / Math.sin((camera.fov * Math.PI) / 360)) * 1.1;
  camera.position.copy(centre).addScaledVector(new Vector3(0.55, -0.9, 0.95).normalize(), dist);
  camera.near = dist / 200;
  camera.far = dist * 50;
  camera.updateProjectionMatrix();
  controls.target.copy(centre);
  controls.update();
  render();
}

/** Forget the mesh and everything that described it, so nothing is drawn until the next part builds. */
function dropMesh() {
  if (mesh) {
    scene.remove(mesh, edges);
    mesh.geometry.dispose();
    edges.geometry.dispose();
  }
  mesh = null;
  edges = null;
  box = null;
  fitted = false;
  pendingWarnings = [];
  meshWarnings = [];
  pendingNotes = [];
  meshNotes = [];
  showMessages([], meshWarnings, meshNotes);
  placeGrid();
  render();
}

function showModel(buffer) {
  const geometry = loader.parse(buffer);
  geometry.computeBoundingBox();
  if (mesh) {
    scene.remove(mesh, edges);
    mesh.geometry.dispose();
    edges.geometry.dispose();
  }
  mesh = new Mesh(geometry, material);
  meshWarnings = pendingWarnings;
  meshNotes = pendingNotes;
  edges = new LineSegments(new EdgesGeometry(geometry, 40), edgeMaterial);
  scene.add(mesh, edges);
  const previous = box;
  box = geometry.boundingBox.clone();
  placeGrid();
  // Refit on first load or when the part size changes a lot; otherwise keep the user's view.
  const size = (b) => b.getSize(new Vector3()).length();
  if (!fitted || Math.abs(size(box) / size(previous) - 1) > 0.3) {
    fit();
    fitted = true;
  }
  render();
}

function resize() {
  const { clientWidth: w, clientHeight: h } = canvas.parentElement;
  if (!w || !h) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  render();
}

// ---------------------------------------------------------------- wiring

const reportLoadError = (err) => showMessages([`Could not load the part: ${err.message}`], mesh ? meshWarnings : [], mesh ? meshNotes : []);

form.addEventListener('submit', (e) => e.preventDefault());
// A field with a default is never remembered: carrying a typed value of one would override the
// counterpart's row values (D-02, D-03). Typing a field empty forgets it, and a write that is not
// typing (Reset, a link, Back, a kind change) forgets a value the field no longer holds, so a link
// never carries an empty or stale number (owner ruling 2026-10-21, review WR-08). The memory is keyed
// by formKind, the kind of the controls the user typed into, never by currentKind (WR-07).
function rememberTyped(input) {
  if (formKind === null || defaults[input.name] !== undefined) return;
  const typed = { ...lastTyped.get(formKind) };
  const value = read(input);
  if (value === '') delete typed[input.name];
  else typed[input.name] = value;
  lastTyped.set(formKind, typed);
}
function forgetUntyped(input) {
  const typed = lastTyped.get(formKind);
  if (typed !== undefined && input.name in typed && read(input) !== typed[input.name]) {
    delete typed[input.name];
  }
}
form.addEventListener('input', (e) => { rememberTyped(e.target); scheduleUpdate(); });
window.addEventListener('hashchange', () => navigate().catch(reportLoadError));
kindSelect.addEventListener('change', () => {
  const q = new URLSearchParams();
  if (kindSelect.value !== kinds.default) q.set('kind', kindSelect.value);
  writeHash(q); // a new kind starts from its own defaults, so no field carries over
  navigate().catch(reportLoadError);
});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);
new ResizeObserver(resize).observe(canvas.parentElement);

$('#fit').addEventListener('click', fit);
$('#reset').addEventListener('click', () => {
  for (const [name, { input }] of fields) write(input, defaults[name]);
  for (const { input } of fields.values()) forgetUntyped(input);
  update();
});
$('#copy-link').addEventListener('click', async (e) => {
  const button = e.currentTarget;
  try {
    await navigator.clipboard.writeText(location.href);
    button.textContent = 'Copied';
    setTimeout(() => { button.textContent = 'Copy link'; }, 1500);
  } catch {
    window.prompt('Copy this link:', location.href); // clipboard API needs HTTPS or localhost
  }
});

(async () => {
  applyTheme();
  resize();
  try {
    await loadKinds();
    await navigate();
  } catch (err) {
    showMessages([`Could not load the part kinds and schema: ${err.message}`]);
  }
})();
