from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location
import bom_part_data as bpd
import bought_bits as bb
import frame.frame_abstract as frame_abstract
import lap.lap_abstract as lap_abstract
import mast.mast_abstract as mast_abstract
import frame_mast_joint.frame_mast_joint_abstract as frame_mast_joint
from machine import MachineConfig as cfg


class FrameAssembly(frame_abstract.FrameAssemblyBase):
    """Class representing the entire frame assembly."""

    lap: lap_abstract.LapAssemblyBase | None = None
    mast: mast_abstract.MastAssemblyBase | None = None
    mast_joint: frame_mast_joint.FrameMastJointBase | None = None
    frame_ext_width: float = 20.0
    frame_ext_height: float = 20.0
    frame_leg_length: float = 40.0
    mast_vis_x: float = 100.0

    def frame_width(self) -> float:
        assert self.lap is not None
        return self.lap.required_frame_width() + self.frame_ext_width

    def frame_width_internal(self) -> float:
        return self.frame_width() - self.frame_ext_width * 2

    def frame_rail_width(self) -> float:
        return (
            self.frame_width_internal()
            - cfg.FRAME_RAIL_DIA
            - cfg.FRAME_RAIL_SPACING * 2
        )

    def mast_space(self) -> float:
        return self.frame_length() - self.lap_space_from_left() - 20

    def frame_length(self) -> float:
        assert self.lap is not None
        return (
            math.ceil(
                (self.frame_width() / 2
                 + self.lap.sg_OD() / 2
                 + cfg.MAST_DESIRED_SPACE
                 + 20)
                / 20
            )
            * 20
        )

    def lap_pos_from_left(self) -> float:
        return self.frame_width() / 2

    def lap_space_from_left(self) -> float:
        assert self.lap is not None
        return self.lap_pos_from_left() + self.lap.sg_OD() / 2

    def validate(self) -> None:
        assert self.lap is not None
        assert self.lap.sg_OD() < cfg.printer_safe_size(), (
            "Splash guard diameter exceeds 3D printer size!"
        )

    def set_mast_joint(
        self, mast_joint: frame_mast_joint.FrameMastJointBase
    ) -> None:
        self.mast_joint = mast_joint

    def make_assembly(self) -> cq.Assembly:
        """Create the frame assembly."""
        assert self.lap is not None
        assert self.mast is not None

        assembly = (
            cq.Assembly()
            .add(
                FrameExtrusions.make(self),
                name="frame_extrusions",
                loc=Location((0, 0, 0)),
                color=cq.Color("lightgray"),
            )
            .add(
                MastRails.make(self),
                name="mast_rails",
                loc=Location((0, 0, 0)),
                color=cq.Color("yellow"),
            )
            .add(
                MastCarriage(
                    carriage_length=cfg.MAST_CARRIAGE_LENGTH,
                    carriage_clearance=cfg.MAST_CARRIAGE_CLEARANCE,
                    carriage_thickness=cfg.MAST_CARRIAGE_THICKNESS,
                    frame_rail_dia=cfg.FRAME_RAIL_DIA,
                    mast_holder_thickness=cfg.MAST_HOLDER_THICKNESS,
                    mast_holder_height=cfg.MAST_HOLDER_HEIGHT,
                    frame_width_internal=self.frame_width_internal(),
                    frame_rail_width=self.frame_rail_width(),
                    mast_spine_ext_width=self.mast.spine_ext_width,  # type: ignore[union-attr]
                    mast_spine_ext_thickness=self.mast.spine_ext_thickness,  # type: ignore[union-attr]
                ).get_object(),
                name="mast_carriage",
                loc=Location((-self.frame_length() / 2 + self.mast_vis_x, 0, 20)),
                color=cq.Color("red"),
            )
            .add(
                FrameLeg.make_legs(self),
                name="frame_leg",
                loc=Location((0, 0, 0)),
                color=cq.Color("green"),
            )
            .add(
                self.lap.make_assembly(),
                name="lap_assembly",
                loc=Location(
                    (self.frame_length() / 2 - self.lap_pos_from_left(), 0, 20)
                ),
            )
            .add(
                self.mast.make_assembly(),
                name="mast_assembly",
                loc=Location(
                    (-self.frame_length() / 2 + self.mast_vis_x, 0, 20)
                ),
            )
        )

        return assembly

    def get_BOM(self) -> bpd.BOM:
        assert self.lap is not None and self.mast is not None
        bom = bpd.BOM()
        # Printed parts
        bom.add(MastCarriage(
            carriage_length=cfg.MAST_CARRIAGE_LENGTH,
            carriage_clearance=cfg.MAST_CARRIAGE_CLEARANCE,
            carriage_thickness=cfg.MAST_CARRIAGE_THICKNESS,
            frame_rail_dia=cfg.FRAME_RAIL_DIA,
            mast_holder_thickness=cfg.MAST_HOLDER_THICKNESS,
            mast_holder_height=cfg.MAST_HOLDER_HEIGHT,
            frame_width_internal=self.frame_width_internal(),
            frame_rail_width=self.frame_rail_width(),
            mast_spine_ext_width=self.mast.spine_ext_width,
            mast_spine_ext_thickness=self.mast.spine_ext_thickness,
        ))
        bom.add(FrameLeg(
            ext_width=self.frame_ext_width,
            ext_height=self.frame_ext_height,
            leg_length=self.frame_leg_length,
        ), 4)
        # Off-the-shelf
        bom.add(bb.TslotExtrusion2020(self.frame_width()), 2)
        bom.add(bb.TslotExtrusion2020(self.frame_length() - 40), 2)
        bom.add(bb.SmoothRod(diameter=cfg.FRAME_RAIL_DIA, length=self.mast_space()), 2)
        return bom


