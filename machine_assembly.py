from lap_assembly import LapAssembly
from mast_assembly import MastAssembly
from frame_assembly import FrameAssembly


class MachineAssembly:
    """Class representing the entire machine assembly."""

    frame = FrameAssembly()
    lap = LapAssembly()
    mast = MastAssembly()

    frame.lap_assembly = lap
    frame.mast_assembly = mast

    def validate(self):
        self.frame.validate()

    def make_assembly(self):
        """Create the entire machine assembly."""

        assembly = self.frame.make_assembly()

        return assembly


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    machine = MachineAssembly()
    machine.validate()  # Validate the configuration before building.
    result = machine.make_assembly()
    show_object(result)
