"""Cited ISO rows for the hex head bolts and screws: data only, a leaf of the module graph.

The modules here store the numeric values the product needs, one record per size with a
required typed `Source(standard, edition, table, column, status)` on every row (TABL-02). They
do not reproduce clause wording, notes, figures or the printed table layout (D-16). The
purchased PDFs and their page renders never enter git; `.gitignore` refuses `*.pdf`.

Every row is entered twice, independently, and the two copies are diffed cell by cell in
`make verify` (D-14, `tests/test_tables_second_entry.py`). A row marked `unverified` cannot
pass that gate (D-15). Nothing here depends on `screw.params`, `screw.calc`, the kernel or a web
framework (module-boundary contract 7), and `params` and `calc.thread` never reach this package
(contract 6): a link rebuilds a part from its millimetre fields without consulting a table.
"""
