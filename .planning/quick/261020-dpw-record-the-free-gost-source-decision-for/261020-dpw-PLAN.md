---
phase: quick-261020-dpw
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - docs/requirements/standards-sources.md
  - docs/requirements/README.md
  - docs/architecture/decision_log.md
  - docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md
  - docs/tech_debt/INDEX.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md
  - .planning/STATE.md
autonomous: true
requirements: [TABL-04]

estimate:
  tokens: 40000
  raw_tokens: 40000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "docs/requirements/standards-sources.md exists. It maps each ISO document Phase 5 needs (ISO 4032:2023, ISO 4014:2022, ISO 724:2023, ISO 965-2:2024, ISO 4753) to the GOST text read instead, with its relation to ISO and its free-text URL. It warns that DIN 934 and GOST 5915-70 are not equivalent. It records the BIS alternatives that were not chosen. It flags every edition gap as UNVERIFIED. It lists all 12 source URLs. It contains no millimetre value from any standard (05 D-16)"
    - "docs/architecture/decision_log.md ends with an L14 entry. L14 quotes the owner's reply of 2026-10-20 and records the GOST-only choice. It narrows TABL-04 and 05 D-14, D-15 and D-16. It keeps ruling-B double entry. It says the 6g/6H limits are derived (GOST 24705-2004 basic plus GOST 16093-2004 deviations) and labelled derived. It requires every Source and panel label to name the GOST designation and the ISO edition that designation adopts. It makes the M6 s/m cross-check a stop-and-ask before plan 05-06. It says the pending plans 05-06 to 05-18 are amended when the phase resumes. Its revisit trigger is the debt item. No line above L14 changes"
    - "docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md exists from TEMPLATE.md with Severity: must and a named trigger. It lists the five ISO documents to buy, gives the owner's ~$400 figure, and has the owner's sign-off line for the 2026-10-20 deferral. docs/tech_debt/INDEX.md has its row under ## Active"
    - "05-OWNER-READS.md gains one added, dated note that points to L14. The recorded s 10.0 / m 5.2, the permanence line and the rulings R1 to R13 are byte-identical (git diff shows 0 deleted lines)"
    - "In .planning/STATE.md, the Phase 5 precondition bullet and the ISO 4753 bullet under Blockers/Concerns point to L14 and the debt item. They no longer say the owner holds the Phase 5 ISO texts"
    - "`make verify` passes standalone and again in the pre-commit hook. One commit `docs: source Phase 5 table values from free GOST equivalents` contains exactly the seven files above and ends with the Co-Authored-By trailer"
  artifacts:
    - path: "docs/requirements/standards-sources.md"
      provides: "the ISO-to-GOST source map, the not-equivalent warning, the not-chosen alternatives, the UNVERIFIED edition gaps, the Sources list"
      contains: "GOST ISO 4032-2014"
    - path: "docs/architecture/decision_log.md"
      provides: "L14, the locked GOST-only source decision"
      contains: "## L14 "
    - path: "docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md"
      provides: "the deferred ISO purchase, Severity must, named trigger, owner sign-off"
      contains: "Severity: must"
    - path: "docs/tech_debt/INDEX.md"
      provides: "the Active row for the debt item"
      contains: "active/2026-10-20-iso-standards-not-purchased.md"
  key_links:
    - from: "docs/architecture/decision_log.md L14"
      to: "docs/requirements/standards-sources.md"
      via: "L14 names the doc as the source map"
      pattern: "standards-sources.md"
    - from: "docs/architecture/decision_log.md L14"
      to: "docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md"
      via: "L14's revisit trigger is the debt item"
      pattern: "2026-10-20-iso-standards-not-purchased.md"
    - from: ".planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md"
      to: "docs/architecture/decision_log.md L14"
      via: "the dated note names L14"
      pattern: "L14"
---

<objective>
Record the owner's decision of 2026-10-20 in the repository. Phase 5 reads its table values from free
GOST (Russian interstate) texts that adopt the ISO standards, instead of buying the ISO PDFs. Buying
the ISO texts becomes Severity-must debt with a named trigger. Docs only, no code.

Purpose: Phase 5 is stopped on the precondition "owner holds purchased copies" (05 D-14, TABL-04).
The owner lifted that precondition by decision, not by purchase. The decision has to be locked in the
decision log (single source of locked decisions), the source map has to live in one durable document,
and the deferred purchase has to survive as debt (CLAUDE.md "Capturing ideas and debt"). Otherwise the
next Phase 5 executor either stops for good or reads from an unsanctioned source.

Output: one new reference doc, decision L14, one debt item plus its INDEX row, pointer notes in
05-OWNER-READS.md and STATE.md, one commit.

