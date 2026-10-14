# Phase 5: Hex Nut and Kernel Pair Proof - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-14
**Phase:** 05-hex-nut-and-kernel-pair-proof
**Areas discussed:** Clearance field and the matching part, What the pair proof judges, Thread ends and the gate, Nut fields / info rows / STL deflection

---

## Clearance field and the matching part

### How does the nut kind ship without a measured clearance default (PAIR-02), given L02 freezes any shipped default forever?

| Option | Description | Selected |
|--------|-------------|----------|
| Required field, no default | 422 `missing` naming `clearance` on the API, `--clearance` required on the CLI; the form opens empty; Phase 6 adds the measured default as the first one; the parity test learns one required field | ✓ |
| Default 0.0 plus a standing warning | Nominal nut, proof inconclusive by definition; every link omitting the field means 0 forever, so the measured value could never become the default | |
| Required on API/CLI, page pre-fills a labelled value | Model has no default; the page pre-fills 0.20 mm (INTERIM) and writes it into the hash; two sources of a default | |

**User's choice:** Required field, no default.

### Where does the matching-part derivation (TYPE-04) live, and what does the link carry?

| Option | Description | Selected |
|--------|-------------|----------|
| Info document `counterpart` key, page renders a link | `PartInfo.counterpart: {kind, fields} \| null` computed kernel-free in `calc`; bolt→nut carries d, pitch, left_hand plus the ISO 4032 row's s, m; nut→bolt the ISO 4017 row's s, k; the page builds the link generically; API and CLI print the same key; clearance never in it | ✓ |
| Page-only: kind selector carries d, pitch, hand across | No document change; unobservable outside the browser; parity cannot cover it | |
| A dedicated route/subcommand | `GET /api/bolt/counterpart`, `screw counterpart`; new route shape per kind, hand-written subcommand | |

**User's choice:** Info document `counterpart` key.

### When the part sits on no ISO row (custom d or pitch), what does `counterpart` carry? And for nut→bolt, which length?

| Option | Description | Selected |
|--------|-------------|----------|
| Shared fields only + a warning; nut→bolt leaves length at the bolt default | d, pitch, left_hand only; the target opens with its frozen defaults and reads custom; a pinned warning names the fields to set; no invented length | ✓ |
| Nearest row fills s, m / smallest standard length | Snap to the nearest ISO size — the plausible number 04 D-09 rejected | |
| counterpart is null off a row | No link unless both parts have a row; a custom-pitch bolt loses its nut link | |

**User's choice:** Shared fields only + a warning.

### What values may `clearance` take at the params boundary?

| Option | Description | Selected |
|--------|-------------|----------|
| Any finite value; c <= 0 builds and warns | Finite, `le=INTERIM_MAX_MM`, no lower bound; root-radius rule reads c; the document warns and `screw pair` reads inconclusive; the spike's diagnostic rows stay reproducible | ✓ |
| gt=0 only | 422 on c <= 0; the nominal nut is refused | |
| ge=0, negative refused | c = 0 allowed, c < 0 a policy 422 needing its own reason | |

**User's choice:** Any finite value; c <= 0 builds and warns.

**Notes:** Claude's discretion: the empty-field page state, 422/exit-2 wording, the `counterpart` key's exact shape.

---

## What the pair proof judges

### Which bodies does the shipped pair proof judge?

| Option | Description | Selected |
|--------|-------------|----------|
| Spike bodies as the verdict, shipped solids as evidence | `solid/pair.py` moves the measured check in (rod piece + plain blank, m from the verified row), so the `2026-10-08-a-pair` expectations transfer; a slower row intersects the shipped solids as evidence beside the verdict, never an input | ✓ |
| Shipped solids only | Proves the download, but the pre-registered verdicts become predictions on other bodies; cost unmeasured | |
| Spike bodies only | Smallest change; the shipped ends are never intersected | |

**User's choice:** Spike bodies as the verdict, shipped solids as evidence.

### What is the shape of `screw pair` and the solid-package function?

| Option | Description | Selected |
|--------|-------------|----------|
| `screw pair nut <nut flags>`: one model, bolt derived | Flags generated from `NutParams`; `solid.pair.prove(p) -> PairReport`; JSON; exit 0/1/2 | ✓ |
| `screw pair --bolt ... --nut ...`: two parameter sets | Two models in one command; hand-written flags | |
| `screw pair bolt ...` and `screw pair nut ...` both | From the bolt side the clearance has no field; a hand-written flag the parity rule must exempt | |

