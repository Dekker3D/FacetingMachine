from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Vector
import bom_part_data as bpd
import bought_bits as bb
import frame.frame_abstract as frame_abstract
import lap.lap_abstract as lap_abstract
import mast.mast_abstract as mast_abstract
import frame_mast_joint.frame_mast_joint_abstract as frame_mast_joint
from machine import MachineConfig as cfg


class FrameAssembly(frame_abstract.FrameAssemblyBase):
    """Frame assembly: extrusions, rails, carriage, legs, lap + mast."""

    frame_ext_width: float = 20.0
    frame_ext_height: float = 20.0
    frame_leg_length: float = 40.0
    mast_vis_x: float = 100.0

    # ── dimensions ──────────────────────────────────────────────

    def frame_width(self) -> float:
        assert self.lap is not None
        return self.lap.required_frame_width() + self.frame_ext_width

    def frame_width_internal(self) -> float:
        return self.frame_width() - self.frame_ext_width * 2

    def frame_rail_width(self) -> float:
        return self.frame_width_internal() - cfg.FRAME_RAIL_DIA - cfg.FRAME_RAIL_SPACING * 2

    def mast_space(self) -> float:
        return self.frame_length() - self.lap_space_from_left() - 20

    def frame_length(self) -> float:
        assert self.lap is not None
        return math.ceil(
            (self.frame_width() / 2 + self.lap.sg_OD() / 2
             + cfg.MAST_DESIRED_SPACE + 20) / 20
        ) * 20

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

    # ═══════════════════════════════════════════════════════════

    def __init__(
        self,
        lap: lap_abstract.LapAssemblyBase | None = None,
        mast: mast_abstract.MastAssemblyBase | None = None,
        mast_joint: frame_mast_joint.FrameMastJointBase | None = None,
    ) -> None:
        super().__init__(name="Frame Assembly")
        self._current_group = self.name
        self.lap = lap
        self.mast = mast
        self.mast_joint = mast_joint

        assert lap is not None and mast is not None

        # Frame extrusions (inline, not a separate part)
        extrusions = self._make_extrusions()
        self._assembly.add(extrusions, name="frame_extrusions",  # type: ignore[union-attr]
                           loc=Location(0, 0, 0), color=cq.Color("lightgray"))

        # Mast rails (inline)
        rails = self._make_rails()
        self._assembly.add(rails, name="mast_rails",  # type: ignore[union-attr]
                           loc=Location(0, 0, 0), color=cq.Color("yellow"))

        # Mast carriage
        carriage = MastCarriage.create(
            carriage_length=cfg.MAST_CARRIAGE_LENGTH,
            carriage_clearance=cfg.MAST_CARRIAGE_CLEARANCE,
            carriage_thickness=cfg.MAST_CARRIAGE_THICKNESS,
            frame_rail_dia=cfg.FRAME_RAIL_DIA,
            mast_holder_thickness=cfg.MAST_HOLDER_THICKNESS,
            mast_holder_height=cfg.MAST_HOLDER_HEIGHT,
            frame_width_internal=self.frame_width_internal(),
            frame_rail_width=self.frame_rail_width(),
            mast_spine_ext_width=mast.spine_ext_width,
            mast_spine_ext_thickness=mast.spine_ext_thickness,
        )
        self._add(carriage,
                  loc=Location(-self.frame_length() / 2 + self.mast_vis_x, 0, 20),
                  color="red", name="mast_carriage")

        # Legs x4 (symmetrical — just position at 4 corners)
        leg = FrameLeg.create(
            ext_width=self.frame_ext_width,
            ext_height=self.frame_ext_height,
            leg_length=self.frame_leg_length,
        )
        lx = self.frame_length() / 2 - 10 - self.frame_ext_width
        ly = self.frame_width() / 2
        corners = {"leg_bl": (1, 1), "leg_tl": (1, -1), "leg_br": (-1, 1), "leg_tr": (-1, -1)}
        for name, (sx, sy) in corners.items():
            rot_z = 180 if sy < 0 else 0
            self._add(leg, loc=Location(lx * sx, ly * sy, 0, 0, 0, rot_z),
                      color="green", name=name)

        # Lap + mast assemblies
        self._add(lap, loc=Location(self.frame_length() / 2 - self.lap_pos_from_left(), 0, 20),
                  name="lap_assembly")
        self._add(mast, loc=Location(-self.frame_length() / 2 + self.mast_vis_x, 0, 20),
                  name="mast_assembly")

        # Off-the-shelf
        ext_w = bb.TslotExtrusion2020.get(length=self.frame_width())
        ext_l = bb.TslotExtrusion2020.get(length=self.frame_length() - 40)
        rod = bb.SmoothRod(diameter=cfg.FRAME_RAIL_DIA, length=self.mast_space())
        self._bom.add(ext_w, 2)  # type: ignore[union-attr]
        self._bom.add(ext_l, 2)  # type: ignore[union-attr]
        self._bom.add(rod, 2)    # type: ignore[union-attr]
        for p in (ext_w, ext_l, rod):
            self._bom._groups[p] = self.name  # type: ignore[union-attr]

    # ── inline geometry ─────────────────────────────────────────

    def _make_extrusions(self) -> cq.Workplane:
        fl = self.frame_length()
        fw = self.frame_width()
        frame = (
            cq.Workplane("XZ")
            .moveTo(fl / 2 - 10, 0).box(20, 20, fw, centered=(True, False, True))
            .moveTo(-fl / 2 + 10, 0).box(20, 20, fw, centered=(True, False, True))
            .chamfer(1.0)
        )
        frame = frame.union(
            cq.Workplane("YZ")
            .moveTo(fw / 2 - 10, 0).box(20, 20, fl - 40, centered=(True, False, True))
            .moveTo(-fw / 2 + 10, 0).box(20, 20, fl - 40, centered=(True, False, True))
            .chamfer(1.0)
        )
        return frame

    def _make_rails(self) -> cq.Workplane:
        fl = self.frame_length()
        return (
            cq.Workplane("YZ", origin=(-fl / 2 + 20, 0, 0))
            .moveTo(self.frame_rail_width() / 2, 20 - cfg.FRAME_RAIL_DIA / 2)
            .cylinder(self.mast_space(), 4, centered=(True, True, False))
            .moveTo(-self.frame_rail_width() / 2, 20 - cfg.FRAME_RAIL_DIA / 2)
            .cylinder(self.mast_space(), 4, centered=(True, True, False))
        )


