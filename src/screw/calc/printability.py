"""What the Phase 6 printed test measured, as constants and the warning that says where it did not.

Kernel-free and standard-library only, run on every keystroke like the rest of `screw.calc`. Every
constant here is pinned to its record by `tests/test_print_rules.py`, never typed from a guide
(PAIR-02, INFO-04).
"""

from __future__ import annotations

# The decision entry that set the nut's clearance default, and the printed run it reads (L17).
CLEARANCE_ENTRY = "L17"
CLEARANCE_RUN = "06-print-run-1"

# D-09, R6 (r6-a): the clearance default is one absolute value for every size, but run 1 printed
# only M6 to M12, so the d of its smallest and largest size bound what was measured. Compared
# exactly on the stored float, no tolerance: a nut one float outside M6 is a size nobody printed.
MEASURED_D_MIN_MM = 6.0
MEASURED_D_MAX_MM = 12.0


def measured_range_warning(d: float, pitch: float) -> str | None:  # noqa: ARG001
    """The warning for a nut whose size the clearance default was not measured on, else None.

    Pure size test: it reads `d` alone (R6) and never the clearance, so a nut that took the default
    and one with a typed clearance carry it identically. It warns and changes nothing: the nut is
    built as asked and no row is dropped (D-09, L02). `pitch` is in the signature the plan fixes
    (06-07 key link) and R6 reads it not at all, hence the ARG001 waiver.
    """
    # Written as "inside, else warn" so a NaN d, which compares false both ways, warns too.
    if MEASURED_D_MIN_MM <= d <= MEASURED_D_MAX_MM:
        return None
    return (f"d {d:g} mm is outside M6 to M12, the sizes the clearance default was measured on "
            f"({CLEARANCE_ENTRY}, run {CLEARANCE_RUN})")
