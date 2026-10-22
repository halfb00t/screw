# Standards sources

This file says which document every standards-derived table value is read from, and why. For
Phase 5 the owner chose, on 2026-10-20 (L14), to read the values from free GOST (Russian
interstate) texts that adopt the ISO standards, instead of buying the ISO PDFs. The ISO
purchase is deferred debt (`docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md`).

Licence rule (05 D-16, L13): this file names documents, editions, sizes and dates. It never
states a dimension, a clause wording or a table layout. The values themselves live in
`src/screw/tables/`, one typed `Source` per row.

## Rules

- A value is read from the document its row names in this file, and from no other.
- Every `Source` and every panel label names the document actually read and the ISO edition
  that document adopts. It never names an ISO edition that was not read (L14).
- DIN 934 and GOST 5915-70 are never a source (see "Not equivalent" below).
- Ruling-B double entry applies to every row (L13, L14): an owner copy, the agent's
  independent read, a cell-by-cell diff in `make verify`, one relation test per row, and
  UNVERIFIED rows refused.
- IDT means identical: the national text is the international text. MOD means modified: the
  national text departs from the international one and says where.

## Already read before Phase 5 (unchanged by L14)

- ISO 68-1:2023: read by the owner on 2026-10-06, the basic profile (02 D-01).
- ISO 262:2023, ISO 4017:2022 and ISO 4014:2022: the Phase 4 rows, as L13 records them.

L14 neither re-reads nor re-labels these.

## Phase 5 sources (L14)