**User's choice:** `screw pair nut <nut flags>`.

### The tiers: which cell runs in `make verify`, and how is the CI grid shaped?

| Option | Description | Selected |
|--------|-------------|----------|
| M6 right-hand c = 0.10 in verify; a `pair` marker + its own workflow | One proven cell in a child process plus the kernel-free rule tests; 120 same-hand cells plus mixed-hand in `pair.yml` (the grid.yml shape) against the expected-verdict table derived from the records before the first run | ✓ |
| Both hands at M6 in verify, grid folded into grid.yml | Two cells in the gate; grid.yml's shard wall time grows unmeasured | |
| Verify runs the mixed-hand `violated` cell only | Never runs a proven path in the gate | |

**User's choice:** M6 right-hand c = 0.10 in verify; a `pair` marker + its own workflow.

### How bounded is the M18 control diagnosis (SC6), and what counts as done?

| Option | Description | Selected |
|--------|-------------|----------|
| One pre-registered probe file, fixed probe list, one PR | `05-M18-DIAGNOSIS.md` lands before the probe runs; probes: repeat N times, theta steps, c = -0.05 same pose, fuzzy value on, operands swapped; a RESULTS entry and an L entry; done = written | ✓ |
| Re-run the twelve M18 cells once | Determinism only | |
| Open investigation until the cause is found | Unbounded; the revision rejected a diagnosis phase | |

**User's choice:** One pre-registered probe file, fixed probe list, one PR.

**Notes:** Claude's discretion: `PairReport` names, the expected-verdict table's home and deriving script, the `pair` make target, `_KEEP` child-process handling, the diagnosis PR's place in the phase order.

---

## Thread ends and the gate

### Lead-in chamfers on the bolt tip and the nut thread (THRD-05): how does the THRD-04 gate judge a chamfered end?

