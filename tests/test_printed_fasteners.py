from __future__ import annotations

import unittest

import cadquery as cq

from printed_fasteners import SideLoadedCaptiveNutHole


def intersection_volume(first: cq.Workplane, second: cq.Workplane) -> float:
    result = first.intersect(second).val()
    assert isinstance(result, cq.Shape)
    return result.Volume()


class SideLoadedCaptiveNutHoleTests(unittest.TestCase):
    def test_can_leave_half_mm_bridge_above_nut_channel(self) -> None:
        cutout = SideLoadedCaptiveNutHole(
            shaft_diameter=3.2,
            shaft_depth=25.0,
            nut_width_across_flats=5.9,
            nut_depth=2.6,
            nut_drop_from_interface=8.0,
            channel_length=12.0,
            bridge_thickness=0.5,
            bridge_side="above_nut",
        ).make_cutout()

        bridge_probe = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(-0.3)
            .translate((0.0, 0.0, -7.6))
        )
        shaft_above = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(-0.2)
            .translate((0.0, 0.0, -7.2))
        )
        nut_cavity = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(-0.2)
            .translate((0.0, 0.0, -8.1))
        )

        self.assertLess(intersection_volume(cutout, bridge_probe), 0.001)
        self.assertGreater(intersection_volume(cutout, shaft_above), 0.5)
        self.assertGreater(intersection_volume(cutout, nut_cavity), 0.5)

    def test_can_leave_half_mm_bridge_below_nut_channel(self) -> None:
        cutout = SideLoadedCaptiveNutHole(
            shaft_diameter=3.2,
            shaft_depth=25.0,
            nut_width_across_flats=5.9,
            nut_depth=2.6,
            nut_drop_from_interface=8.0,
            channel_length=12.0,
            bridge_thickness=0.5,
            bridge_side="below_nut",
        ).make_cutout()

        bridge_probe = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(-0.3)
            .translate((0.0, 0.0, -10.7))
        )
        nut_cavity = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(-0.2)
            .translate((0.0, 0.0, -10.2))
        )
        shaft_below = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(-0.2)
            .translate((0.0, 0.0, -11.3))
        )

        self.assertLess(intersection_volume(cutout, bridge_probe), 0.001)
        self.assertGreater(intersection_volume(cutout, nut_cavity), 0.5)
        self.assertGreater(intersection_volume(cutout, shaft_below), 0.5)

    def test_builds_single_valid_cutout_with_positive_y_channel(self) -> None:
        cutout = SideLoadedCaptiveNutHole(
            shaft_diameter=3.2,
            shaft_depth=25.0,
            nut_width_across_flats=5.9,
            nut_depth=2.6,
            nut_drop_from_interface=8.0,
            channel_length=12.0,
        ).make_cutout()

        self.assertEqual(cutout.solids().size(), 1)
        shape = cutout.val()
        self.assertIsInstance(shape, cq.Shape)
        assert isinstance(shape, cq.Shape)
        self.assertTrue(shape.isValid())
        bounds = shape.BoundingBox()
        self.assertAlmostEqual(bounds.zmax, 0.0, places=6)
        self.assertAlmostEqual(bounds.zmin, -25.0, places=6)
        # The insertion slot and the rotated hex are exactly the configured
        # across-flats width in local X. Across-corners is used only to feed
        # CadQuery's polygon constructor and to validate forward reach.
        self.assertAlmostEqual(bounds.xlen, 5.9, places=6)
        self.assertGreaterEqual(bounds.ymax, 12.0)

    def test_caller_can_rotate_channel_to_opposite_direction(self) -> None:
        positive = SideLoadedCaptiveNutHole(
            shaft_diameter=3.2,
            shaft_depth=25.0,
            nut_width_across_flats=5.9,
            nut_depth=2.6,
            nut_drop_from_interface=8.0,
            channel_length=12.0,
        ).make_cutout()
        negative = positive.rotate((0, 0, 0), (0, 0, 1), 180)

        positive_shape = positive.val()
        negative_shape = negative.val()
        self.assertIsInstance(positive_shape, cq.Shape)
        self.assertIsInstance(negative_shape, cq.Shape)
        assert isinstance(positive_shape, cq.Shape)
        assert isinstance(negative_shape, cq.Shape)
        positive_bounds = positive_shape.BoundingBox()
        negative_bounds = negative_shape.BoundingBox()
        self.assertAlmostEqual(positive_bounds.ymax, -negative_bounds.ymin)
        self.assertAlmostEqual(positive_bounds.ymin, -negative_bounds.ymax)

    def test_rejects_non_positive_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "shaft diameter"):
            SideLoadedCaptiveNutHole(
                shaft_diameter=0.0,
                shaft_depth=25.0,
                nut_width_across_flats=5.9,
                nut_depth=2.6,
                nut_drop_from_interface=8.0,
                channel_length=12.0,
            )

    def test_rejects_bridge_that_consumes_adjacent_shaft(self) -> None:
        with self.assertRaisesRegex(ValueError, "entry-side shaft"):
            SideLoadedCaptiveNutHole(
                shaft_diameter=3.2,
                shaft_depth=25.0,
                nut_width_across_flats=5.9,
                nut_depth=2.6,
                nut_drop_from_interface=0.5,
                channel_length=12.0,
                bridge_thickness=0.5,
                bridge_side="above_nut",
            )
        with self.assertRaisesRegex(ValueError, "end-side shaft"):
            SideLoadedCaptiveNutHole(
                shaft_diameter=3.2,
                shaft_depth=10.6,
                nut_width_across_flats=5.9,
                nut_depth=2.6,
                nut_drop_from_interface=8.0,
                channel_length=12.0,
                bridge_thickness=0.5,
                bridge_side="above_nut",
            )
        with self.assertRaisesRegex(ValueError, "end-side shaft"):
            SideLoadedCaptiveNutHole(
                shaft_diameter=3.2,
                shaft_depth=11.0,
                nut_width_across_flats=5.9,
                nut_depth=2.6,
                nut_drop_from_interface=8.0,
                channel_length=12.0,
                bridge_thickness=0.5,
                bridge_side="below_nut",
            )

    def test_rejects_invalid_bridge_options(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            SideLoadedCaptiveNutHole(
                shaft_diameter=3.2,
                shaft_depth=25.0,
                nut_width_across_flats=5.9,
                nut_depth=2.6,
                nut_drop_from_interface=8.0,
                channel_length=12.0,
                bridge_thickness=-0.1,
            )
        with self.assertRaisesRegex(ValueError, "bridge side"):
            SideLoadedCaptiveNutHole(
                shaft_diameter=3.2,
                shaft_depth=25.0,
                nut_width_across_flats=5.9,
                nut_depth=2.6,
                nut_drop_from_interface=8.0,
                channel_length=12.0,
                bridge_thickness=0.5,
                bridge_side="sideways",  # type: ignore[arg-type]
            )

    def test_channel_must_reach_past_hex_corner(self) -> None:
        with self.assertRaisesRegex(ValueError, "reach beyond the nut pocket"):
            SideLoadedCaptiveNutHole(
                shaft_diameter=3.2,
                shaft_depth=25.0,
                nut_width_across_flats=5.9,
                nut_depth=2.6,
                nut_drop_from_interface=8.0,
                channel_length=5.9 / 2,
            )


if __name__ == "__main__":
    unittest.main()