| ISO named by the plans | Used for | GOST read instead | Relation to ISO | Free text |
|---|---|---|---|---|
| ISO 4032:2023 | nut rows: s, m, e, mw, dw and the chamfer read | GOST ISO 4032-2014 (ГОСТ ISO 4032-2014) | IDT ISO 4032:2012; in force from 2017-01-01; replaced the coarse-thread part of GOST 5915-70 | sources 2 and 3 |
| ISO 4014:2022 | a new ISO 4014 value only (R1's fillet r,min); Phase 4 rows unchanged | GOST ISO 4014-2014 (ГОСТ ISO 4014-2014) | adopts ISO 4014:2011; degree of equivalence not recorded | source 4 |
| ISO 724:2023 | basic d2, D1, D2 (R13: agreement test only) | GOST 24705-2004 (ГОСТ 24705-2004) | MOD ISO 724:1993 | source 5 |
| ISO 965-2:2024 | 6g and 6H limits | GOST 16093-2004 (ГОСТ 16093-2004) | based on ISO 965-1:1998 and ISO 965-3:1998; NOT a copy of ISO 965-2. It prints deviations and tolerances, so each limit is derived (next section) | source 6 |
| ISO 4753 (the plans name no edition; the debt buys ISO 4753:2011) | tip end form (D-09, R2) | GOST 12414-94 (ГОСТ 12414-94) | authentic text of ISO 4753-83, plus two extra stepped ends (cone, sphere) that are not ISO ends | source 7 |

GOST 12414-94's two extra ends are not ISO 4753 ends and are out of scope: the plans model only
the ISO tip end (D-09, R2).

ISO 4014 row, open question. The owner's purchase list names ISO 4014:2022, while L13 records
the ISO 4014:2022 rows as read from a purchased copy. Nothing records why the document is on
the list. A new ISO 4014 value is read from the owner's ISO 4014:2022 copy if that copy holds
the value, else from GOST ISO 4014-2014. Which applies is asked at the precondition of plan
05-12.

## How the 6g and 6H limits are obtained

No GOST here reproduces ISO 965-2's limit tables. Each limit the panel reports is derived: the
basic dimension printed in GOST 24705-2004 plus the deviation or tolerance printed in
GOST 16093-2004. Only printed values are added. A needed value that GOST 16093-2004 gives only
as a formula is a stop-and-ask, never computed (05-CONTEXT rejected ISO 965-1 formulas as
plausible and unverified).

The panel and the `Source` mark each limit as derived and name both GOST designations. R13
stands: the panel's d2, D1 and D2 are the basic-profile values, and the GOST 24705-2004 table
is only the agreement test.

## Not equivalent: do not read these

DIN 934 and GOST 5915-70 are the pre-ISO national nuts. Against ISO 4032, the across-flats
width differs at M10, M12, M14 and M22, and the height differs from M5 to M39 (source 1). They
are never a source for a row. No width or height figure is written here.

## Edition gaps (UNVERIFIED)

| ISO edition the plans name | Edition the GOST adopts | What is known |
|---|---|---|
| ISO 4032:2023 | ISO 4032:2012 | UNVERIFIED: no comparison has been made |
| ISO 724:2023 | ISO 724:1993 (MOD) | UNVERIFIED: no comparison has been made |
| ISO 965-2:2024 | derived from ISO 965-1:1998 and ISO 965-3:1998 | UNVERIFIED: no comparison has been made |
| ISO 4753:2011 | ISO 4753-83 | UNVERIFIED: no comparison has been made |
| ISO 4014:2022 | ISO 4014:2011 | UNVERIFIED: no comparison has been made |

Whether any value Phase 5 uses differs between these editions is UNVERIFIED, and nothing here
claims it does or does not.

M6 cross-check. The frozen nut defaults recorded in
`.planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md` (fields s and m, read from
a GlobalFastener print of ISO 4032:2023) are compared with the GOST ISO 4032-2014 M6 row before
plan 05-06. A mismatch is a stop-and-ask, because D-15 is one-way. The numbers are not restated
here.

Reproduction faithfulness. The free texts are web reproductions, not copies bought from the
publisher, so their faithfulness to the published GOST is UNVERIFIED. Also UNVERIFIED: whether
GOST 16093-2004 prints, as table values, every deviation and tolerance the eight D-16 limits
need. Both double-entry copies read the same text, so the diff catches a reading slip and cannot
catch an error in the reproduction (the L13 caveat, carried over).

## Not chosen: free sources closer to the current ISO editions

Option 1, the BIS (Bureau of Indian Standards) list. Recorded for a future choice, not adopted
(L14).

- IS 1364 (Part 3):2025: aligned with ISO 4032:2023. Whether it can be downloaded free is
  unconfirmed: BIS excludes ISO/IEC standards from free download (source 12).
- IS 4218 (Part 3):1999: identical to ISO 724:1993 (source 8).
- IS 14962 (Part 2):2001: equivalent to ISO 965-2:1998, so the limits are printed and need no
  derivation (source 9).
- IS 1368:2018: identical to ISO 4753:2011 (source 10).
- BIS free-download steps (source 11).

## Sources

Research date: 2026-10-19.

1. DIN 934 against DIN EN ISO 4032, Dresselhaus shop overview page: https://eshop.dresselhaus.de/en/Standardisation-overview/DIN-934-%3E-DIN-EN-ISO-4032.html
2. GOST ISO 4032-2014, gostinfo.ru catalogue record: https://cn.gostinfo.ru/catalog/Details/?id=6101733
3. GOST ISO 4032-2014, meganorm.ru text of the standard: https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/2/gost_ISO_4032-2014_mezhgosudarstvennyy_standart_gayki.html
4. GOST ISO 4014-2014, garant.ru record: https://base.garant.ru/70815754/
5. GOST 24705-2004 (ISO 724:1993), meganorm.ru text of the standard: https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/4/gost_24705-2004_iso_724_1993_mezhgosudarstvennyy_standart.html
6. GOST 16093-2004, dnaop.com text of the standard: https://dnaop.com/html/65576/doc-%D0%93%D0%9E%D0%A1%D0%A2_16093-2004
7. GOST 12414-94 (ISO 4753-83), meganorm.ru text of the standard: https://meganorm.ru/mega_doc/norm/gost_gosudarstvennyj-standart/10/gost_12414-94_iso_4753-83_mezhgosudarstvennyy_standart.html
8. IS 4218 (Part 3):1999, law.resource.org PDF: https://law.resource.org/pub/in/bis/S01/is.4218.3.1999.pdf
9. IS 14962 (Part 2):2001, BIS standards details page: https://services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/Indian_standards/isdetails/Njk2NA==
10. IS 1368:2018, BIS standards details page: https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/Indian_standards/isdetails/NTM4NA==
11. BIS, steps to download Indian standards, PDF: https://www.bis.gov.in/wp-content/uploads/2021/09/STEPS-TO-DOWNLOAD-INDIAN-STANDARDS.pdf
12. IS 1364 (Part 3), infralens.in code page: https://infralens.in/code/IS-1364-Part-3-2018
