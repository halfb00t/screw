"""The D-10 probe of Phase 5: what the bolt's tip cone, the shank fillet ring and the nut's two
cutter families do to the shipped thread and void, against kernel-free oracles.

Phase 4 left both thread ends plain (04 D-01, D-02) and Phase 5 adds an end model before the
standards are read (ISO 4753, ISO 4032), so nothing has measured whether a cone, a ring or a
countersink keeps the solid count, validity, mesh closedness and export size. This records it
before any end model or tolerance is fixed. It bounds nothing: single runs, one host, load not
controlled. Kernel side (it imports `cadquery`), run by hand: `python -m bench.end_cuts`.

Every angle, radius, `s`, `m` and `r` below is an UNVERIFIED probe input chosen to span the sizes,
not a table row and not a clause of ISO 4753 or ISO 4032 (no table value of either is read
anywhere in this repository yet, TABL-04). D-15's UNVERIFIED scan covers `src/screw/tables/`
only, and nothing under `src/` reads this module.

The bodies are the shipped `screw.solid.helical.thread` (rod and void) and the shipped
`screw.solid.bolt.thread` / `assemble`, never a copy, so what is measured is the thread that
ships. Only the cutters are new, and they are built here. The bolt rows fuse the chamfered head
(`bench.head_fuse.product_head`) and their closed form carries the chamfer term, since 06.1; the
rows in `bench/RESULTS.md` predate that and are the sharp-head probe.

The oracles are plain `math` on the section of the thread, which is the same at every z, so a
cut's removed volume is a one-dimensional integral; they share no code path with the kernel.
05-RESEARCH F4 derived them and this module first held them. Since plan 05-11 they live in
`screw.calc.thread` and are imported back here, so what was probed is what ships (02 D-18);
`tests/test_end_oracles.py` checks each against an identity that does not use it, because the
first arc formula written for the hexagon was off by a factor of 2.2.
"""

from __future__ import annotations

import math
import resource
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import partial

import cadquery as cq

from bench import machine_facts
from bench.head_fuse import head_chamfer_term, product_head
from bench.quiet import Reading, read_now
from bench.thread_spike.maths import NUT_HEIGHT
from bench.thread_spike.measure import gzip1, mesh_stl, stl_check
from screw.calc.thread import (
    FINE_STL_ROWS,
    T_GATE,
    bolt_closed_volume,
    closed_volume,
    countersink_volume,
    face_chamfer_volume,
    fillet_ring_volume,
    hex_prism_volume,
    section_area,
    thread_depth,
    tip_cone_volume,
)
from screw.params import BoltParams
from screw.solid import TESSELLATION, bolt, helical, precise_volume

# The INTERIM export budget (L13): a fine STL plus its gzip level-1 copy must fit in it.
BUDGET_BYTES = 64 * 1024 * 1024

# Radial clearance of every nut void in the probe, mm. A probe input, not a default.
NUT_CLEARANCE = 0.1

# Everything below is an UNVERIFIED probe input.
CSK_HALF_ANGLE_DEG = 45.0   # 90 degrees included
CHAMFER_ANGLE_DEG = 30.0    # from the face, starting on the inscribed circle
CROSS_FRACTION = 0.3        # a crossing cone ends this fraction of the thread depth below the root


# --- kernel-free helpers -------------------------------------------------------------------


def _radii(d: float, pitch: float, c: float) -> tuple[float, float]:
    """(crest radius, root radius) of the section with the radial clearance `c` added."""
    return d / 2 + c, d / 2 - thread_depth(pitch) + c


def one_significant_figure_up(x: float) -> float:
    """`x` rounded up to one significant figure, the rounding L11's gate factor used."""
    scale = 10.0 ** math.floor(math.log10(x))
    return math.ceil(x / scale) * scale


# --- kernel side --------------------------------------------------------------------------


def _shape(made: object) -> cq.Shape:
    if not isinstance(made, cq.Shape):
        raise TypeError(f"the kernel produced {type(made).__name__}, expected a shape")
    return made