| Option | Description | Selected |
|--------|-------------|----------|
| Kernel-free numeric oracle for the cut volume, same T_GATE | ISO 4753 read first; one cone cut per end; a midpoint integral of the section against the cone (the spike's `interference_area` recipe); same T_GATE with a positive control; cost evidence `2026-10-08-a-trim` | ✓ |
| Gate the plain body, then bound the chamfer's effect | A weaker band check on the end only | |
| Ends stay plain cuts; THRD-05 moves to Phase 6 | Contradicts SC1 | |

**User's choice:** Kernel-free numeric oracle for the cut volume, same T_GATE.

### The under-head fillet: an OCCT fillet on the fused junction is the fragile op nothing measured. What ships?

| Option | Description | Selected |
|--------|-------------|----------|
| Revolved ring with a closed form, on a plain shank only | A solid of revolution of radius r fused at the junction, exact volume; ISO 4014 bolts only; ISO 4017 screws get none and say so; probed first | ✓ |
| Defer the fillet to Phase 6 / v1.x; THRD-05 amended | Only the lead-in chamfers ship | |
| OCCT fillet op on the fused junction | Fragile; volume from the kernel's own number | |

**User's choice:** Revolved ring with a closed form, on a plain shank only.

### ISO 4032's face chamfers and the nut's thread lead-in: when the purchased text gives a band or nothing, what is modelled?

| Option | Description | Selected |
|--------|-------------|----------|
| Read first; a band becomes one stated model in the decision entry | A single number is cited; a band or no clause becomes one stated model (PITFALLS M5), labelled as a model on the panel; the head keeps its plain prism | ✓ |
| Face chamfers plain like the head; lead-in cones only | Contradicts SC1's "chamfers on both faces" | |
| Chamfers as explicit fields (angle, dw) | A field for geometry the standard does not fix by one number | |

**User's choice:** Read first; a band becomes one stated model in the decision entry.

### The owner read checkpoint: one opening session over all four standards, or one per plan?

| Option | Description | Selected |
|--------|-------------|----------|
| One opening read, then ruling-B double entry per table | ISO 4032, 724, 965-2, 4753 read before any geometry plan, recorded in `05-OWNER-READS.md`; tables follow ruling B | ✓ |
| Per-plan checkpoints as each table is needed | Spreads the owner's time; the chamfer model arrives late | |

**User's choice:** One opening read, then ruling-B double entry per table.

**Notes:** Claude's discretion: the integration recipe and its positive control, the standing-warning rewrite, where the cone cut sits relative to the two gates, the pre-plan probe.

---

## Nut fields, info rows, STL deflection

### The nut's fields: which ones, and does `s` move to the shared base?

| Option | Description | Selected |
|--------|-------------|----------|
| `NutParams`: s, m, clearance; `s` stays per kind | `e`, `mw`, `dw` reported from the row only; `s` declared per kind with its own row-backed default and its own `s > d` rule; frozen defaults are the ISO 4032 M6 row as the owner reads it | ✓ |
| `s` on `FastenerParams` | One declaration; the nut's default would be the base's; wrong group and message for a nut | |
| Nut also carries `mw`, `dw` as fields | `dw` would feed the chamfer cone; an off-row nut has no honest `dw` | |

**User's choice:** `NutParams`: s, m, clearance; `s` stays per kind.

### ISO 965-2:2024 rows (INFO-02): which columns ship, and what does the panel show off a row?

| Option | Description | Selected |
|--------|-------------|----------|
| Only the limits the panel reports: four pairs per size, coarse M2–M20 | 6g major d and pitch d2 max/min; 6H minor D1 and pitch D2 min/max; one typed row per (size, class); ruling B; one relation test per row; present only on an exact ISO 262 match under INFO-02's label; d2/D1/D2 nominal from ISO 724 always present | ✓ |
| Every column the table prints for M2–M20 coarse | More rows to double-enter for numbers no panel row shows | |
| Formulas from ISO 965-1 instead of rows | Not purchased; UNVERIFIED; plausible number for a non-ISO pitch | |

**User's choice:** Only the limits the panel reports.

### FRNT-06: how is the download STL's chord deviation chosen against the clearance?

| Option | Description | Selected |
|--------|-------------|----------|
| One fixed fine deflection, cited against the smallest proof clearance | A stated fraction of 0.05 mm from the `2026-10-08-a-ladder` evidence, recorded in L14; same mesh for bolt and nut; the researcher verifies `ControlSurfaceDeflection`; preview may stay coarser and is labelled | ✓ |
| Per-request deflection from the nut's clearance | Two meshes for one pair; cache keys and caps change | |
| Keep spur's 0.01 mm and only document it | A gear's number with no stated rule | |

**User's choice:** One fixed fine deflection, cited against the smallest proof clearance.

### The saved preview STL names its quality (idea 2026-10-12): adopt here?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes: `_preview` suffix in the file name for the non-default quality | `<slug>_preview.stl` for `quality=preview`; fine STL and STEP unchanged; one rule for `_serve` and `screw export`; pinned by a parity test; the idea moves to Done | ✓ |
| Not now; keep the idea open | Wait for a user report | |

**User's choice:** Yes: `_preview` suffix.

**Notes:** Claude's discretion: pair rows on the nut's panel only; the M18 note text; the `informative / historical` copy; the nut's standing warning; the `Nut`/`Pair` group names.

---

## Claude's Discretion

- `PairReport` field names; the expected-verdict table's format, location and deriving script; `pair.yml` schedule and sharding; the `pair` command's parity rule.
- The numeric oracle's recipe, error bound and positive controls; where the cone cut and the fillet ring sit in `_build`.
- 422 and exit-2 wording beyond the named fields; group name strings; the `informative / historical` copy; the designation element.
- The nut page with `clearance` empty; `Reset` leaves it empty; the counterpart link's placement and static label.
- The pre-plan probe's scope and record; the typing of the three new tables; the owner-copy generator's extension.
- The order of plans; the diagnosis protocol PR's place; the phase branch from `main` at `0ef52e8`.

## Deferred Ideas

- Shipped solids as the pair verdict (after a campaign pre-registers them); head chamfer / washer face; head-side run-out fade; bolt-side `undersize` (Phase 6); clearance default and hint (Phase 6); per-request deflection (rejected); ISO 965-1 formulas (rejected); `mw`/`dw` fields (rejected); pair proof endpoint (out of scope); WR-03/IN-02 amendments (before the next campaign); DIN 934 alias (v2); caps, pair-tier wall time and deflection on linux/amd64 (Phase 7).
