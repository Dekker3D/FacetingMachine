from __future__ import annotations

import cadquery as cq
from cadquery import Location

import bom_part_data as bpd
import quill.quill_abstract as quill_abstract
import quill_holder.quill_holder_abstract as quill_holder_abstract


class QuillHolderAssembly(quill_holder_abstract.QuillHolderAssemblyBase):
    """AliExpress-style quill holder with a swappable replacement quill."""

    # Vertical swing joint connecting the holder to the mast carriage.
    swing_dia: float = 15.0
    swing_height: float = 50.0
    swing_joint_thickness: float = 5.0

    # Measured pitch interface. The holder has open slots, not bearings.
    pitch_joint_od: float = 38.0
    shoulder_clearance: float = 48.0
    user_slot_dia: float = 7.0
    user_cheek_thickness: float = 8.0
    away_slot_dia: float = 6.0
    # One millimetre shorter than the 5 mm nub. The exposed end joins the
    # angle-indicator tab without pinching that tab against the holder.
    away_cheek_thickness: float = 4.0
    slot_angle: float = 45.0
    web_overlap: float = 4.0

    def __init__(
        self,
        quill: quill_abstract.QuillAssemblyBase | None = None,
    ) -> None:
        super().__init__(name="Quill Holder Assembly")
        self._current_group = self.name
        holder = QuillHolder.create(
            swing_dia=self.swing_dia,
            swing_height=self.swing_height,
            swing_joint_thickness=self.swing_joint_thickness,
            pitch_joint_od=self.pitch_joint_od,
            shoulder_clearance=self.shoulder_clearance,
            user_slot_dia=self.user_slot_dia,
            user_cheek_thickness=self.user_cheek_thickness,
            away_slot_dia=self.away_slot_dia,
            away_cheek_thickness=self.away_cheek_thickness,
            slot_angle=self.slot_angle,
            web_overlap=self.web_overlap,
        )

        pitch_x = holder.pitch_joint_x_offset()
        pitch_z = holder.pitch_joint_z_offset()
        self._add(holder, loc=Location(0, 0, 0), name="quill_holder")
        if quill is not None:
            self._add(
                quill,
                loc=Location(pitch_x, 0, pitch_z),
                name="quill_assembly",
            )


