from lap_assembly import LapAssembly
from mast_design import MastAssembly
from frame_assembly import FrameAssembly
import cadquery as cq
from cadquery import Location
from machine import MachineConfig as cfg


class MachineAssembly:
    """Class representing the entire machine assembly."""

    @classmethod
    def make_assembly(cls):
        """Create the entire machine assembly."""

        assembly = (
            cq.Assembly()
            .add(
                FrameAssembly.make_assembly(),
                name="frame_assembly",
                loc=Location((0, 0, 0)),
            )
            .add(
                LapAssembly.make_assembly(),
                name="lap_assembly",
                loc=Location((cfg.frame_length() / 2 - cfg.lap_pos_from_side(), 0, 20)),
            )
            .add(
                MastAssembly.make_assembly(),
                name="mast_assembly",
                loc=Location((-cfg.frame_length() / 2 + 50, 0, 20)),
            )
        )

        return assembly


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    cfg.validate()  # Validate the configuration before building.
    result = MachineAssembly().make_assembly()
    show_object(result)
