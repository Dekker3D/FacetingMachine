from __future__ import annotations
import cadquery as cq
import bom_part_data as bpd
from quill.quill_joint_abstract import QuillJointBase


class QuillJointAli(bpd.PrintedPart, QuillJointBase):
    """Printed part: the hinge structure that fits into the quill holder's
    diagonal U-slot. Includes both nubs, shoulders, angle indicator, and
    a base plate that connects to the main quill block.

    Printed flat on the bed — the base plate at Z=0, joint rising upward.
    Nubs and shoulders are along the Y axis (hinge = pitch axis)."""

    @classmethod
    def create(
        cls,
        shoulder_dia: float,
        shoulder_gap: float,
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
        # Build geometry once
        obj = (
            self._make_base_plate()
            .union(self._make_pillar(+self._half_gap()))
            .union(self._make_pillar(-self._half_gap()))
            .union(self._make_shoulder(+self._half_gap()))
            .union(self._make_shoulder(-self._half_gap()))
            .union(self._make_user_nub())
            .union(self._make_away_nub())
            .union(self._make_angle_indicator())
        )
        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("blue"))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.shoulder_dia, self.shoulder_gap,
            self.user_nub_dia, self.user_nub_length,
            self.away_nub_dia, self.away_nub_length,
            self.hinge_height, self.angle_indicator_height,
            self.angle_indicator_thickness,
            self.base_plate_thickness, self.base_plate_x, self.base_plate_y,
        )

    # ── derived positions ──────────────────────────────────────────

    def _half_gap(self) -> float:
        return self.shoulder_gap / 2

    def _hinge_z(self) -> float:
        """Z of the hinge centerline above the bed."""
        return self.base_plate_thickness + self.hinge_height

    # ── geometry helpers ────────────────────────────────────────────

    def _make_base_plate(self) -> cq.Workplane:
        """Base plate: extends in +X to also support the main block."""
        # Offset so more plate is in +X (where the block sits)
        x_center = self.base_plate_x * 0.3  # shift toward +X
        return (
            cq.Workplane("XY")
            .box(self.base_plate_x, self.base_plate_y,
                 self.base_plate_thickness,
                 centered=(True, True, False))
            .translate((x_center, 0, 0))
        )

    def _make_pillar(self, y_center: float) -> cq.Workplane:
        """Rectangular support from base plate up to shoulder height."""
        pillar_w = self.shoulder_dia + 4
        return (
            cq.Workplane("XY")
            .box(pillar_w, pillar_w, self.hinge_height,
                 centered=(True, True, False))
            .translate((0, y_center, self.base_plate_thickness))
        )

    def _make_shoulder(self, y_center: float) -> cq.Workplane:
        """Cylindrical shoulder — axis along Y (hinge = pitch axis)."""
        # XZ workplane → cylinder extrudes along Y
        return (
            cq.Workplane("XZ")
            .cylinder(self.shoulder_dia, self.shoulder_dia / 2,
                      centered=(True, True, True))
            .translate((0, y_center, self._hinge_z()))
        )

    def _make_user_nub(self) -> cq.Workplane:
        """Nub facing +Y (toward user). Extends from shoulder outward."""
        y_base = self._half_gap() + self.shoulder_dia / 2
        # XZ workplane → extrude along Y from y_base outward
        return (
            cq.Workplane("XZ")
            .circle(self.user_nub_dia / 2)
            .extrude(self.user_nub_length)
            .translate((0, y_base, self._hinge_z()))
        )

    def _make_away_nub(self) -> cq.Workplane:
        """Nub facing -Y (away from user). Extends from shoulder outward."""
        y_base = -(self._half_gap() + self.shoulder_dia / 2)
        # Extrude in -Y direction
        return (
            cq.Workplane("XZ")
            .workplane(offset=-self.away_nub_length)
            .circle(self.away_nub_dia / 2)
            .extrude(self.away_nub_length)
            .translate((0, y_base - self.away_nub_length, self._hinge_z()))
        )

    def _make_angle_indicator(self) -> cq.Workplane:
        """Thin tab above the -Y nub, pointing up (+Z)."""
        y_center = -(self._half_gap() + self.shoulder_dia / 2)
        base_z = self._hinge_z() + self.shoulder_dia / 2
        tip_z = base_z + self.angle_indicator_height
        thickness = self.angle_indicator_thickness

        # Profile in the YZ plane (vertical tab)
        base_w = self.shoulder_dia
        tip_w = 2.0
        mid_z = base_z + self.angle_indicator_height * 0.3
        mid_w = base_w * 0.5

        pts = [
            (0, base_z),
            (base_w / 2, base_z),
            (mid_w / 2, mid_z),
            (tip_w / 2, tip_z),
            (-tip_w / 2, tip_z),
            (-mid_w / 2, mid_z),
        ]

        profile = (
            cq.Workplane("YZ")
            .polyline(pts)
            .close()
            .extrude(thickness)
            .translate((y_center - thickness / 2, 0, 0))
        )

        return profile
