# The small-d bolt wall of 9 (L37) refuses bolts the shipped sweep built

Severity: must
Status: active
Date: 2026-11-03
Source: plan 08-03, protocol stop S5 and the owner's ruling `c` (L37, 08-SWEEP-PROTOCOL.md F15)
Related files:
- docs/architecture/decision_log.md (L37)
- bench/results/phase-08/fine-bands-41635270998/
- src/screw/calc/thread.py (`pitch_too_fine_refusal`; the wall lands there in plan 08-12)

## Context
The band walk refused 40 check cells at d 0.5 to 0.85 mm, all with 90 turns, at d / pitch 12.5 and
above. The owner ruled a bolt wall of 9 for d strictly between 0.45 and 0.9 mm (L37). The wall reads
d / pitch only, so it also refuses cells of the same walk that built: 104 of 144 check cells in that
interval above 9 read `ok` (all of the 3- and 30-turn cells and the left-hand q 12.5 cells at 90
turns), and 236 of 244 readings of the Phase 7 pitch walk (`walls-pitch-41074314305`). The refusal
is before the kernel, so no wrong part is built (L02 holds), but a link that carried such a part
now gets a 422 naming d and pitch.

## Why it matters
A user who asks for d 0.6, pitch 0.04 and a short thread gets a 422 for a part that builds. Every
failure seen was a 90-turn thread; a turns ceiling would keep the short ones.

## Owner sign-off
2026-11-03, after the over-refusal above was put to the owner with three paths (keep L37, supersede
it now with a turns ceiling, or keep L37 and fix it as debt after the release), the owner replied
`3`: L37 ships in the first release and the turns ceiling is this item's fix, after the release.
The parts it refuses have pitches of 0.025 to 0.068 mm.

## Next step
After the first release, or sooner if a user report names a refused part. The fix is a turns
ceiling for d 0.45 to 0.9 mm read by F8's rule over a new pre-registered walk of that interval, as
a supersession of L37.

<!-- On resolve: set Status: resolved, add `Resolved in: <commit sha>`,
     git mv into resolved/, move the INDEX row to Resolved — same commit as the fix. -->
