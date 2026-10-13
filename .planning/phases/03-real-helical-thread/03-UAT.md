---
status: complete
phase: 03-real-helical-thread
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md, 03-05-SUMMARY.md, 03-06-SUMMARY.md, 03-07-SUMMARY.md]
started: 2026-10-13T05:52:21Z
updated: 2026-10-13T07:23:54.637Z
restarted_from: "03-UAT.md at fa760cf (7 passed, built from 03-VERIFICATION.md; owner rulings on WR-05, THRD-02 and the refused-link status line live there)"
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running screw server. Clear ephemeral state (.venv stays; any lock files, temp exports). Run `make serve` from a cold shell. The server boots on http://127.0.0.1:8000 without errors; GET /api/health returns 200; GET / loads the page; GET /api/bolt/info with no query returns the default threaded bolt's info document (d, pitch, length, turns, volume, thread_depth, minor_diameter) with the threaded-rod warning first.
result: pass
note: "Run by the agent on 2026-10-13 at the owner's request. `make serve` from a cold shell, no server running, port 8000 free: log shows Started server process, Application startup complete, Uvicorn running on http://127.0.0.1:8000, no error lines. GET /api/health 200 {status ok, pool workers 2, queue_available 4}; GET / 200 text/html 1808 bytes; GET /api/bolt/info 200 with rows d 6.0, pitch 1.0, length 20.0, turns 20.0, thread_depth 0.5412658773652741, minor_diameter 4.917468245269452, volume 805.5542424753626 mm³. Deviation from the expected text only: since Phase 4 the default is 'Hexagon head screw ISO 4017 - M6 x 20' and the first warning is 'plain-cut thread ends, no tip chamfer or under-head fillet; not a product build', not the Phase 3 threaded-rod warning. Expected text was derived from the Phase 3 SUMMARYs; the app behaves as Phase 4 shipped it."

