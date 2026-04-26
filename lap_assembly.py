import cadquery as cq
from cadquery import Location, Color
from machine import MachineConfig as cfg


class LapHolderBottom:
    """Class representing the bottom part of the faceting lap holder."""

    @classmethod
    def cone_height(cls):
        return 20.0

    @classmethod
    def make(cls):
        """Create the bottom part of the faceting lap holder."""

        bump_height = cls.cone_height() + (cfg.LAP_THICKNESS / 2.0)
        cone_points = [
            (cfg.LAP_AXLE_DIA / 2, 0),
            (cfg.LAP_AXLE_DIA / 2 + 2.0, 0),
            (cfg.LAP_AXLE_DIA / 2 + 2.0 + cls.cone_height(), cls.cone_height()),
            (cfg.LAP_HOLE_DIA / 2 - 0.1, cls.cone_height()),
            (cfg.LAP_HOLE_DIA / 2 - 0.1, bump_height),
            (cfg.LAP_AXLE_DIA / 2, bump_height)
        ]
        holder = (cq.Workplane("XZ")
                  .polyline(cone_points)
                  .close()
                  .revolve(360, (0, 0, 0), (0, 1, 0))
                  )

        return holder

    @classmethod
    def top_height(cls):
        """Return the offset for the top part."""
        return cls.cone_height() + cfg.LAP_THICKNESS  # The lap is 2 mm thick.


class LapHolderTop:
    """Class representing the top part of the faceting lap holder."""

    @classmethod
    def cone_height(cls):
        return 6.0

    @classmethod
    def cone_dia(cls):
        return 40.0

    @classmethod
    def make(cls):
        """Create the top part of the faceting lap holder."""

        cone_points = [
            (cfg.LAP_AXLE_DIA / 2, 0),
            (cfg.LAP_AXLE_DIA / 2, cls.cone_height()),
            (cfg.LAP_AXLE_DIA / 2 + 4.0, cls.cone_height()),
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
    # The ID of the drain hole.
    HOLE_ID = 6.0

    def make(self):
        """Create the splash guard."""

        guard = (cq.Workplane("XY")
                 .cylinder(
                     cfg.SG_HEIGHT + cfg.SG_THICKNESS,
                     cfg.sg_ID() / 2 + cfg.SG_THICKNESS,
                     centered=(True, True, False)
                     )
                 )

        # Create a cylinder of the right radius. Excess height, shaped by later cone.
        cutout = (guard.faces(">Z")
                  .workplane(invert=True, offset=-50)
                  .cylinder(
                      cfg.SG_HEIGHT + 100,
                      cfg.sg_ID() / 2,
                      centered=(True, True, False),
                      combine=False
                      )
                  )

        conepts = [
            (0, 0),
            (500, cfg.SG_SLOPE * 500),
            (500, 500),
            (0, 500)
        ]

        # Create slope towards drain hole.
        cutout = cutout.intersect(
            cq.Workplane("XZ", origin=(50, -50, self.THICKNESS))
            .polyline(conepts)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        ).edges().fillet(5.0)

        # Add drain hole.
        cutout = cutout.union(
            cq.Workplane("XY", origin=(50, -50, self.THICKNESS - 50))
            .cylinder(100, self.HOLE_ID / 2, centered=(True, True, False))
        ).edges().fillet(1.0)

        guard = guard.cut(cutout)

        return guard


class LapAssembly:
    """Class representing the entire faceting lap assembly."""

    def make_assembly():
        """Assemble the faceting lap components with colors for visualization."""

        assembly = (
            cq.Assembly()
            .add(
                LapHolderBottom().make(),
                name="lap_holder_bottom",
                loc=Location((0, 0, 0)),
                color=Color("red"),
            )
            .add(
                LapHolderTop().make(),
                name="lap_holder_top",
                loc=Location((0, 0, LapHolderBottom.top_height())),
                color=Color("yellow"),
            )
            .add(
                SplashGuard().make(),
                name="splash_guard",
                loc=Location((0, 0, 0)),
                color=Color("blue"),
            )
        )

        return assembly


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    cfg.validate()  # Validate the configuration before building.
    result = LapAssembly().make_assembly()
    show_object(result)
