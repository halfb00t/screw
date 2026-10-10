---
phase: 02-thread-spike
plan: 07
subsystem: testing
tags: [thread-spike, campaign, quiet-gate, bench-results, d-17, d-18, sha256]

requires:
  - phase: 02-thread-spike
    provides: the pre-registered protocol on main (fd40abc), the harness, the run guard and the one-command campaign driver (plans 02-02 to 02-06)
provides:
  - "bench/results/thread-spike/: nine block records (2026-10-08-a-<block>.jsonl and .md for ksweep, grid, frontier, ladder, trim, controls, rss, pair, container) and the campaign log 2026-10-08-a-campaign.md"
  - "bench/RESULTS.md section '## Thread spike (Phase 2)': one entry per block and one for the campaign, each with run window, platform, HEAD, protocol blob/commit, quiet-gate release and readings, JSONL path/line count/sha256, the output verbatim, and a short what-it-shows paragraph"
  - "the campaign's verdict output, recorded verbatim and uninterpreted: not a pass, escape clause fired for M18 pair"
affects: [02-08 verdict and decision entry]

actuals:
  tokens: 4097819   # chars/4 over the added lines of `git diff 32cdeac af790ea` (16 391 277 chars, 20 files); dominated by the verbatim outputs and the nine JSONL files, not by authored prose
  tasks: 3
  commits: 1        # MEASURED: git rev-list --count 32cdeacce53cedc2fe3791d27104b599197f45e9..af790ea (the records commit; this file's metadata commit follows it)
plan_head_before: 32cdeacce53cedc2fe3791d27104b599197f45e9
plan_head_after: af790ea8615b8bee0ca6162d459a54792e9fe52d

tech-stack:
  added: []
  patterns:
    - "RESULTS.md entries are built by a script that cats each run's own .md into a fenced block, then proven byte-identical with awk + cmp, so no transcription step exists between the run and the record"

key-files:
  created:
    - bench/results/thread-spike/2026-10-08-a-ksweep.jsonl
    - bench/results/thread-spike/2026-10-08-a-ksweep.md
    - bench/results/thread-spike/2026-10-08-a-grid.jsonl
    - bench/results/thread-spike/2026-10-08-a-grid.md
    - bench/results/thread-spike/2026-10-08-a-frontier.jsonl
    - bench/results/thread-spike/2026-10-08-a-frontier.md
    - bench/results/thread-spike/2026-10-08-a-ladder.jsonl
    - bench/results/thread-spike/2026-10-08-a-ladder.md
    - bench/results/thread-spike/2026-10-08-a-trim.jsonl
    - bench/results/thread-spike/2026-10-08-a-trim.md
    - bench/results/thread-spike/2026-10-08-a-controls.jsonl
    - bench/results/thread-spike/2026-10-08-a-controls.md
    - bench/results/thread-spike/2026-10-08-a-rss.jsonl
    - bench/results/thread-spike/2026-10-08-a-rss.md
    - bench/results/thread-spike/2026-10-08-a-pair.jsonl
    - bench/results/thread-spike/2026-10-08-a-pair.md
    - bench/results/thread-spike/2026-10-08-a-container.jsonl
    - bench/results/thread-spike/2026-10-08-a-container.md
    - bench/results/thread-spike/2026-10-08-a-campaign.md
  modified:
    - bench/RESULTS.md

key-decisions:
  - "Host mismatch option A (owner, 2026-10-08): run on the M5 Max host without amending the protocol's Environment section; the kernel pair is identical, so the protocol's re-measure trigger did not fire"
  - "Owner ruling R4 overridden by the owner (2026-10-08): the campaign ran from the orchestrating agent session with other applications open; each block's own readings, not the orchestrator's observations, decide whether it is decisive"
  - "Non-decisive blocks (ksweep, grid, frontier, container) are recorded as non-decisive; nothing was re-run toward a pass"

patterns-established:
  - "A records commit stages only bench/RESULTS.md and bench/results/thread-spike/; the harness files stay byte-identical to origin/main (git diff --quiet origin/main -- bench/thread_spike bench/quiet.py)"

requirements-completed: [INFR-03]

