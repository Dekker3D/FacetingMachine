import cadquery as cq
from cadquery import Location, Color
import bought_bits as bb
import lap_abstract
import math


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

    def make_assembly(self):
        """Assemble the faceting lap components with colors for visualization."""

        assembly = (
            cq.Assembly()
            .add(
                LapHolderBottom().make(self),
                name="lap_holder_bottom",
                loc=Location((0, 0, 0)),
                color=Color("red"),
            )
            .add(
                LapHolderTop().make(self),
                name="lap_holder_top",
                loc=Location((0, 0, LapHolderBottom.top_height(self))),
                color=Color("yellow"),
            )
            .add(
                SplashGuard().make(self),
                name="splash_guard",
                loc=Location((0, 0, 0)),
                color=Color("blue"),
            )
            .add(
                SplashGuardBottom().make(self),
                name="splash_guard_bottom",
                loc=Location((0, 0, 0)),
                color=Color("green"),
            )
        )

        return assembly


class LapHolderBottom:
    """Class representing the bottom part of the faceting lap holder."""

    @classmethod
    def cone_height(cls):
        return 20.0

    @classmethod
    def make(cls, la: LapAssembly):
        """Create the bottom part of the faceting lap holder."""

        bump_height = cls.cone_height() + (la.LAP_THICKNESS / 2.0)
        cone_points = [
            (la.LAP_AXLE_DIA / 2, 0),
            (la.LAP_AXLE_DIA / 2 + 2.0, 0),
            (la.LAP_AXLE_DIA / 2 + 2.0 + cls.cone_height(), cls.cone_height()),
            (la.LAP_HOLE_DIA / 2 - 0.1, cls.cone_height()),
            (la.LAP_HOLE_DIA / 2 - 0.1, bump_height),
            (la.LAP_AXLE_DIA / 2, bump_height)
        ]
        holder = (cq.Workplane("XZ")
                  .polyline(cone_points)
                  .close()
                  .revolve(360, (0, 0, 0), (0, 1, 0))
                  )

        return holder

    @classmethod
    def top_height(cls, la: LapAssembly):
        """Return the offset for the top part."""
        return cls.cone_height() + la.LAP_THICKNESS  # The lap is 2 mm thick.


class LapHolderTop:
    """Class representing the top part of the faceting lap holder."""

    @classmethod
    def cone_height(cls):
        return 6.0

    @classmethod
    def cone_dia(cls):
        return 40.0

    @classmethod
    def make(cls, la: LapAssembly):
        """Create the top part of the faceting lap holder."""

        cone_points = [
            (la.LAP_AXLE_DIA / 2, 0),
            (la.LAP_AXLE_DIA / 2, cls.cone_height()),
            (la.LAP_AXLE_DIA / 2 + 4.0, cls.cone_height()),
            (cls.cone_dia() / 2, 1.0),
            (cls.cone_dia() / 2, 0.0)
        ]
        holder = (cq.Workplane("XZ")
                  .polyline(cone_points)
                  .close()
                  .revolve(360, (0, 0, 0), (0, 1, 0))
                  )

        return holder


class SplashGuard:
    """Class representing the splash guard."""

    # The height of the splash guard, including the lip that extends above the lap.
    HEIGHT = 30.0
    # The thickness of the splash guard walls.
    THICKNESS = 2.0

    def make(self, la: LapAssembly):
        """Create the splash guard."""

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
            cq.Workplane("XZ", origin=(la.sg_drain_offset(), 0, self.THICKNESS))
            .polyline(conepts)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        ).edges().fillet(5.0)

        # Add drain hole.
        cutout = cutout.union(
            cq.Workplane("XY", origin=(la.sg_drain_offset(), 0, self.THICKNESS - 50))
            .cylinder(100, la.SG_DRAIN_ID / 2, centered=(True, True, False))
        ).edges().fillet(1.0)

        guard = guard.cut(cutout)

        return guard


class SplashGuardBottom:
    """Class representing the bottom part of the splash guard."""

    @classmethod
    def make(cls, la: LapAssembly):
        """Create the bottom part of the splash guard."""

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


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    result = LapAssembly().make_assembly()
    show_object(result)
