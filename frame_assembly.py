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
                 )

        frame = frame.union(
            cq.Workplane("YZ")
            .moveTo(cfg.frame_width() / 2 - 10, 0)
            .box(20, 20, cfg.frame_length() - 20, centered=(True, False, True))
            .moveTo(-cfg.frame_width() / 2 + 10, 0)
            .box(20, 20, cfg.frame_length() - 20, centered=(True, False, True))
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
    """Rides on the rails, holds 2020 extrusion of mast."""

    @classmethod
    def make(cls):
        rail_Z = 20 - cfg.FRAME_RAIL_DIA / 2

        carriage = (cq.Workplane("XY", origin=(0, 0, rail_Z + 1))
                    .box(
                        cfg.MAST_CARRIAGE_LENGTH,
                        cfg.frame_width_internal() - cfg.MAST_CARRIAGE_CLEARANCE * 2,
                        cfg.MAST_CARRIAGE_THICKNESS + cfg.FRAME_RAIL_DIA / 2 - 1,
                        centered=(True, True, False)
                        )
                    .faces(">X")
                    .workplane(centerOption="ProjectedOrigin")
                    .moveTo(cfg.frame_rail_width() / 2, -1)
                    .hole(cfg.FRAME_RAIL_DIA)
                    .moveTo(-cfg.frame_rail_width() / 2, -1)
                    .hole(cfg.FRAME_RAIL_DIA)
                    )

        carriage = carriage.cut(
            cq.Workplane("XY", origin=(cfg.MAST_CARRIAGE_LENGTH / 2 - 10, 0, 20))
            .box(cfg.MAST_CARRIAGE_LENGTH, 20.0, 20.0, centered=(True, True, False))
        )

        return carriage


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
                loc=Location((-cfg.frame_length() / 2 + cfg.MAST_VIS_X, 0, 0)),
                color=cq.Color("red")
            )
        )

        return assembly


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    cfg.validate()  # Validate the configuration before building.
    result = FrameAssembly().make_assembly()
    show_object(result)