def _one(shape: cq.Shape) -> cq.Solid:
    """The one solid of `shape`, or a raised error: a cut that splits the part is a finding, and
    it is recorded as a failed row instead of being measured as if it were whole."""
    solids = shape.Solids()
    if len(solids) != 1:
        raise ValueError(f"the cut left {len(solids)} solids, not 1")
    return solids[0]


def _revolved(profile: list[tuple[float, float]]) -> cq.Shape:
    """A solid of revolution about Z; the profile is (radius, z) points of a closed polygon."""
    return _shape(cq.Workplane("XZ").polyline(profile).close().revolve(
        360, (0, 0, 0), (0, 1, 0)).val())


def tip_cut(rod: cq.Solid, d: float, pitch: float, length: float, alpha_deg: float) -> cq.Solid:
    """The thread cut by a tip cone at z = 0: the rod intersected with a revolved envelope (the
    `2026-10-08-a-trim` recipe), the envelope extended past the rod so no face is shared."""
    minor = d / 2 - thread_depth(pitch)
    outer = d / 2 + 1.0
    run = (outer - minor) * math.tan(math.radians(alpha_deg))
    envelope = _revolved([(0, length + 1.0), (outer, length + 1.0), (outer, run),
                          (minor, 0.0), (0, 0.0)])
    return _one(rod.intersect(envelope))


def fillet_ring(d: float, length: float, r: float) -> cq.Shape:
    """The quarter-circle ring under a head whose underside is z = `length`: it shares the shank
    cylinder (radius d/2) and the underside plane, and fuses onto both."""
    root = d / 2
    mid = r / math.sqrt(2)
    return _shape(cq.Workplane("XZ").moveTo(root, length).lineTo(root + r, length)
                  .threePointArc((root + r - mid, length - r + mid), (root, length - r))
                  .close().revolve(360, (0, 0, 0), (0, 1, 0)).val())


@dataclass(frozen=True)
class NutCase:
    label: str
    d: float
    pitch: float
    s: float
    m: float
    left_hand: bool
    countersink: bool
    chamfer: bool
    grazing: bool = False

    @property
    def r_face(self) -> float:
        """Countersink radius at the face: past the crest radius d/2 + c, so the cone crosses
        the void (F8), and inside the chamfer's start radius s/2."""
        return self.d / 2 + NUT_CLEARANCE + self.pitch / 2

    @property
    def r_root(self) -> float:
        return _radii(self.d, self.pitch, NUT_CLEARANCE)[1]

    @property
    def r_inner(self) -> float:
        """Where the countersink cone ends: below the root radius to cross it, on it to graze."""
        if self.grazing:
            return self.r_root
        return self.r_root - CROSS_FRACTION * thread_depth(self.pitch)

    @property
    def csk_depth(self) -> float:
        return (self.r_face - self.r_inner) / math.tan(math.radians(CSK_HALF_ANGLE_DEG))

    @property
    def r0(self) -> float:
        return self.s / 2

    @property
    def chamfer_depth(self) -> float:
        """The cone's own depth at the hexagon corner, where the oracle's cap does not bind."""
        corner = self.s / 2 / math.cos(math.pi / 6)
        return (corner - self.r0) * math.tan(math.radians(CHAMFER_ANGLE_DEG))

    def check_overlap_conditions(self) -> None:
        """P10's four validity conditions of the additive oracle; a case outside them would be
        measured against an oracle that double-counts, so it is refused here."""
        if not (self.r_face <= self.s / 2 and self.r_face <= self.r0
                and 2 * self.csk_depth <= self.m and self.chamfer_depth <= self.m / 2):
            raise ValueError(f"{self.label}: the cutters overlap, the additive oracle is invalid")

    def oracle_removed(self) -> float:
        """Material both faces lose to the cutters this variant has, by the oracles."""
        removed = 0.0
        if self.countersink:
            removed += 2 * countersink_volume(self.d, self.pitch, NUT_CLEARANCE, self.s,
                                              self.r_face, CSK_HALF_ANGLE_DEG, self.csk_depth)
        if self.chamfer:
            removed += 2 * face_chamfer_volume(self.s, self.r0, CHAMFER_ANGLE_DEG,
                                               self.chamfer_depth)
        return removed


