import cadquery as cq
from cadquery import Location, Color
import bought_bits as bb
import lap.lap_abstract as lap_abstract
import math
import bom_part_data as bpd


class LapAssembly(lap_abstract.LapAssemblyBase):
    """Class representing the entire faceting lap assembly."""

    # Lap dimensions.
    # Diameter of the arbor hole.
    LAP_HOLE_DIA = 12.7
    # Diameter of the axle. M8 bolt.
    LAP_AXLE_DIA = 8.0
    # Diameter of the lap, 6 inches.
    LAP_DIA = 152.4
    # Thickness of the lap.
    LAP_THICKNESS = 2.0

    # Splash guard dimensions.
    # Space to reach for stuff that fell under the lap.
    SG_EXTRA_SPACE = 10.0
    # Height, includes lip.
    SG_HEIGHT = 30.0
    # Material thickness.
    SG_THICKNESS = 2.0
    # Slope of splash guard interior.
    SG_SLOPE = 0.04
    # The ID and OD of the drain hole.
    SG_DRAIN_ID = 6.0
    SG_DRAIN_OD = 10.0
    
    _ready = False

    # Spacing. Basically attach at 4 points around the lap.
    # Round to 20 mm increments for ease with 2020 extrusions.
    def sg_screw_spacing(self):
        return math.ceil(self.sg_OD() * math.sqrt(0.5) / 20) * 20

    # Inner diameter.
    def sg_ID(self):
        return self.LAP_DIA + self.SG_EXTRA_SPACE * 2

    def sg_OD(self):
        return self.sg_ID() + self.SG_THICKNESS * 2

    def sg_bottom_dia(self):
        return bb.Bearing608ZZ.OD + 10

    def sg_drain_offset(self):
        return self.sg_bottom_dia() / 2 + 3 + self.SG_DRAIN_OD / 2

    # Screw hole spacing for bottom part.
    def bottom_screw_spacing(self):
        return self.sg_bottom_dia() / 2 + 6.0

    def required_frame_width(self):
        return self.sg_screw_spacing() + 20.0  # So that the middle of the 2020 matches the screw spacing.

    def ready(self):
        if not self._ready:
            self._lhb = LapHolderBottom(self.LAP_AXLE_DIA, self.LAP_THICKNESS, self.LAP_HOLE_DIA)
            self._lht = LapHolderTop(self.LAP_AXLE_DIA)
            self._sg = SplashGuard(self)
            self._sgb = SplashGuardBottom(self)
            self._ready = True

    def make_assembly(self):
        """Assemble the faceting lap components with colors for visualization."""

        self.ready()

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
        bom.add(self._lhb)
        bom.add(self._lht)
        bom.add(self._sg)
        bom.add(self._sgb)
        return bom


class LapHolderBottom(bpd.PrintedPart):
    """Class representing the bottom part of the faceting lap holder."""

    def __init__(self, axle_dia: float, lap_thickness: float, bore_dia: float):
        self.axle_dia = axle_dia
        self.lap_thickness = lap_thickness
        self.bore_dia = bore_dia
        super().__init__(name="Lap Holder Bottom")

    def __eq__(self, other):
        return (isinstance(other, LapHolderBottom)
                and self.name == other.name
                and self.axle_dia == other.axle_dia
                and self.lap_thickness == other.lap_thickness)

    def __hash__(self):
        return hash((self.axle_dia, self.lap_thickness, self.name))

    def cone_height(self):
        return 20.0

    def get_object(self):
        """Create the bottom part of the faceting lap holder."""

        bump_height = self.cone_height() + (self.lap_thickness / 2.0)
        cone_points = [
            (self.axle_dia / 2, 0),
            (self.axle_dia / 2 + 2.0, 0),
            (self.axle_dia / 2 + 2.0 + self.cone_height(), self.cone_height()),
            (self.bore_dia / 2, self.cone_height()),
            (self.bore_dia / 2 - 0.1, bump_height),
            (self.axle_dia / 2, bump_height)
        ]
        holder = (cq.Workplane("XZ")
                  .polyline(cone_points)
                  .close()
                  .revolve(360, (0, 0, 0), (0, 1, 0))
                  )

        return holder

    def make(self):
        return self.get_object()

    def top_height(self):
        """Return the offset for the top part."""
        return self.cone_height() + self.lap_thickness  # The lap is 2 mm thick.


