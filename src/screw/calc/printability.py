"""What the Phase 6 printed tests measured, as constants and the warnings that say where not.

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


def _exact(x: float) -> str:
    """`x` as `:g` prints it when that reads back as the same float, else as `repr` does.

    `:g` keeps six significant digits, so d 3.999999 printed as "4" under a sentence saying it is
    below 4 (phase-6 review WR-01); a number the tool prints is a number someone cuts metal to
    (L02). A whole size such as 5 still prints as "5", so the pinned sentences hold.
    """
    short = f"{x:g}"
    return short if float(short) == x else repr(x)


def measured_range_warning(d: float, pitch: float) -> str | None:  # noqa: ARG001
    """The warning for a nut whose size the clearance default was not measured on, else None.

    Pure size test: it reads `d` alone (R6) and never the clearance, so a nut that took the default
    and one with a typed clearance carry it identically. It warns and changes nothing: the
    parameters are left as set and no row is dropped (D-09, L02). `pitch` is in the signature the
    plan fixes (06-07 key link) and R6 reads it not at all, hence the ARG001 waiver.
    """
    # Written as "inside, else warn" so a NaN d, which compares false both ways, warns too.
    if MEASURED_D_MIN_MM <= d <= MEASURED_D_MAX_MM:
        return None
    return (f"d {_exact(d)} mm is outside M6 to M12, the sizes the clearance default was measured "
            f"on ({CLEARANCE_ENTRY}, run {CLEARANCE_RUN})")


# D-10, D-11, R7 (r7-a): the printability threshold is the size `threshold_from` reads from the
# pinned run-2 record, `RUN_2_SHA256` in bench/print_rules.py. Run 2 is the owner's earlier prints
# accepted under R10, so it is weaker evidence than the pre-registered run (L18 says so). M3 did
# not print a thread (0 of 3), M4 and M5 threaded by hand in 3 of 3 at the L17 default. The two
# floats are M4's d and coarse pitch; tests/test_print_rules.py re-derives them from the record,
# so editing either one alone fails there. Nothing below this size or pitch was printed to work.
THRESHOLD_ENTRY = "L18"
THRESHOLD_RUN = "06-print-run-2"
THRESHOLD_SIZE = "M4"
D_MIN_MM = 4.0
P_MIN_MM = 0.7


def printability_warning(d: float, pitch: float) -> str | None:
    """The warning for a part below what the printed test showed to print, else None (D-13).

    One sentence naming each crossed edge, `d` first. Strict `<` on the stored floats, no rounding
    or tolerance: exactly at the threshold is the size that printed. It warns and changes nothing:
    the parameters are left as set, because no d or pitch can be trimmed without overriding one the
    user set (L02). It does not promise a build: another rule may still refuse the part (WR-02).
    """
    crossed: list[str] = []
    if d < D_MIN_MM:
        crossed.append(f"d {_exact(d)} mm is below d_min {D_MIN_MM:g} mm")
    if pitch < P_MIN_MM:
        crossed.append(f"pitch {_exact(pitch)} mm is below P_min {P_MIN_MM:g} mm")
    if not crossed:
        return None
    return (f"{' and '.join(crossed)}: {THRESHOLD_SIZE} is the smallest size that printed and "
            f"threaded by hand in run {THRESHOLD_RUN} ({THRESHOLD_ENTRY}); parameters left as set")
