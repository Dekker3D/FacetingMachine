from __future__ import annotations
import cadquery as cq


class HandWheel:
    """A handwheel to attach to the top of the leadscrew."""

    wheel_height: float = 10.0
    wheel_dia: float = 60.0
    attachment_dia: float = 30.0
    attachment_height: float = 10.0
    axle_dia: float = 8.0
    screw_dia: float = 3.2
    nut_face_to_face: float = 5.6
    nut_thickness: float = 2.5

    def make(self) -> cq.Workplane:
        """Make the handwheel, centered on origin. Uses captive nut."""
        hw = (
            cq.Workplane("XY")
            .cylinder(
                self.attachment_height,
                self.attachment_dia / 2,
                centered=(True, True, False),
            )
            .faces(">Z")
            .workplane()
            .polygon(4, self.wheel_dia, circumscribed=True)
            .extrude(self.wheel_height)
            .rotate((0, 0, 0), (0, 0, 1), 45)
            .faces(">Z")
            .workplane(offset=-self.wheel_height)
            .polygon(4, self.wheel_dia, circumscribed=True)
            .extrude(self.wheel_height)
            .edges("|Z")
            .fillet(self.wheel_dia * 0.2)
            .faces(">Z")
            .workplane()
            .hole(self.axle_dia)
        )

        hw = hw.cut(
            cq.Workplane(
                "bottom", origin=(0, 0, self.attachment_height / 2)
            )
            .circle(self.screw_dia / 2)
            .extrude(self.attachment_dia)
        )

        hw = hw.cut(
            cq.Workplane(
                "bottom",
                origin=(0, -(self.axle_dia / 2 + 3.0),
                        self.attachment_height / 2),
            )
            .polygon(6, self.nut_face_to_face, circumscribed=True)
            .extrude(self.nut_thickness)
        )

        hw = hw.cut(
            cq.Workplane(
                "bottom",
                origin=(0, -(self.axle_dia / 2 + 3.0),
                        self.attachment_height / 2),
            )
            .box(
                self.nut_face_to_face,
                self.attachment_height,
                self.nut_thickness,
                centered=(True, False, False),
            )
            .translate((0, 0, -self.attachment_height))
        )

        return hw
