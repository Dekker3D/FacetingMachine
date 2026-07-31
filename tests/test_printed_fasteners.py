from __future__ import annotations

import unittest

import cadquery as cq

from printed_fasteners import SideLoadedCaptiveNutHole


class SideLoadedCaptiveNutHoleTests(unittest.TestCase):
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
