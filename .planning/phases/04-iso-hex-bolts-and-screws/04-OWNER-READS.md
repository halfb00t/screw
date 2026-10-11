# Phase 4: Owner reads

Record of the owner's opening read for phase 4 (plan 04-01, Task 2 checkpoint, answered 2026-10-11).
It carries the owner's words and the numbers the owner confirmed; no clause wording, figure or
printed table layout is copied here (D-16). Plans 04-03, 04-07 and 04-09 read it.

## Opening read (owner, 2026-10-11)

The owner read ISO 4017:2022 and ISO 262:2023 for M6 from the purchased copies, typed the M6 lines
into the owner copy, and replied `defaults: confirmed`. The D-07 defaults are therefore:

| Field | Value | Source the owner confirmed it against |
| ----- | ----- | ------------------------------------- |
| d | 6.0 mm | ISO 262:2023 Table 1, first choice, coarse column |
| pitch | 1.0 mm | ISO 262:2023 Table 1, first choice, coarse column |
| s | 10.0 mm (nominal = maximum) | ISO 4017:2022 Table 1, M6, grade A |
| k | 4.0 mm (nominal) | ISO 4017:2022 Table 1, M6, grade A |
| length | 20 mm | listed M6 length of ISO 4017:2022 Table 1, grade A |

The owner confirmed that 20 mm is in the ISO 4017:2022 M6 series.

Permanence acknowledged: 2026-10-11, permanent: accepted (D-07: links that omit s, k or thread_length mean these values forever)

The owner typed `permanent: accepted` as a reply on its own, after being told that every shareable
link that omits `s`, `k` or `thread_length` means these values forever and that this is the only stop
for them: plan 04-03 commits exactly these values without asking again.

## Owner copy

Owner copy directory: /Users/halfb00t/Documents/standards/screw-owner-copy

Outside the repository; never copied into it (D-16). Three tab-separated UTF-8 files, header line
first, decimal point, one record per line, per-size numbers only:

- `iso262.tsv`: `size  d  pitch  choice  table  column`
- `iso4017_heads.tsv`: `size  grade  pitch  s  s_min  e_min  k  k_min  k_max  dw_min  table  column`
- `iso4017_lengths.tsv`: `size  length  grade  table  column`

Typed so far: the `M6` line of `iso262.tsv`; the `M6` grade `A` line of `iso4017_heads.tsv`; eleven
`M6` lines of `iso4017_lengths.tsv` (lengths 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, all grade A,
Table 1, column M6). Every other size and the ISO 4014 files: see 04-09. The directory also holds
`designation.txt`, the owner's Clause 7 transcription; it is not one of the three TSVs.

## Designation

Designation: `Hexagon head screw ISO 4017 - M6 x 20` and `Hexagon head bolt ISO 4014 - M10 x 80`
(property class left out).

- Decimal sizes: written with a comma in the standard, so `M3,5`.
- Left-hand form: `none`. Clause 7 of both standards gives no left-hand form, so the designation is
  withheld for left-hand parts.
- Typography: both clauses defer to ISO 8991 and print an en-dash (U+2013) between the parts and a
  multiplication sign (U+00D7) between size and length. The owner did not object to the ASCII form,
  so the tool prints ASCII `-` and `x`.

## Rendering route and the PDFs

Rendering route: a (`brew install poppler`, then `pdftoppm`), PDFs at `/Users/halfb00t/Documents/standards`
(`ISO-262-2023.pdf`, `ISO-4014-2022.pdf`, `ISO-4017-2022.pdf`), outside the repository.

Route proved on page 7 of `ISO-4017-2022.pdf` (printed page 3, the page with the head-dimension table for
M1,6 to M7), 2026-10-11: `pdftoppm -png -r 150 -f 7 -l 7` rendered it to a PNG in the agent's session
scratch directory (never the repository) and the Read tool displayed the M6 column legibly. This step
proved legibility only; no value was read off the page into any file. poppler 26.10.0 from the
Homebrew formula; no Python or JS package was added.

### Owner ruling on the on-disk PDFs (2026-10-11)

Literal owner line: `A - 3.`, answering the orchestrator's option 3.

The PDFs at `/Users/halfb00t/Documents/standards/` are preview portions (7, 10 and 10 pages), not the
complete purchased documents: the contents page of `ISO-4017-2022.pdf` places Clause 7 on page 8 and
Annex A on page 9, and the file carries no Clause 7 body and no bibliography. The owner holds the full
text elsewhere (the Clause 7 screenshots came from it). The owner RULES that the preview pages are the
same pages as the purchased edition and may serve as the agent's independent second copy for the
tables they contain (D-14). Provenance for a later reader: the second copy is read from preview pages,
under this ruling dated 2026-10-11, and from nothing else.

Observation for plan 04-09 and the verifier, not a ruling: the rendered page bears a preview watermark
of the iTeh preview service. Plan 04-01's prohibition names "the iTeh previews" as a forbidden source
of table values; the owner's ruling above is the standing exception, scoped to the tables these
preview pages contain, and the owner's own typed copy stays the first copy.
