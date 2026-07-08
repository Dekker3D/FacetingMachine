from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location
import bom_part_data as bpd
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
                MastCarriage.make(self),
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
        return bpd.BOM()


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


class MastCarriage:
    """
    Rides on the rails, holds 2020 extrusion of mast.
    Z=0 is at the top of the frame.
    """

    @classmethod
    def make(cls, fa: FrameAssembly) -> cq.Workplane:
        assert fa.mast is not None
        rail_Z = -cfg.FRAME_RAIL_DIA / 2

        holder_width = fa.mast.spine_ext_width + cfg.MAST_HOLDER_THICKNESS * 2
        holder_thickness = (
            fa.mast.spine_ext_thickness + cfg.MAST_HOLDER_THICKNESS * 2
        )

        carriage = (
            cq.Workplane("XY", origin=(0, 0, rail_Z + 1))
            .box(
                cfg.MAST_CARRIAGE_LENGTH,
                fa.frame_width_internal() - cfg.MAST_CARRIAGE_CLEARANCE * 2,
                cfg.MAST_CARRIAGE_THICKNESS + cfg.FRAME_RAIL_DIA / 2 - 1,
                centered=(True, True, False),
            )
            # Rail slots
            .faces(">X")
            .workplane(origin=(0, 0, rail_Z))
            .moveTo(fa.frame_rail_width() / 2, 0)
            .hole(cfg.FRAME_RAIL_DIA)
            .moveTo(-fa.frame_rail_width() / 2, 0)
            .hole(cfg.FRAME_RAIL_DIA)
        )

        # Structure to hold mast.
        carriage = carriage.union(
            cq.Workplane("XY", origin=(0, 0, 0))
            .box(
                holder_thickness,
                holder_width,
                cfg.MAST_HOLDER_HEIGHT,
                centered=(True, True, False),
            )
        )

        cutoutPoints = [
            (-fa.mast.spine_ext_thickness / 2, -fa.mast.spine_ext_width / 2),
            (fa.mast.spine_ext_thickness / 2, -fa.mast.spine_ext_width / 2),
            (40, -40),
            (40, 40),
            (fa.mast.spine_ext_thickness / 2, fa.mast.spine_ext_width / 2),
            (-fa.mast.spine_ext_thickness / 2, fa.mast.spine_ext_width / 2),
        ]
        carriage = carriage.cut(
            cq.Workplane("XY", origin=(0, 0, 0))
            .polyline(cutoutPoints)
            .close()
            .extrude(cfg.MAST_HOLDER_HEIGHT)
        )

        return carriage


class FrameLeg:
    """Just a leg for the machine to stand on."""

    @classmethod
    def make(cls, fa: FrameAssembly) -> cq.Workplane:
        leg_pts = [
            (-fa.frame_ext_width, fa.frame_ext_height),
            (0, fa.frame_ext_height),
            (20, 0),
            (20, -fa.frame_leg_length),
            (0, -fa.frame_leg_length),
            (0, -20),
            (-fa.frame_ext_width, 0),
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
            cq.Workplane("XY", origin=(0, -fa.frame_ext_width / 2, 0))
            .box(
                20, fa.frame_ext_width, fa.frame_ext_height,
                centered=(True, True, False),
            )
        )

        leg = (
            leg.faces(">Y")
            .workplane(origin=(0, 0, fa.frame_ext_height / 2))
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
        legs = cls.make(fa).translate(
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
