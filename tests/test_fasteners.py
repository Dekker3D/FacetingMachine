from __future__ import annotations

import unittest

import bought_bits as bb


class MetricFastenerDimensionTests(unittest.TestCase):
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
