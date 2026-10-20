# Phase 5: Owner reads and rulings

Record of the owner's opening read and rulings for phase 5 (plan 05-02, Task 2 checkpoint, answered
2026-10-14). It carries the owner's answers, the two M6 defaults and paths only; no clause wording,
page render, PDF or table row is copied here (D-16, TABL-04). Plans 05-04 to 05-18 read it.

**2026-10-20: the sources change (L14).** The owner chose free GOST texts in place of purchased ISO
copies; the map is `docs/requirements/standards-sources.md`. Where this record names ISO 4032, ISO 724,
ISO 965-2 or ISO 4753, the pending reads and the owner copy read the GOST equivalent L14 names; the
owner-copy file names stay as written until the plan amendments. The recorded s and m, the permanence
line and the rulings R1 to R13 are unchanged. Before plan 05-06, s and m are cross-checked against the
GOST ISO 4032-2014 M6 row, and a mismatch is a stop-and-ask (D-15). The ISO purchase is debt:
`docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md`.

**This record is partial, and its one source is secondary.** Read this section before relying on any
line below.

- **Source of `s` and `m` (D-14 deviation).** The two values under "ISO 4032:2023 M6 defaults" were
  read by Claude (Opus 5.5, the orchestrator), not by the owner, from
  `~/Downloads/ISO standards/ISO 4032 - 2023 Hexagon Regular Nuts, Style 1 - Product Grades A and B.pdf`.
  That file is NOT the ISO standard. It is a one-page print of the GlobalFastener.com web page that
  transcribes ISO 4032:2023. The owner approved this secondary source explicitly ("use it") as a
  deviation from D-14's "read of the purchased standard". No second independent read of the ISO text
  exists; nothing in this record has been checked against the standard itself.
- **The owner holds the standards only partly.** Reads 3 to 7 (and the form half of read 2) are
  PENDING. Each names the plan that needs it. Nothing was typed in their place (L02, D-15).
- **Plan 05-02's own truth "all reads before any geometry or table plan" is therefore not met.** Plans
  05-04 and 05-05 need only `s`, `m` and the permanence line, which are below; plans 05-06, 05-07,
  05-08, 05-09, 05-11, 05-12 and 05-13 need a pending read each and must stop on their precondition
  until it lands. The deviation is recorded in `05-02-SUMMARY.md`.

## ISO 4032:2023 M6 defaults

Read on 2026-10-14 from the secondary source named above (not from the standard).

| Field | Value | Column the field takes |
| ----- | ----- | ---------------------- |
| s | 10.0 mm | `s` max, which equals the nominal width across flats |
| m | 5.2 mm | `m` max (option a of read 1; the owner chose it, as `k` took the nominal in phase 4) |

Size M6, product grade A, coarse pitch 1.0 mm (the pitch the owner copy and the phase 4 defaults use).
The page also prints minimum values for `s` and `m` and the columns `e`, `dw` and `mw`; they are
deliberately not recorded here (D-16), they belong in the owner copy and in plan 05-06's transcription.

Permanence acknowledged: 2026-10-14, permanent: accepted (D-15: links that omit s or m mean these values forever)

The owner's reply carried `permanent: accepted`, given 2026-10-14 after being told that every
shareable link that omits `s` or `m` means these values forever and that this is the only stop for
them: plan 05-04 commits exactly these values without asking again. The permanence covers values read
from the secondary source; the owner was told the source.

## Owner copy

Owner copy directory: PENDING — none exists yet. Needed before plan 05-06 (`iso4032.tsv`), plan 05-08
(`iso965_2.tsv`, and `iso724.tsv` if ISO 724 is a table) and plan 05-12 (`iso4014_fillets.tsv`).

Expected files, per the plan: `iso4032.tsv` (header `size grade pitch s s_min e_min m_max m_min mw_min
dw_min informative table column`, or the columns read 2 finds), `iso965_2.tsv` (header `size class
limit value table column`), `iso724.tsv` if ISO 724 is a table (header `size pitch d2 d1 table
column`), and under R1 a `iso4014_fillets.tsv` (header `size pitch r_min table column`). The directory
must be absolute and outside the repository.

## Designation

Designation: PENDING — needed before plan 05-07. The form, with the property class left out (expected
`Hexagon nut ISO 4032 - M6`), is not on the secondary source's page.

- Decimal-size form: PENDING — needed before plan 05-07 (not on the page).
- Left-hand form: PENDING — needed before plan 05-07 (not on the page).

## ISO 4032 sizes and columns

- Annex A sizes: from the secondary source, the sizes it marks historical (its footnote: not
  conforming to ISO 898-2 / 3506-2) are M1.6, M2, M2.5, M3, M3.5, M4 and M42 to M64. The small end is
  consistent with the expected Annex A coverage of M1.6 to M4; this is a reading of a web page, not of
  the standard's annex.
- M3.5 has a row: yes. M7 has a row: yes. Both are non-preferred sizes (printed in parentheses).
- Columns printed per size on the secondary source: P, c max/min, da max/min, dw min, e min, m max/min,
  mw min, s max/min. Plan 05-06 adjusts its dataclass to the columns the owner copy ends up carrying.
- Face chamfer clause (read 3): PENDING — needed before plan 05-11 (R3, R4 and the oracle models
  depend on whether one number, a band or nothing is printed) and plan 05-13.

## ISO 724

PENDING — needed before plan 05-08 (read 4: whether `d2`, `D1`, `D2` come from a formula or a table,
for coarse M2 to M20). R13 below depends on the answer.

## ISO 965-2

PENDING — needed before plan 05-08 and plan 05-09 (read 5: which columns exist for 6g, major `d`
max/min and pitch `d2` max/min, and for 6H, minor `D1` min/max and pitch `D2` min/max, and in which
table).