# ═══════════════════════════════════════════════════════════════════════
# Printed parts
# ═══════════════════════════════════════════════════════════════════════


class MastCarriage(bpd.PrintedPart):
    """Rides on the frame rails, holds the mast's 2020 extrusion."""

    @classmethod
    def create(
        cls,
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
    ) -> MastCarriage:
        return cls.get(
            carriage_length=carriage_length,
            carriage_clearance=carriage_clearance,
            carriage_thickness=carriage_thickness,
            frame_rail_dia=frame_rail_dia,
            mast_holder_thickness=mast_holder_thickness,
            mast_holder_height=mast_holder_height,
            frame_width_internal=frame_width_internal,
            frame_rail_width=frame_rail_width,
            mast_spine_ext_width=mast_spine_ext_width,
            mast_spine_ext_thickness=mast_spine_ext_thickness,
        )

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

        rail_Z = -self.frame_rail_dia / 2
        holder_width = self.mast_spine_ext_width + self.mast_holder_thickness * 2
        holder_thickness = self.mast_spine_ext_thickness + self.mast_holder_thickness * 2
        obj = (
            cq.Workplane("XY", origin=(0, 0, rail_Z + 1))
            .box(self.carriage_length,
                 self.frame_width_internal - self.carriage_clearance * 2,
                 self.carriage_thickness + self.frame_rail_dia / 2 - 1,
                 centered=(True, True, False))
            .faces(">X").workplane(origin=(0, 0, rail_Z))
            .moveTo(self.frame_rail_width / 2, 0).hole(self.frame_rail_dia)
            .moveTo(-self.frame_rail_width / 2, 0).hole(self.frame_rail_dia)
        )
        obj = obj.union(
            cq.Workplane("XY", origin=(0, 0, 0))
            .box(holder_thickness, holder_width, self.mast_holder_height,
                 centered=(True, True, False))
        )
        cutout_pts = [
            (-self.mast_spine_ext_thickness / 2, -self.mast_spine_ext_width / 2),
            (self.mast_spine_ext_thickness / 2, -self.mast_spine_ext_width / 2),
            (40, -40), (40, 40),
            (self.mast_spine_ext_thickness / 2, self.mast_spine_ext_width / 2),
            (-self.mast_spine_ext_thickness / 2, self.mast_spine_ext_width / 2),
        ]
        obj = obj.cut(
            cq.Workplane("XY", origin=(0, 0, 0))
            .polyline(cutout_pts).close().extrude(self.mast_holder_height)
        )
        self._object = obj
        self._assembly = cq.Assembly(obj, name=self.name)

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.carriage_length, self.carriage_clearance,
            self.carriage_thickness, self.frame_rail_dia,
            self.mast_holder_thickness, self.mast_holder_height,
            self.frame_width_internal, self.frame_rail_width,
            self.mast_spine_ext_width, self.mast_spine_ext_thickness,
        )


class FrameLeg(bpd.PrintedPart):
    """A single leg for the machine to stand on. Printed 4×."""

    @classmethod
    def create(
        cls, ext_width: float, ext_height: float, leg_length: float,
    ) -> FrameLeg:
        return cls.get(ext_width=ext_width, ext_height=ext_height, leg_length=leg_length)

    def __init__(
        self, ext_width: float, ext_height: float, leg_length: float,
    ) -> None:
        self.ext_width = ext_width
        self.ext_height = ext_height
        self.leg_length = leg_length
        super().__init__(name="Frame Leg")
        leg_pts = [
            (-self.ext_width, self.ext_height),
            (0, self.ext_height), (20, 0),
            (20, -self.leg_length), (0, -self.leg_length),
            (0, -20), (-self.ext_width, 0),
        ]
        obj = (
            cq.Workplane("YZ")
            .polyline(leg_pts).close()
            .extrude(10, both=True)
            .edges("<Z").fillet(3.0)
            .edges("|X").fillet(8.0)
        )
        obj = obj.cut(
            cq.Workplane("XY", origin=(0, -self.ext_width / 2, 0))
            .box(20, self.ext_width, self.ext_height, centered=(True, True, False))
        )
        obj = (
            obj.faces(">Y").workplane(origin=(0, 0, self.ext_height / 2))
            .cboreHole(5.2, 8.0, 15.0, 20.0)
        )
        obj = (
            obj.faces(cq.selectors.NearestToPointSelector((0, -10, 0)))
            .workplane(origin=(0, -10, 0), offset=20, invert=True)
            .cboreHole(5.2, 8.0, 15.0, 20.0)
        )
        self._object = obj
        self._assembly = cq.Assembly(obj, name=self.name)

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.ext_width, self.ext_height, self.leg_length)


if __name__ == "__cq_main__":
    fa = FrameAssembly()
    fa.validate()
    result = fa.get_assembly()
    show_object(result)  # type: ignore[name-defined]  # noqa: F821
