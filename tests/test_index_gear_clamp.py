from __future__ import annotations

import unittest

import cadquery as cq
from quill.quill_assembly import (
    IndexGearStandardMk1,
    QuillAssemblyStandardMk1,
    QuillBody,
    QuillCheaterGearSection,
    gear_tooth_profile_polar_points,
)


def shape_volume(workplane: cq.Workplane) -> float:
    shape = workplane.val()
    assert isinstance(shape, cq.Shape)
    return shape.Volume()


class IndexGearClampTests(unittest.TestCase):
    def test_shared_tooth_profile_alternates_valleys_and_tips(self) -> None:
        profile = gear_tooth_profile_polar_points(
            range(3),
            angular_pitch=1.0,
            root_radius=10.0,
            tip_radius=11.0,
            valley_angle_offset=-0.5,
        )

        self.assertEqual(
            profile,
            [(-0.5, 10.0), (0.0, 11.0), (0.5, 10.0), (1.0, 11.0), (1.5, 10.0), (2.0, 11.0)],
        )

    def test_mating_gears_receive_shared_relief_and_neutral_contact_values(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        parts = [part for part, _quantity in quill.get_BOM().items()]
        index_gear = next(part for part in parts if isinstance(part, IndexGearStandardMk1))
        cheater_gear = next(part for part in parts if isinstance(part, QuillCheaterGearSection))

        self.assertEqual(quill.cheater_gear_section_neutral_clearance, 0.0)
        self.assertEqual(quill.gear_tooth_root_relief_tangential_width, 0.2)
        self.assertEqual(quill.gear_tooth_root_relief_radial_depth, 1.0)
        self.assertEqual(index_gear.tooth_root_relief_tangential_width, 0.2)
        self.assertEqual(index_gear.tooth_root_relief_radial_depth, 1.0)
        self.assertEqual(cheater_gear.tooth_root_relief_tangential_width, 0.2)
        self.assertEqual(cheater_gear.tooth_root_relief_radial_depth, 1.0)

    def test_neutral_meshing_uses_pitch_circle_center_distance(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)

        index_pitch_radius = quill.index_gear_pitch_radius()
        cheater_pitch_radius = quill.cheater_gear_section_pitch_radius()
        tip_circle_center_distance = (
            quill.index_gear_tip_radius()
            + quill.cheater_gear_section_tooth_tip_radius()
        )

        self.assertAlmostEqual(
            quill.cheater_gear_section_neutral_center_distance(),
            index_pitch_radius + cheater_pitch_radius,
        )
        self.assertAlmostEqual(
            tip_circle_center_distance
            - quill.cheater_gear_section_neutral_center_distance(),
            quill.index_gear_tooth_depth,
        )
        self.assertAlmostEqual(
            quill.cheater_gear_section_tooth_contact_z(),
            quill.block_center_z()
            + quill.cheater_gear_section_neutral_center_distance()
            - quill.cheater_gear_section_tooth_tip_radius(),
        )

    def test_pitch_diameter_controls_tooth_profile_and_matching_curvature(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        gear = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, IndexGearStandardMk1)
        )

        self.assertEqual(quill.index_gear_pitch_diameter, 40.0)
        self.assertAlmostEqual(quill.index_gear_pitch_radius(), 20.0)
        self.assertAlmostEqual(gear.pitch_diameter, quill.index_gear_pitch_diameter)
        self.assertAlmostEqual(gear.pitch_radius(), quill.index_gear_pitch_radius())
        self.assertAlmostEqual(gear.tooth_root_radius(), 19.6)
        self.assertAlmostEqual(gear.tooth_tip_radius(), 20.4)
        self.assertAlmostEqual(gear.mechanical_outer_diameter(), 40.8)
        self.assertAlmostEqual(quill.index_gear_mechanical_outer_diameter(), 40.8)
        self.assertAlmostEqual(
            gear.marking_band_radius(),
            gear.tooth_root_radius() - 0.2,
        )
        self.assertAlmostEqual(
            quill.cheater_gear_section_pitch_radius(),
            quill.index_gear_pitch_radius(),
        )
        self.assertAlmostEqual(
            quill.cheater_gear_section_neutral_center_distance(),
            2 * quill.index_gear_pitch_radius(),
        )

    def test_markings_use_separate_axial_number_and_tick_bands(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        gear = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, IndexGearStandardMk1)
        )

        self.assertAlmostEqual(gear.number_engraving_z, gear.numbers_width / 3 + 1.0)
        self.assertLess(gear.number_engraving_z, gear.tick_band_start_z)
        self.assertGreater(gear.tick_band_start_z, 0.0)
        self.assertAlmostEqual(gear.tick_band_end_z, gear.numbers_width)
        self.assertLessEqual(gear.tick_band_end_z, gear.numbers_width)

    def test_tick_hierarchy_uses_number_interval_midpoint_and_small_number_ticks(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        gear = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, IndexGearStandardMk1)
        )
        number_interval = gear.number_interval_teeth
        midpoint = number_interval // 2

        self.assertEqual(gear.tick_mark_length(0), gear.small_tick_length())
        self.assertEqual(
            gear.tick_mark_length(midpoint),
            gear.large_midpoint_tick_length(),
        )
        self.assertEqual(
            gear.tick_mark_length(gear.tick_interval_teeth),
            gear.small_tick_length(),
        )
        self.assertEqual(
            gear.tick_mark_length(number_interval - gear.tick_interval_teeth),
            gear.small_tick_length(),
        )
        self.assertEqual(
            gear.tick_mark_length(number_interval),
            gear.small_tick_length(),
        )

    def test_cheater_gear_extension_stays_below_screws_with_head_clearances(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        cheater_gear = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, QuillCheaterGearSection)
        )
        shape = cheater_gear.get_assembled_object().val()
        assert isinstance(shape, cq.Shape)
        bounds = shape.BoundingBox()

        self.assertAlmostEqual(bounds.ymax, quill.cheater_rocker_width_y / 2, places=6)
        self.assertAlmostEqual(bounds.ymin, -quill.cheater_rocker_width_y / 2, places=6)
        self.assertAlmostEqual(
            bounds.xmin,
            quill.cheater_gear_section_negative_x()
            - quill.cheater_gear_section_negative_x_extension,
            places=6,
        )
        extension_test_x = (
            quill.cheater_gear_section_negative_x()
            - quill.cheater_gear_section_negative_x_extension / 2
        )
        retained_extension_z = (
            cheater_gear.backing_bottom_z + cheater_gear.screw_z
        ) / 2
        self.assertTrue(
            shape.isInside(  # type: ignore[reportAttributeAccessIssue]
                cq.Vector(
                    extension_test_x,
                    -0.5,
                    retained_extension_z,
                )
            )
        )
        self.assertFalse(
            shape.isInside(  # type: ignore[reportAttributeAccessIssue]
                cq.Vector(
                    extension_test_x,
                    quill.cheater_rocker_width_y / 4,
                    retained_extension_z,
                )
            )
        )
        self.assertFalse(
            shape.isInside(  # type: ignore[reportAttributeAccessIssue]
                cq.Vector(
                    extension_test_x,
                    -quill.cheater_rocker_width_y / 4,
                    cheater_gear.screw_z + 1.0,
                )
            )
        )
        head_clearance_radius = cheater_gear.screw_head_diameter / 2 + 1.0
        for screw_y in (-cheater_gear.screw_spacing_y / 2, cheater_gear.screw_spacing_y / 2):
            self.assertFalse(
                shape.isInside(  # type: ignore[reportAttributeAccessIssue]
                    cq.Vector(
                        extension_test_x,
                        screw_y + head_clearance_radius - 0.25,
                        cheater_gear.screw_z,
                    )
                )
            )
        self.assertEqual(cheater_gear.tooth_count, quill.cheater_gear_section_tooth_count())
        self.assertEqual(
            cheater_gear.mating_index_gear_tooth_count,
            quill.index_gear_num_teeth,
        )
        self.assertGreater(cheater_gear.tooth_count_engraving_z, cheater_gear.screw_z)

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
        self.assertAlmostEqual(
            quill.index_gear_clamp_screw_adjustment_available(),
            quill.index_gear_clamp_screw_adjustment_target,
        )
        self.assertAlmostEqual(quill.index_gear_clamp_nut_bore_wall(), 2.6)
        self.assertGreaterEqual(
            quill.index_gear_clamp_nut_bore_wall(),
            quill.index_gear_clamp_nut_bore_wall_min,
        )

    def test_nut_position_tracks_screw_length_and_adjustment_target(self) -> None:
        class LongerClampScrewQuill(QuillAssemblyStandardMk1):
            index_gear_clamp_screw_length = 9.0

        default = QuillAssemblyStandardMk1(explode=False)
        longer = LongerClampScrewQuill(explode=False)

        self.assertAlmostEqual(
            longer.index_gear_clamp_nut_inner_radius()
            - default.index_gear_clamp_nut_inner_radius(),
            1.0,
        )
        self.assertAlmostEqual(
            longer.index_gear_clamp_screw_adjustment_available(),
            longer.index_gear_clamp_screw_adjustment_target,
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

    def test_rejects_screw_too_short_for_adjustment_and_bore_wall(self) -> None:
        class ShortClampScrewQuill(QuillAssemblyStandardMk1):
            index_gear_clamp_screw_length = 6.0

        with self.assertRaisesRegex(ValueError, "cannot provide the requested"):
            ShortClampScrewQuill(explode=False)

    def test_rejects_adjustment_target_that_would_break_bore_wall(self) -> None:
        class ExcessiveAdjustmentQuill(QuillAssemblyStandardMk1):
            index_gear_clamp_screw_adjustment_target = 4.0

        with self.assertRaisesRegex(ValueError, "minimum bore wall"):
            ExcessiveAdjustmentQuill(explode=False)

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
