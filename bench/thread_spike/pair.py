"""The pair check the spike measured, now owned by the product (kernel module).

The bodies moved to `screw/solid/pair.py` in Phase 5 (D-05) and are imported back below, so
what was measured is what ships (02 D-18). What stays here is the spike's own name for the
blank, `nut`. The boolean's `_KEEP` is the same list object, so the M18 probe's
`pair._KEEP.append` still parks what it must.

It measures; whether a reading proves anything is decided in the parent by
`verdict.cell_verdict`, against a closed form this process never sees.
"""

from __future__ import annotations

from screw.solid.pair import _KEEP as _KEEP
from screw.solid.pair import _span as _span
from screw.solid.pair import blank as blank
from screw.solid.pair import check_cover as check_cover
from screw.solid.pair import common as common
from screw.solid.pair import place as place
from screw.solid.pair import rod_piece as rod_piece

# The spike's name for the verdict body, pinned by tests/test_bench.py.
nut = blank
