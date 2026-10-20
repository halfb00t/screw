# The ISO standards Phase 5 reads are not purchased: rows come from free GOST texts of older editions

Severity: must
Status: active
Date: 2026-10-20
Source: the owner's decision of 2026-10-20 (quick task 261020-dpw), L14
Related files:
- docs/architecture/decision_log.md (L14)
- docs/requirements/standards-sources.md (the source map and the edition gaps)
- .planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md (the M6 defaults)
- .planning/REQUIREMENTS.md (TABL-04)
- src/screw/calc/__init__.py (`NUT_NO_ROW_WARNING` names GOST ISO 4032-2014 (ISO 4032:2012) since plan 05-07)

## Context
Phase 5 reads its table values from free GOST texts that adopt the ISO standards (L14), and the
purchase of the ISO texts is deferred. The five documents to buy are ISO 4032:2023, ISO 965-2:2024,
ISO 724:2023, ISO 4753:2011 and ISO 4014:2022, about $400 in total by the owner's figure (not checked
against ISO's price list).

Open question: the purchase list names ISO 4014:2022, while L13 records Phase 4's ISO 4014:2022 rows as
read from a purchased copy. Nothing records why the document is on the list. L14 sets the rule: a new
ISO 4014 value is read from the owner's ISO 4014:2022 copy if it holds the value, else from
GOST ISO 4014-2014. It is asked at plan 05-12's precondition.

Owner sign-off: the owner approved this deferral on 2026-10-20. The owner's reply, verbatim: "put this
table description and sources into a document and choose second option. I don't want to spend $400
for MVP so lets put ISO into a techdebt".

## Why it matters
Rows cite 1993 to 2012 editions, and whether a value differs from the current ISO edition is
UNVERIFIED. A release cannot claim ISO 4032:2023 (or any current-edition) conformance. A differing
value is a number someone cuts metal to (L02).

## Next step
Revisit before the Phase 6 release, or before any public release that claims ISO conformance,
whichever comes first. Buy the five. Re-read every GOST-sourced row against the ISO edition under
ruling-B double entry, and diff. Re-cite. File each difference. A changed frozen default is a
stop-and-ask (D-15). Record the outcome as an entry superseding L14.