coverage:
  - id: D1
    description: "The nine block records and the campaign log are committed under bench/results/thread-spike/ and every JSONL's sha256 appears in bench/RESULTS.md"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "the plan's sha256 loop over bench/results/thread-spike/*.jsonl against bench/RESULTS.md (exit 0, n=9)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Each embedded output in bench/RESULTS.md equals its .md file byte for byte (nine block entries plus the campaign entry)"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "awk extraction of each entry's first fenced block, then cmp against bench/results/thread-spike/2026-10-08-a-<block>.md (10 of 10 identical)"
        status: pass
    human_judgment: false
  - id: D3
    description: "bench/thread_spike/ and bench/quiet.py are identical to origin/main's, so what was measured is the code that was reviewed"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "git diff --quiet origin/main -- bench/thread_spike bench/quiet.py (exit 0), re-run after the commit"
        status: pass
    human_judgment: false
  - id: D4
    description: "make verify is green with the records in place"
    requirement: INFR-03
    verification:
      - kind: other
        ref: "make verify (ruff, mypy --strict, 7 contracts kept, 695 passed in 28.22s, coverage 95.56%); also run by the pre-commit hook on the records commit"
        status: pass
    human_judgment: false
  - id: D5
    description: "The campaign ran under conditions that differ from the protocol's: a different host than the registered one, and ruling R4 overridden so agents and applications stayed open. Whether the four non-decisive blocks are acceptable evidence for the plan 02-08 decision is a call for the owner."
    requirement: INFR-03
    verification: []
    human_judgment: true
    rationale: "The owner made both departures knowingly on 2026-10-08. Whether the resulting record is good enough for the decision entry (which verdict inputs are non-decisive, which timings are unestablished) is interpretation, which belongs to plan 02-08 and the owner, not to this recording plan."

duration: 8 min
completed: 2026-10-09
status: complete
---

# Phase 2 Plan 07: Campaign Run Record Summary

**The pre-registered thread spike campaign `2026-10-08-a` ran once (nine blocks, 11:01Z to 01:11Z over 2026-10-08 and 2026-10-09) on an M5 Max under owner overrides of the host and of R4, and its outputs, raw records and sha256 hashes are committed verbatim with five blocks decisive, four non-decisive, and a verdict that reads "not a pass".**

## Performance

- **Duration:** 8 min for this session (record, verify, commit). The campaign itself ran 2026-10-08T11:01:06Z (first gate reading of ksweep) to 2026-10-09T01:11:06Z (container end reading), about 14 h 10 min. Task 1 was done in an earlier session on 2026-10-08.
- **Started (this session):** 2026-10-09T01:15Z (approximate)
- **Completed:** 2026-10-09T01:24Z (approximate; the metadata commit follows)
- **Tasks:** 3 (Task 1 done earlier and re-confirmed; Task 2 not executed as written, see Deviations; Task 3 done)
- **Files modified:** 20 in the records commit (nine `.jsonl`, nine `.md`, the campaign log, `bench/RESULTS.md`)

## Accomplishments

- Run-id prefix `2026-10-08-a`: all nine blocks and the campaign log are on disk and committed; none was restarted, interrupted or refused.
- `bench/RESULTS.md` now has `## Thread spike (Phase 2)` (lines 243 on) with ten `### 2026-10-08-a-...` entries, built by concatenation and proven byte-identical to the run files.
- Decisive: **ladder** (released 2026-10-08T19:31:21Z), **trim** (19:36:55Z), **controls** (19:39:55Z), **rss** (19:42:50Z), **pair** (20:01:15Z). Non-decisive: **ksweep**, **grid**, **frontier** (each "non-decisive after 900 s (31 readings)"), and **container** (non-decisive by construction: linux/amd64 under emulation, gate read at 2026-10-08T23:31:33Z).
- The campaign log's verdict is recorded verbatim and not interpreted (that is plan 02-08): "selected K: 3"; "estimator: precise; max abs error 8.147e-06; T_gate 9e-05"; "pass bar: held" with "mesh checks skipped: 1025 of 7160 meshes unchecked"; "escape clause: FIRED" with "pair: not falsifiable for size M18 (right, left hand)"; turn caps "not established (non-decisive gate)" in the seconds column; "**Verdict:** not a pass: see the sections above"; then "campaign finished".

## Task 1 evidence (done 2026-10-08, no commit; cheap checks re-run 2026-10-09)

