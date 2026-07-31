from __future__ import annotations

import unittest

import cadquery as cq
from quill.quill_assembly import QuillAssemblyStandardMk1, QuillBody


def shape_volume(workplane: cq.Workplane) -> float:
    shape = workplane.val()
    assert isinstance(shape, cq.Shape)
    return shape.Volume()


class AngleIndicatorMountTests(unittest.TestCase):
    def test_body_pilot_holes_extend_eight_mm_from_indicator_interface(self) -> None:
        quill = QuillAssemblyStandardMk1(explode=False)
        body = next(
            part
            for part, _quantity in quill.get_BOM().items()
            if isinstance(part, QuillBody)
        )
        body_object = body.get_object()
        self.assertIsInstance(body_object, cq.Workplane)
        assert isinstance(body_object, cq.Workplane)

        interface_y = (
            -quill.joint_shoulder_gap / 2
            + quill.joint_angle_indicator_thickness
        )
        hinge_z = quill.base_plate_thickness + quill.joint_hinge_height

        for z in (hinge_z - 6.0, hinge_z + 6.0):
            with self.subTest(z=z):
                # Stay 0.1 mm inside both ends to avoid coincident-face noise.
                expected_void = (
                    cq.Workplane("XZ")
                    .center(-6.0, z)
                    .circle(1.0)
                    .extrude(-7.8)
                    .translate((0.0, interface_y + 0.1, 0.0))
                )
                self.assertLess(
                    shape_volume(body_object.intersect(expected_void)),
                    0.001,
                )

                material_beyond_pilot = (
                    cq.Workplane("XZ")
                    .center(-6.0, z)
                    .circle(0.8)
                    .extrude(-0.8)
                    .translate((0.0, interface_y + 8.1, 0.0))
                )
                self.assertGreater(
                    shape_volume(body_object.intersect(material_beyond_pilot)),
                    1.0,
                )


if __name__ == "__main__":
    unittest.main()