def _at(case: NutCase, depth: float, from_top: bool) -> float:
    """z of a point `depth` mm into the nut from its bottom face, or from its top face."""
    return case.m - depth if from_top else depth


def build_nut(case: NutCase) -> cq.Shape:
    """A hexagonal prism of across-flats `s` and height `m` on z in [0, m], less the shipped
    void (`helical.thread` of m + 2P from z = -P at clearance 0.1), then the variant's cutters.
    Each cutter crosses the surface it cuts and is extended past the faces (F8, P7)."""
    prism = _shape(cq.Workplane("XY").polygon(6, case.s, circumscribed=True).extrude(case.m).val())
    void = helical.thread(case.d, case.pitch, case.m + 2 * case.pitch, clearance=NUT_CLEARANCE,
                          left_hand=case.left_hand).translate(cq.Vector(0, 0, -case.pitch))
    nut = prism.cut(void)
    if case.countersink:
        tan_half = math.tan(math.radians(CSK_HALF_ANGLE_DEG))
        out = case.r_face + tan_half
        zi = case.csk_depth
        for flip in (False, True):
            nut = nut.cut(_revolved([(0, _at(case, -1.0, flip)), (out, _at(case, -1.0, flip)),
                                     (case.r_inner, _at(case, zi, flip)),
                                     (0, _at(case, zi, flip))]))
    if case.chamfer:
        tan_beta = math.tan(math.radians(CHAMFER_ANGLE_DEG))
        corner = case.s / 2 / math.cos(math.pi / 6)
        outer = corner + 1.0
        inner = case.r0 - 0.5 / tan_beta
        for flip in (False, True):
            nut = nut.cut(_revolved([(inner, _at(case, -0.5, flip)),
                                     (outer, _at(case, -0.5, flip)),
                                     (outer, _at(case, (outer - case.r0) * tan_beta, flip))]))
    return nut


@dataclass(frozen=True)
class Row:
    label: str
    group: str
    seconds: float = 0.0
    solids: int = 0
    valid: bool = False
    piece_error: float | None = None
    whole_error: float | None = None
    open_preview: int | None = None
    open_fine: int | None = None
    fine_seconds: float | None = None
    peak_rss: int = 0
    raw_bytes: int | None = None
    gzip_bytes: int | None = None
    gzip_seconds: float | None = None
    volume: float | None = None
    failure: str = ""


