from lap.lap_assembly import LapAssembly
from mast.mast_assembly import MastAssembly
from frame.frame_assembly import FrameAssembly
from quill_joint.quill_joint import QuillHolderJointAli
from frame_mast_joint.frame_mast_joint import FrameMastJointSmoothRodRails
import bom_part_data as bpd
import os


class MachineAssembly(bpd.PartAssembly):
    """Class representing the entire machine assembly."""

    frame = FrameAssembly()
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

    def get_BOM(self) -> bpd.BOM:
        bom = bpd.BOM()
        bom.merge(self.frame.get_BOM())
        bom.merge(self.lap.get_BOM())
        # TODO: Add other components as they are updated to support get_BOM.
        return bom

    def export_everything(self, folder: str = "export"):
        """Export all printable parts and the BOM."""
        bom = self.get_BOM()
        bom.export_parts(os.path.join(folder, "parts"))
        bom.export_text(os.path.join(folder, "BOM.txt"))
        print(f"Exported to {folder}")


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    machine = MachineAssembly()
    machine.validate()  # Validate the configuration before building.
    result = machine.make_assembly()
    show_object(result)
    print(machine.get_BOM().tostring())
    print("done")
