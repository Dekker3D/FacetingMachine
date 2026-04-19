import cadquery as cq
from cadquery import Location, Color
from machine import MachineConfig as cfg


class LapHolderBottom:
    """Class representing the bottom part of the faceting lap holder."""

    CONE_HEIGHT = 10.0
    BUMP_HEIGHT = CONE_HEIGHT + 1.0

    @classmethod
    def make(cls):
        """Create the bottom part of the faceting lap holder."""

        cone_points = [
            (cfg.LAP_AXLE_DIA / 2, 0),
            (cfg.LAP_AXLE_DIA / 2 + 2.0, 0),
            (cfg.LAP_AXLE_DIA / 2 + 2.0 + cls.CONE_HEIGHT, cls.CONE_HEIGHT),
            (cfg.LAP_HOLE_DIA / 2 - 0.1, cls.CONE_HEIGHT),
            (cfg.LAP_HOLE_DIA / 2 - 0.1, cls.BUMP_HEIGHT),
            (cfg.LAP_AXLE_DIA / 2, cls.BUMP_HEIGHT)
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
        return cls.CONE_HEIGHT + cfg.LAP_THICKNESS  # The lap is 2 mm thick.


class LapHolderTop:
    """Class representing the top part of the faceting lap holder."""

    CONE_HEIGHT = 6.0
    CONE_DIA = 30.0

    @classmethod
    def make(cls):
        """Create the top part of the faceting lap holder."""

        cone_points = [
            (cfg.LAP_AXLE_DIA / 2, 0),
            (cfg.LAP_AXLE_DIA / 2, cls.CONE_HEIGHT),
            (cfg.LAP_AXLE_DIA / 2 + 2.0, cls.CONE_HEIGHT),
            (cls.CONE_DIA / 2, 1.0),
            (cls.CONE_DIA / 2, 0.0)
        ]
        holder = (cq.Workplane("XZ")
                  .polyline(cone_points)
                  .close()
                  .revolve(360, (0, 0, 0), (0, 1, 0))
                  )

        return holder


def make_assembly():
    """Assemble the faceting lap components with colors for visualization."""

    assembly = (
        cq.Assembly()
        .add(
            LapHolderBottom.make(),
            name="lap_holder_bottom",
            loc=Location((0, 0, 0)),
            color=Color("red"),
        )
        .add(
            LapHolderTop.make(),
            name="lap_holder_top",
            loc=Location((0, 0, LapHolderBottom.top_height())),
            color=Color("yellow"),
        )
    )

    return assembly


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    result = make_assembly()
    show_object(result)