### 2. Repeated query key or CLI flag is refused naming it (03-04)
expected: `curl -s 'http://127.0.0.1:8000/api/bolt/info?d=8&d=9'` is a 422 `duplicate` naming `d`, before validation; the same on `/api/bolt/model.stl`. On the CLI, `screw info` with the same flag given twice exits 2 and names the flag. (Coverage block marked validation_failed: verification kind string invalid in 03-04-SUMMARY.md, so the parity test's pass is not auto-credited here.)
result: pass
note: "Run by the agent on 2026-10-13. GET /api/bolt/info?d=8&d=9 → 422 {loc [query, d], type duplicate, msg 'd was given more than once.'}; GET /api/bolt/model.stl?d=8&d=9 → 422; ?kind=bolt&kind=bolt → 422 naming kind. CLI: `screw info bolt --d 8 --d 9` → exit 2, 'screw info bolt: error: --d was given more than once (again as --d)'."

### 3. Page loads with `left_hand` in the schema and builds the right-hand part (03-04)
expected: Open http://127.0.0.1:8000/ with an empty hash. The form builds from /api/schema, the default bolt renders, no console error. (03-04 shipped the schema property before 03-05 gave it a checkbox; this confirms the page did not break in between and still builds the right-hand default.)
result: pass

### 4. Left-hand checkbox and thread hand in a browser (03-05)
expected: The Thread fieldset, after Size, shows a "Left-hand thread" checkbox, unchecked, at its natural width in both themes. Ticking it triggers a rebuild after the debounce and the preview's thread visibly reverses hand; unticking restores right-hand. app.js reads no field name or row key: the control comes from /api/schema alone. (No browser in the gate, L01.)
result: pass

### 5. `left_hand=true` round trip through hash, reload, Reset and Copy link (03-05)
expected: The link gains `left_hand=true` only while the checkbox is checked and loses it when unchecked. Reloading `/#left_hand=true` opens with the checkbox checked and the left-hand mesh. Reset unchecks it and drops the key. Copy link copies the current hash exactly.
result: pass

### 6. Link refusals in a browser (03-05)
expected: Each of `/#d=8&m=5`, `/#d=1&d=2`, `/#kind=bolt&kind=bolt`, `/#left_hand=banana`, `/#d=abc`, `/#d=` is refused with a message naming the key; the form is empty, the panel empty, downloads disabled, nothing builds. Then `/#d=8` opens normally. (`#d=abc` rests on the browser turning `abc` into an empty number input: browser behaviour, never run in the gate.)
result: pass

### 7. Per-mesh warnings stay with the mesh after a failed update or refused link (03-05)
expected: After a failing edit (a 422, a gate `build_error`, a lost connection) the last mesh, the text "Showing the last valid part" and that mesh's own warnings are on screen together below the error; the warnings change only when a new mesh replaces it; the startup failure shows none. (Fetch interleaving of info and STL is observable only in a running page.)
result: pass

### 8. 01-UI-SPEC.md describes the page as built (03-05)
expected: Read .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md rules 1, 2, 6, 9, 10, 15, 16, 19, 21, 24, 29, Copywriting, E2, E3, E5, E9, E10 and OI-2, OI-3, OI-7 against the running page. Each sentence says what the page does; no rule describes a control or a message the page no longer has. (Coverage block marked validation_failed in 03-05-SUMMARY.md.)
result: pass

### 9. Both UI debt items resolved and moved (03-05)
expected: docs/tech_debt/resolved/2026-10-06-ui-drops-foreign-hash-keys.md and docs/tech_debt/resolved/2026-10-06-ui-hides-warnings-on-failed-update.md exist with `Status: resolved` and a fix sha reachable from HEAD; docs/tech_debt/INDEX.md lists both under resolved and neither under active. (Coverage block marked validation_failed in 03-05-SUMMARY.md.)
result: pass
note: "Owner ruling 2026-10-13: pass. Measured: both files Status: resolved, INDEX rows under resolved, nothing ui- in active/. The Resolved in: shas 05fb4ed and 909dec3 are NOT reachable from main; they exist only on local branch gsd/phase-03-real-helical-thread, PR #10 squash-merged as 66d9393. Same for 5 other resolved records (de9304e, eaaac85, cfe00a4 on branches; ef37f23, 0e2f437 on no branch). Owner accepted branch shas as the citation; not filed as a gap."

### 10. First grid run on a GitHub runner is recorded and fits the timeout (03-06)
expected: bench/RESULTS.md section "### GitHub runner: run 38240380994 (2026-10-12)" records 15 of 15 shards green, 7160 rows, pytest wall and job wall per size, ref main at 57d05c6, trigger `schedule`. Slowest shard M20: 1686.74 s pytest, 29:03 job, against `timeout-minutes: 120`. Owner accepts the recorded numbers as the measurement 03-06 left open, and decides whether grid.yml's "UNVERIFIED" sizing comment and the 120 min timeout stay as they are.
result: pass
note: "Owner ruling 2026-10-13: numbers accepted; grid.yml's UNVERIFIED comment and timeout-minutes: 120 stay as they are."

### 11. L12 reads as the code behaves (03-07)
expected: docs/architecture/decision_log.md "## L12 — The bolt is the L11 thread behind a gate in screw.solid; turns, root radius and the over-budget fine STL are refused, never trimmed; left_hand is on every kind" names the builder, the gate, the caps, the pitch bound, the hand, the link refusals, the standing warning and the slow tier; every L11 value cites its run id; every probe figure is labelled. The owner reads the entry later phases will cite and finds no sentence that says something the code does not do. (A grep proved the terms present, not the sentences true.)
result: pass
note: "Owner read L12 (decision_log.md lines 428-538) on 2026-10-13: pass."

### 12. Default bolt is a gated ISO 68-1 thread (03-01, automated)
expected: The default bolt is one valid solid whose precise volume is within T_GATE of the closed form and more than 1 % from the old cylinder, with z exact and x/y within 1e-4.
result: pass
source: automated

### 13. Same gated thread on API STEP, CLI STL and the pool (03-01, automated)
expected: The default part is the same gated thread on the API STEP route, the CLI STL export and the worker pool.
result: pass
source: automated

### 14. Gate refuses wrong builds and never caches them (03-01, automated)
expected: The gate refuses wrong builds by volume and sign, never caches them, and runs in the fixed order count, validity, volume; lengths off whole turns build and end at their length; tiny lengths refuse before the kernel.
result: pass
source: automated

### 15. Broken export is a BuildError (03-01, automated)
expected: A broken export (exportStl False, STEP status not RetDone, bad STL header) is a BuildError and the collapsed-solid blocker is retired.
result: pass
source: automated

### 16. Pitch with no root radius is a 422 pitch_too_coarse (03-02, automated)
expected: A pitch with no root radius (including pitch=1e300) is a 422 pitch_too_coarse with ctx.fields [d, pitch] on both bolt routes and an exit-2 error naming d and pitch on the CLI, before any build.
result: pass
source: automated

### 17. Length past 250 turns is a 422 turn_cap (03-02, automated)
expected: A length past 250 turns, read as exact decimals, is a 422 turn_cap naming length and pitch, 250 and 2026-10-08-a-frontier; exactly 250 turns and all 15 measured rows are accepted.
result: pass
source: automated

### 18. Info document order, closed-form volume and standing warning (03-02, automated)
expected: The info document lists d, pitch, length, turns, volume, thread_depth, minor_diameter in that order with the closed-form volume, exact turns and the profile-labelled depth and minor diameter, and carries the threaded-rod warning first on the API and the CLI.
result: pass
source: automated
note: "Expected text is the Phase 3 contract (`66d9393`). Phase 4 (L13, `e8df305`) superseded it: the order on main is d, pitch, length, thread_length, shank_length, turns, thread_depth, minor_diameter, the head values, then volume (`tests/test_calc.py` KEYS), and the standing warning is 'plain-cut thread ends, no tip chamfer or under-head fillet; not a product build'. The pass is the automated coverage of the current contract (closed-form volume, exact turns, profile-labelled depth and minor diameter, warning first), not of the Phase 3 order or wording; same deviation as test 1."

### 19. Non-finite row is left out and explained (03-02, automated)
expected: A computed row that is not a finite number is left out and explained in warnings, and the standing warning stays first.
result: pass
source: automated

### 20. API refuses the fine STL above the bytes cap (03-03, automated)
expected: The API refuses the fine STL at each of L11's seven measured rows above its bytes cap with a 422 fine_stl_cap naming length, the cap in mm and turns and the run id, and the backend is never called.
result: pass
source: automated

### 21. Preview STL, STEP and info of a capped part are served (03-03, automated)
expected: The preview STL, the STEP and the info route of a capped part are served; the cap itself and an off-row part reach the backend as asked.
result: pass
source: automated

### 22. screw export refuses the same fine STL (03-03, automated)
expected: screw export refuses the same fine STL with exit 2, 'error: length:' and the run id, writes no file, and exports the same part as STEP or preview STL.
result: pass
source: automated

### 23. Capped part's info carries the refusal as a warning (03-03, automated)
expected: The info document of a capped part carries the refusal text as a warning after the standing warning; at the cap or off the measured rows the warnings stay the standing one only.
result: pass
source: automated

### 24. left_hand is a boolean on every kind's model (03-04, automated)
expected: left_hand is a boolean on every kind's model: default False, in the Thread group, ordered d, pitch, left_hand, length in the schema, the OpenAPI query and the CLI flags; an omitted key or flag means right-hand.
result: pass
source: automated

### 25. Left-hand rod is left-handed by an independent probe (03-04, automated)
expected: A left-hand rod is left-handed by an independent isInside probe (inside at -theta, outside at +theta; right-hand the reverse) and passes the same THRD-04 gate as the right-hand rod; the probe fails when the builder ignores the hand.
result: pass
source: automated

### 26. ?left_hand=true and --left-hand deliver the left-hand bytes (03-04, automated)
expected: ?left_hand=true on the API and --left-hand on the CLI deliver the left-hand solid's bytes; --no-left-hand and the omitted flag deliver the right-hand ones; ?left_hand=banana is a 422 on the field; a value after the flag exits 2.
result: pass
source: automated

### 27. Spike imports the moved maths and the protocol still matches (03-06, automated)
expected: The spike imports the moved maths, builder and estimator back from src/; the pre-registered protocol still matches the code and check-protocol holds.
result: pass
source: automated

### 28. Full measured grid runs in a slow tier (03-06, automated)
expected: The full measured grid runs through helical.thread and check_solid in a slow tier: 60 cells collected by -m grid, deselected by make verify, selected per size by make grid SIZE=.
result: pass
source: automated

### 29. grid.yml is dispatch + schedule only (03-06, automated)
expected: grid.yml is dispatch + schedule only, contents: read, one job per size, and neither ci.yml nor required-jobs.txt nor pr_land.py knows it.
result: pass
source: automated

### 30. Docs describe the bolt as a threaded rod (03-07, automated)
expected: overview.md, README.md, the package docstring and the bench docs describe the bolt as a threaded rod and name calc/thread.py, solid/helical.py, the gate and the grid tier; no tracked description outside the exempt records calls the bolt a cylinder.
result: pass
source: automated

### 31. INTERIM register lists the three bounds (03-07, automated)
expected: The INTERIM register lists MIN_TAIL_MM, MAX_TURNS and FINE_STL_ROWS with their sources and records the D-18 figures; still Severity must with the Phase 7 trigger.
result: pass
source: automated

### 32. Retired items name reachable fix commits (03-07, automated)
expected: Each of the four items Phase 3 retired names its fix commit in Resolved in: and in its INDEX row, and every sha is reachable from HEAD.
result: pass
source: automated
note: "The shas named (de9304e, 05fb4ed, eaaac85, 909dec3) exist but are not reachable from main: they are Phase 3 branch commits, squash-merged as `66d9393` (PR #10). Passed under the owner's ruling on test 9 (2026-10-13: branch shas accepted as the citation, not filed as a gap); the 'reachable from HEAD' clause as written does not hold on main."

### 33. Coverage floor re-measured (03-07, automated)
expected: The coverage floor is re-measured on the 843-test suite by spur L34's rule and fail_under equals its result (96).
result: pass
source: automated

## Summary

total: 33
passed: 33
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

