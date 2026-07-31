from __future__ import annotations

import unittest

import cadquery as cq
from quill.quill_assembly import QuillAssemblyStandardMk1, QuillBody


def intersection_volume(shape: cq.Workplane, probe: cq.Workplane) -> float:
    result = shape.intersect(probe).val()
    assert isinstance(result, cq.Shape)
    return result.Volume()


class QuillCaptiveNutBridgeTests(unittest.TestCase):
    def test_body_has_half_mm_bridge_above_each_top_loaded_nut(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        body = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, QuillBody)
        )
        body_object = body.get_object()
        self.assertIsInstance(body_object, cq.Workplane)
        assert isinstance(body_object, cq.Workplane)

        block = body.main_block
        positions = (
            *block.bearing_holder_screw_positions(),
            *block.cheater_top_screw_positions(),
        )
        for x, y in positions:
            with self.subTest(x=x, y=y):
                is_holder = (x, y) in block.bearing_holder_screw_positions()
                interface_z = (
                    block.split_height - block.holder_split_gap / 2
                    if is_holder
                    else block.split_height
                )
                nut_top_z = interface_z - block.removable_top_nut_drop
                global_x = body.block_x + x
                bridge_probe = (
                    cq.Workplane("XY")
                    .center(global_x, y)
                    .circle(1.0)
                    .extrude(0.3)
                    .translate((0.0, 0.0, nut_top_z + 0.1))
                )
                shaft_probe = (
                    cq.Workplane("XY")
                    .center(global_x, y)
                    .circle(1.0)
                    .extrude(0.2)
                    .translate((0.0, 0.0, nut_top_z + 0.7))
                )
                nut_probe = (
                    cq.Workplane("XY")
                    .center(global_x, y)
                    .circle(1.0)
                    .extrude(0.2)
                    .translate((0.0, 0.0, nut_top_z - 0.3))
                )

                self.assertGreater(
                    intersection_volume(body_object, bridge_probe),
                    0.5,
                )
                self.assertLess(
                    intersection_volume(body_object, shaft_probe),
                    0.001,
                )
                self.assertLess(
                    intersection_volume(body_object, nut_probe),
                    0.001,
                )


if __name__ == "__main__":
    unittest.main()