| Check | Command | Result |
|---|---|---|
| Guard | `.venv/bin/python -m bench.thread_spike check-protocol` | exit 0, "protocol guard: held"; origin/main protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`, HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9` (re-run 2026-10-09T01:17Z, identical) |
| Image | `make image`, then `docker image inspect screw:latest --format '{{.Id}} {{.Created}} {{.Architecture}} {{.Os}}'` | `sha256:7d992a89557b01bf2e35e0d368f8b68fd11e9c2774bbdfb45a26f1f7a31638f6 2026-10-08T16:52:13.591964824+06:00 amd64 linux` (10:52:13Z; re-run 2026-10-09T01:17Z, identical) |
| Reference package | `PYTHONPATH="$HOME/.cache/screw-spike/cq_warehouse-daa4650" .venv/bin/python -c "import cq_warehouse.thread"` | exit 0 (re-run 2026-10-09, exit 0). Scratch checkout of cq_warehouse at `daa46507ecc429c0e2dce11d9d5ffd09b12a42af`, installed outside the repo with `--no-deps` |
| Disk | `df -h .` | 1.7 TiB free at Task 1; 1.6 TiB free at 2026-10-09T01:17Z (threshold 50 GiB) |
| Harness health | `.venv/bin/python -m bench.thread_spike smoke` | exit 0 (M6 right hand 5 turns, class `ok`, relative error +1.694e-06, watertight). Not recorded, as the plan says; not re-run |
| Prefix | `ls bench/results/thread-spike/` | none existed; chosen `2026-10-08-a` |

## Task Commits

1. **Task 1: Prepare the host run** - no commit (checks and an image build only), as the plan requires.
2. **Task 2: Owner runs the campaign** - no commit; not executed as written (see Deviations).
3. **Task 3: Record every block verbatim and commit the raw records** - `af790ea8615b8bee0ca6162d459a54792e9fe52d` (docs: `docs(02-07): record the thread spike campaign 2026-10-08-a verbatim with its raw records`)

**Plan metadata:** the `docs(02-07): complete the campaign run plan` commit that carries this file (hash in the return message).

## Files Created/Modified

- `bench/RESULTS.md` - gains the `## Thread spike (Phase 2)` section (4906 added lines; the file is now 5147 lines)
- `bench/results/thread-spike/2026-10-08-a-<block>.jsonl` and `.md` for ksweep, grid, frontier, ladder, trim, controls, rss, pair, container - the raw per-row records (header line, then one line per row) and each run's Markdown output
- `bench/results/thread-spike/2026-10-08-a-campaign.md` - the campaign log with the verdict output

JSONL line counts and sha256 (computed with `wc -l` and `shasum -a 256` on 2026-10-09T01:17Z, and again from the committed blobs):

| Block | Lines | sha256 |
|---|---|---|
| ksweep | 193 | `b37e51137000318eda411215671e4b1e865c2bc6c769be01b27be2b07b5ea73a` |
| grid | 7161 | `365b059f3f54036b663c7898b3041c25d80a7c439cc03131f03999b5f3e947bb` |
| frontier | 2237 | `f8e95669384442f816aa426f254c8a73d7bbe3fe33999f46607bb63b3ebba781` |
| ladder | 17 | `5ab37e15d8ab45f72f31f3dc907cc2bfa2dddc33b35d06e104352202d582e5c2` |
| trim | 31 | `967b3a6bc72ca423af08e24fde94da83a6d510f16cc058bb6afaca81ee17c185` |
| controls | 86 | `723564de2ccce0783288d29bf7315585c3e40b5aa5263acad8baaa458cfd68de` |
| rss | 91 | `b23c2cb92965f90cf1903069a9b868e75195442ba65ebb234c5fde95abd78dd5` |
| pair | 273 | `1644650ed5b418fc2b43bfa8fd875d371f0fc4940018f67b5b3241df6c84d9f3` |
| container | 7161 | `2b88dd843e05f97f0f992ca6a1abc8c1a0ab2bf01e49a8c818606b0d41a9be47` |

## Verification

| Check | Command | Result |
|---|---|---|
| Every JSONL hash is in RESULTS.md | the plan's loop (`for f in bench/results/thread-spike/*.jsonl; do ... grep -q "$h" bench/RESULTS.md ...`) | exit 0, no output, n = 9 |
| Harness unchanged; section present | `git diff --quiet origin/main -- bench/thread_spike bench/quiet.py && grep -n '^## Thread spike (Phase 2)' bench/RESULTS.md` | exit 0; `243:## Thread spike (Phase 2)`. Re-run after the commit: still exit 0, and `git diff --name-only origin/main..HEAD` lists no file under `bench/thread_spike/` or `bench/quiet.py` |
| Gate | `make verify` | exit 0: "All checks passed!", "Success: no issues found in 43 source files", "Contracts: 7 kept, 0 broken.", "695 passed in 28.22s", coverage 95.56 % (the pre-commit hook ran it again on the commit and passed) |
| Byte equality | for each of the 9 blocks and the campaign: `awk` extracts the first fenced block after `### 2026-10-08-a-<name>` / `Output verbatim:`, `cmp -s` against `bench/results/thread-spike/2026-10-08-a-<name>.md` | 10 of 10 byte-identical (grid 94 902 bytes, campaign 76 667 bytes among them) |
| Committed JSONL equals disk | `git show HEAD:<file> \| shasum -a 256` against the file | no mismatch for 9 of 9 |
| Guard after commit | `check-protocol` | "protocol guard: held" |

