from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Color
import bought_bits as bb
import bom_part_data as bpd
import lap.lap_abstract as lap_abstract


class LapAssembly(lap_abstract.LapAssemblyBase):
    """Class representing the entire faceting lap assembly."""

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

    _ready: bool = False
    _lhb: LapHolderBottom | None = None
    _lht: LapHolderTop | None = None
    _sg: SplashGuard | None = None
    _sgb: SplashGuardBottom | None = None

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

    def ready(self) -> None:
        if not self._ready:
            self._lhb = LapHolderBottom(
                self.LAP_AXLE_DIA, self.LAP_THICKNESS, self.LAP_HOLE_DIA
            )
            self._lht = LapHolderTop(self.LAP_AXLE_DIA)
            self._sg = SplashGuard(self)
            self._sgb = SplashGuardBottom(self)
            self._ready = True

    def make_assembly(self) -> cq.Assembly:
        """Assemble the faceting lap components."""
        self.ready()
        assert self._lhb is not None
        assert self._lht is not None
        assert self._sg is not None
        assert self._sgb is not None

        assembly = (
            cq.Assembly()
            .add(
                self._lhb.make(),
                name="lap_holder_bottom",
                loc=Location((0, 0, 0)),
                color=Color("red"),
            )
            .add(
                self._lht.make(),
                name="lap_holder_top",
                loc=Location((0, 0, self._lhb.top_height())),
                color=Color("yellow"),
            )
            .add(
                self._sg.make(self),
                name="splash_guard",
                loc=Location((0, 0, 0)),
                color=Color("blue"),
            )
            .add(
                self._sgb.make(self),
                name="splash_guard_bottom",
                loc=Location((0, 0, 0)),
                color=Color("green"),
            )
        )

        return assembly

    def get_BOM(self) -> bpd.BOM:
        self.ready()
        bom = bpd.BOM()
        if self._lhb:
            bom.add(self._lhb)
        if self._lht:
            bom.add(self._lht)
        if self._sg:
            bom.add(self._sg)
        if self._sgb:
            bom.add(self._sgb)
        return bom


class LapHolderBottom(bpd.PrintedPart):
    """Class representing the bottom part of the faceting lap holder."""

    def __init__(
        self, axle_dia: float, lap_thickness: float, bore_dia: float
    ) -> None:
        self.axle_dia: float = axle_dia
        self.lap_thickness: float = lap_thickness
        self.bore_dia: float = bore_dia
        super().__init__(name="Lap Holder Bottom")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.axle_dia, self.lap_thickness, self.bore_dia)

    def cone_height(self) -> float:
        return 20.0

    def get_object(self) -> cq.Workplane:
        """Create the bottom part of the faceting lap holder."""
        bump_height = self.cone_height() + (self.lap_thickness / 2.0)
        cone_points = [
            (self.axle_dia / 2, 0),
            (self.axle_dia / 2 + 2.0, 0),
            (self.axle_dia / 2 + 2.0 + self.cone_height(), self.cone_height()),
            (self.bore_dia / 2, self.cone_height()),
            (self.bore_dia / 2 - 0.1, bump_height),
            (self.axle_dia / 2, bump_height),
        ]
        holder = (
            cq.Workplane("XZ")
            .polyline(cone_points)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )

        return holder

    def make(self) -> cq.Workplane:
        return self.get_object()

    def top_height(self) -> float:
        """Return the offset for the top part."""
        return self.cone_height() + self.lap_thickness


class LapHolderTop(bpd.PrintedPart):
    """Class representing the top part of the faceting lap holder."""

    def __init__(self, axle_dia: float) -> None:
        self.axle_dia: float = axle_dia
        super().__init__(name="Lap Holder Top")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.axle_dia)

    def cone_height(self) -> float:
        return 6.0

    def cone_dia(self) -> float:
        return 40.0

    def get_object(self) -> cq.Workplane:
        """Create the top part of the faceting lap holder."""
        cone_points = [
            (self.axle_dia / 2, 0),
            (self.axle_dia / 2, self.cone_height()),
            (self.axle_dia / 2 + 4.0, self.cone_height()),
            (self.cone_dia() / 2, 1.0),
            (self.cone_dia() / 2, 0.0),
        ]
        holder = (
            cq.Workplane("XZ")
            .polyline(cone_points)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )

        return holder

    def make(self) -> cq.Workplane:
        return self.get_object()


class SplashGuard(bpd.PrintedPart):
    """Class representing the splash guard."""

    def __init__(self, la: LapAssembly) -> None:
        self.la: LapAssembly = la
        super().__init__(name="Splash Guard")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name,)

    def get_object(self) -> cq.Workplane:
        """Create the splash guard."""
        la = self.la
        guard = cq.Workplane("XY").cylinder(
            la.SG_HEIGHT + la.SG_THICKNESS,
            la.sg_ID() / 2 + la.SG_THICKNESS,
            centered=(True, True, False),
        )

        cutout = (
            guard.faces(">Z")
            .workplane(invert=True, offset=-50)
            .cylinder(
                la.SG_HEIGHT + 100,
                la.sg_ID() / 2,
                centered=(True, True, False),
                combine=False,
            )
        )

        conepts = [
            (0, 0),
            (500, la.SG_SLOPE * 500),
            (500, 500),
            (0, 500),
        ]

        cutout = (
            cutout.intersect(
                cq.Workplane(
                    "XZ", origin=(la.sg_drain_offset(), 0, la.SG_THICKNESS)
                )
                .polyline(conepts)
                .close()
                .revolve(360, (0, 0, 0), (0, 1, 0))
            )
            .edges()
            .fillet(5.0)
        )

        cutout = (
            cutout.union(
                cq.Workplane(
                    "XY",
                    origin=(la.sg_drain_offset(), 0, la.SG_THICKNESS - 50),
                )
                .cylinder(100, la.SG_DRAIN_ID / 2, centered=(True, True, False))
            )
            .edges()
            .fillet(1.0)
        )

        guard = guard.cut(cutout)

        return guard

    def make(self, la: LapAssembly) -> cq.Workplane:
        return self.get_object()


class SplashGuardBottom(bpd.PrintedPart):
    """Class representing the bottom part of the splash guard."""

    def __init__(self, la: LapAssembly) -> None:
        self.la: LapAssembly = la
        super().__init__(name="Splash Guard Bottom")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name,)

    def get_object(self) -> cq.Workplane:
        """Create the bottom part of the splash guard."""
        la = self.la
        dia = bb.Bearing608ZZ.OD + 10

        base_pts = [
            (0, 0),
            (dia / 2 + 15, 0),
            (dia / 2, -15),
            (dia / 2, -20),
            (0, -20),
        ]

        bottom = (
            cq.Workplane("XZ")
            .polyline(base_pts)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
            .faces("<Z")
            .workplane(origin=(0, 0, 0))
            .hole(la.LAP_AXLE_DIA)
            .faces("<Z")
            .workplane(origin=(0, 0, 0))
            .hole(bb.Bearing608ZZ.OD, bb.Bearing608ZZ.WIDTH)
            .faces(">Z")
            .workplane(origin=(0, 0, 0), invert=True, offset=20)
            .polarArray(
                radius=la.bottom_screw_spacing(),
                count=4, startAngle=45, angle=360,
            )
            .cboreHole(3.2, 6, 15)
        )

        return bottom

    def make(self, la: LapAssembly) -> cq.Workplane:
        return self.get_object()


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    result = LapAssembly().make_assembly()
    show_object(result)  # type: ignore[name-defined]  # noqa: F821
