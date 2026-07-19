from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Vector
import bought_bits as bb
import bom_part_data as bpd
import lap.lap_abstract as lap_abstract


class LapAssembly(lap_abstract.LapAssemblyBase):
    """Faceting lap assembly: lap holder, splash guard, bearings."""

    LAP_HOLE_DIA: float = 12.7
    LAP_AXLE_DIA: float = 8.0
    LAP_DIA: float = 152.4
    LAP_THICKNESS: float = 2.0

    SG_EXTRA_SPACE: float = 10.0
    SG_HEIGHT: float = 30.0
    SG_THICKNESS: float = 2.0
    SG_SLOPE: float = 0.04
    SG_DRAIN_ID: float = 6.0
    SG_DRAIN_OD: float = 10.0

    def sg_screw_spacing(self) -> float:
        return math.ceil(self.sg_OD() * math.sqrt(0.5) / 20) * 20

    def sg_ID(self) -> float:
        return self.LAP_DIA + self.SG_EXTRA_SPACE * 2

    def sg_OD(self) -> float:
        return self.sg_ID() + self.SG_THICKNESS * 2

    def sg_bottom_dia(self) -> float:
        return bb.Bearing608ZZ.OD + 10

    def sg_drain_offset(self) -> float:
        return self.sg_bottom_dia() / 2 + 3 + self.SG_DRAIN_OD / 2

    def bottom_screw_spacing(self) -> float:
        return self.sg_bottom_dia() / 2 + 6.0

    def required_frame_width(self) -> float:
        return self.sg_screw_spacing() + 20.0

    # ═══════════════════════════════════════════════════════════

    def __init__(self) -> None:
        super().__init__(name="Lap Assembly")
        lhb = LapHolderBottom.create(
            axle_dia=self.LAP_AXLE_DIA,
            lap_thickness=self.LAP_THICKNESS,
            bore_dia=self.LAP_HOLE_DIA,
        )
        lht = LapHolderTop.create(axle_dia=self.LAP_AXLE_DIA)
        sg = SplashGuard.create(la=self)
        sgb = SplashGuardBottom.create(la=self)

        self._add(lhb, loc=Location(0, 0, 0), color="red",
                  name="lap_holder_bottom")
        self._add(lht, loc=Location(0, 0, lhb.top_height()), color="yellow",
                  name="lap_holder_top")
        self._add(sg, loc=Location(0, 0, 0), color="blue",
                  name="splash_guard")
        self._add(sgb, loc=Location(0, 0, 0), color="green",
                  name="splash_guard_bottom")

        # Off-the-shelf
        self._bom.add(bb.Bearing608ZZ.get(name="608ZZ Bearing"))  # type: ignore[union-attr]
        self._bom.add(bpd.PartWithMetadata(  # type: ignore[union-attr]
            name=f"Lap Disc {self.LAP_DIA:.0f}mm",
            description="6-inch diamond grinding lap",
        ))


# ═══════════════════════════════════════════════════════════════════════
# Printed parts
# ═══════════════════════════════════════════════════════════════════════


class LapHolderBottom(bpd.PrintedPart):
    """Bottom part of the faceting lap holder."""

    @classmethod
    def create(
        cls, axle_dia: float, lap_thickness: float, bore_dia: float,
    ) -> LapHolderBottom:
        return cls.get(axle_dia=axle_dia, lap_thickness=lap_thickness, bore_dia=bore_dia)

    def __init__(
        self, axle_dia: float, lap_thickness: float, bore_dia: float,
    ) -> None:
        self.axle_dia = axle_dia
        self.lap_thickness = lap_thickness
        self.bore_dia = bore_dia
        super().__init__(name="Lap Holder Bottom")
        bump_height = self.cone_height() + (self.lap_thickness / 2.0)
        cone_points = [
            (self.axle_dia / 2, 0),
            (self.axle_dia / 2 + 2.0, 0),
            (self.axle_dia / 2 + 2.0 + self.cone_height(), self.cone_height()),
            (self.bore_dia / 2, self.cone_height()),
            (self.bore_dia / 2 - 0.1, bump_height),
            (self.axle_dia / 2, bump_height),
        ]
        obj = (
            cq.Workplane("XZ")
            .polyline(cone_points)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )
        self._object = obj
        self._assembly = cq.Assembly(obj, name=self.name)

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.axle_dia, self.lap_thickness, self.bore_dia)

    def cone_height(self) -> float:
        return 15.0

    def top_height(self) -> float:
        return self.cone_height() + self.lap_thickness


class LapHolderTop(bpd.PrintedPart):
    """Top part of the faceting lap holder."""

    @classmethod
    def create(cls, axle_dia: float) -> LapHolderTop:
        return cls.get(axle_dia=axle_dia)

    def __init__(self, axle_dia: float) -> None:
        self.axle_dia = axle_dia
        super().__init__(name="Lap Holder Top")
        cone_points = [
            (self.axle_dia / 2, 0),
            (self.axle_dia / 2, self.cone_height()),
            (self.axle_dia / 2 + 4.0, self.cone_height()),
            (self.cone_dia() / 2, 1.0),
            (self.cone_dia() / 2, 0.0),
        ]
        obj = (
            cq.Workplane("XZ")
            .polyline(cone_points)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )
        self._object = obj
        self._assembly = cq.Assembly(obj, name=self.name)

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.axle_dia)

    def cone_height(self) -> float:
        return 6.0

    def cone_dia(self) -> float:
        return 40.0