No `.md` file contains a line starting with three backticks, so a three-backtick fence was used throughout (checked with `grep -l '^```'` before building).

## Acceptance criteria (Task 3)

| Criterion | Evidence | Result |
|---|---|---|
| One `### <prefix>-<block>` entry per block file plus `### <prefix>-campaign` | `grep -c '^### 2026-10-08-a-' bench/RESULTS.md` = 10 (9 blocks + campaign) | PASS |
| Every JSONL sha256 in RESULTS.md; every embedded output equals its .md | loop exit 0; 10 of 10 `cmp` identical | PASS |
| Every entry states decisive or non-decisive with timestamped readings at start and end | each entry carries the release line, gate reading count, first and last gate readings with UTC times, and the end reading with its time and the "includes this run's own load" label | PASS |
| `bench/thread_spike/` and `bench/quiet.py` unchanged against origin/main | `git diff --quiet origin/main -- bench/thread_spike bench/quiet.py` exit 0 | PASS |
| Task 1: guard holds, image amd64 and fresh, reference package imports, smoke exits 0 | see the Task 1 table | PASS |
| Task 1: SUMMARY notes image id, creation time, prefix | this file | PASS |
| Task 2: log ends with "campaign finished"; block files exist | log tail reads "campaign finished" then "make: *** [Makefile:167: bench.thread] Error 1"; all block files exist | PASS, but Task 2 was not run as written (see Deviations) |

## Decisions Made

- Both departures from the protocol's registered conditions are stated at the head of the RESULTS.md section as plain fact, not buried in an entry, so a reader of any single block sees them.
- Per-block paragraphs name only facts already in the block's output (row counts, classes, release status, the output's own caveats such as "UNVERIFIED") and add no figure; interpretation is left to plan 02-08.
- The entries repeat the gate's first, last and end readings with their times and say "every reading is in the output below" rather than retyping all readings, so the full list exists in exactly one place per block (the verbatim output).

## Deviations from Plan

### Task 2 not executed as written

**1. [Plan deviation, owner-directed] Task 2 (`checkpoint:human-action`) was replaced by an owner decision**
- **Found during:** Task 2 (Owner closes every agent session and runs the campaign detached on a quiet host)
- **Plan said:** the owner closes every agent session (this one too) and starts the campaign from a plain terminal, because an open agent session keeps the host load near 2.0, above the 1.5 bar (D-17, owner ruling R4).
- **What happened:** on 2026-10-08 the owner declined to idle for a day. His words: "No, I don't want to idle for the whole day. Run yourself as is, I won't exit any app".
  - **Host mismatch, option A:** run without amending the protocol's Environment section. The protocol registers `Apple M2 Max, 12 CPUs, arm64, 32 GiB RAM` and Python 3.12.13; the host that ran is Apple M5 Max, 18 CPUs, arm64, 64 GiB RAM (68719476736 bytes), macOS 27.0.1 (build 26A434), Python 3.12.15. The kernel pair is identical to the protocol's (cadquery 2.8.0, cadquery-ocp 7.9.3.1.1), so the protocol's re-measure trigger did not fire.
  - **R4 overridden by the owner:** the campaign was launched by the orchestrating Claude Code session, with agent sessions and other applications open, not from a plain terminal with agents closed.
