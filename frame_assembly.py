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
            )
        )

        return assembly


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    cfg.validate()  # Validate the configuration before building.
    result = FrameAssembly().make_assembly()
    show_object(result)
