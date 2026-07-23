from __future__ import annotations
import cadquery as cq
import bom_part_data as bpd


class HandWheel(bpd.PrintedPart):
    """A handwheel to attach to the top of the leadscrew. Uses captive nut."""

    @classmethod
    def create(
        cls,
        wheel_height: float = 10.0,
        wheel_dia: float = 60.0,
        attachment_dia: float = 30.0,
        attachment_height: float = 10.0,
        axle_dia: float = 8.0,
        screw_dia: float = 3.2,
        nut_face_to_face: float = 5.6,
        nut_thickness: float = 2.5,
    ) -> HandWheel:
        return cls.get(
            wheel_height=wheel_height,
            wheel_dia=wheel_dia,
            attachment_dia=attachment_dia,
            attachment_height=attachment_height,
            axle_dia=axle_dia,
            screw_dia=screw_dia,
            nut_face_to_face=nut_face_to_face,
            nut_thickness=nut_thickness,
        )

    def __init__(
        self,
        wheel_height: float = 10.0,
        wheel_dia: float = 60.0,
        attachment_dia: float = 30.0,
        attachment_height: float = 10.0,
        axle_dia: float = 8.0,
        screw_dia: float = 3.2,
        nut_face_to_face: float = 5.6,
        nut_thickness: float = 2.5,
    ) -> None:
        self.wheel_height = wheel_height
        self.wheel_dia = wheel_dia
        self.attachment_dia = attachment_dia
        self.attachment_height = attachment_height
        self.axle_dia = axle_dia
        self.screw_dia = screw_dia
        self.nut_face_to_face = nut_face_to_face
        self.nut_thickness = nut_thickness
        super().__init__(name="Handwheel")
        # Build geometry once
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
            cq.Workplane("bottom", origin=(0, 0, self.attachment_height / 2))
            .circle(self.screw_dia / 2)
            .extrude(self.attachment_dia)
        )
        hw = hw.cut(
            cq.Workplane(
                "bottom",
                origin=(0, -(self.axle_dia / 2 + 3.0), self.attachment_height / 2),
            )
            .polygon(6, self.nut_face_to_face, circumscribed=True)
            .extrude(self.nut_thickness)
        )
        hw = hw.cut(
            cq.Workplane(
                "bottom",
                origin=(0, -(self.axle_dia / 2 + 3.0), self.attachment_height / 2),
            )
            .box(
                self.nut_face_to_face,
                self.attachment_height,
                self.nut_thickness,
                centered=(True, False, False),
            )
            .translate((0, 0, -self.attachment_height))
        )
        self._object = hw
        self._assembly.add(hw, name="body", color=cq.Color("green"))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.wheel_height, self.wheel_dia,
            self.attachment_dia, self.attachment_height,
            self.axle_dia, self.screw_dia,
            self.nut_face_to_face, self.nut_thickness,
        )