- **Launch:** from the orchestrator session at about 2026-10-08T11:01Z, branch `gsd/phase-02-thread-spike-runs` at HEAD `32cdeac`, with `SCREW_SPIKE_CQW="$HOME/.cache/screw-spike/cq_warehouse-daa4650"` and `DOCKER_DEFAULT_PLATFORM=linux/amd64`: `nohup caffeinate -i make bench.thread ARGS="campaign --run-id 2026-10-08-a" > "$HOME/screw-campaign-2026-10-08-a.log" 2>&1 & disown`. Python pid 23960.
- **Run window:** first gate reading 2026-10-08T11:01:06Z (ksweep header); the campaign log ends with "campaign finished"; the process was gone at the orchestrator's 2026-10-09T01:13:36Z check. The console log is `$HOME/screw-campaign-2026-10-08-a.log` (outside the repo; 349 402 bytes).
- **Handling:** no block was restarted, interrupted or refused; the orchestrator only watched files. The host carried other load throughout (other agent CLIs, an LLM server, the terminal). The orchestrator saw 1-minute load between about 1.1 and 12.5; the numbers recorded in RESULTS.md are each block's own readings, not those observations.
- **Effect on the record:** the quiet gate did what it is built to do. Four blocks did not release (ksweep, grid, frontier: "non-decisive after 900 s (31 readings)"; container is non-decisive by construction) and are recorded as non-decisive. Five blocks released as decisive once load fell (ladder, trim, controls, rss, pair).
- **Files modified:** none (a process deviation).
- **Committed in:** not applicable; recorded in the RESULTS.md section head and here.

---

**Total deviations:** 1 owner-directed (Task 2), no auto-fixed code deviations. **Impact on plan:** the run is not the plan's quiet-terminal run and is not on the registered host. Both facts are in the record. The harness, protocol and code are untouched, so what ran is what was reviewed. Whether the non-decisive blocks are enough for the decision is plan 02-08's and the owner's call (coverage item D5).

## Issues Encountered

- **Campaign exit code.** The console log ends "campaign finished" followed by `make: *** [Makefile:167: bench.thread] Error 1`. The `campaign` command's help text says it "exits 1 unless clean", and the verdict reads "not a pass", so the exit is the designed one for that verdict, not a crash. Recorded in the campaign entry.
- **Container reported unhealthy (orchestrator's observation; cause inferred, not verified).** During the container block, `docker ps` showed the worker container `screw-spike-23960-0` as "Up 2 hours (unhealthy)". The image's HEALTHCHECK probes the web app's `/api/health`, and the spike worker does not run the web app, so the probe cannot pass. There is no restart policy and no effect on the rows: all 7160 container rows read class ok. Not a defect claim.
- **Size of RESULTS.md.** Owner ruling R3 says RESULTS.md carries each run's header, host state, load readings and every non-ok or over-budget row, with the raw output in `bench/results/thread-spike/`. This plan's Task 3 and its acceptance criterion require the whole `.md` verbatim in RESULTS.md and byte-equal to the run file, so RESULTS.md grew by 4906 lines (to 5147). The plan was followed. If the file's size is a concern for later readers, that is a decision for the owner; nothing was filed.
- No harness defect was found, so no stop-and-surface was needed. No tech-debt or idea item was filed.
- The `.planning/WINDOWS.md` broken-windows ledger was not appended: the two departures are owner-accepted and documented, and not stubs, skipped tests or unrun verifies. The orchestrator may add a `deviation` entry if the ship gate should see them.

## Known Stubs

None. This plan wrote records and prose only; no source, UI or data-source code.

## Threat Flags

None. No network endpoint, auth path, file-access pattern or schema was added. Threat register T-02-20, T-02-21 and T-02-22 are mitigated as planned: outputs are embedded by concatenation and byte-compared (T-02-20), each entry repeats the release status and timed readings and nothing was re-run toward a pass (T-02-21), and the harness diff against origin/main is empty with the guard holding (T-02-22).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for plan 02-08 (reproducible verdict, Results and Verdict by citation, owner decision, L11). Its inputs are on disk and in RESULTS.md with hashes; the campaign verdict reads "not a pass" with the escape clause fired for M18, and four of nine blocks are non-decisive. None of that is interpreted here.
- Blocker for the owner to weigh in 02-08, not for this plan: the non-decisive ksweep, grid and frontier blocks mean the seconds-based turn caps read "not established (non-decisive gate)". The plan forbids re-running toward a pass, so any change to that is a new, visible decision.

## Self-Check: PASSED

- FOUND: `bench/RESULTS.md` (section at line 243), `bench/results/thread-spike/2026-10-08-a-campaign.md` and all nine `.jsonl` and nine `.md` block files (19 files under `bench/results/thread-spike/`).
- FOUND: `af790ea8615b8bee0ca6162d459a54792e9fe52d` is an ancestor of HEAD (`git merge-base --is-ancestor`).
- Verification commands and byte-equality proofs re-run above; all pass.

---
*Phase: 02-thread-spike*
*Completed: 2026-10-09*
