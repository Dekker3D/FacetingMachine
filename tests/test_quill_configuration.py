from __future__ import annotations

import math
import unittest

import cadquery as cq
import bom_part_data as bpd
import bought_bits as bb
from quill.quill_assembly import (
    QuillAssemblyStandardMk1,
    QuillCheaterAdjustmentWheel,
    QuillCheaterBearingTop,
    QuillCheaterRocker,
)


def _solid_contains(shape: cq.Solid, point: cq.Vector) -> bool:
    """Call CadQuery's runtime method despite its broken generic self stub."""
    return bool(getattr(shape, "isInside")(point))


class CompressionSpringTests(unittest.TestCase):
    def test_rejects_free_length_below_modeled_solid_height(self) -> None:
        with self.assertRaisesRegex(ValueError, "modeled solid height"):
            bb.CompressionSpring(
                wire_diameter=1.0,
                outside_diameter=5.0,
                free_length=2.0,
                coil_count=8,
            )

    def test_rejects_non_finite_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "wire diameter must be finite"):
            bb.CompressionSpring(
                wire_diameter=math.nan,
                outside_diameter=8.0,
                free_length=15.0,
            )

    def test_rejects_fractional_coil_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive integer"):
            bb.CompressionSpring(
                wire_diameter=0.5,
                outside_diameter=8.0,
                free_length=15.0,
                coil_count=2.5,  # type: ignore[arg-type]
            )

    def test_rejects_display_length_above_free_length(self) -> None:
        spring = bb.CompressionSpring(
            wire_diameter=0.5,
            outside_diameter=8.0,
            free_length=15.0,
        )
        with self.assertRaisesRegex(ValueError, "cannot exceed its free length"):
            spring.object_at_length(15.1)


