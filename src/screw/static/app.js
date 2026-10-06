import {
  Color, DirectionalLight, EdgesGeometry, GridHelper, HemisphereLight,
  LineBasicMaterial, LineSegments, Mesh, MeshStandardMaterial, PerspectiveCamera,
  Scene, Vector3, WebGLRenderer, OrbitControls, STLLoader,
} from './vendor/three.bundle.min.js';

const $ = (sel) => document.querySelector(sel);
const form = $('#params');
const kindSelect = $('#kind');
let kinds = { default: null, kinds: [] }; // the /api/kinds body
let currentKind = null; // the kind the form below was built for; null while none is valid
const fields = new Map(); // name -> { input, wrap, title }
let defaults = {};

// Nothing here knows a field name, a row key or a kind's label: the form, the hash, the
// info panel and the download links are all read off what the API sends, so a new
// registered kind needs no edit in this file (D-10; tests/test_parity.py pins it).
const fmt = (v) => Number(v).toFixed(3).replace(/\.?0+$/, '');
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
}

async function buildForm(kind) {
  const mine = formSeq;
  const res = await fetch(`api/schema?kind=${encodeURIComponent(kind)}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  const schema = await res.json();
  if (mine !== formSeq) return false;
  clearForm();
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
  ++formSeq;
  const h = new URLSearchParams(location.hash.slice(1));
  const kind = h.get('kind') ?? kinds.default;

  if (!kinds.kinds.includes(kind)) {
    // Showing a different part than the one the link names would be a silent change of
    // the part (L02): say so, and build nothing.
    clearForm();
    currentKind = null;
    kindSelect.selectedIndex = -1;
    $('#dims').replaceChildren();
    setDownloads(null);
    setStatus('');
    showMessages([`Unknown kind "${kind}". Known kinds: ${kinds.kinds.join(', ')}.`]);
    return;
  }

  if (kind !== currentKind) {
    if (!(await buildForm(kind))) return;
    currentKind = kind;
  }
  kindSelect.value = kind;
  for (const [name, { input }] of fields) input.value = h.get(name) ?? defaults[name];
  await update();
}

/** Query string with only the parameters that differ from the defaults. */
function partQuery() {
  const q = new URLSearchParams();
  for (const [name, { input }] of fields) {
    if (input.value === '') continue;
    // 6.0 and 6 are the same default; a string compare would put the first in the link.
    const changed = input.type === 'number'
      ? Number(input.value) !== Number(defaults[name])
      : input.value !== String(defaults[name]);
    if (changed) q.set(name, input.value);
  }
  return q;
}

function writeHash(q) {
  const hash = q.toString();
  history.replaceState(null, '', hash ? `#${hash}` : location.pathname + location.search);
}

// ---------------------------------------------------------------- messages

function showMessages(errors = [], warnings = []) {
  const box = $('#messages');
  box.replaceChildren(
    ...errors.map((t) => Object.assign(document.createElement('p'), { className: 'error', textContent: t })),
    ...warnings.map((t) => Object.assign(document.createElement('p'), { className: 'warning', textContent: t })),
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

function renderInfo(info) {
  const rows = [];
  for (const row of info.rows) {
    const line = document.createElement('div');
    line.append(
      Object.assign(document.createElement('dt'), { textContent: row.label }),
      Object.assign(document.createElement('dd'), { textContent: `${fmt(row.value)} ${row.unit}`.trim() }),
    );
    rows.push(line);
  }
  $('#dims').replaceChildren(...rows);
  showMessages([], info.warnings ?? []);
}

function setDownloads(q) {
  for (const fmt of ['stl', 'step']) {
    const a = $(`#dl-${fmt}`);
    if (q) {
      const qs = q.toString();
      a.href = `api/${currentKind}/model.${fmt}${qs ? `?${qs}` : ''}`;
      a.removeAttribute('aria-disabled');
    } else {
      a.removeAttribute('href');
      a.setAttribute('aria-disabled', 'true');
    }
  }
}

const setStatus = (text) => { $('#status').textContent = text; };

// ---------------------------------------------------------------- update loop

let seq = 0;
let inflight = null;

async function update() {
  if (currentKind === null) return;
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
    showMessages(errors);
    $('#dims').replaceChildren();
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
    setDownloads(q);
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

function showModel(buffer) {
  const geometry = loader.parse(buffer);
  geometry.computeBoundingBox();
  if (mesh) {
    scene.remove(mesh, edges);
    mesh.geometry.dispose();
    edges.geometry.dispose();
  }
  mesh = new Mesh(geometry, material);
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

const reportLoadError = (err) => showMessages([`Could not load the part: ${err.message}`]);

form.addEventListener('submit', (e) => e.preventDefault());
form.addEventListener('input', scheduleUpdate);
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
  for (const [name, { input }] of fields) input.value = defaults[name];
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
