from __future__ import annotations
import os
import cadquery as cq

import bom_part_data as bpd
from lap.lap_assembly import LapAssembly
from mast.mast_assembly import MastAssembly
from frame.frame_assembly import FrameAssembly
from quill_holder.quill_holder_assembly import QuillHolderAssembly
from quill.quill_assembly import QuillAssembly
from quill_holder_joint.quill_holder_joint import QuillHolderJointAli
from frame_mast_joint.frame_mast_joint import FrameMastJointSmoothRodRails


class MachineAssembly(bpd.PartAssembly):
    """Class representing the entire machine assembly."""

    frame: FrameAssembly = FrameAssembly()
    lap: LapAssembly = LapAssembly()
    mast: MastAssembly = MastAssembly()
    quill: QuillAssembly = QuillAssembly()
    quill_holder: QuillHolderAssembly = QuillHolderAssembly()
    quill_joint: QuillHolderJointAli = QuillHolderJointAli()
    mast_joint: FrameMastJointSmoothRodRails = FrameMastJointSmoothRodRails()

    frame.lap = lap
    frame.mast = mast
    frame.mast_joint = mast_joint
    mast.quill = quill_holder
    mast.quill_joint = quill_joint
    quill_holder.quill = quill

    def validate(self) -> None:
        self.frame.validate()

    def make_assembly(self) -> cq.Assembly:
        """Create the entire machine assembly."""
        return self.frame.make_assembly()

    def get_BOM(self) -> bpd.BOM:
        bom = bpd.BOM()
        bom.merge(self.frame.get_BOM())
        bom.merge(self.lap.get_BOM())
        bom.merge(self.mast.get_BOM())
        if self.mast.quill is not None:
            bom.merge(self.mast.quill.get_BOM())
        return bom
    def export_everything(self, folder: str = "export") -> None:
        """Export all printable parts and the BOM."""
        bom = self.get_BOM()
        bom.export_parts(os.path.join(folder, "parts"))
        bom.export_text(os.path.join(folder, "BOM.txt"))
        print(f"Exported to {folder}")


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    machine = MachineAssembly()
    machine.validate()
    result = machine.make_assembly()
    show_object(result)  # type: ignore[name-defined]  # noqa: F821
    machine.export_everything()
    print(machine.get_BOM().tostring())
    print("done")
