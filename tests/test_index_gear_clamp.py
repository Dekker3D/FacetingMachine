from __future__ import annotations

import unittest

import cadquery as cq
from quill.quill_assembly import (
    IndexGearStandardMk1,
    QuillAssemblyStandardMk1,
    QuillBody,
)


def shape_volume(workplane: cq.Workplane) -> float:
    shape = workplane.val()
    assert isinstance(shape, cq.Shape)
    return shape.Volume()


class IndexGearClampTests(unittest.TestCase):
    def test_default_clamp_uses_selected_m3_hardware(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)

        screw = quill.index_gear_clamp_screw()
        nut = quill.index_gear_clamp_nut()

        self.assertEqual(screw.name, "M3×8mm Set Screw")
        self.assertEqual(nut.name, "M3 Nut")
        self.assertAlmostEqual(
            quill.index_gear_clamp_screw_hole_dia(),
            screw.diameter() + quill.index_gear_clamp_screw_clearance,
        )
        self.assertAlmostEqual(
            quill.index_gear_clamp_nut_pocket_width(),
            nut.width_across_flats() + quill.index_gear_clamp_nut_clearance,
        )
        self.assertAlmostEqual(
            quill.index_gear_clamp_nut_pocket_depth(),
            nut.height() + quill.index_gear_clamp_nut_depth_clearance,
        )
        self.assertLess(
            quill.index_gear_clamp_nut_pocket_corner_dia(),
            quill.index_gear_numbers_width,
        )

    def test_clamp_angle_is_halfway_between_number_positions(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)

        tooth_pitch = 360.0 / quill.index_gear_num_teeth
        self.assertAlmostEqual(
            quill.index_gear_clamp_angle(),
            tooth_pitch * quill.index_gear_number_interval_teeth / 2,
        )

    def test_clamp_hardware_is_in_quill_bom(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        items = dict(quill.get_BOM().items())

        self.assertEqual(items[quill.index_gear_clamp_screw()], 1)
        self.assertEqual(items[quill.index_gear_clamp_nut()], 9)

    def test_index_gear_receives_derived_clamp_dimensions(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        gear = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, IndexGearStandardMk1)
        )

        self.assertAlmostEqual(
            gear.clamp_screw_hole_dia,
            quill.index_gear_clamp_screw_hole_dia(),
        )
        self.assertAlmostEqual(
            gear.clamp_nut_width_across_flats,
            quill.index_gear_clamp_nut_pocket_width(),
        )
        self.assertAlmostEqual(
            gear.clamp_nut_depth,
            quill.index_gear_clamp_nut_pocket_depth(),
        )
        self.assertAlmostEqual(gear.clamp_angle, quill.index_gear_clamp_angle())
        self.assertAlmostEqual(quill.index_gear_clamp_nut_bore_wall(), 4.65)
        self.assertGreaterEqual(
            quill.index_gear_clamp_nut_bore_wall(),
            quill.index_gear_clamp_nut_bore_wall_min,
        )

    def test_clamp_hardware_fits_printed_cutouts_without_overlap(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        gear = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, IndexGearStandardMk1)
        )
        gear_object = gear.get_object()
        self.assertIsInstance(gear_object, cq.Workplane)
        assert isinstance(gear_object, cq.Workplane)
        screw_object, nut_object = quill.index_gear_clamp_hardware_local_objects()

        self.assertLess(shape_volume(gear_object.intersect(screw_object)), 0.001)
        self.assertLess(shape_volume(gear_object.intersect(nut_object)), 0.001)
        self.assertLess(shape_volume(screw_object.intersect(nut_object)), 0.001)

        shank_envelope = cq.Workplane("XY").cylinder(
            gear.teeth_width + gear.numbers_width,
            gear.bore_dia / 2,
            centered=(True, True, False),
        )
        self.assertLess(shape_volume(screw_object.intersect(shank_envelope)), 0.001)

    def test_rejects_clamp_screw_that_cannot_reach_shank(self) -> None:
        class ShortClampScrewQuill(QuillAssemblyStandardMk1):
            index_gear_clamp_screw_length = 6.0

        with self.assertRaisesRegex(ValueError, "cannot reach the ER11 shank"):
            ShortClampScrewQuill(explode=False)

    def test_rejects_nut_pocket_with_less_than_two_mm_bore_wall(self) -> None:
        class ThinBoreWallQuill(QuillAssemblyStandardMk1):
            index_gear_clamp_nut_inset = 13.0

        with self.assertRaisesRegex(ValueError, "too little material"):
            ThinBoreWallQuill(explode=False)

    def test_rejects_number_layout_that_does_not_align_with_teeth(self) -> None:
        class MisalignedNumbersQuill(QuillAssemblyStandardMk1):
            index_gear_number_interval_teeth = 7

        with self.assertRaisesRegex(
            ValueError, "divisible by index_gear_number_interval_teeth"
        ):
            MisalignedNumbersQuill(explode=False)

    def test_axial_bearing_clearance_remains_explicit(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)

        self.assertEqual(quill.bearing_radial_tolerance, 0.0)
        self.assertAlmostEqual(
            quill.bearing_pocket_depth() - quill.bearing_type.WIDTH,
            quill.bearing_axial_tolerance,
        )

    def test_gear_installation_pocket_extends_ten_mm_toward_negative_x(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        body = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, QuillBody)
        )

        self.assertEqual(quill.body_index_gear_axial_clearance, 10.0)
        (
            gear_start_x,
            gear_width_x,
            _axis_z,
            _clearance_radius,
            axial_clearance,
        ) = body.index_gear_clearance_dimensions
        clearance_start_x = gear_start_x - axial_clearance
        clearance_end_x = clearance_start_x + gear_width_x + axial_clearance
        self.assertEqual(axial_clearance, quill.body_index_gear_axial_clearance)
        self.assertAlmostEqual(clearance_start_x, gear_start_x - 10.0)
        self.assertAlmostEqual(clearance_end_x, body.block_x)


if __name__ == "__main__":
    unittest.main()
