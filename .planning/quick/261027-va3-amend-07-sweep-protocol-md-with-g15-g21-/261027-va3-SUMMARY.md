---
phase: quick-261027-va3
plan: 01
status: complete
commits: 10
plan_head_before: 8aa143fa959f3bf34c2ac3c8bcc32e68abbc1caa
plan_head_after: e30affe
requirements: [OPER-01, OPER-02, OPER-03]
---

# Quick 261027-va3: fold G15 to G23 into 07-SWEEP-PROTOCOL.md Summary

R12, R16, R19, R21, R22, R23, R25, R28 and the header of the Phase 7 protocol are amended in the protocol's own voice, one commit and one key-phrase test per gap, and the owner's G22, G23 and reading of G16 are recorded in 07-GAP-RULINGS.md.

## Branches

- Rulings commit: `gsd/phase-07-operability-re-sweep`, main checkout.
- Protocol commits: `gsd/phase-07-preregistration-a3`, worktree `/Users/half/git/halfb00t/screw/.claude/worktrees/phase-07-preregistration-a2`, created with `switch --no-track` off `origin/main`. No upstream. Not pushed. No PR.
- BASE (equals `origin/main`): `8aa143fa959f3bf34c2ac3c8bcc32e68abbc1caa`.

## Commits

| Sha | Branch | Gap | Subject |
|---|---|---|---|
| 2777bb7 | gsd/phase-07-operability-re-sweep | G22, G23, G16 reading | docs(07): record the owner's rulings on G22 and G23 and the reading of G16 |
| b88a9fc | gsd/phase-07-preregistration-a3 | G15 (R19) | docs(07): pass a gzip level at every STL bound point and compare level 9 with the adopted level |
| 02cd0cd | gsd/phase-07-preregistration-a3 | G16 (R21) | docs(07): size the export cache from the explore parts ok at all three artifacts by their level-1 gzip bytes |
| fe61e00 | gsd/phase-07-preregistration-a3 | G17 (R23) | docs(07): keep the arena trim only if memory.current of Z(A) is lower at every artifact |
| 37347e7 | gsd/phase-07-preregistration-a3 | G18 (R25) | docs(07): take the health wall from the HEALTHCHECK command over the picked N's load readings |
| 7fd91f8 | gsd/phase-07-preregistration-a3 | G19 (R28) | docs(07): build the dense boundary from bolts at the 15 sizes, coarse pitch and the largest admitted turns |
| 0acf53a | gsd/phase-07-preregistration-a3 | G20 (R16, R22) | docs(07): ship the larger of the mem_limit built from W and the one built from W(K) |
| 946bf57 | gsd/phase-07-preregistration-a3 | G21 (R12) | docs(07): widen the envelope on the R19 gzip and R23 arena readings |
| c81d4b5 | gsd/phase-07-preregistration-a3 | G22 (R19, R23) | docs(07): stop the phase when a max the gzip or arena comparison needs is missing |
| e30affe | gsd/phase-07-preregistration-a3 | G23 (header) | docs(07): name plans 07-03 to 07-21 in the protocol header |

The G15 to G23 subjects each end with the gap id in parentheses.

## Verification

- `make verify` in the A3 worktree after the last commit: `======================= 4037 passed in 153.80s (0:02:33) =======================`. ruff, mypy, import boundaries and the unfinished-work scan passed in the same run. The pre-commit hook ran `make verify` on every commit.
- The plan's final automated check printed `ALLOK`: nine commits since `origin/main`, G15 to G23 once each, the diff touches only `07-SWEEP-PROTOCOL.md` and `tests/test_oper.py`, no gap label in the protocol, no `bench/points` change, no upstream.
- The main checkout's dirty files (`.planning/state.json`, `HANDOFF.json`, `ui-reviews/`, the phase 05 `.continue-here.md`, the phase 06.1 `.gitkeep`, the quick task dir) were not staged and are unchanged. The rulings commit holds `07-GAP-RULINGS.md` only.

## Deviations from Plan

**1. [Commit trailer] Used `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`, not `Claude Opus 5.5`.**
- The plan and the orchestrator constraints name Opus 5.5. The session's attribution rule names the model that actually ran, Sonnet 5.5, and an Opus trailer would credit a model that did not write the commits.
- All ten commits carry the Sonnet 5.5 trailer. If the owner wants Opus, the commits need a trailer rewrite before the push; this is the owner's call.

**2. [Formatting] Rewrapped R23's `max_tasks_per_child` sentence in the G22 commit.** G17's insertion had left one line of about 120 characters; the G22 edit touched the same paragraph, so the paragraph is rewrapped to about 100. Wording is unchanged.

Otherwise: plan executed as written. Every planned replaced-text quote matched after whitespace normalisation (the file wraps lines differently from the plan's quotes), and no ruling needed an approximation.

## Open item

- **Q5 is still open:** R6 has no shard-charge rule for the R19 gzip set or the R23 arena set. 07-15-PLAN.md charges each such part its explore group's largest `wall_s`, but no rule states it, and a gzip reading also compresses at levels 6 and 9, which an explore wall does not include. R30 freezes R6 at the first runner reading, so the owner should rule before 07-05. Out of scope here.

## Known Stubs

None.

## Filed items

No tech-debt or idea file was filed.

## Next steps (the owner's)

1. Push `gsd/phase-07-preregistration-a3` and open PR A3.
2. Merge PR A3.
3. Merge `main` into `gsd/phase-07-operability-re-sweep` before 07-05 takes its first reading.

## Self-Check: PASSED

All ten shas are on their branches (`git log` listed the nine A3 commits; 2777bb7 is the phase-branch tip). The protocol and test file exist in the A3 worktree.