def _rss() -> int:
    """ru_maxrss is the peak over the whole process so far (bytes on macOS, KiB on Linux), so a
    row reads the largest case run before it, not its own."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def _open_edges(shape: cq.Shape, quality: str) -> tuple[int, float]:
    tolerance, angular = TESSELLATION[quality]
    data, seconds = mesh_stl(shape, tolerance, angular)
    return stl_check(data).open_edges, seconds


def _row(label: str, group: str, seconds: float, shape: cq.Shape, *, piece: float | None,
         whole: float, qualities: tuple[str, ...] = ("preview", "fine")) -> Row:
    preview = _open_edges(shape, "preview")[0] if "preview" in qualities else None
    fine, fine_seconds = _open_edges(shape, "fine") if "fine" in qualities else (None, None)
    return Row(label, group, seconds, len(shape.Solids()), bool(shape.isValid()), piece, whole,
               preview, fine, fine_seconds, _rss())


def _relative(measured: float, oracle: float) -> float:
    return (measured - oracle) / oracle


def probe_tip_bare(d: float, pitch: float, alpha: float, left_hand: bool) -> Row:
    """A bare thread of 8 pitches with a tip cone: removed volume against `tip_cone_volume`."""
    length = 8 * pitch
    t0 = time.perf_counter()
    rod = helical.thread(d, pitch, length, left_hand=left_hand)
    cut = tip_cut(rod, d, pitch, length, alpha)
    seconds = time.perf_counter() - t0
    oracle = tip_cone_volume(d, pitch, alpha)
    removed = precise_volume(rod) - precise_volume(cut)
    whole = precise_volume(cut) / (closed_volume(d, pitch, length) - oracle) - 1
    hand = "left" if left_hand else "right"
    return _row(f"tip {alpha:g} M{d:g} {hand}", "tip", seconds, cut,
                piece=_relative(removed, oracle), whole=whole)


@dataclass(frozen=True)
class BoltCase:
    label: str
    d: float
    pitch: float
    length: float
    s: float
    k: float
    t: float
    left_hand: bool = False

    def params(self) -> BoltParams:
        return BoltParams(d=self.d, pitch=self.pitch, length=self.length, s=self.s, k=self.k,
                          thread_length=self.t, left_hand=self.left_hand)

    def closed(self) -> float:
        return (bolt_closed_volume(self.d, self.pitch, self.length, self.s, self.k, self.t)
                - head_chamfer_term(self.params()))


def probe_tip_bolt(case: BoltCase, alpha: float) -> Row:
    """The shipped bolt with a tip cone on its thread before the head is fused."""
    p = case.params()
    t0 = time.perf_counter()
    thread = bolt.thread(p)
    cut = tip_cut(thread, case.d, case.pitch, case.t, alpha)
    part = bolt.assemble(p, cut, product_head(p))
    seconds = time.perf_counter() - t0
    oracle = tip_cone_volume(case.d, case.pitch, alpha)
    removed = precise_volume(thread) - precise_volume(cut)
    whole = precise_volume(part) / (case.closed() - oracle) - 1
    return _row(f"tip {alpha:g} bolt {case.label}", "tip-bolt", seconds, part,
                piece=_relative(removed, oracle), whole=whole)


def probe_ring(case: BoltCase, r: float, group: str = "ring") -> Row:
    """The shipped bolt with a fillet ring fused under the head: added volume against Pappus."""
    p = case.params()
    t0 = time.perf_counter()
    part = bolt.assemble(p, bolt.thread(p), product_head(p))
    fused = part.fuse(fillet_ring(case.d, case.length, r))
    seconds = time.perf_counter() - t0
    oracle = fillet_ring_volume(case.d, r)
    added = precise_volume(fused) - precise_volume(part)
    whole = precise_volume(fused) / (case.closed() + oracle) - 1
    return _row(f"ring r {r:g} {case.label}", group, seconds, fused,
                piece=_relative(added, oracle), whole=whole)


def probe_nut(case: NutCase, base_volume: float | None) -> Row:
    """A nut variant: removed volume against the oracles (when `base_volume`, the same nut with
    no cutters, is known) and the whole nut against the closed form less the oracle pieces."""
    case.check_overlap_conditions()
    t0 = time.perf_counter()
    nut = build_nut(case)
    seconds = time.perf_counter() - t0
    volume = precise_volume(nut)
    oracle = case.oracle_removed()
    closed = (hex_prism_volume(case.s, case.m)
              - section_area(case.d, case.pitch, NUT_CLEARANCE) * case.m - oracle)
    piece = None
    if base_volume is not None and oracle > 0:
        piece = _relative(base_volume - volume, oracle)
    group = "nut-graze" if case.grazing else "nut"
    row = _row(case.label, group, seconds, nut, piece=piece, whole=volume / closed - 1)
    return replace(row, volume=volume)


def probe_nut_cap(case: NutCase) -> Row:
    """A finished nut at a fine-STL cap: raw and gzip level-1 bytes against the 64 MiB budget.
    Closedness is read on the preview mesh only (3 us per triangle on a fine mesh of millions)."""
    t0 = time.perf_counter()
    nut = build_nut(case)
    seconds = time.perf_counter() - t0
    closed = (hex_prism_volume(case.s, case.m)
              - section_area(case.d, case.pitch, NUT_CLEARANCE) * case.m - case.oracle_removed())
    whole = precise_volume(nut) / closed - 1
    tolerance, angular = TESSELLATION["fine"]
    data, fine_seconds = mesh_stl(nut, tolerance, angular)
    compressed, gzip_seconds = gzip1(data)
    preview = _open_edges(nut, "preview")[0]
    return Row(case.label, "nut-cap", seconds, len(nut.Solids()), bool(nut.isValid()), None,
               whole, preview, None, fine_seconds, _rss(), len(data), compressed, gzip_seconds)


def control_tip(label: str, d: float, pitch: float, length: float,
                built_alpha: float | None, expected_alpha: float) -> Row:
    """Positive control: a tip cut skipped (`built_alpha` None) or built at the wrong angle,
    judged against the oracle of `expected_alpha`. The whole-part comparison at T_GATE and the
    piece comparison both read it."""
    t0 = time.perf_counter()
    rod = helical.thread(d, pitch, length)
    cut = rod if built_alpha is None else tip_cut(rod, d, pitch, length, built_alpha)
    seconds = time.perf_counter() - t0
    oracle = tip_cone_volume(d, pitch, expected_alpha)
    removed = precise_volume(rod) - precise_volume(cut)
    whole = precise_volume(cut) / (closed_volume(d, pitch, length) - oracle) - 1
    return _row(label, "control", seconds, cut, piece=_relative(removed, oracle), whole=whole,
                qualities=("preview",))


def control_ring_dropped(case: BoltCase, r: float) -> Row:
    """Positive control: the ring was expected and not fused."""
    p = case.params()
    t0 = time.perf_counter()
    part = bolt.assemble(p, bolt.thread(p), product_head(p))
    seconds = time.perf_counter() - t0
    oracle = fillet_ring_volume(case.d, r)
    whole = precise_volume(part) / (case.closed() + oracle) - 1
    return _row(f"ring dropped r {r:g} {case.label}", "control", seconds, part,
                piece=_relative(0.0, oracle), whole=whole, qualities=("preview",))


def guarded(label: str, group: str, work: Callable[[], Row]) -> Row:
    """One recorded row whether the case builds or raises: a case that raises is a finding."""
    try:
        return work()
    except Exception as error:  # a kernel failure is a row, not a dead probe
        return Row(label, group, failure=f"{type(error).__name__}: {error}"[:200])


# s, m, and every cutter size are UNVERIFIED probe inputs. m is the spike's preview height.
NUT_SIZES: tuple[tuple[str, float, float, float], ...] = (
    ("M2", 2.0, 0.4, 4.0), ("M6", 6.0, 1.0, 10.0), ("M10", 10.0, 1.5, 16.0),
    ("M20", 20.0, 2.5, 30.0),
)
VARIANTS: tuple[tuple[str, bool, bool], ...] = (
    ("none", False, False), ("countersinks", True, False), ("face chamfers", False, True),
    ("both", True, True),
)
# s, k and t are UNVERIFIED preview readings, as in `bench.head_fuse`.
FILLET_BOLTS: tuple[tuple[BoltCase, float], ...] = (
    (BoltCase("M6 x 30", 6.0, 1.0, 30.0, 10.0, 4.0, 18.0), 0.25),
    (BoltCase("M10 x 80", 10.0, 1.5, 80.0, 16.0, 6.4, 26.0), 0.4),
    (BoltCase("M20 x 100", 20.0, 2.5, 100.0, 30.0, 12.5, 46.0), 0.8),
    (BoltCase("M6 x 30 left", 6.0, 1.0, 30.0, 10.0, 4.0, 18.0, True), 0.25),
)
TIP_BOLTS: tuple[tuple[BoltCase, float], ...] = (
    (BoltCase("M6 x 20", 6.0, 1.0, 20.0, 10.0, 4.0, 20.0), 30.0),
    (BoltCase("M10 x 80", 10.0, 1.5, 80.0, 16.0, 6.4, 26.0), 45.0),
)
CONTROL_BOLTS: tuple[tuple[BoltCase, float], ...] = (
    (BoltCase("M6 x 60", 6.0, 1.0, 60.0, 10.0, 4.0, 18.0), 0.25),
    (BoltCase("M10 x 200", 10.0, 1.5, 200.0, 16.0, 6.4, 26.0), 0.4),
)
# (label size, d, pitch, s, left_hand): the three rod rows whose caps are measured.
CAP_NUTS: tuple[tuple[str, float, float, float, bool], ...] = (
    ("M10 right", 10.0, 1.5, 16.0, False), ("M20 right", 20.0, 2.5, 30.0, False),
    ("M20 left", 20.0, 2.5, 30.0, True),
)


def _nut_cases(size: str, d: float, pitch: float, s: float, left_hand: bool) -> list[NutCase]:
    hand = "left" if left_hand else "right"
    m = NUT_HEIGHT[size]
    return [NutCase(f"nut {size} {hand} {name}", d, pitch, s, m, left_hand, csk, ch)
            for name, csk, ch in VARIANTS]


def run_rows(emit: Callable[[Row], None]) -> list[Row]:
    rows: list[Row] = []

    def add(row: Row) -> None:
        rows.append(row)
        emit(row)

    for left_hand in (False, True):
        hand = "left" if left_hand else "right"
        for size, d, pitch, _ in NUT_SIZES:
            for alpha in (30.0, 45.0):
                add(guarded(f"tip {alpha:g} {size} {hand}", "tip",
                            partial(probe_tip_bare, d, pitch, alpha, left_hand)))
    for bolt_case, alpha in TIP_BOLTS:
        add(guarded(f"tip {alpha:g} bolt {bolt_case.label}", "tip-bolt",
                    partial(probe_tip_bolt, bolt_case, alpha)))
    for bolt_case, r in FILLET_BOLTS:
        add(guarded(f"ring r {r:g} {bolt_case.label}", "ring", partial(probe_ring, bolt_case, r)))
    for left_hand in (False, True):
        for size, d, pitch, s in NUT_SIZES:
            base: float | None = None
            for nut in _nut_cases(size, d, pitch, s, left_hand):
                row = guarded(nut.label, "nut", partial(probe_nut, nut, base))
                add(row)
                if not nut.countersink and not nut.chamfer:
                    base = row.volume
    for left_hand in (False, True):
        hand = "left" if left_hand else "right"
        graze = NutCase(f"nut M6 {hand} countersinks grazing", 6.0, 1.0, 10.0,
                        NUT_HEIGHT["M6"], left_hand, True, False, grazing=True)
        add(guarded(graze.label, "nut-graze", partial(probe_nut, graze, None)))
    for d, pitch, length, name in ((6.0, 1.0, 60.0, "M6 L60"), (10.0, 1.5, 200.0, "M10 L200")):
        skipped = f"control tip cut skipped {name}"
        add(guarded(skipped, "control", partial(control_tip, skipped, d, pitch, length, None,
                                                30.0)))
        wrong = f"control tip 45 built, 30 expected {name}"
        add(guarded(wrong, "control", partial(control_tip, wrong, d, pitch, length, 45.0, 30.0)))
    for bolt_case, r in CONTROL_BOLTS:
        add(guarded(f"control ring dropped {bolt_case.label}", "control",
                    partial(control_ring_dropped, bolt_case, r)))
    for label, d, pitch, s, left_hand in CAP_NUTS:
        cap = FINE_STL_ROWS[(d, pitch, left_hand)]
        for m in (cap, cap + 1.0):
            nut = NutCase(f"nut {label} m {m:g}", d, pitch, s, m, left_hand, True, True)
            add(guarded(nut.label, "nut-cap", partial(probe_nut_cap, nut)))
    return rows


def _e(x: float | None) -> str:
    return "-" if x is None else f"{x:+.2e}"


def _pair(a: int | None, b: int | None) -> str:
    return f"{'-' if a is None else a} / {'-' if b is None else b}"


def main_row(r: Row) -> str:
    if r.failure:
        return f"| {r.label} | FAILED: {r.failure} | | | | | | | |"
    fine = "-" if r.fine_seconds is None else f"{r.fine_seconds:.2f}"
    return (f"| {r.label} | {r.seconds:.2f} | {r.solids} | {r.valid} | {_e(r.piece_error)} "
            f"| {_e(r.whole_error)} | {_pair(r.open_preview, r.open_fine)} | {fine} "
            f"| {r.peak_rss} |")


def cap_row(r: Row) -> str:
    if r.failure:
        return f"| {r.label} | FAILED: {r.failure} | | | | | | | | | |"
    assert r.raw_bytes is not None
    assert r.gzip_bytes is not None
    assert r.fine_seconds is not None
    assert r.gzip_seconds is not None
    total = r.raw_bytes + r.gzip_bytes
    return (f"| {r.label} | {r.seconds:.2f} | {r.solids} | {r.valid} | {_e(r.whole_error)} "
            f"| {r.raw_bytes} | {r.gzip_bytes} | {total} | {total / BUDGET_BYTES:.3f} "
            f"| {r.fine_seconds:.2f} | {r.gzip_seconds:.2f} | {r.peak_rss} |")


def _load(reading: Reading) -> str:
    return f"load1 {reading.load1:.2f} at {reading.utc}"


MAIN_HEADER = ("| Case | build+cut s | solids | isValid | piece rel. error | whole rel. error "
               "| open edges preview / fine | fine mesh s | peak RSS so far (bytes, macOS) |\n"
               "|---|---|---|---|---|---|---|---|---|")
CAP_HEADER = ("| Case | build s | solids | isValid | whole rel. error | fine STL bytes "
              "| gzip-1 bytes | sum | sum / 64 MiB | fine mesh s | gzip s "
              "| peak RSS so far (bytes, macOS) |\n"
              "|---|---|---|---|---|---|---|---|---|---|---|---|")


def main() -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
    print(f"host: {machine_facts()}")
    print(f"HEAD: {head}")
    print(f"before: {_load(read_now())}")
    print(MAIN_HEADER, flush=True)
    in_caps = False

    def emit(r: Row) -> None:
        nonlocal in_caps
        if r.group == "nut-cap" and not in_caps:
            in_caps = True
            print(f"\n{CAP_HEADER}", flush=True)
        print(cap_row(r) if r.group == "nut-cap" else main_row(r), flush=True)

    rows = run_rows(emit)
    honest = [r for r in rows if r.group in ("tip", "tip-bolt", "ring", "nut")
              and r.piece_error is not None]
    largest = max(abs(r.piece_error) for r in honest if r.piece_error is not None)
    gate = one_significant_figure_up(10 * largest)
    print()
    for group in ("tip", "tip-bolt", "ring", "nut"):
        errors = [abs(r.piece_error) for r in honest if r.group == group
                  and r.piece_error is not None]
        print(f"largest |piece error| {group}: {max(errors):.3e} over {len(errors)} rows")
    print(f"largest |piece error| overall: {largest:.3e} over {len(honest)} rows")
    print(f"R11 arithmetic as proposed, not adopted: 10 x largest rounded up to one significant "
          f"figure = {gate:g}; T_GATE = {T_GATE:g}")
    print()
    print("| Control | piece rel. error | piece flagged at that gate | whole rel. error "
          "| whole flagged at T_GATE |")
    print("|---|---|---|---|---|")
    for r in rows:
        if r.group != "control" or r.failure or r.piece_error is None or r.whole_error is None:
            continue
        print(f"| {r.label} | {_e(r.piece_error)} | {abs(r.piece_error) > gate} "
              f"| {_e(r.whole_error)} | {abs(r.whole_error) > T_GATE} |")
    print(f"\nafter: {_load(read_now())} (includes the run's own meshing load)")


if __name__ == "__main__":
    main()
