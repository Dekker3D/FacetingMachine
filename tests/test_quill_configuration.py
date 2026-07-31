from __future__ import annotations

import math
import unittest

import cadquery as cq
import bom_part_data as bpd
import bought_bits as bb
from quill.quill_assembly import QuillAssemblyStandardMk1


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
    def test_default_configuration_builds_valid_printed_parts(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
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

    def test_rejects_spring_without_preload(self) -> None:
        class ShortSpringQuill(QuillAssemblyStandardMk1):
            cheater_spring_free_length = 8.0

        with self.assertRaisesRegex(ValueError, "provide preload"):
            ShortSpringQuill(explode=False)

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
