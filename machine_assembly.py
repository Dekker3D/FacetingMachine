from lap.lap_assembly import LapAssembly
from mast.mast_assembly import MastAssembly
from frame.frame_assembly import FrameAssembly
from quill_joint.quill_joint import QuillHolderJointAli
from frame_mast_joint.frame_mast_joint import FrameMastJointSmoothRodRails


class MachineAssembly:
    """Class representing the entire machine assembly."""

    frame = FrameAssembly()
    frame.set_mast_joint(MastAssembly())
    lap = LapAssembly()
    mast = MastAssembly()
    quill_joint = QuillHolderJointAli()
    mast_joint = FrameMastJointSmoothRodRails()

    frame.lap = lap
    frame.mast = mast
    frame.mast_joint = mast_joint
    mast.quill_joint = quill_joint

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
