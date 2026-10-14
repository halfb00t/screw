# Head and drive families beyond the hex head

Date: 2026-10-13
Source: the owner, in conversation after the Phase 4 verification refresh (PR #14)
Related files:
- .planning/REQUIREMENTS.md (TYP2-01 at line 81; the out-of-scope table at lines 98 to 110)
- .planning/PROJECT.md (the v2 socket cap line at 100; countersunk and set screws at 127)
- .planning/ROADMAP.md (line 15, the second release)
- src/screw/params.py (`BoltParams`: `s`, `k`, `thread_length` — the head is two explicit mm fields today)

## Context
The owner wants bolts and screws that are not the ISO hex head: headless (set screws, threaded
rod), hex socket, hexalobular (Torx), cross recess (Phillips), recessed and low heads. Today
`bolt` is the only kind, its head is a hexagon described by two explicit millimetre fields, and
the ISO 4014 / 4017 presets fill those fields from cited rows. The planning docs already place
one of the wanted kinds: the hex socket head cap screw (ISO 4762) is v2, requirement TYP2-01,
priced at one phase on the proven thread path. Countersunk screws and set screws are listed as
"not in the first two releases; revisit once socket cap has shipped". Hexalobular and cross
recess drives, low heads and threaded rod appear nowhere in REQUIREMENTS or ROADMAP; threaded
rod is named only in CLAUDE.md's product line.

The wanted parts sit on two axes, not one list. Head shape: hex, cylindrical, button, countersunk,
pan, low, none. Drive: external hex, hex socket, hexalobular, cross recess, slot, none. Each ISO
standard pins one combination with its own table. From memory, UNVERIFIED until a purchased copy
is read (the TABL-04 rule): ISO 4762 cylindrical head with hex socket; ISO 14579 cylindrical head
with hexalobular socket; ISO 10664 the hexalobular recess itself; ISO 7380 button head with hex
socket; ISO 10642 countersunk head with hex socket; ISO 4757 the cross recess, used by ISO 7045
(pan) and ISO 7046 (countersunk); ISO 4026 to 4029 hex socket set screws with flat, cone, dog and
cup points; ISO 4766 slotted set screws. Threaded rod and low (thin) socket heads have DIN
sheets rather than ISO ones (DIN 975 / 976, DIN 7984 and 6912) and need a source decision of
their own.

## Why it matters
Product: a user who prints a Torx button head or a grub screw gets today either nothing or a hex
head they did not ask for. The thread, the proof of a mating pair and the parity of UI, API and
CLI are shared, so each new head is a table plus a head solid, not a new product.

Cost, under L02 and TABL-04, per standard: buy the copy, enter the rows with their citations, one
invariant test per row, a build-time measurement, and new geometry for the drive. The hexalobular
and cross recess profiles carry their own tolerance bands and are the first non-trivial recess
solids in the kernel; set-screw points start from the chamfer and fillet work THRD-05 brings in
Phase 5. A "custom" head with no table is the cheaper route and already exists for the hex: explicit
millimetre fields and a `custom` badge.

## Next step
Revisit when TYP2-01 (ISO 4762) has shipped on the proven path: it is the first non-hex head and
settles how a head solid and a drive recess plug into the shared bolt. Then the owner names the
standards to buy, in the order the users ask for them, and `/gsd-new-milestone` turns the matrix
above into requirements, one head-and-drive combination per TYPx row with its own table and tests.
Model the head shape and the drive as two choices rather than one kind per standard, so a
custom head (explicit mm, no table) stays possible for every combination.