class FrameExtrusions:
    """Just do the extrusions in one class, fuck it."""

    @classmethod
    def make(cls, fa: FrameAssembly) -> cq.Workplane:
        frame = (
            cq.Workplane("XZ")
            .moveTo(fa.frame_length() / 2 - 10, 0)
            .box(20, 20, fa.frame_width(), centered=(True, False, True))
            .moveTo(-fa.frame_length() / 2 + 10, 0)
            .box(20, 20, fa.frame_width(), centered=(True, False, True))
            .chamfer(1.0)
        )

        frame = frame.union(
            cq.Workplane("YZ")
            .moveTo(fa.frame_width() / 2 - 10, 0)
            .box(20, 20, fa.frame_length() - 40, centered=(True, False, True))
            .moveTo(-fa.frame_width() / 2 + 10, 0)
            .box(20, 20, fa.frame_length() - 40, centered=(True, False, True))
            .chamfer(1.0)
        )

        return frame


class MastRails:
    """Two smooth rods, for the mast to ride on."""

    @classmethod
    def make(cls, fa: FrameAssembly) -> cq.Workplane:
        rail = (
            cq.Workplane("YZ", origin=(-fa.frame_length() / 2 + 20, 0, 0))
            .moveTo(
                fa.frame_rail_width() / 2,
                20 - cfg.FRAME_RAIL_DIA / 2,
            )
            .cylinder(fa.mast_space(), 4, centered=(True, True, False))
            .moveTo(
                -fa.frame_rail_width() / 2,
                20 - cfg.FRAME_RAIL_DIA / 2,
            )
            .cylinder(fa.mast_space(), 4, centered=(True, True, False))
        )

        return rail


