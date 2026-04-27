import cadquery as cq
from cadquery import Location
from machine import MachineConfig as cfg


class FrameExtrusions:
    """Just do the extrusions in one class, fuck it."""

    @classmethod
    def make(cls):
        frame = (cq.Workplane("XZ")
                 .moveTo(cfg.frame_length() / 2 - 10, 0)
                 .box(20, 20, cfg.frame_width(), centered=(True, False, True))
                 .moveTo(-cfg.frame_length() / 2 + 10, 0)
                 .box(20, 20, cfg.frame_width(), centered=(True, False, True))
                 .chamfer(1.0)
                 )

        frame = frame.union(
            cq.Workplane("YZ")
            .moveTo(cfg.frame_width() / 2 - 10, 0)
            .box(20, 20, cfg.frame_length() - 40, centered=(True, False, True))
            .moveTo(-cfg.frame_width() / 2 + 10, 0)
            .box(20, 20, cfg.frame_length() - 40, centered=(True, False, True))
            .chamfer(1.0)
            )

        return frame


class MastRails:
    """Two smooth rods, for the mast to ride on."""

    @classmethod
    def make(cls):
        rail = (cq.Workplane("YZ", origin=(-cfg.frame_length() / 2 + 20, 0, 0))
                .moveTo(cfg.frame_rail_width() / 2, 20 - cfg.FRAME_RAIL_DIA / 2)
                .cylinder(cfg.mast_space(), 4, centered=(True, True, False))
                .moveTo(-cfg.frame_rail_width() / 2, 20 - cfg.FRAME_RAIL_DIA / 2)
                .cylinder(cfg.mast_space(), 4, centered=(True, True, False))
                )

        return rail


class MastCarriage:
    """
        Rides on the rails, holds 2020 extrusion of mast.
        Z=0 is at the top of the frame.
    """

    @classmethod
    def make(cls):
        rail_Z = -cfg.FRAME_RAIL_DIA / 2

        holder_width = cfg.MAST_EXT_WIDTH + cfg.MAST_HOLDER_THICKNESS * 2
        holder_thickness = cfg.MAST_EXT_THICKNESS + cfg.MAST_HOLDER_THICKNESS * 2

        carriage = (cq.Workplane("XY", origin=(0, 0, rail_Z + 1))
                    .box(
                        cfg.MAST_CARRIAGE_LENGTH,
                        cfg.frame_width_internal() - cfg.MAST_CARRIAGE_CLEARANCE * 2,
                        cfg.MAST_CARRIAGE_THICKNESS + cfg.FRAME_RAIL_DIA / 2 - 1,
                        centered=(True, True, False)
                        )

                    # Rail slots
                    .faces(">X")
                    .workplane(origin=(0, 0, rail_Z))
                    .moveTo(cfg.frame_rail_width() / 2, 0)
                    .hole(cfg.FRAME_RAIL_DIA)
                    .moveTo(-cfg.frame_rail_width() / 2, 0)
                    .hole(cfg.FRAME_RAIL_DIA)
                    )

        # Structure to hold mast.
        carriage = carriage.union(
            cq.Workplane("XY", origin=(0, 0, 0))
            .box(
                holder_thickness, holder_width, cfg.MAST_HOLDER_HEIGHT,
                centered=(True, True, False)
            )
        )

        cutoutPoints = [
            (-cfg.MAST_EXT_THICKNESS / 2, -cfg.MAST_EXT_WIDTH / 2),
            (cfg.MAST_EXT_THICKNESS / 2, -cfg.MAST_EXT_WIDTH / 2),
            (40, -40),
            (40, 40),
            (cfg.MAST_EXT_THICKNESS / 2, cfg.MAST_EXT_WIDTH / 2),
            (-cfg.MAST_EXT_THICKNESS / 2, cfg.MAST_EXT_WIDTH / 2)
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
    def make(cls):
        leg_pts = [
            (-cfg.FRAME_EXT_WIDTH, cfg.FRAME_EXT_HEIGHT),
            (0, cfg.FRAME_EXT_HEIGHT),
            (20, 0),
            (20, -cfg.FRAME_LEG_LENGTH),
            (0, -cfg.FRAME_LEG_LENGTH),
            (0, -20),
            (-cfg.FRAME_EXT_WIDTH, 0)
        ]

        leg = (
            cq.Workplane("YZ")
            .polyline(leg_pts)
            .close()
            .extrude(10, both=True)
            .edges("<Z")
            .fillet(3.0)  # Bottom
            .edges("|X")
            .fillet(8.0)  # Curves
            )

        leg = leg.cut(
            cq.Workplane("XY", origin=(0, -cfg.FRAME_EXT_WIDTH / 2, 0))
            .box(20, cfg.FRAME_EXT_WIDTH, cfg.FRAME_EXT_HEIGHT, centered=(True, True, False))
            )

        leg = (
            leg.faces(">Y")
            .workplane(origin=(0, 0, cfg.FRAME_EXT_HEIGHT / 2))
            .cboreHole(5.2, 8.0, 15.0, 20.0)
        )

        leg = (
            # Ugly hack. Why won't CQ let me place a new workplace in a specific position with a specific stack?
            leg.faces(cq.selectors.NearestToPointSelector((0, -10, 0)))
            .workplane(origin=(0, -10, 0), offset=20, invert=True)
            .cboreHole(5.2, 8.0, 15.0, 20.0)
        )

        return leg

    @classmethod
    def make_legs(cls):
        legs = (
            cls.make()
            .translate((cfg.frame_length() / 2 - 10 - cfg.FRAME_EXT_WIDTH, cfg.frame_width() / 2, 0))
        )

        legs = legs.mirror((1, 0, 0)).add(legs)
        legs = legs.mirror((0, 1, 0)).add(legs)

        return legs


class FrameAssembly:
    """Class representing the entire machine assembly."""

    @classmethod
    def make_assembly(cls):
        """Create the frame assembly."""

        assembly = (
            cq.Assembly()
            .add(
                FrameExtrusions.make(),
                name="frame_extrusions",
                loc=Location((0, 0, 0)),
                color=cq.Color("lightgray")
            )
            .add(
                MastRails.make(),
                name="mast_rails",
                loc=Location((0, 0, 0)),
                color=cq.Color("yellow")
            )
            .add(
                MastCarriage.make(),
                name="mast_carriage",
                loc=Location((-cfg.frame_length() / 2 + cfg.MAST_VIS_X, 0, 20)),
                color=cq.Color("red")
            )
            .add(
                FrameLeg.make_legs(),
                name="frame_leg",
                loc=Location((0, 0, 0)),
                color=cq.Color("green")
            )
        )

        return assembly


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    cfg.validate()  # Validate the configuration before building.
    result = FrameAssembly().make_assembly()
    show_object(result)
