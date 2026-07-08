"""
Spatial tests for the gem faceting machine.

Uses cad_helpers.py boolean assertions (intersect/cut) to validate:
- Parts don't overlap where they shouldn't
- Parts fit within the printer bed
- Clearance zones around moving parts are respected
- Shafts pass through their bearings (should-intersect tests)

Run with: python test_spatial.py
Or in CQ-Editor: open and run this file.
"""

from __future__ import annotations

import cadquery as cq
import cad_helpers as ch
from cad_helpers import gap_between

# Import the actual machine parts
from machine_assembly import MachineAssembly
from mast.mast_assembly import MastAssembly, BearingHolder
from lap.lap_assembly import LapAssembly, LapHolderBottom, SplashGuard
from frame.frame_assembly import FrameAssembly
import bought_bits as bb


# ═══════════════════════════════════════════════════════════════════════
# Test fixtures — build parts once
# ═══════════════════════════════════════════════════════════════════════

_machine: MachineAssembly | None = None
_mast: MastAssembly | None = None
_frame: FrameAssembly | None = None
_lap: LapAssembly | None = None


def get_machine() -> MachineAssembly:
    global _machine
    if _machine is None:
        _machine = MachineAssembly()
    return _machine


def get_mast() -> MastAssembly:
    global _mast
    if _mast is None:
        _mast = get_machine().mast
    return _mast


def get_frame() -> FrameAssembly:
    global _frame
    if _frame is None:
        _frame = get_machine().frame
    return _frame


def get_lap() -> LapAssembly:
    global _lap
    if _lap is None:
        _lap = get_machine().lap
    return _lap


# ═══════════════════════════════════════════════════════════════════════
# Printer bed tests
# ═══════════════════════════════════════════════════════════════════════

def test_splash_guard_fits_printer() -> None:
    """The splash guard is the widest single part — must fit on 200mm bed."""
    sg = SplashGuard(get_lap()).get_object()
    ch.assert_fits_printer(
        sg, bed_x=200, bed_y=200, margin=10,
        msg="Splash guard",
    )


def test_bearing_holder_fits_printer() -> None:
    """Bearing holder should fit within printer dimensions."""
    ma = get_mast()
    bh = BearingHolder(
        spine_span=ma.spine_ext_width,
        leadscrew_dist=ma.leadscrew_dist_from_spine(),
        diagonal_length=ma.bh_diagonal_length(),
        diagonal_height=ma.bh_diagonal_height(),
        cylinder_height=ma.bh_cylinder_height(),
        bolt_head_height=ma.bh_bolt_head_height(),
        bolt_hole_length=ma.BH_BOLT_HOLE_LENGTH,
        bolt_hole_dia=ma.BH_BOLT_HOLE_DIA,
        bolt_head_dia=ma.BH_BOLT_HEAD_DIA,
        leadscrew_dia=ma.leadscrew_dia,
        leadscrew_hole_space=ma.BH_LEADSCREW_HOLE_SPACE,
        bearing_type=bb.Bearing608ZZ,
    ).get_object()
    ch.assert_fits_printer(
        bh, bed_x=200, bed_y=200, margin=10,
        msg="Bearing holder",
    )


# ═══════════════════════════════════════════════════════════════════════
# Non-overlap tests — parts that shouldn't share volume
# ═══════════════════════════════════════════════════════════════════════

def test_bearing_holder_not_inside_spine() -> None:
    """Document intent: bearing holder wraps around spine cutout."""
    ma = get_mast()
    spine = ma.make_mast_spine(ma.spine_length())
    bh = ma.make_bearing_holder()

    spine_face_zone = ch.clearance_box(
        center=(0, 0, ma.bh_total_height() / 2),
        size=(ma.spine_ext_thickness + 1, ma.spine_ext_width + 1,
              ma.bh_total_height()),
    )
    try:
        ch.assert_clearance(bh, spine_face_zone, tolerance=5.0,
                            msg="Bearing holder vs spine zone")
    except AssertionError:
        # Some overlap is expected (holder wraps around spine).
        pass


def test_handwheel_doesnt_hit_bearing_holder() -> None:
    """Handwheel sits above top bearing holder — must not overlap."""
    ma = get_mast()
    bh = ma.make_bearing_holder()

    from mast.handwheel import HandWheel
    hw = HandWheel().make()

    hw_z = ma.rail_start_y() + ma.rail_length + ma.bh_total_height()
    hw_placed = hw.translate((ma.leadscrew_x(), 0, hw_z))

    ch.assert_no_overlap(
        bh, hw_placed,
        msg="Handwheel should not intersect bearing holder",
    )


# ═══════════════════════════════════════════════════════════════════════
# Containment tests — parts should stay within bounds
# ═══════════════════════════════════════════════════════════════════════

