from __future__ import annotations

import cadquery as cq

import bom_part_data as bpd
from quill.quill_joint_abstract import QuillJointBase


class QuillJointAli(bpd.PrintedPart, QuillJointBase):
    """AliExpress-holder-compatible hinge for the replacement quill.

    The measured ``shoulder_gap`` is the distance between the two outer
    shoulder faces.  The unequal nubs start at those faces and run along the
    pitch axis (+/-Y).  The base plate is printed flat and supports both the
    hinge and the quill main block.
    """

    @classmethod
    def create(
        cls,
        shoulder_dia: float,
        shoulder_gap: float,
        shoulder_thickness: float,
        user_nub_dia: float,
        user_nub_length: float,
        away_nub_dia: float,
        away_nub_length: float,
        hinge_height: float,
        angle_indicator_height: float,
        angle_indicator_thickness: float,
        base_plate_thickness: float,
        base_plate_x: float,
        base_plate_y: float,
    ) -> QuillJointAli:
        return cls.get(
            shoulder_dia=shoulder_dia,
            shoulder_gap=shoulder_gap,
            shoulder_thickness=shoulder_thickness,
            user_nub_dia=user_nub_dia,
            user_nub_length=user_nub_length,
            away_nub_dia=away_nub_dia,
            away_nub_length=away_nub_length,
            hinge_height=hinge_height,
            angle_indicator_height=angle_indicator_height,
            angle_indicator_thickness=angle_indicator_thickness,
            base_plate_thickness=base_plate_thickness,
            base_plate_x=base_plate_x,
            base_plate_y=base_plate_y,
        )

    def __init__(
        self,
        shoulder_dia: float,
        shoulder_gap: float,
        shoulder_thickness: float,
        user_nub_dia: float,
        user_nub_length: float,
        away_nub_dia: float,
        away_nub_length: float,
        hinge_height: float,
        angle_indicator_height: float,
        angle_indicator_thickness: float,
        base_plate_thickness: float,
        base_plate_x: float,
        base_plate_y: float,
    ) -> None:
        self.shoulder_dia = shoulder_dia
        self.shoulder_gap = shoulder_gap
        self.shoulder_thickness = shoulder_thickness
        self.user_nub_dia = user_nub_dia
        self.user_nub_length = user_nub_length
        self.away_nub_dia = away_nub_dia
        self.away_nub_length = away_nub_length
        self.hinge_height = hinge_height
        self.angle_indicator_height = angle_indicator_height
        self.angle_indicator_thickness = angle_indicator_thickness
        self.base_plate_thickness = base_plate_thickness
        self.base_plate_x = base_plate_x
        self.base_plate_y = base_plate_y
        super().__init__(name="Quill Joint")

        obj = (
            self._make_base_plate()
            .union(self._make_support_block())
            .union(self._make_hinge_barrel())
            .union(self._make_shoulder(+1))
            .union(self._make_shoulder(-1))
            .union(self._make_user_nub())
            .union(self._make_away_nub())
            .union(self._make_angle_indicator())
        )
        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("blue"))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.shoulder_dia,
            self.shoulder_gap,
            self.shoulder_thickness,
            self.user_nub_dia,
            self.user_nub_length,
            self.away_nub_dia,
            self.away_nub_length,
            self.hinge_height,
            self.angle_indicator_height,
            self.angle_indicator_thickness,
            self.base_plate_thickness,
            self.base_plate_x,
            self.base_plate_y,
        )

    def _hinge_z(self) -> float:
        return self.base_plate_thickness + self.hinge_height

    def _shoulder_center_y(self, side: int) -> float:
        return side * (self.shoulder_gap - self.shoulder_thickness) / 2

    def _make_base_plate(self) -> cq.Workplane:
        x_center = self.base_plate_x * 0.3
        return (
            cq.Workplane("XY")
            .box(
                self.base_plate_x,
                self.base_plate_y,
                self.base_plate_thickness,
                centered=(True, True, False),
            )
            .translate((x_center, 0, 0))
        )

    def _make_support_block(self) -> cq.Workplane:
        """Solid support spanning the full width beneath the hinge barrel."""
        support_x = self.shoulder_dia + 4.0
        return (
            cq.Workplane("XY")
            .box(
                support_x,
                self.shoulder_gap,
                self.hinge_height,
                centered=(True, True, False),
            )
            .translate((0, 0, self.base_plate_thickness))
        )

    def _make_shoulder(self, side: int) -> cq.Workplane:
        return (
            cq.Workplane("XZ")
            .cylinder(
                self.shoulder_thickness,
                self.shoulder_dia / 2,
                centered=(True, True, True),
            )
            .translate((0, self._shoulder_center_y(side), self._hinge_z()))
        )

    def _make_hinge_barrel(self) -> cq.Workplane:
        """Solid core between the two outer shoulder faces."""
        return (
            cq.Workplane("XZ")
            .circle(self.shoulder_dia / 2)
            .extrude(self.shoulder_gap)
            .translate((0, self.shoulder_gap / 2, self._hinge_z()))
        )

    def _make_user_nub(self) -> cq.Workplane:
        # XZ's positive normal points toward -Y, so a negative extrusion
        # sends this +Y/user-side nub outward from the shoulder face.
        return (
            cq.Workplane("XZ")
            .circle(self.user_nub_dia / 2)
            .extrude(-self.user_nub_length)
            .translate((0, self.shoulder_gap / 2, self._hinge_z()))
        )

    def _make_away_nub(self) -> cq.Workplane:
        # Positive XZ extrusion points toward -Y, outward on the away side.
        return (
            cq.Workplane("XZ")
            .circle(self.away_nub_dia / 2)
            .extrude(self.away_nub_length)
            .translate((0, -self.shoulder_gap / 2, self._hinge_z()))
        )

    def _make_angle_indicator(self) -> cq.Workplane:
        """Tapered tab inside the joint, above the away-side support."""
        # Start at the nub centreline so the tab overlaps the upper half of
        # the nub instead of becoming a separate, merely face-touching solid.
        base_z = self._hinge_z()
        tip_z = self._hinge_z() + self.angle_indicator_height
        mid_z = base_z + (tip_z - base_z) * 0.35
        base_half_width = self.shoulder_dia / 2
        mid_half_width = self.shoulder_dia / 4
        tip_half_width = 1.0
        away_inner_y = -self.shoulder_gap / 2 + self.shoulder_thickness

        profile = (
            cq.Workplane("XZ")
            .polyline(
                [
                    (-base_half_width, base_z),
                    (base_half_width, base_z),
                    (mid_half_width, mid_z),
                    (tip_half_width, tip_z),
                    (-tip_half_width, tip_z),
                    (-mid_half_width, mid_z),
                ]
            )
            .close()
            # Negative XZ extrusion points toward +Y, into the joint.
            .extrude(-self.angle_indicator_thickness)
            .translate((0, away_inner_y, 0))
        )
        return profile
