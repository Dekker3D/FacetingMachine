from __future__ import annotations
import cadquery as cq
from cadquery import Location, Vector
import bom_part_data as bpd
import bought_bits as bb
import quill_holder.quill_holder_abstract as quill_holder_abstract
import quill.quill_abstract as quill_abstract


class QuillHolderAssembly(quill_holder_abstract.QuillHolderAssemblyBase):
    """Quill holder + swappable quill. Swing joint dimensions owned here."""

    # Swing joint dimensions
    swing_dia: float = 15.0
    swing_height: float = 50.0
    swing_joint_thickness: float = 5.0

    # Pitch joint dimensions
    pitch_joint_thickness: float = 8.0
    quill_width: float = 50.0

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
            pitch_joint_thickness=self.pitch_joint_thickness,
            quill_width=self.quill_width,
            bearing_od=bb.Bearing608ZZ.OD,
            bearing_width=bb.Bearing608ZZ.WIDTH,
        )
        qt_X = holder.pitch_joint_X_offset()
        qt_Z = holder.pitch_joint_Z_offset()

        self._add(holder, loc=Location(0, 0, 0), color="orange",
                  name="quill_holder")
        if quill is not None:
            self._add(quill, loc=Location(qt_X, 0, qt_Z),
                      name="quill_assembly")

        self._bom.add(bb.Bearing608ZZ.get(name="608ZZ Bearing"), 2)  # type: ignore[union-attr]


class QuillHolder(bpd.PrintedPart):
    """
    Printed part: holds the quill and allows it to pitch up/down.
    The holder body swings left/right on the quill carriage.
    """

    @classmethod
    def create(
        cls,
        swing_dia: float,
        swing_height: float,
        swing_joint_thickness: float,
        pitch_joint_thickness: float,
        quill_width: float,
        bearing_od: float,
        bearing_width: float,
    ) -> QuillHolder:
        return cls.get(
            swing_dia=swing_dia,
            swing_height=swing_height,
            swing_joint_thickness=swing_joint_thickness,
            pitch_joint_thickness=pitch_joint_thickness,
            quill_width=quill_width,
            bearing_od=bearing_od,
            bearing_width=bearing_width,
        )

    def __init__(
        self,
        swing_dia: float,
        swing_height: float,
        swing_joint_thickness: float,
        pitch_joint_thickness: float,
        quill_width: float,
        bearing_od: float,
        bearing_width: float,
    ) -> None:
        self.swing_dia = swing_dia
        self.swing_height = swing_height
        self.swing_joint_thickness = swing_joint_thickness
        self.pitch_joint_thickness = pitch_joint_thickness
        self.quill_width = quill_width
        self.bearing_od = bearing_od
        self.bearing_width = bearing_width
        super().__init__(name="Quill Holder")
        # Build geometry once
        holder = cq.Workplane("XY").cylinder(
            self.swing_height,
            self.swing_joint_OD() / 2,
            centered=(True, True, False),
        )
        holder = holder.cut(
            cq.Workplane("XY").cylinder(
                self.swing_height,
                self.swing_dia / 2,
                centered=(True, True, False),
            )
        )
        # Pitch joint bearing holders
        holder = holder.union(
            cq.Workplane("XZ")
            .move(self.pitch_joint_X_offset(), self.pitch_joint_Z_offset())
            .cylinder(
                self.quill_width + self.bearing_width * 2,
                self.pitch_joint_OD() / 2,
            )
            .faces(">Z")
            .hole(self.bearing_od)
        )
        holder = holder.cut(
            cq.Workplane("XZ")
            .move(self.pitch_joint_X_offset(), self.pitch_joint_Z_offset())
            .box(self.pitch_joint_OD(), 100, self.quill_width)
        )
        self._object = holder
        self._assembly = cq.Assembly(holder, name=self.name)

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.swing_dia, self.swing_height,
            self.swing_joint_thickness, self.pitch_joint_thickness,
            self.quill_width, self.bearing_od, self.bearing_width,
        )

    def swing_joint_OD(self) -> float:
        return self.swing_dia + self.swing_joint_thickness * 2

    def pitch_joint_OD(self) -> float:
        return self.bearing_od + self.pitch_joint_thickness * 2

    def pitch_joint_X_offset(self) -> float:
        return self.swing_joint_OD() / 2 + self.pitch_joint_OD() / 2

    def pitch_joint_Z_offset(self) -> float:
        return self.pitch_joint_OD() / 2
