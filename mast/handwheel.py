import cadquery as cq

class HandWheel:
    """A handwheel to attach to the top of the leadscrew."""

    wheel_height = 10.0
    wheel_dia = 60.0
    attachment_dia = 30.0
    attachment_height = 10.0
    axle_dia = 8.0
    screw_dia = 3.2
    nut_face_to_face = 5.6  # 5.32-5.5 nominal, 0.1 mm tolerance
    nut_thickness = 2.5  # 2.15-2.4 nominal

    def make(self):
        """
            Make the handwheel, centered on origin.
            Uses a captive nut to attach to leadscrew.
        """

        hw = (
            cq.Workplane("XY")
            .cylinder(self.attachment_height, self.attachment_dia / 2, centered=(True, True, False))
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
            .fillet(self.wheel_dia * 0.2)  # Just right, for this 8-lobed shape.
            #.cylinder(self.wheel_height, self.wheel_dia / 2, centered=(True, True, False))
            .faces(">Z")
            .workplane()
            .hole(self.axle_dia)
        )

        hw = hw.cut(
                    # Workplane facing outward from middle.
                    cq.Workplane("bottom", origin=(0, 0, self.attachment_height / 2))
                    .circle(self.screw_dia / 2)
                    .extrude(self.attachment_dia)
                    )

        hw = hw.cut(
                    cq.Workplane("bottom", origin=(0, -(self.axle_dia / 2 + 3.0), self.attachment_height / 2))
                    .polygon(6, self.nut_face_to_face, circumscribed=True)
                    .extrude(self.nut_thickness)
        )

        hw = hw.cut(
                    cq.Workplane("bottom", origin=(0, -(self.axle_dia / 2 + 3.0), self.attachment_height / 2))
                    .box(self.nut_face_to_face, self.attachment_height, self.nut_thickness, centered=(True, False, False))
                    .translate((0, 0, -self.attachment_height))
        )

        return hw