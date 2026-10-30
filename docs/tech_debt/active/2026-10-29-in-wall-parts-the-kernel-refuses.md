# Parts inside the fine-pitch walls that the kernel still refuses

Severity: must
Status: active
Date: 2026-10-29 (re-scoped 2026-10-30, plan 07-18, after L25)
Source: plan 07-09 (cost model fit). The owner chose "File must debt, continue" on 2026-10-28.
Re-scoped to the residual by the owner's rulings G35 ("Must debt, don't block (Recommended)") and
G36 ("Rule nut W = 8, island to debt (Recommended)").
Related files:
- src/screw/calc/thread.py (`MAX_BOLT_D_PER_PITCH`, `MAX_NUT_D_PER_PITCH`, `pitch_too_fine_refusal`)
- src/screw/solid/helical.py (`twist`, `SECTION_SAMPLES`: the sweep's accuracy)
- src/screw/solid/bolt.py (`tip_cut`), src/screw/solid/nut.py (`finish`, `assemble`)
- bench/results/phase-07/walls-pitch-41074314305/ (the walk's readings)
- .planning/debug/resolved/in-wall-kernel-builderror.md (the diagnosis, evidence E1 to E32)

## Context
Explore run 40646117094 read 20 parts that the L20 walls admitted and the kernel refused with
`BuildError`. The diagnosis: the OCCT booleans that cut the pipe-swept thread (the bolt's tip cone,
the nut's lead-in countersink and its prism minus void) return a wrong result while reporting
success once the swept surface's representation error is not small against the thread depth. That
error grows with d / pitch. The gates refuse every bad cut, so no wrong part is served.

L25 (07 R31) now refuses a bolt above d / pitch 20 and a nut above 8 with the 422
`pitch_too_fine`. That refuses all 20, and no catalogue row. It does not hold every refusal. What
is left inside the walls:

- **The nut island.** Walk run 41074314305 refused 6 nuts at d 2.2 mm, d / pitch 7 (forms base, s4
  and m1, both hands; labels `pitch-nut-<form>-d2.2-q7-<hand>`), every neighbouring cell ok. They
  are the only refused walk readings at or below a shipped wall
  (`python -m bench.oper_sets pitch-walls --from bench/results/phase-07/walls-pitch-41074314305`).
  The margin rule would have put the nut's wall at 5; the owner ruled 8, the catalogue's largest
  d / pitch.
- **Long-thread bolts.** The walk read 3-turn bolts only. The debug session's grids (E27, E30, E32)
  found bolts refused at d / pitch 20 or less as the thread gets longer, in the size bands d 0.5 to
  0.85 and 1.6 to 3.3 mm: on macOS arm64 83 of 2789 built cells (n30 36 of 687, n60 12 of 307,
  n80 3 of 6, n90 32 of 281; n3 and n3s none), on linux/amd64 13 of 178. An ordinary part is among
  them: d 3, pitch 0.35, 25 mm of thread, right hand (71.4 turns; its left twin builds), admitted at
  stl-preview and stl-fine (E31).
- **Isolated nut cells.** The debug grid found no refused nut at d / pitch 10 or less on macOS
  (1056 cells) or linux/amd64 (132 cells), but its grid had no d / pitch 7 and the walk found the
  island there. Isolated failures tied to a seam near a face cannot be bounded by a grid (E32).

Such a part still gets a build error after validation, never a wrong part (L02 holds).

**Option 2 of the debug session, the kernel fix (not applied).** Raise the sweep's accuracy:
MakePipeShell's approximation tolerance to 1e-6 and the flank spline to 56 samples
(`helical.SECTION_SAMPLES`, 14 today). Measured in the debug session:

- It builds all 20 through every product gate, on macOS arm64 and linux/amd64 (E12, E14).
- The tolerance alone clears 13 of them.
- It builds the nut cells it was tried on at d / pitch 11, 14 and 17, except d 0.8, pitch 0.0470589,
  m 0.8, right hand: "2 solids" (E31).
- It is not monotone. It breaks 4 parts that build today, all at d / pitch 250, with "Geometry
  kernel produced 0 solids from the tip cut": `bolt-d100-p0.4-n3` and `bolt-d250-p1-n3`, both
  hands (E15, E31). The wall of 20 sits in front of those 4.
- It builds every catalogue row of the explore set and the 167 free-space explore parts the model
  took then, with no regression inside that set (E19).
- It costs 1.33x to 1.54x the build time and 2.3x to 4.5x the STEP bytes on catalogue rows (macOS
  arm64, 3 cold builds each, E21). The STEP of iso4017:M20x200 would be 22867610 B, over B-01's
  step bytes budget of 9748694.773917168 B. L21's cost model, B-01's budgets and the bound tier
  were measured on the shipped sweep, so the variant voids them until a full re-sweep.

## Why it matters
A request the model admits can still get a build error instead of a part. It holds a worker for the
build, and the user gets no field to change. The long-thread band reaches ordinary small parts. The
cost model is fitted without these points.

## Next step
Before the first release: try option 2 behind the L25 walls. Re-read the 20, the island and the
long-thread bands on linux/amd64 with it. Then re-sweep the cost of the parts it changes, and
supersede L25 if it holds. If it does not, a guard on thread length per size band is the fallback.
The debug session did not recommend that guard, because its bands are piecewise in d.