class QuillSpringConfigurationTests(unittest.TestCase):
    def test_cheater_wheel_hex_pocket_preserves_inner_material_floor(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        wheel = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, QuillCheaterAdjustmentWheel)
        )

        self.assertAlmostEqual(wheel.outside_diameter, 30.0)
        self.assertAlmostEqual(wheel.width, quill.cheater_wheel_width())
        self.assertAlmostEqual(wheel.width, 14.5)
        self.assertAlmostEqual(quill.cheater_wheel_material_beneath_head, 3.0)
        self.assertAlmostEqual(
            wheel.hex_depth,
            quill.cheater_wheel_hex_pocket_depth(),
        )
        self.assertAlmostEqual(wheel.hex_depth, 11.5)
        self.assertAlmostEqual(
            wheel.width - wheel.hex_depth,
            quill.cheater_wheel_material_beneath_head,
        )
        self.assertLess(wheel.hex_depth, wheel.width)

    def test_selected_spring_and_seat_contract(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        spring = quill.cheater_spring()

        self.assertAlmostEqual(spring.outside_diameter, 6.0)
        self.assertAlmostEqual(spring.free_length, 20.0)
        self.assertAlmostEqual(spring.wire_diameter, 1.0)
        self.assertEqual(spring.coil_count, 8)
        self.assertAlmostEqual(quill.cheater_spring_preload_compression, 1.0)
        self.assertAlmostEqual(quill.cheater_spring_installed_length(), 19.0)
        self.assertGreaterEqual(
            quill.cheater_spring_installed_length(),
            (spring.coil_count + 1) * spring.wire_diameter,
        )
        self.assertAlmostEqual(
            quill.cheater_spring_center_x(),
            quill.cheater_pivot_x() + quill.cheater_spring_center_from_pivot_x,
        )

        parts = [part for part, _quantity in quill.get_BOM().items()]
        top = next(part for part in parts if isinstance(part, QuillCheaterBearingTop))
        rocker = next(part for part in parts if isinstance(part, QuillCheaterRocker))
        self.assertAlmostEqual(rocker.spring_pocket_depth, 3.0)
        self.assertAlmostEqual(
            top.spring_pocket_floor_z + top.spring_pocket_lip_height,
            quill.cheater_spring_top_pocket_lip_top_z(),
        )
        self.assertAlmostEqual(top.spring_pocket_lip_height, 3.0)
        self.assertFalse(top.spring_pocket_needs_boss)
        self.assertFalse(quill.cheater_spring_top_pocket_needs_boss())
        self.assertAlmostEqual(top.spring_pocket_boss_outer_diameter, 10.5)
        self.assertGreaterEqual(
            quill.cheater_spring_center_x() - quill.cheater_spring_pocket_diameter() / 2,
            quill.cheater_top_start_x() + quill.cheater_rocker_stop_width_x,
        )

        class BossRequiredQuill(QuillAssemblyStandardMk1):
            cheater_spring_preload_compression = 5.0

        boss_required = BossRequiredQuill(explode=False)
        self.assertTrue(boss_required.cheater_spring_top_pocket_needs_boss())
        self.assertAlmostEqual(
            boss_required.cheater_spring_top_pocket_lip_top_z(),
            boss_required.cheater_spring_top_pocket_floor_z()
            + boss_required.cheater_spring_top_pocket_lip_height,
        )

    def test_cheater_pivot_leverage_and_rocker_stop_contract(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)

        old_pivot_x = quill.index_teeth_positive_x() + 40.0
        self.assertAlmostEqual(
            quill.cheater_pivot_x(),
            old_pivot_x - 10.0,
        )
        self.assertAlmostEqual(quill.cheater_spring_lever_arm_x(), 20.0)
        self.assertAlmostEqual(
            quill.cheater_spring_center_x(), quill.cheater_pivot_x() + 20.0
        )
        self.assertAlmostEqual(quill.cheater_rocker_stop_width_x, 3.0)
        self.assertAlmostEqual(
            quill.cheater_rocker_extra_gear_side_down_travel,
            2.0,
        )
        self.assertAlmostEqual(
            quill.cheater_rocker_stop_width_y(), quill.cheater_rocker_width_y
        )

        limit_angle = quill.cheater_rocker_stop_limit_angle()
        gear_side_radius = quill.cheater_rocker_gear_side_radius_x()
        self.assertAlmostEqual(
            gear_side_radius * math.sin(limit_angle),
            quill.cheater_rocker_extra_gear_side_down_travel,
        )
        expected_contact_top_z = (
            quill.cheater_rocker_neutral_underside_z()
            - quill.cheater_rocker_stop_contact_radius_x()
            * math.sin(limit_angle)
        )
        limited_contact_x = (
            quill.cheater_pivot_x()
            - quill.cheater_rocker_stop_contact_radius_x() * math.cos(limit_angle)
        )
        self.assertAlmostEqual(
            quill.cheater_rocker_stop_contact_top_z(), expected_contact_top_z
        )
        self.assertGreaterEqual(limited_contact_x, quill.cheater_top_start_x())
        self.assertLessEqual(
            limited_contact_x,
            quill.cheater_top_start_x() + quill.cheater_rocker_stop_width_x,
        )

    def test_cheater_bearing_wall_profile_keeps_pivot_and_45_degree_print_face(
        self,
    ) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        cheater_top = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if part.name == "Quill Cheater Bearing Top"
        )
        self.assertIsInstance(cheater_top, QuillCheaterBearingTop)
        assert isinstance(cheater_top, QuillCheaterBearingTop)

        self.assertAlmostEqual(cheater_top.pivot_x, quill.cheater_pivot_x())
        self.assertAlmostEqual(cheater_top.pivot_z, quill.cheater_pivot_z())
        self.assertAlmostEqual(
            cheater_top.outer_arc_center_x,
            quill.cheater_pivot_x(),
        )
        self.assertAlmostEqual(
            cheater_top.outer_arc_center_z,
            quill.cheater_pivot_z(),
        )
        self.assertAlmostEqual(
            cheater_top.outer_arc_radius,
            quill.cheater_wall_outer_radius(),
        )
        for tangent_x, tangent_z in (
            (
                cheater_top.negative_x_profile_tangent_x,
                cheater_top.negative_x_profile_tangent_z,
            ),
            (
                cheater_top.positive_x_profile_tangent_x,
                cheater_top.positive_x_profile_tangent_z,
            ),
        ):
            self.assertAlmostEqual(
                math.hypot(
                    tangent_x - cheater_top.outer_arc_center_x,
                    tangent_z - cheater_top.outer_arc_center_z,
                ),
                cheater_top.outer_arc_radius,
            )
        self.assertAlmostEqual(
            cheater_top.negative_x_profile_base_x,
            cheater_top.negative_x_profile_tangent_x,
        )
        self.assertAlmostEqual(
            cheater_top.negative_x_profile_base_z,
            quill.block_height_z(),
        )
        # A vertical -X support and the +X direct support are both tangent to
        # the same circle: each support direction is perpendicular to radius.
        negative_radius = (
            cheater_top.negative_x_profile_tangent_x
            - cheater_top.outer_arc_center_x,
            cheater_top.negative_x_profile_tangent_z
            - cheater_top.outer_arc_center_z,
        )
        negative_support = (
            cheater_top.negative_x_profile_base_x
            - cheater_top.negative_x_profile_tangent_x,
            cheater_top.negative_x_profile_base_z
            - cheater_top.negative_x_profile_tangent_z,
        )
        positive_radius = (
            cheater_top.positive_x_profile_tangent_x
            - cheater_top.outer_arc_center_x,
            cheater_top.positive_x_profile_tangent_z
            - cheater_top.outer_arc_center_z,
        )
        positive_support = (
            cheater_top.positive_x_profile_endpoint_x
            - cheater_top.positive_x_profile_tangent_x,
            cheater_top.positive_x_profile_endpoint_z
            - cheater_top.positive_x_profile_tangent_z,
        )
        self.assertAlmostEqual(
            negative_radius[0] * negative_support[0]
            + negative_radius[1] * negative_support[1],
            0.0,
        )
        self.assertAlmostEqual(
            positive_radius[0] * positive_support[0]
            + positive_radius[1] * positive_support[1],
            0.0,
        )
        self.assertAlmostEqual(
            cheater_top.positive_x_profile_endpoint_x,
            quill.cheater_wall_positive_x_endpoint_x(),
        )
        self.assertAlmostEqual(
            cheater_top.positive_x_profile_endpoint_z,
            quill.block_height_z(),
        )
        self.assertAlmostEqual(
            cheater_top.positive_x_profile_slope_angle(),
            45.0,
        )
        self.assertLessEqual(
            cheater_top.positive_x_profile_slope_angle(),
            quill.cheater_wall_max_print_angle,
        )

    def test_default_configuration_builds_valid_printed_parts(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)

        self.assertAlmostEqual(
            quill.bearing_pocket_depth(),
            quill.bearing_type.WIDTH + quill.bearing_axial_tolerance,
        )
        self.assertAlmostEqual(
            quill.index_side_bearing_x(), quill.bearing_retaining_lip_depth
        )
        self.assertAlmostEqual(
            quill.collet_side_bearing_x(),
            quill.block_length_x()
            - quill.bearing_retaining_lip_depth
            - quill.bearing_type.WIDTH,
        )
        self.assertAlmostEqual(
            quill.index_gear_modeled_spacer_width(),
            quill.index_gear_spacer_width + quill.bearing_retaining_lip_depth,
        )

        body_object = next(
            part for part, _quantity in quill.get_BOM().items()
            if part.name == "Quill Body"
        ).get_object()
        assert body_object is not None
        self.assertIsInstance(body_object, cq.Workplane)
        assert isinstance(body_object, cq.Workplane)
        body_shape = body_object.solids().val()
        self.assertIsInstance(body_shape, cq.Solid)
        assert isinstance(body_shape, cq.Solid)
        block_x = quill.block_x_offset
        axis_z_below_split = quill.block_center_z() - 2.0
        block_length = quill.block_length_x()
        for lip_x in (block_x + 0.5, block_x + block_length - 0.5):
            self.assertTrue(
                _solid_contains(
                    body_shape, cq.Vector(lip_x, 13.5, axis_z_below_split)
                )
            )
            self.assertFalse(
                _solid_contains(
                    body_shape, cq.Vector(lip_x, 12.0, axis_z_below_split)
                )
            )
        for pocket_x in (block_x + 1.5, block_x + block_length - 1.5):
            self.assertFalse(
                _solid_contains(
                    body_shape, cq.Vector(pocket_x, 13.5, axis_z_below_split)
                )
            )

        index_gear_object = next(
            part for part, _quantity in quill.get_BOM().items()
            if part.name == "Index Gear"
        ).get_object()
        assert index_gear_object is not None
        self.assertIsInstance(index_gear_object, cq.Workplane)
        assert isinstance(index_gear_object, cq.Workplane)
        index_gear_shape = index_gear_object.solids().val()
        self.assertIsInstance(index_gear_shape, cq.Solid)
        assert isinstance(index_gear_shape, cq.Solid)
        self.assertAlmostEqual(
            index_gear_shape.BoundingBox().zmax,
            quill.index_gear_width() + quill.bearing_retaining_lip_depth,
        )

        printed_parts = [
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, bpd.PrintedPart)
        ]

        self.assertGreater(len(printed_parts), 0)
        for part in printed_parts:
            obj = part.get_object()
            self.assertIsNotNone(obj, part.name)
            assert obj is not None
            self.assertEqual(obj.solids().size(), 1, part.name)
            shape = obj.val() if isinstance(obj, cq.Workplane) else obj
            self.assertIsInstance(shape, cq.Shape, part.name)
            assert isinstance(shape, cq.Shape)
            self.assertTrue(shape.isValid(), part.name)

    def test_rejects_main_bearing_that_does_not_match_shank(self) -> None:
        with self.assertRaisesRegex(ValueError, "shank diameter must match"):
            QuillAssemblyStandardMk1(
                bearing_type=bb.Bearing608ZZ,
                explode=False,
            )

    def test_rejects_retaining_lip_that_reaches_past_outer_race(self) -> None:
        class ExcessiveLipQuill(QuillAssemblyStandardMk1):
            bearing_retaining_lip_overlap = 8.0

        with self.assertRaisesRegex(ValueError, "touch only the outer race"):
            ExcessiveLipQuill(explode=False)

    def test_rejects_spring_without_preload(self) -> None:
        class ShortSpringQuill(QuillAssemblyStandardMk1):
            cheater_spring_free_length = 8.0

        with self.assertRaisesRegex(ValueError, "installed length"):
            ShortSpringQuill(explode=False)

    def test_rejects_lip_that_blocks_index_gear_spacer(self) -> None:
        class ExcessiveLipOverlapQuill(QuillAssemblyStandardMk1):
            bearing_retaining_lip_overlap = 6.0

        with self.assertRaisesRegex(ValueError, "opening must clear"):
            ExcessiveLipOverlapQuill(explode=False)

    def test_rejects_spring_pocket_wider_than_rocker(self) -> None:
        class WideSpringQuill(QuillAssemblyStandardMk1):
            cheater_spring_outside_diameter = 20.0

        with self.assertRaisesRegex(ValueError, "narrower than the rocker"):
            WideSpringQuill(explode=False)

    def test_rejects_spring_pocket_outside_short_rocker_arm(self) -> None:
        class ShortRockerQuill(QuillAssemblyStandardMk1):
            cheater_rocker_positive_x_length = 1.0

        with self.assertRaisesRegex(ValueError, "does not fit within the rocker arm"):
            ShortRockerQuill(explode=False)

    def test_accepts_thicker_wire_when_coil_count_keeps_solid_height_valid(self) -> None:
        class ThickWireQuill(QuillAssemblyStandardMk1):
            cheater_spring_wire_diameter = 2.0
            cheater_spring_coil_count = 5

        quill = ThickWireQuill(explode=False)

        self.assertEqual(quill.cheater_spring().coil_count, 5)
        self.assertGreaterEqual(
            quill.cheater_spring_installed_length(),
            (quill.cheater_spring_coil_count + 1)
            * quill.cheater_spring_wire_diameter,
        )


if __name__ == "__main__":
    unittest.main()