class SplashGuard(bpd.PrintedPart):
    """Splash guard — outer shell with sloped floor and central tower."""

    @classmethod
    def create(cls, la: LapAssembly) -> SplashGuard:
        return cls.get(la=la)

    def __init__(self, la: LapAssembly) -> None:
        self.la = la
        super().__init__(name="Splash Guard")
        obj = self._build()
        self._object = obj
        self._assembly = cq.Assembly(obj, name=self.name)

    def _comparables(self) -> tuple[object, ...]:
        return (self.name,)

    def _build(self) -> cq.Workplane:
        la = self.la
        guard = cq.Workplane("XY").cylinder(
            la.SG_HEIGHT + la.SG_THICKNESS,
            la.sg_ID() / 2 + la.SG_THICKNESS,
            centered=(True, True, False),
        )
        cutout = (
            guard.faces(">Z")
            .workplane(invert=True, offset=-50)
            .cylinder(la.SG_HEIGHT + 100, la.sg_ID() / 2,
                      centered=(True, True, False), combine=False)
        )
        conepts = [(0, 0), (500, la.SG_SLOPE * 500), (500, 500), (0, 500)]
        cutout = (
            cutout.intersect(
                cq.Workplane("XZ", origin=(la.sg_drain_offset(), 0, la.SG_THICKNESS))
                .polyline(conepts).close().revolve(360, (0, 0, 0), (0, 1, 0))
            )
            .edges().fillet(5.0)
        )
        cutout = (
            cutout.union(
                cq.Workplane("XY", origin=(la.sg_drain_offset(), 0, la.SG_THICKNESS - 50))
                .cylinder(100, la.SG_DRAIN_ID / 2, centered=(True, True, False))
            )
            .edges().fillet(1.0)
        )
        guard = guard.cut(cutout)

        # Central tower
        tower_od = 56.0
        tower_h = 15.0
        floor_z = la.SG_THICKNESS
        cone_top_r = tower_od / 2 - 5
        cone_floor_r = la.LAP_AXLE_DIA / 2 + 1
        cone_cut_pts = [
            (0, tower_h), (cone_top_r, tower_h),
            (cone_floor_r, 0), (0, 0),
        ]
        cone_cutout = (
            cq.Workplane("XZ")
            .polyline(cone_cut_pts).close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )
        tower = (
            cq.Workplane("XY")
            .cylinder(tower_h, tower_od / 2, centered=(True, True, False))
            .translate((0, 0, floor_z))
            .cut(cone_cutout.translate((0, 0, floor_z)))
            .faces("<Z").workplane().hole(la.LAP_AXLE_DIA + 0.5)
        )
        guard = guard.union(tower)

        # Screw holes through tower
        screw_r = la.bottom_screw_spacing()
        screw_positions = [
            (screw_r * math.cos(math.radians(a)), screw_r * math.sin(math.radians(a)))
            for a in (45, 135, 225, 315)
        ]
        guard = (
            guard.faces("<Z").workplane()
            .pushPoints(screw_positions)
            .hole(3.2, tower_h + la.SG_THICKNESS - 3)
        )
        return guard


class SplashGuardBottom(bpd.PrintedPart):
    """Bottom part of the splash guard with drain path."""

    @classmethod
    def create(cls, la: LapAssembly) -> SplashGuardBottom:
        return cls.get(la=la)

    def __init__(self, la: LapAssembly) -> None:
        self.la = la
        super().__init__(name="Splash Guard Bottom")
        obj = self._build()
        self._object = obj
        self._assembly = cq.Assembly(obj, name=self.name)

    def _comparables(self) -> tuple[object, ...]:
        return (self.name,)

    def _build(self) -> cq.Workplane:
        la = self.la
        dia = bb.Bearing608ZZ.OD + 10
        base_pts = [
            (0, 0), (dia / 2 + 15, 0),
            (dia / 2, -15), (dia / 2, -20), (0, -20),
        ]
        bottom = (
            cq.Workplane("XZ")
            .polyline(base_pts).close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
            .faces("<Z").workplane(origin=(0, 0, 0)).hole(la.LAP_AXLE_DIA)
            .faces("<Z").workplane(origin=(0, 0, 0))
            .hole(bb.Bearing608ZZ.OD, bb.Bearing608ZZ.WIDTH)
            .faces(">Z").workplane(origin=(0, 0, 0), invert=True, offset=20)
            .polarArray(radius=la.bottom_screw_spacing(), count=4,
                        startAngle=45, angle=360)
            .cboreHole(3.2, 6, 15)
        )
        # Drain position marker
        marker_h = la.SG_THICKNESS + 3
        drain_marker = (
            cq.Workplane("XY")
            .transformed(offset=(la.sg_drain_offset(), 0, 0))
            .cylinder(marker_h, la.SG_DRAIN_OD / 2 + 1,
                      centered=(True, True, False))
            .translate((0, 0, -marker_h))
        )
        # Torus drain path
        arc_r = 20.0
        profile_r = la.SG_DRAIN_ID / 2
        drain_x = la.sg_drain_offset()
        arc_center = cq.Vector(drain_x + arc_r, 0, 0)
        arc_edge = cq.Edge.makeCircle(arc_r, arc_center, cq.Vector(0, 1, 0), 180, 225)
        arc_wire = cq.Wire.assembleEdges([arc_edge])
        torus_section = (
            cq.Workplane("XY")
            .transformed(offset=(la.sg_drain_offset(), 0, 0))
            .circle(profile_r)
            .sweep(arc_wire)
        )
        bottom = bottom.union(torus_section)
        return bottom


if __name__ == "__cq_main__":
    result = LapAssembly().get_assembly()
    show_object(result)  # type: ignore[name-defined]  # noqa: F821