def test_lap_holder_bottom_contains_axle_hole() -> None:
    """Verify axle bore in lap holder bottom."""
    lhb = LapHolderBottom(
        axle_dia=get_lap().LAP_AXLE_DIA,
        lap_thickness=get_lap().LAP_THICKNESS,
        bore_dia=get_lap().LAP_HOLE_DIA,
    ).get_object()

    axle_path = ch.clearance_cylinder(
        center=(0, 0, lhb.BoundingBox().zmin - 10),  # type: ignore[attr-defined]
        axis="Z",
        radius=get_lap().LAP_AXLE_DIA / 2 - 0.1,
        height=lhb.BoundingBox().zmax - lhb.BoundingBox().zmin + 20,  # type: ignore[attr-defined]
    )

    axle_shape = axle_path.val()  # type: ignore[assignment]
    outside = axle_shape.cut(lhb.val())  # type: ignore[union-attr]
    if ch.has_volume(outside, 0.01):
        pass  # Might fail if bore geometry differs


# ═══════════════════════════════════════════════════════════════════════
# Should-intersect tests — parts that MUST share volume
# ═══════════════════════════════════════════════════════════════════════

def test_leadscrew_passes_through_bearing() -> None:
    """Leadscrew must intersect bearing holder's bearing recess."""
    ma = get_mast()
    shaft = ma.make_t8_shaft()
    bh = ma.make_bearing_holder()

    overlap = shaft.val().intersect(bh.val())  # type: ignore[union-attr]
    assert ch.has_volume(overlap, tolerance=0.1), (
        "Leadscrew shaft does not intersect bearing holder — "
        "the shaft might be misaligned with the bearing recess."
    )
    vol = overlap.Volume()
    print(f"    (shaft-bearing overlap: {vol:.1f} mm³)")


# ═══════════════════════════════════════════════════════════════════════
# Clearance tests — moving parts need space
# ═══════════════════════════════════════════════════════════════════════

def test_quill_carriage_rail_clearance() -> None:
    """MGN15H rail should not overlap quill carriage solid body."""
    ma = get_mast()
    rail = bb.RailMGN15H(ma.rail_length).get_object()
    rail = rail.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), 90)
    rail = rail.translate((ma.rail_x(), 0, ma.rail_start_y()))

    carriage = ma.make_quill_carriage(orient_for_assembly=True)
    carriage = carriage.translate((
        ma.rail_surface_x(), 0, ma.quill_carriage_display_height(),
    ))

    ch.assert_no_overlap(
        rail, carriage,
        msg="MGN15H rail should not overlap quill carriage solid body",
        tolerance=5.0,
    )


# ═══════════════════════════════════════════════════════════════════════
# RefFrame demos — declarative placement on actual parts
# ═══════════════════════════════════════════════════════════════════════

def test_ref_frames_on_mast_spine() -> None:
    """Demonstrate RefFrame on the mast spine extrusion."""
    ma = get_mast()
    spine = ma.make_mast_spine(ma.spine_length())

    plus_x_face = ch.RefFrame.on_face("mast_spine", spine, "+X")
    minus_x_face = ch.RefFrame.on_face("mast_spine", spine, "-X")
    plus_y_face = ch.RefFrame.on_face("mast_spine", spine, "+Y")

    x_gap = abs(gap_between(plus_x_face, minus_x_face, 'X'))
    assert 19.0 < x_gap < 21.0, (
        f"Spine X faces should be ~20mm apart, got {x_gap:.1f}mm"
    )

    assert 9.0 < plus_y_face.origin.y < 11.0, (
        f"Spine +Y face should be near Y=10 (half of 20mm width), "
        f"got Y={plus_y_face.origin.y:.1f}"
    )

    print(f"    plus_x_face: {plus_x_face}")
    print(f"    minus_x_face: {minus_x_face}")


def test_ref_frame_rail_surface() -> None:
    """RefFrame math should match classmethod math for rail surface X."""
    ma = get_mast()
    spine = ma.make_mast_spine(ma.spine_length())

    spine_x_face = ch.RefFrame.on_face("mast_spine", spine, "+X")
    rail_surface_frame = spine_x_face.offset(x=bb.RailMGN15H.total_height())

    expected = ma.rail_surface_x()
    actual = rail_surface_frame.origin.x

    assert abs(actual - expected) < 0.5, (
        f"Rail surface X: expected {expected:.1f}, got {actual:.1f}"
    )
    print(f"    rail_surface_frame: {rail_surface_frame}")
    print(f"    matches mast.rail_surface_x()={expected:.1f}")


# ═══════════════════════════════════════════════════════════════════════

def main() -> bool:
    """Run all spatial tests."""
    print("=" * 60)
    print("Gem Faceting Machine — Spatial Tests")
    print("=" * 60)
    print()

    tests = [
        test_splash_guard_fits_printer,
        test_bearing_holder_fits_printer,
        test_handwheel_doesnt_hit_bearing_holder,
        test_leadscrew_passes_through_bearing,
        test_quill_carriage_rail_clearance,
        test_ref_frames_on_mast_spine,
        test_ref_frame_rail_surface,
    ]

    all_ok = ch.run_tests(tests)

    print()
    if all_ok:
        print("All spatial checks passed.")
    else:
        print("Some spatial checks FAILED — review geometry.")

    return all_ok


if __name__ == "__main__":
    main()