## ISO 4753

PENDING — needed before plan 05-11 and plan 05-12 (read 6: the tip end form ISO 4014/4017 reference,
its angle and length rule, single number or band). R2 depends on the answer.

## Rendering route and the PDFs

Rendering route: a (`brew install poppler`, then `pdftoppm`), executed on 2026-10-14: poppler 26.10.0
is installed on this machine. Renders go to the session scratch directory, never the repository.

PDFs' path on this machine: `/Users/half/Downloads/ISO standards/` (outside the repository). The real
ISO PDFs are not there yet; the folder holds the secondary-source print named at the top (read 8 is
answered for the route and the folder, not for the standards' own pages). Plans 05-06 and 05-08 render
an ISO page as a precondition and cannot pass it until the real PDFs exist.

## Rulings

The owner accepted Claude's recommendation on every ruling and chose R6 a, on 2026-10-14. The literal
answers follow, each with the plan that applies it. A ruling whose answer is conditional on a pending
read says which read.

- R1 (fillet radius `r`, D-11): `a`. One `r,min` per size typed in `calc/thread.py` keyed on exact (d, pitch), double-entered and pinned by a test, no fillet off a row. Applied by plans 05-11 and 05-12.
- R2 (tip end, D-09): the single number if printed, else the stated model ("<angle> from the end face, starting at the minor diameter"). Conditional on read 6 (PENDING). Applied by plans 05-11 and 05-12.
- R3 (nut lead-in countersink, D-09, D-12): `a` if one number is printed, else `b`. Conditional on read 3 (PENDING). Either way the face radius must exceed the void's crest radius `d/2 + c` so the cone crosses the void (F8). Applied by plans 05-11 and 05-13.
- R4 (face chamfer, D-12): `b` if one number is printed, else `a` (labelled a model). Conditional on read 3 (PENDING). Applied by plans 05-11 and 05-12.
- R5 (small `m` where the cutters would overlap, P10): `a`. Cap the countersink depth to the validity limit and warn naming `m` (L02 cap-and-warn). Applied by plans 05-11 and 05-13.
- R6 (FRNT-06 fraction): `a`. 0.5 of the 0.05 mm proof clearance, keep the 0.01 mm fine preset, cite the rule. The owner answered the fraction without the agent choosing it. Applied by plan 05-17.
- R7 (mixed-hand cells, P3): `yes`. An internal keyword `rod_left_hand` on `prove`, never on the CLI or the model. Applied by plan 05-14.
- R8 (`prove` at c <= 0, P14): `yes`. Return `inconclusive` by definition with no booleans; the nut solid still builds. Applied by plan 05-14.
- R9 (D-22, `screw export`): `yes`. `download_name(p, fmt, quality)` names the file when `-o` is a directory; a file path given by the user is written as given and the `wrote` line names the quality. Applied by plan 05-17, as plan 05-02 lists it (plan 05-18 also reads it).
- R10 (kind switch with an empty clearance, P9c): `a`. Drop the old mesh and show nothing until a valid nut. Applied by plan 05-10.
- R11 (differential end-cut gate, P8): `yes`. Tolerance = 10 x the largest piece error the probe recorded, rounded up to one significant figure. The probe's largest piece error is 2.737e-03 (`bench/RESULTS.md`, "End-cut probe (Phase 5, D-10)", tip 45 degrees on the M2 right-hand rod, one single-run maximum over 46 honest rows), so the owner's tolerance is 10 x 2.737e-03 = 2.737e-02, rounded up to one significant figure = 0.03. Applied to each cut or ring by plan 05-11.
- R12 (nut fine-STL cap): owner's literal answer: "reuse `FINE_STL_ROWS` if the probe shows it". The probe's table follows; the owner chose no reading beyond the ruling's own condition ("reuse `FINE_STL_ROWS` on `m` if the probe's nut bytes at each cap fit the 64 MiB budget and the cap + 1 mm does not; otherwise measure nut caps in their own run"). Applied by plan 05-05.

  | Nut fine STL, countersinks and chamfers on both faces | m (mm) | fine STL + gzip-1 bytes | sum / 64 MiB |
  | --- | --- | --- | --- |
  | M10 right, at the cap | 56 | 64 182 297 | 0.956 |
  | M10 right, cap + 1 | 57 | 65 279 123 | 0.973 |
  | M20 right, at the cap | 64 | 61 802 769 | 0.921 |
  | M20 right, cap + 1 | 65 | 62 818 273 | 0.936 |
  | M20 left, at the cap | 91 | 67 318 345 | 1.003 |
  | M20 left, cap + 1 | 92 | 68 351 237 | 1.019 |

  What the table means for "reuse", stated and not chosen: at M10 right and M20 right the nut fits the
  budget at the cap and also at cap + 1, so the rod's cap is conservative there and the second half of
  the condition (cap + 1 does not fit) is not shown. At M20 left the nut is already over the budget at
  the cap itself (1.003), so the first half (the nut fits at the cap) is not shown either. The condition
  as the ruling words it is shown on none of the three sizes the probe measured, and the probe measured
  none of the other 10 capped (d, pitch, hand) rows. The probe's cap rows are nut heights of 56 to 92
  mm, far above any nut height read so far, so they say what the rod caps would do on a nut and not
  what a nut costs. Plan 05-05 branches on this ruling and must surface the table to the owner before
  it edits `download_refusal`; this record does not decide between reusing the rod caps and a separate
  nut run.
- R13 (`d2`, `D1`, `D2` on the panel, D-16): `b`. The basic-profile value everywhere (`d - 3H/4`, `d - 5H/4`), the ISO 724 table only as a test that the two agree. Moot if read 4 finds ISO 724 gives a formula (read 4 PENDING). Applied by plans 05-08 and 05-09.
