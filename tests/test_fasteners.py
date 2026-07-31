from __future__ import annotations

import unittest

import cadquery as cq
import bought_bits as bb


class MetricFastenerDimensionTests(unittest.TestCase):
    def test_m3_set_screw_is_headless(self) -> None:
        screw = bb.SetScrew.get(size=3.0, length=8.0)

        self.assertEqual(screw.name, "M3×8mm Set Screw")
        self.assertEqual(screw.diameter(), 3.0)
        self.assertEqual(screw.shaft_length(), 8.0)
        screw_shape = screw.get_object().val()
        self.assertIsInstance(screw_shape, cq.Shape)
        assert isinstance(screw_shape, cq.Shape)
        bounds = screw_shape.BoundingBox()
        self.assertAlmostEqual(bounds.xlen, 3.0)
        self.assertAlmostEqual(bounds.ylen, 3.0)
        self.assertAlmostEqual(bounds.zlen, 8.0)

        uncut_envelope = cq.Workplane("XY").cylinder(
            screw.shaft_length(),
            screw.diameter() / 2,
            centered=(True, True, False),
        )
        removed = uncut_envelope.cut(screw.get_object())
        removed_shape = removed.val()
        self.assertIsInstance(removed_shape, cq.Shape)
        assert isinstance(removed_shape, cq.Shape)
        self.assertGreater(removed_shape.Volume(), 0.1)

    def test_pan_head_has_visible_straight_slot(self) -> None:
        screw = bb.Bolt.get(size=3.0, length=10.0, head="pan")
        uncut = (
            cq.Workplane("XY")
            .cylinder(
                screw.head_height(),
                screw.head_diameter() / 2,
                centered=(True, True, False),
            )
            .faces("<Z")
            .workplane()
            .cylinder(
                screw.shaft_length(),
                screw.diameter() / 2,
                centered=(True, True, False),
            )
        )
        removed_shape = uncut.cut(screw.get_object()).val()
        self.assertIsInstance(removed_shape, cq.Shape)
        assert isinstance(removed_shape, cq.Shape)
        self.assertGreater(removed_shape.Volume(), 0.1)

    def test_countersunk_head_has_visible_phillips_recess(self) -> None:
        screw = bb.Bolt.get(size=3.0, length=10.0, head="countersunk")
        head = (
            cq.Workplane("XY")
            .circle(screw.diameter() / 2)
            .workplane(offset=screw.head_height())
            .circle(screw.head_diameter() / 2)
            .loft()
        )
        uncut = head.faces("<Z").workplane().cylinder(
            screw.shaft_length(),
            screw.diameter() / 2,
            centered=(True, True, False),
        )
        removed_shape = uncut.cut(screw.get_object()).val()
        self.assertIsInstance(removed_shape, cq.Shape)
        assert isinstance(removed_shape, cq.Shape)
        self.assertGreater(removed_shape.Volume(), 0.1)
        self.assertLess(removed_shape.Volume(), 5.0)
        self.assertGreater(
            removed_shape.BoundingBox().zmin,
            screw.head_height() / 3,
        )

    def test_wood_screw_heads_have_matching_drive_recesses(self) -> None:
        for head in ("pan", "countersunk"):
            with self.subTest(head=head):
                screw = bb.WoodScrew.get(size=3.0, length=12.0, head=head)
                if head == "pan":
                    uncut_head = cq.Workplane("XY").cylinder(
                        screw.head_height(),
                        screw.head_diameter() / 2,
                        centered=(True, True, False),
                    )
                else:
                    uncut_head = (
                        cq.Workplane("XY")
                        .circle(screw.head_diameter() / 2)
                        .workplane(offset=screw.head_height())
                        .circle(screw.diameter() / 2)
                        .loft()
                    )
                shaft = (
                    cq.Workplane("XY")
                    .cylinder(
                        screw.shaft_length(),
                        screw.diameter() / 2,
                        centered=(True, True, False),
                    )
                    .translate((0.0, 0.0, screw.head_height()))
                )
                removed_shape = uncut_head.union(shaft).cut(
                    screw.get_object()
                ).val()
                self.assertIsInstance(removed_shape, cq.Shape)
                assert isinstance(removed_shape, cq.Shape)
                self.assertGreater(removed_shape.Volume(), 0.1)

    def test_m2_5_hex_fasteners_use_exact_standard_dimensions(self) -> None:
        bolt = bb.Bolt(size=2.5, length=10.0)
        nut = bb.Nut(size=2.5)
        washer = bb.Washer(size=2.5)
        nyloc = bb.NylocNut(size=2.5)

        self.assertEqual(bolt.name, "M2.5×10mm hex Bolt")
        self.assertAlmostEqual(bolt.head_diameter(), 5.0)
        self.assertAlmostEqual(bolt.head_height(), 2.5)
        self.assertEqual(nut.name, "M2.5 Nut")
        self.assertAlmostEqual(nut.width_across_flats(), 5.0)
        self.assertAlmostEqual(nut.height(), 2.0)
        self.assertEqual(washer.name, "M2.5 Washer")
        self.assertAlmostEqual(washer.outer_diameter(), 6.0)
        self.assertAlmostEqual(washer.height(), 0.5)
        self.assertEqual(nyloc.name, "M2.5 Nyloc Nut")
        self.assertAlmostEqual(nyloc.width_across_flats(), 5.0)

    def test_m2_standard_dimensions_are_supported(self) -> None:
        bolt = bb.Bolt(size=2.0, length=8.0)
        nut = bb.Nut(size=2.0)
        washer = bb.Washer(size=2.0)

        self.assertAlmostEqual(bolt.head_diameter(), 4.0)
        self.assertAlmostEqual(nut.width_across_flats(), 4.0)
        self.assertAlmostEqual(washer.outer_diameter(), 5.0)

    def test_fractional_bolt_length_is_preserved_in_name(self) -> None:
        bolt = bb.Bolt(size=2.5, length=10.5)

        self.assertEqual(bolt.name, "M2.5×10.5mm hex Bolt")

    def test_unsupported_hex_bolt_size_is_rejected_instead_of_truncated(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported ISO metric fastener size"):
            bb.Bolt(size=3.9, length=10.0)

    def test_unsupported_nut_size_is_rejected_instead_of_truncated(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported ISO metric fastener size"):
            bb.Nut(size=3.9)

    def test_unsupported_nyloc_size_is_rejected_instead_of_truncated(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported ISO metric fastener size"):
            bb.NylocNut(size=3.9)

    def test_unsupported_washer_size_is_rejected_instead_of_truncated(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported ISO metric fastener size"):
            bb.Washer(size=3.9)


if __name__ == "__main__":
    unittest.main()