class LapHolderTop(bpd.PrintedPart):
    """Class representing the top part of the faceting lap holder."""

    def __init__(self, axle_dia: float):
        self.axle_dia = axle_dia
        super().__init__(name="Lap Holder Top")

    def __eq__(self, other):
        return (isinstance(other, LapHolderTop)
                and self.name == other.name
                and self.axle_dia == other.axle_dia)

    def __hash__(self):
        return hash((self.axle_dia, self.name))

    def cone_height(self):
        return 6.0

    def cone_dia(self):
        return 40.0

    def get_object(self):
        """Create the top part of the faceting lap holder."""

        cone_points = [
            (self.axle_dia / 2, 0),
            (self.axle_dia / 2, self.cone_height()),
            (self.axle_dia / 2 + 4.0, self.cone_height()),
            (self.cone_dia() / 2, 1.0),
            (self.cone_dia() / 2, 0.0)
        ]
        holder = (cq.Workplane("XZ")
                  .polyline(cone_points)
                  .close()
                  .revolve(360, (0, 0, 0), (0, 1, 0))
                  )

        return holder

    def make(self):
        return self.get_object()


class SplashGuard(bpd.PrintedPart):
    """Class representing the splash guard."""

    def __init__(self, la: 'LapAssembly'):
        self.la = la
        super().__init__(name="Splash Guard")

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, SplashGuard)

    def get_object(self):
        """Create the splash guard."""
        la = self.la
        guard = (cq.Workplane("XY")
                 .cylinder(
                     la.SG_HEIGHT + la.SG_THICKNESS,
                     la.sg_ID() / 2 + la.SG_THICKNESS,
                     centered=(True, True, False)
                     )
                 )

        # Create a cylinder of the right radius. Excess height, shaped by later cone.
        cutout = (guard.faces(">Z")
                  .workplane(invert=True, offset=-50)
                  .cylinder(
                      la.SG_HEIGHT + 100,
                      la.sg_ID() / 2,
                      centered=(True, True, False),
                      combine=False
                      )
                  )

        conepts = [
            (0, 0),
            (500, la.SG_SLOPE * 500),
            (500, 500),
            (0, 500)
        ]

        # Create slope towards drain hole.
        cutout = cutout.intersect(
            cq.Workplane("XZ", origin=(la.sg_drain_offset(), 0, la.SG_THICKNESS))
            .polyline(conepts)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        ).edges().fillet(5.0)

        # Add drain hole.
        cutout = cutout.union(
            cq.Workplane("XY", origin=(la.sg_drain_offset(), 0, la.SG_THICKNESS - 50))
            .cylinder(100, la.SG_DRAIN_ID / 2, centered=(True, True, False))
        ).edges().fillet(1.0)

        guard = guard.cut(cutout)

        return guard

    def make(self, la: 'LapAssembly'):
        return self.get_object()


class SplashGuardBottom(bpd.PrintedPart):
    """Class representing the bottom part of the splash guard."""

    def __init__(self, la: 'LapAssembly'):
        self.la = la
        super().__init__(name="Splash Guard Bottom")

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, SplashGuardBottom)

    def get_object(self):
        """Create the bottom part of the splash guard."""
        la = self.la
        dia = bb.Bearing608ZZ.OD + 10

        base_pts = [
            (0, 0),
            (dia / 2 + 15, 0),
            (dia / 2, -15),  # Slope
            (dia / 2, -20),  # Holds bearings
            (0, -20)
        ]

        bottom = (cq.Workplane("XZ")
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
                  .polarArray(radius=la.bottom_screw_spacing(), count=4, startAngle=45, angle=360)
                  .cboreHole(3.2, 6, 15)
                  )

        return bottom

    def make(self, la: 'LapAssembly'):
        return self.get_object()



if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    result = LapAssembly().make_assembly()
    show_object(result)