class QuillHolder(bpd.PrintedPart):
    """Holder matching the original AliExpress machine's open pitch joint.

    Each side cheek has a differently sized diagonal U-slot. The replacement
    quill drops into those slots on its unequal hinge nubs; no pitch bearings
    are present in this design.
    """

    @classmethod
    def create(
        cls,
        swing_dia: float,
        swing_height: float,
        swing_joint_thickness: float,
        pitch_joint_od: float,
        shoulder_clearance: float,
        user_slot_dia: float,
        user_cheek_thickness: float,
        away_slot_dia: float,
        away_cheek_thickness: float,
        slot_angle: float,
        web_overlap: float,
    ) -> QuillHolder:
        return cls.get(
            swing_dia=swing_dia,
            swing_height=swing_height,
            swing_joint_thickness=swing_joint_thickness,
            pitch_joint_od=pitch_joint_od,
            shoulder_clearance=shoulder_clearance,
            user_slot_dia=user_slot_dia,
            user_cheek_thickness=user_cheek_thickness,
            away_slot_dia=away_slot_dia,
            away_cheek_thickness=away_cheek_thickness,
            slot_angle=slot_angle,
            web_overlap=web_overlap,
        )

    def __init__(
        self,
        swing_dia: float,
        swing_height: float,
        swing_joint_thickness: float,
        pitch_joint_od: float,
        shoulder_clearance: float,
        user_slot_dia: float,
        user_cheek_thickness: float,
        away_slot_dia: float,
        away_cheek_thickness: float,
        slot_angle: float,
        web_overlap: float,
    ) -> None:
        self.swing_dia = swing_dia
        self.swing_height = swing_height
        self.swing_joint_thickness = swing_joint_thickness
        self.pitch_joint_od = pitch_joint_od
        self.shoulder_clearance = shoulder_clearance
        self.user_slot_dia = user_slot_dia
        self.user_cheek_thickness = user_cheek_thickness
        self.away_slot_dia = away_slot_dia
        self.away_cheek_thickness = away_cheek_thickness
        self.slot_angle = slot_angle
        self.web_overlap = web_overlap
        super().__init__(name="Quill Holder")

        holder = self._make_swing_tube().union(self._make_back_web())
        holder = holder.union(
            self._make_cheek(
                side=+1,
                thickness=self.user_cheek_thickness,
                slot_dia=self.user_slot_dia,
            )
        )
        holder = holder.union(
            self._make_cheek(
                side=-1,
                thickness=self.away_cheek_thickness,
                slot_dia=self.away_slot_dia,
            )
        )

        self._object = holder
        self._assembly.add(holder, name="body", color=cq.Color("green"))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.swing_dia,
            self.swing_height,
            self.swing_joint_thickness,
            self.pitch_joint_od,
            self.shoulder_clearance,
            self.user_slot_dia,
            self.user_cheek_thickness,
            self.away_slot_dia,
            self.away_cheek_thickness,
            self.slot_angle,
            self.web_overlap,
        )

    def swing_joint_od(self) -> float:
        return self.swing_dia + self.swing_joint_thickness * 2

    def pitch_joint_x_offset(self) -> float:
        return self.swing_joint_od() / 2 + self.pitch_joint_od / 2

    def pitch_joint_z_offset(self) -> float:
        return self.pitch_joint_od / 2

    def _make_swing_tube(self) -> cq.Workplane:
        outer = cq.Workplane("XY").cylinder(
            self.swing_height,
            self.swing_joint_od() / 2,
            centered=(True, True, False),
        )
        bore = cq.Workplane("XY").cylinder(
            self.swing_height,
            self.swing_dia / 2,
            centered=(True, True, False),
        )
        return outer.cut(bore)

    def _make_back_web(self) -> cq.Workplane:
        """Connect the swing tube to both cheeks behind the open slots."""
        swing_radius = self.swing_joint_od() / 2
        pitch_radius = self.pitch_joint_od / 2
        pitch_left_x = self.pitch_joint_x_offset() - pitch_radius
        web_end_x = pitch_left_x + self.web_overlap
        y_min = -self.shoulder_clearance / 2 - self.away_cheek_thickness
        y_max = self.shoulder_clearance / 2 + self.user_cheek_thickness
        return (
            cq.Workplane("XY")
            .box(
                web_end_x + swing_radius,
                y_max - y_min,
                self.pitch_joint_od,
                centered=(False, True, False),
            )
            .translate((-swing_radius, (y_min + y_max) / 2, 0))
        )

    def _make_cheek(
        self,
        side: int,
        thickness: float,
        slot_dia: float,
    ) -> cq.Workplane:
        pitch_x = self.pitch_joint_x_offset()
        pitch_z = self.pitch_joint_z_offset()
        inner_y = side * self.shoulder_clearance / 2
        # CadQuery's XZ workplane normal points toward -Y. Negating the
        # extrusion for the +Y/user side therefore makes both cheeks extend
        # outward from their respective inner faces.
        extrusion = -side * thickness
        cheek = (
            cq.Workplane("XZ")
            .circle(self.pitch_joint_od / 2)
            .extrude(extrusion)
            .translate((pitch_x, inner_y, pitch_z))
        )

        # Circular seat plus a diagonal channel opening toward +X/+Z.
        seat_start_y = side * (self.shoulder_clearance / 2 - 1)
        seat = (
            cq.Workplane("XZ")
            .circle(slot_dia / 2)
            .extrude(-side * (thickness + 2))
            .translate((pitch_x, seat_start_y, pitch_z))
        )
        channel_center_y = side * (
            self.shoulder_clearance / 2 + thickness / 2
        )
        channel = (
            cq.Workplane("XY")
            .box(
                slot_dia,
                thickness + 2,
                self.pitch_joint_od,
                centered=(True, True, False),
            )
            .rotate((0, 0, 0), (0, 1, 0), self.slot_angle)
            .translate((pitch_x, channel_center_y, pitch_z))
        )
        return cheek.cut(seat.union(channel))