Owner's literal reply (quote verbatim in L14 and in the debt item): "put this table description and
sources into a document and choose second option. I don't want to spend $400 for MVP so lets put ISO
into a techdebt". Option 2 = GOST only: one source family, every text free to read, but every edition
is 2012 or older, so each one lags the ISO edition the plans name.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/STATE.md
@docs/architecture/decision_log.md
@.planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md
@docs/tech_debt/TEMPLATE.md
@docs/tech_debt/INDEX.md
@docs/requirements/README.md

Read only these ranges of the large files:
- docs/architecture/decision_log.md lines 1-30 (header, entry shape) and lines 558-820 (L13 in full: the Date line, bold lead-ins, the "Reason:" and "Reversibility:" closers, the ruling-B paragraph).
- .planning/phases/05-hex-nut-and-kernel-pair-proof/05-CONTEXT.md lines 188-221 (D-14, D-15, D-16).
- docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md (the house shape of a filled-in debt item).

## Planner decisions (Claude's discretion, documented)

- **Where the source map lives: docs/requirements/standards-sources.md.** docs/requirements/README.md says the directory holds "what stays true after a phase is archived". The source map governs every table row from Phase 5 on, the Phase 6 release trigger and any later ISO re-read, so it outlives the phase. .planning/ is phase-scoped. docs/architecture/ holds the system map and the decision log, and this map is reference data that L14 cites, not a decision. Because the README currently says nothing is written there yet, it gets a surgical pointer edit.
- **STATE.md is edited surgically (two Blockers/Concerns bullets).** STATE.md is the first file every session reads. Its Phase 5 precondition bullet still says the owner holds the Phase 5 ISO texts, and L14 retires that claim. ROADMAP.md (Phase 5 precondition, line 230) and REQUIREMENTS.md (TABL-04) are NOT edited here. L14 names both as narrowed, and their text is amended with the Phase 5 plan amendments when the phase resumes, the same rule the brief sets for the plans.
- **Spelling.** In English prose use the Latin form `GOST`. standards-sources.md gives the Cyrillic proper name `ГОСТ` once per designation, beside the Latin form.
- **Open question, recorded and not resolved (an evidence conflict).** The owner's purchase list names ISO 4014:2022. L13 records Phase 4's ISO 4014:2022 rows as read from the purchased copy, with the agent's second copy taken from preview pages under ruling A-3 (04-OWNER-READS.md). Nothing records why ISO 4014:2022 is on the list. L14 and the debt item state both facts. L14's rule for a new ISO 4014 value (R1's fillet r,min, plan 05-12) is: read it from the owner's ISO 4014:2022 copy if that copy holds it, else from GOST ISO 4014-2014. Which applies is asked at 05-12's precondition. Phase 4's shipped rows are untouched.
</context>

<source_facts>
Web research of 2026-10-19, supplied by the orchestrator. These facts are recorded and cited, not
re-researched. Copy designations, relations, dates and URLs exactly. Copy no dimension value
(05 D-16: no standard value enters the repository except recorded answers).

Chosen GOST map (option 2):

| ISO named by Phase 5 | Used for | GOST read instead | Relation to ISO | Free text |
|---|---|---|---|---|
| ISO 4032:2023 | nut rows (s, m, e, mw, dw, the chamfer read) | GOST ISO 4032-2014 / ГОСТ ISO 4032-2014 | IDT ISO 4032:2012; in force 2017-01-01; replaced the coarse-thread part of GOST 5915-70 | https://cn.gostinfo.ru/catalog/Details/?id=6101733 ; https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/2/gost_ISO_4032-2014_mezhgosudarstvennyy_standart_gayki.html |
| ISO 4014:2022 | a new ISO 4014 value only (R1's fillet r,min); Phase 4 rows unchanged | GOST ISO 4014-2014 / ГОСТ ISO 4014-2014 | adopts ISO 4014:2011 (degree of equivalence not recorded) | https://base.garant.ru/70815754/ |
| ISO 724:2023 | basic d2, D1, D2 (R13: agreement test only) | GOST 24705-2004 / ГОСТ 24705-2004 | MOD ISO 724:1993 | https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/4/gost_24705-2004_iso_724_1993_mezhgosudarstvennyy_standart.html |
| ISO 965-2:2024 | 6g / 6H limits | GOST 16093-2004 / ГОСТ 16093-2004 | based on ISO 965-1:1998 and ISO 965-3:1998, NOT a copy of ISO 965-2. It prints deviations and tolerances, so each limit is derived: basic (GOST 24705-2004) plus deviation (GOST 16093-2004) | https://dnaop.com/html/65576/doc-%D0%93%D0%9E%D0%A1%D0%A2_16093-2004 |
| ISO 4753 (the plans name no edition; the debt buys ISO 4753:2011) | tip end form (D-09, R2) | GOST 12414-94 / ГОСТ 12414-94 | authentic text of ISO 4753-83 plus two extra stepped ends (cone, sphere) that are not ISO ends | https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/10/gost_12414-94_iso_4753-83_mezhgosudarstvennyy_standart.html |

Not equivalent (must not be used): DIN 934 and GOST 5915-70 are the pre-ISO national nuts. Against
ISO 4032, the across-flats width differs at M10, M12, M14 and M22, and the height differs from M5 to
M39. Source: https://eshop.dresselhaus.de/en/Standardisation-overview/DIN-934-%3E-DIN-EN-ISO-4032.html.
Name the sizes, not the values.

Not chosen (option 1, recorded for the future), BIS India:
- IS 1364 (Part 3):2025, aligned with ISO 4032:2023. Free download unconfirmed: BIS excludes ISO/IEC standards from free download. Page: https://infralens.in/code/IS-1364-Part-3-2018
- IS 4218 (Part 3):1999, identical to ISO 724:1993: https://law.resource.org/pub/in/bis/S01/is.4218.3.1999.pdf
- IS 14962 (Part 2):2001, equivalent to ISO 965-2:1998, so the limits are printed and need no derivation: https://services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/Indian_standards/isdetails/Njk2NA==
- IS 1368:2018, identical to ISO 4753:2011: https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/Indian_standards/isdetails/NTM4NA==
- BIS free-download steps: https://www.bis.gov.in/wp-content/uploads/2021/09/STEPS-TO-DOWNLOAD-INDIAN-STANDARDS.pdf

UNVERIFIED (never state either way as fact): whether any value Phase 5 uses differs between
ISO 4032:2012 and :2023, ISO 724:1993 and :2023, ISO 965 1998 and 2024, ISO 4753 1983 and 2011, and
ISO 4014:2011 and :2022. Also UNVERIFIED: whether each free web reproduction is faithful to the
published GOST (none is a copy bought from the publisher), and whether GOST 16093-2004 prints, as
table values, every deviation and tolerance the eight D-16 limits need.

The 12 URLs (all must appear in standards-sources.md):
1. https://eshop.dresselhaus.de/en/Standardisation-overview/DIN-934-%3E-DIN-EN-ISO-4032.html
2. https://cn.gostinfo.ru/catalog/Details/?id=6101733
3. https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/2/gost_ISO_4032-2014_mezhgosudarstvennyy_standart_gayki.html
4. https://base.garant.ru/70815754/
5. https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/4/gost_24705-2004_iso_724_1993_mezhgosudarstvennyy_standart.html
6. https://dnaop.com/html/65576/doc-%D0%93%D0%9E%D0%A1%D0%A2_16093-2004
7. https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/10/gost_12414-94_iso_4753-83_mezhgosudarstvennyy_standart.html
8. https://law.resource.org/pub/in/bis/S01/is.4218.3.1999.pdf
9. https://services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/Indian_standards/isdetails/Njk2NA==
10. https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/Indian_standards/isdetails/NTM4NA==
11. https://www.bis.gov.in/wp-content/uploads/2021/09/STEPS-TO-DOWNLOAD-INDIAN-STANDARDS.pdf
12. https://infralens.in/code/IS-1364-Part-3-2018
</source_facts>

<tasks>

<!-- planner-discipline-allow: iso-standards-not-purchased -->
<!-- The INDEX gate in Task 2 is positive (exactly one Active row); the debt file name must appear in the actions because Task 2 creates it. -->

<task type="auto">
  <name>Task 1: Write the standards source map and point the requirements README at it</name>
  <files>docs/requirements/standards-sources.md, docs/requirements/README.md</files>
  <read_first>docs/requirements/README.md, the source_facts block above, docs/architecture/decision_log.md lines 558-820 (L13's licence stance, D-16)</read_first>
  <action>
Create docs/requirements/standards-sources.md in English, in the plain declarative house prose of
docs/ (no emoji, no filler). Use these sections, in this order, with these exact headings:

- `# Standards sources`. Intro paragraph: which document every standards-derived table value is read from, and why the choice was made (the owner's call of 2026-10-20, L14). It states the D-16 licence rule: this file names documents, editions, sizes and dates, and never a dimension, clause wording or table layout.
- `## Rules`. Short bullets. A value is read from the document its row names here. Every Source and panel label names the document actually read and the ISO edition that document adopts, never an ISO edition that was not read (L14). DIN 934 and GOST 5915-70 are never a source. Ruling-B double entry applies (L13, L14). Define IDT (identical) and MOD (modified) once.
- `## Already read before Phase 5 (unchanged by L14)`. ISO 68-1:2023 (owner read 2026-10-06, the basic profile, 02 D-01). ISO 262:2023, ISO 4017:2022 and ISO 4014:2022 for the Phase 4 rows as L13 records them. L14 neither re-reads nor re-labels them.
- `## Phase 5 sources (L14)`. The five-row table from source_facts, with these columns: ISO named by the plans, Used for, GOST read instead (Latin form, then the Cyrillic proper name), Relation to ISO, Free text. Under the table: GOST 12414-94's two extra ends are not ISO 4753 ends and are out of scope, because the plans model only the ISO tip end (D-09, R2). On the ISO 4014 row: open question, the owner's purchase list names ISO 4014:2022 while L13 records it as purchased. A new ISO 4014 value is read from the owner's ISO 4014:2022 copy if it holds the value, else from GOST ISO 4014-2014, asked at plan 05-12.
- `## How the 6g and 6H limits are obtained`. No GOST reproduces ISO 965-2's limit tables. Each limit the panel reports is derived: the basic dimension printed in GOST 24705-2004 plus the deviation or tolerance printed in GOST 16093-2004. Only printed values are added. A needed value that GOST 16093-2004 gives only as a formula is a stop-and-ask, never computed (05-CONTEXT rejected ISO 965-1 formulas as plausible and unverified). The panel and the Source mark each limit as derived and name both GOST designations. R13 stands: the panel's d2, D1 and D2 are the basic-profile values, and the GOST 24705-2004 table is only the agreement test.
- `## Not equivalent: do not read these`. DIN 934 and GOST 5915-70: pre-ISO national nuts. The across-flats width differs from ISO 4032 at M10, M12, M14 and M22, and the height differs from M5 to M39 (source 1). Name the sizes only. Write no width or height figure.
- `## Edition gaps (UNVERIFIED)`. A table: ISO edition the plans name | edition the GOST adopts | what is known. Five rows: 4032 2023 vs 2012; 724 2023 vs 1993 (MOD); 965-2 2024 vs derived from 965-1/965-3 1998; 4753 2011 vs 1983; 4014 2022 vs 2011. Every "what is known" cell says UNVERIFIED: no comparison has been made. Then a paragraph on the M6 cross-check. The frozen nut defaults recorded in 05-OWNER-READS.md (read from a GlobalFastener print of ISO 4032:2023) are compared with the GOST ISO 4032-2014 M6 row before plan 05-06. A mismatch is a stop-and-ask, because D-15 is one-way. Refer to the defaults by file and field (s, m). Do not restate their numbers here. Then a paragraph on reproduction faithfulness: the free texts are web reproductions, not copies bought from the publisher, so their faithfulness is UNVERIFIED. Both double-entry copies read the same text, so the diff catches a reading slip and cannot catch an error in the reproduction (the L13 caveat, carried over).
- `## Not chosen: free sources closer to the current ISO editions`. Option 1, the BIS India list from source_facts, each with its edition relation and URL. State plainly what each would have given: IS 14962 (Part 2):2001 prints ISO 965-2:1998's limits, so no derivation is needed. IS 1368:2018 is ISO 4753:2011. Whether IS 1364 (Part 3):2025 can be downloaded free is unconfirmed. Close with: recorded for a future choice, not adopted (L14).
- `## Sources`. A numbered list of all 12 URLs from source_facts, each with a one-line label (document, site, what the page is). Research date: 2026-10-19.

Then edit docs/requirements/README.md surgically, two changes only. (1) Replace the sentence
"Nothing is written here yet, and nothing should be invented to fill it." with a sentence saying the
first file here is `standards-sources.md` (L14) and nothing else should be invented to fill the
directory. (2) Add one bullet to the "What goes where" list: `standards-sources.md`, which document
each standards-derived table value is read from, and the edition gaps (L14). Touch no other line.

Write no TODO-style marker. Write no dimension from any standard. Do not commit; Task 3 makes the
single commit.
  </action>
  <verify>
    <automated>bash -c 'f=docs/requirements/standards-sources.md; test -f "$f" || exit 1; for u in "https://eshop.dresselhaus.de/en/Standardisation-overview/DIN-934-%3E-DIN-EN-ISO-4032.html" "https://cn.gostinfo.ru/catalog/Details/?id=6101733" "https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/2/gost_ISO_4032-2014_mezhgosudarstvennyy_standart_gayki.html" "https://base.garant.ru/70815754/" "https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/4/gost_24705-2004_iso_724_1993_mezhgosudarstvennyy_standart.html" "https://dnaop.com/html/65576/doc-%D0%93%D0%9E%D0%A1%D0%A2_16093-2004" "https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/10/gost_12414-94_iso_4753-83_mezhgosudarstvennyy_standart.html" "https://law.resource.org/pub/in/bis/S01/is.4218.3.1999.pdf" "https://services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/Indian_standards/isdetails/Njk2NA==" "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/Indian_standards/isdetails/NTM4NA==" "https://www.bis.gov.in/wp-content/uploads/2021/09/STEPS-TO-DOWNLOAD-INDIAN-STANDARDS.pdf" "https://infralens.in/code/IS-1364-Part-3-2018"; do grep -qF -- "$u" "$f" || { echo "missing url: $u"; exit 1; }; done; for h in "# Standards sources" "## Rules" "## Phase 5 sources (L14)" "## How the 6g and 6H limits are obtained" "## Not equivalent: do not read these" "## Edition gaps (UNVERIFIED)" "## Not chosen: free sources closer to the current ISO editions" "## Sources"; do grep -qxF -- "$h" "$f" || { echo "missing heading: $h"; exit 1; }; done; for t in "GOST ISO 4032-2014" "ГОСТ ISO 4032-2014" "GOST 24705-2004" "GOST 16093-2004" "GOST 12414-94" "GOST ISO 4014-2014" "DIN 934" "GOST 5915-70" "IS 14962" "UNVERIFIED"; do grep -qF -- "$t" "$f" || { echo "missing term: $t"; exit 1; }; done; test "$(grep -cE "[0-9] ?mm" "$f")" = 0 || { echo "a millimetre value is in the doc"; exit 1; }; grep -qF "standards-sources.md" docs/requirements/README.md || exit 1; echo task1-ok'</automated>
  </verify>
  <done>standards-sources.md has all eight headings, the five-row GOST map with Latin and Cyrillic designations, the derivation rule, the not-equivalent warning (sizes only), the UNVERIFIED edition gaps including the M6 cross-check and the reproduction caveat, the BIS alternatives and all 12 URLs. No line matches a number followed by mm. The README names the file in exactly two edited places.</done>
</task>

<task type="auto">
  <name>Task 2: Lock the decision as L14 and file the ISO purchase as must debt</name>
  <files>docs/architecture/decision_log.md, docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md, docs/tech_debt/INDEX.md</files>
  <read_first>docs/architecture/decision_log.md lines 1-30 and 558-820, .planning/phases/05-hex-nut-and-kernel-pair-proof/05-CONTEXT.md lines 188-221, docs/tech_debt/TEMPLATE.md, docs/tech_debt/INDEX.md, docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md</read_first>
  <action>
**L14.** Append to the end of docs/architecture/decision_log.md: one blank line, then the entry. Edit
no earlier line. Heading, exactly: `## L14 — Phase 5 reads its table values from free GOST texts that
adopt the ISO standards; buying the ISO texts is deferred debt (narrows TABL-04 and 05 D-14 to D-16)`.
Follow L13's shape: a `Date:` paragraph first, then paragraphs with bold lead-ins, then `Reason:` and
`Reversibility:`. Paragraphs, in order:

1. Date and provenance. Date: 2026-10-20, decided by the owner after the web research of 2026-10-19. Quote the owner's literal reply from the objective. Option 2 is described as GOST only: one source family, every text free to read, every edition 2012 or older. The full map, the URLs and the rejected alternatives are in docs/requirements/standards-sources.md. This entry copies no standard value.
2. **The map.** In one sentence each: GOST ISO 4032-2014 (IDT ISO 4032:2012) for the nut. GOST 24705-2004 (MOD ISO 724:1993) for basic d2, D1, D2. GOST 16093-2004 (based on ISO 965-1:1998 and ISO 965-3:1998) for 6g/6H deviations and tolerances. GOST 12414-94 (ISO 4753-83 text plus two non-ISO ends, out of scope) for the tip end. GOST ISO 4014-2014 (ISO 4014:2011) for a new ISO 4014 value, under the conditional rule in the planner decisions. DIN 934 and GOST 5915-70 are never a source.
3. **What it narrows.** TABL-04 ("a table row ships only against a purchased copy of its standard"): for the documents in the map, the free GOST text stands in for the purchased ISO copy. 05 D-14's precondition (purchased copies of all four) reads: the owner has the free GOST text of each. D-15's frozen-default source and D-16's ISO 965-2 rows read through this entry. The ROADMAP Phase 5 precondition and the REQUIREMENTS.md TABL-04 text are amended with the plan amendments (paragraph 8), not in this entry's commit. Phase 4's ISO 262:2023, ISO 4017:2022 and ISO 4014:2022 rows stay exactly as L13 records them.
4. **Double entry still applies (ruling B).** The owner copy is generated from the free GOST text (its text layer or page text). The agent's independent read is from rendered images of the same pages. The cell-by-cell diff runs in `make verify`, with one relation test per row, and UNVERIFIED rows are refused, all as L13. Carry over L13's caveat: both copies read the same reproduction, so the diff cannot catch an error in it. The reproductions are not publisher copies, and their faithfulness is UNVERIFIED.
5. **The 6g/6H limits are derived.** Each limit is the GOST 24705-2004 basic dimension plus the GOST 16093-2004 printed deviation or tolerance. Only printed values are added. A value given only as a formula is a stop-and-ask at plan 05-08 (ISO 965-1 formulas stay rejected, 05-CONTEXT). The Source and the panel label say "derived" and name both designations, never "ISO 965-2:2024 Table". D-16's relation tests still apply. R13 stands, with the "ISO 724 table" read as GOST 24705-2004.
6. **Citations.** Every row's Source and every panel label names the GOST designation and the ISO edition that designation adopts. The exact strings are set by the plan amendments. The shipped NUT_NO_ROW_WARNING in src/screw/calc/__init__.py names ISO 4032:2023. It is reworded when the nut rows land (plan 05-07). This entry does not change code.
7. **Edition gaps and the M6 cross-check.** Whether any value Phase 5 uses differs between the five edition pairs (list them) is UNVERIFIED, and nothing here claims it does not. The frozen nut defaults s 10.0 and m 5.2 (05-OWNER-READS.md, from a GlobalFastener print of ISO 4032:2023, permanent: accepted 2026-10-14, shipped by plan 05-04) are compared with the GOST ISO 4032-2014 M6 grade-A coarse row in the columns they took (s max, m max) before plan 05-06 lands. A match is recorded in 05-OWNER-READS.md. A mismatch is a stop-and-ask, because D-15 is one-way.
8. **Pending plans.** Plans 05-06 to 05-18 name ISO editions (counted 2026-10-20). They read each named ISO document as its GOST equivalent from this entry. Their preconditions are amended when the phase resumes, before 05-06 executes: 05-06's ISO 4032:2023 page render and its "never transcribe from any other source" clause, 05-08's ISO 965-2 and ISO 724 owner copy, 05-11 and 05-12's ISO 4753 read and ISO 4014 fillet copy. The pending reads 3 to 7 of 05-OWNER-READS.md are read from the GOST texts.
9. **Open question.** The ISO 4014:2022 conflict, as in the planner decisions: both facts stated, the conditional rule, asked at 05-12's precondition.
10. `Reason:` The owner's call, not to spend about $400 (the owner's figure) on the MVP. GOST was chosen over mixing national sources because it is one family, freely readable. The cost is edition age, which is why every citation names the edition actually read and the purchase has a named trigger.
11. `Reversibility:` Reversible for the source choice: buying the ISO texts re-reads and re-cites the rows, and the double-entry diff shows every change. One-way for any frozen default a GOST row confirms (D-15), hence the stop-and-ask on a mismatch. Costly for the published citation text on the panel. Revisit: docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md.

**Debt item.** Create docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md from TEMPLATE.md,
in the shape of 2026-10-14-nut-fine-stl-caps-unmeasured.md.
- Title: `# The ISO standards Phase 5 reads are not purchased: rows come from free GOST texts of older editions`.
- Fields: `Severity: must`, `Status: active`, `Date: 2026-10-20`, `Source:` the owner's decision of 2026-10-20 (quick task 261020-dpw), L14.
- Related files: docs/architecture/decision_log.md (L14); docs/requirements/standards-sources.md; .planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md (the M6 defaults); .planning/REQUIREMENTS.md (TABL-04); src/screw/calc/__init__.py (NUT_NO_ROW_WARNING names ISO 4032:2023).
- Context: what is deferred. The five documents to buy are ISO 4032:2023, ISO 965-2:2024, ISO 724:2023, ISO 4753:2011 and ISO 4014:2022, about $400 in total by the owner's figure (not checked against ISO's price list). Note the ISO 4014:2022 open question. Owner sign-off line, verbatim: `Owner sign-off: the owner approved this deferral on 2026-10-20`, followed by the owner's literal reply.
- Why it matters: rows cite 1993 to 2012 editions, and whether a value differs from the current ISO edition is UNVERIFIED. A release cannot claim ISO 4032:2023 (or any current-edition) conformance. A differing value is a number someone cuts metal to (L02).
- Next step: revisit before the Phase 6 release, or before any public release that claims ISO conformance, whichever comes first. Buy the five. Re-read every GOST-sourced row against the ISO edition under ruling-B double entry, and diff. Re-cite. File each difference. A changed frozen default is a stop-and-ask (D-15). Record the outcome as an entry superseding L14.

**INDEX row.** In docs/tech_debt/INDEX.md, add as the first row of the `## Active` table:
`| must | [The ISO standards Phase 5 reads are not purchased: rows come from free GOST texts of older editions](active/2026-10-20-iso-standards-not-purchased.md) | before the Phase 6 release, or any public release that claims ISO conformance |`.
Touch no other row.

Do not commit; Task 3 makes the single commit.
  </action>
  <verify>
    <automated>bash -c 'd=docs/architecture/decision_log.md; test "$(grep -c "^## L14 " "$d")" = 1 || exit 1; grep "^## L" "$d" | tail -1 | grep -q "^## L14 " || exit 1; n=$(git diff --numstat -- "$d") || exit 1; test -n "$n" || { echo "decision log unchanged"; exit 1; }; test "$(printf "%s\n" "$n" | cut -f2)" = 0 || { echo "lines above L14 changed"; exit 1; }; S=$(awk "/^## L14 /{f=1} f" "$d"); for t in "2026-10-20" "choose second option" TABL-04 D-14 D-15 D-16 "ruling B" "GOST ISO 4032-2014" "GOST 24705-2004" "GOST 16093-2004" "GOST 12414-94" "GOST ISO 4014-2014" derived "05-06" "05-18" UNVERIFIED "standards-sources.md" "2026-10-20-iso-standards-not-purchased.md" "Reason:" "Reversibility:"; do printf "%s" "$S" | grep -qF -- "$t" || { echo "L14 lacks: $t"; exit 1; }; done; t=docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md; for x in "Severity: must" "Status: active" "Date: 2026-10-20" "ISO 4032:2023" "ISO 965-2:2024" "ISO 724:2023" "ISO 4753:2011" "ISO 4014:2022" "400" "Owner sign-off: the owner approved this deferral on 2026-10-20" "Phase 6" "L14"; do grep -qF -- "$x" "$t" || { echo "debt item lacks: $x"; exit 1; }; done; a=$(awk "/^## Active/{f=1} /^## Resolved/{f=0} f" docs/tech_debt/INDEX.md) || exit 1; test "$(printf "%s\n" "$a" | grep -cF "iso-standards-not-purchased")" -eq 1 || { echo "INDEX Active row missing or doubled"; exit 1; }; echo task2-ok'</automated>
  </verify>
  <done>L14 is the last entry of the decision log and covers paragraphs 1 to 11. git diff on the decision log shows additions only. The debt item exists with Severity must, the named trigger, the five ISO documents, the ~$400 owner figure and the sign-off line. INDEX.md has exactly one Active row for it.</done>
</task>

<task type="auto">
  <name>Task 3: Point the Phase 5 records at L14, run the gate, make the one commit</name>
  <files>.planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md, .planning/STATE.md</files>
  <read_first>.planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md (whole file, 139 lines), .planning/STATE.md section "### Blockers/Concerns"</read_first>
  <action>
**05-OWNER-READS.md (insert only).** Insert one paragraph after the intro paragraph, the one that ends
"Plans 05-04 to 05-18 read it.", and before the paragraph that starts "**This record is partial".
The paragraph starts `**2026-10-20: the sources change (L14).**`. It says:
- The owner chose free GOST texts in place of purchased ISO copies, and the map is docs/requirements/standards-sources.md.
- Where this record names ISO 4032, ISO 724, ISO 965-2 or ISO 4753, the pending reads and the owner copy read the GOST equivalent L14 names. The owner-copy file names stay as written until the plan amendments.
- The recorded s and m, the permanence line and the rulings R1 to R13 are unchanged.
- Before plan 05-06, s and m are cross-checked against the GOST ISO 4032-2014 M6 row, and a mismatch is a stop-and-ask (D-15).
- The ISO purchase is debt docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md.

Change no other line: values, rulings and PENDING markers stay byte-identical.

**STATE.md (two bullets in `### Blockers/Concerns`, nothing else).**
(1) Replace the whole bullet that begins `- [Phase 5] Precondition (TABL-04):` with this bullet:
`[Phase 5] Precondition (TABL-04), narrowed by L14 (owner, 2026-10-20)`. Its content:
- ISO 262:2023, ISO 4017:2022 and ISO 4014:2022 were read for Phase 4 (D-13, ruling B).
- Phase 5's ISO 4032, 724, 965-2 and 4753 values, and any new ISO 4014 value, are read from the free GOST equivalents in docs/requirements/standards-sources.md.
- The ISO purchase is must debt docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md.
- Before plan 05-06: cross-check the frozen nut s and m against the GOST ISO 4032-2014 M6 row (a mismatch is a stop-and-ask, D-15), and amend the pending plans' ISO preconditions, ROADMAP's Phase 5 precondition and TABL-04's text.

(2) In the bullet that begins `- ISO 4753 (bolt ends, THRD-05) must be read in Phase 5`, replace the
clause about the purchase line with: it is read from GOST 12414-94 (the ISO 4753-83 text, L14). Keep
the trailing ISO 68-1:2023 parenthetical as it is. Edit nothing else in STATE.md: not the
frontmatter, the position or the quick-task table, which the quick orchestrator owns.

**Gate and commit.**
1. Run `make verify` from the checkout root, with the Bash timeout at 600000 ms. Quote its final result line in the SUMMARY.
2. Stage exactly the seven files in this plan's files_modified with an explicit-path `git add`: never `-A` and never `.`, because this plan file and the SUMMARY belong to the orchestrator's own commit.
3. Run a plain `git commit` (the pre-commit hook re-runs make verify; timeout 600000 ms). Use these -m paragraphs: subject `docs: source Phase 5 table values from free GOST equivalents`; a body paragraph in normal Conventional Commits prose, not caveman, naming L14, the source doc, the debt item and the two pointer notes; and the final paragraph `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Keep GitHub Actions skip tokens out of the message (the commit-msg hook refuses them, L08).
4. Never pass --no-verify. If the hook fails, fix the cause and make a NEW commit attempt (never --amend). If a test fails only inside the hook and passes standalone, suspect GIT_* variables leaking from the hook into a test that runs git: stop and report it with the failing test name, and do not work around it.
  </action>
  <verify>
    <automated>bash -c 'o=.planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md; c=$(git log -1 --format=%H -F --grep="docs: source Phase 5 table values from free GOST equivalents") || exit 1; test -n "$c" || { echo "commit not found"; exit 1; }; grep -qF "**2026-10-20: the sources change (L14).**" "$o" || exit 1; n=$(git show --numstat --format= "$c" -- "$o") || exit 1; test "$(printf "%s\n" "$n" | cut -f2)" = 0 || { echo "05-OWNER-READS lost lines"; exit 1; }; grep -qF "| s | 10.0 mm |" "$o" && grep -qF "| m | 5.2 mm |" "$o" || exit 1; grep -qF "narrowed by L14" .planning/STATE.md || exit 1; test "$(grep -c "holds purchased copies of ISO 4032:2023" .planning/STATE.md)" = 0 || { echo "stale precondition still in STATE.md"; exit 1; }; s=$(git log -1 --format=%s "$c") || exit 1; test "$s" = "docs: source Phase 5 table values from free GOST equivalents" || exit 1; b=$(git log -1 --format=%B "$c") || exit 1; printf "%s\n" "$b" | grep -qxF "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" || exit 1; f=$(git show --name-only --format= "$c") || exit 1; want=$(printf "%s\n" docs/requirements/standards-sources.md docs/requirements/README.md docs/architecture/decision_log.md docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md docs/tech_debt/INDEX.md .planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md .planning/STATE.md | sort); test "$(printf "%s\n" "$f" | sed "/^$/d" | sort)" = "$want" || { echo "commit file set differs"; exit 1; }; echo task3-ok' && make verify</automated>
  </verify>
  <done>05-OWNER-READS.md has the dated L14 note, with additions only and the s/m table rows intact. STATE.md's two Phase 5 bullets point to L14 and the debt item. make verify passes, and its result line is quoted. HEAD is the single commit with the exact subject, the Co-Authored-By trailer and exactly the seven files.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| third-party web reproduction -> owner copy / agent read | free GOST texts on aggregator sites enter the double-entry process; not publisher copies |
| standards text -> repository | licence boundary: values with citations only, no clause wording or layout (05 D-16, L13) |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-261020-01 | Tampering | a value read from an unfaithful or older-edition reproduction | high | mitigate | L14 keeps ruling-B double entry, the relation tests and the UNVERIFIED gate. Every citation names the edition actually read. The M6 s/m cross-check is a stop-and-ask. The edition gaps are flagged UNVERIFIED. The debt item's trigger forces a re-read against purchased ISO before the Phase 6 release |
| T-261020-02 | Information disclosure | standard values copied into docs | medium | mitigate | Task 1 verify refuses any number followed by mm in standards-sources.md. The not-equivalent warning names sizes only |
| T-261020-03 | Repudiation | provenance of the source decision | medium | mitigate | L14 and the debt item quote the owner's literal reply and carry the dated sign-off line |
| T-261020-04 | Tampering | derived 6g/6H limits presented as printed ISO values | high | mitigate | L14 requires a "derived" label naming both GOST designations. A value printed only as a formula is a stop-and-ask, never computed |
| T-261020-SC | Tampering | npm/pip/cargo installs | low | accept | this plan installs no package; docs only |
</threat_model>

<verification>
- Task 1, 2 and 3 automated checks print task1-ok, task2-ok and task3-ok.
- `make verify` passes standalone and in the pre-commit hook; the SUMMARY quotes the result line.
- `git show --stat HEAD` lists exactly the seven files; no src/, tests/ or plan file is in the commit.
- Coverage audit. GOAL, brief deliverable 1: Task 1. Deliverables 2 and 3: Task 2. Deliverable 4 and the commit: Task 3. REQ TABL-04: narrowed by L14 (Task 2). CONTEXT D-14, D-15 and D-16: narrowed by L14 (Task 2), with the D-15 cross-check carried in L14, the doc, 05-OWNER-READS and STATE.md. RESEARCH facts (map, not-equivalent, not-chosen, unverified): Task 1. No item is unplanned.
</verification>

<success_criteria>
- The owner's GOST-only decision is a locked, citable L14 that narrows TABL-04 and 05 D-14 to D-16 without touching Phase 4's rows.
- One durable doc holds the source map, the warnings, the rejected alternatives, the UNVERIFIED gaps and all 12 URLs, with no standard values.
- The ISO purchase survives as must debt with a named trigger and the owner's sign-off, and has its INDEX row.
- The Phase 5 records (05-OWNER-READS.md, STATE.md) send the next executor to L14, and no recorded value or ruling changes.
- One docs commit; make verify green.
</success_criteria>

<output>
Create `.planning/quick/261020-dpw-record-the-free-gost-source-decision-for/261020-dpw-SUMMARY.md` when done. It states: the make verify result line, the commit sha, that the debt item filed is docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md, and the open items for the owner: the ISO 4014:2022 purchase-list conflict with L13, the M6 s/m cross-check before 05-06, and the amendments due before 05-06 to the plan preconditions, ROADMAP's Phase 5 precondition and TABL-04's text.
</output>