class MastCarriage(bpd.PrintedPart):
    """Rides on the rails, holds 2020 extrusion of mast. Z=0 is at frame top."""

    def __init__(
        self,
        carriage_length: float,
        carriage_clearance: float,
        carriage_thickness: float,
        frame_rail_dia: float,
        mast_holder_thickness: float,
        mast_holder_height: float,
        frame_width_internal: float,
        frame_rail_width: float,
        mast_spine_ext_width: float,
        mast_spine_ext_thickness: float,
    ) -> None:
        self.carriage_length = carriage_length
        self.carriage_clearance = carriage_clearance
        self.carriage_thickness = carriage_thickness
        self.frame_rail_dia = frame_rail_dia
        self.mast_holder_thickness = mast_holder_thickness
        self.mast_holder_height = mast_holder_height
        self.frame_width_internal = frame_width_internal
        self.frame_rail_width = frame_rail_width
        self.mast_spine_ext_width = mast_spine_ext_width
        self.mast_spine_ext_thickness = mast_spine_ext_thickness
        super().__init__(name="Mast Carriage")

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.carriage_length, self.carriage_clearance,
            self.carriage_thickness, self.frame_rail_dia,
            self.mast_holder_thickness, self.mast_holder_height,
            self.frame_width_internal, self.frame_rail_width,
            self.mast_spine_ext_width, self.mast_spine_ext_thickness,
        )

    def get_object(self) -> cq.Workplane:
        """Create the mast carriage geometry."""
        rail_Z = -self.frame_rail_dia / 2
        holder_width = self.mast_spine_ext_width + self.mast_holder_thickness * 2
        holder_thickness = (
            self.mast_spine_ext_thickness + self.mast_holder_thickness * 2
        )

        carriage = (
            cq.Workplane("XY", origin=(0, 0, rail_Z + 1))
            .box(
                self.carriage_length,
                self.frame_width_internal - self.carriage_clearance * 2,
                self.carriage_thickness + self.frame_rail_dia / 2 - 1,
                centered=(True, True, False),
            )
            # Rail slots
            .faces(">X")
            .workplane(origin=(0, 0, rail_Z))
            .moveTo(self.frame_rail_width / 2, 0)
            .hole(self.frame_rail_dia)
            .moveTo(-self.frame_rail_width / 2, 0)
            .hole(self.frame_rail_dia)
        )

        # Structure to hold mast.
        carriage = carriage.union(
            cq.Workplane("XY", origin=(0, 0, 0))
            .box(
                holder_thickness,
                holder_width,
                self.mast_holder_height,
                centered=(True, True, False),
            )
        )

        cutoutPoints = [
            (-self.mast_spine_ext_thickness / 2, -self.mast_spine_ext_width / 2),
            (self.mast_spine_ext_thickness / 2, -self.mast_spine_ext_width / 2),
            (40, -40),
            (40, 40),
            (self.mast_spine_ext_thickness / 2, self.mast_spine_ext_width / 2),
            (-self.mast_spine_ext_thickness / 2, self.mast_spine_ext_width / 2),
        ]
        carriage = carriage.cut(
            cq.Workplane("XY", origin=(0, 0, 0))
            .polyline(cutoutPoints)
            .close()
            .extrude(self.mast_holder_height)
        )

        return carriage


class FrameLeg(bpd.PrintedPart):
    """A single leg for the machine to stand on. Printed 4x."""

    def __init__(
        self,
        ext_width: float,
        ext_height: float,
        leg_length: float,
    ) -> None:
        self.ext_width = ext_width
        self.ext_height = ext_height
        self.leg_length = leg_length
        super().__init__(name="Frame Leg")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.ext_width, self.ext_height, self.leg_length)

    def get_object(self) -> cq.Workplane:
        """Return one printable leg."""
        leg_pts = [
            (-self.ext_width, self.ext_height),
            (0, self.ext_height),
            (20, 0),
            (20, -self.leg_length),
            (0, -self.leg_length),
            (0, -20),
            (-self.ext_width, 0),
        ]

        leg = (
            cq.Workplane("YZ")
            .polyline(leg_pts)
            .close()
            .extrude(10, both=True)
            .edges("<Z")
            .fillet(3.0)
            .edges("|X")
            .fillet(8.0)
        )

        leg = leg.cut(
            cq.Workplane("XY", origin=(0, -self.ext_width / 2, 0))
            .box(
                20, self.ext_width, self.ext_height,
                centered=(True, True, False),
            )
        )

        leg = (
            leg.faces(">Y")
            .workplane(origin=(0, 0, self.ext_height / 2))
            .cboreHole(5.2, 8.0, 15.0, 20.0)
        )

        leg = (
            leg.faces(cq.selectors.NearestToPointSelector((0, -10, 0)))
            .workplane(origin=(0, -10, 0), offset=20, invert=True)
            .cboreHole(5.2, 8.0, 15.0, 20.0)
        )

        return leg

    @classmethod
    def make_legs(cls, fa: FrameAssembly) -> cq.Workplane:
        """Create the 4-leg compound for assembly visualization."""
        leg_part = cls(
            ext_width=fa.frame_ext_width,
            ext_height=fa.frame_ext_height,
            leg_length=fa.frame_leg_length,
        )
        legs = leg_part.get_object().translate(
            (
                fa.frame_length() / 2 - 10 - fa.frame_ext_width,
                fa.frame_width() / 2,
                0,
            )
        )

        legs = legs.mirror((1, 0, 0)).add(legs)
        legs = legs.mirror((0, 1, 0)).add(legs)

        return legs


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    fa = FrameAssembly()
    fa.validate()
    result = fa.make_assembly()
    show_object(result)  # type: ignore[name-defined]  # noqa: F821
