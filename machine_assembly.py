from __future__ import annotations
import os
import cadquery as cq

import bom_part_data as bpd
import bought_bits as bb
from lap.lap_assembly import LapAssembly
from mast.mast_assembly import MastAssembly
from frame.frame_assembly import FrameAssembly
from quill_holder.quill_holder_assembly import QuillHolderAssembly
from quill.quill_assembly import QuillAssemblyStandardMk1
from quill_holder_joint.quill_holder_joint import QuillHolderJointAli
from frame_mast_joint.frame_mast_joint import FrameMastJointSmoothRodRails


class MachineAssembly(bpd.PartWithMetadata):
    """Class representing the entire machine assembly."""

    exploded_view: bool = True
    lap: LapAssembly = LapAssembly()
    quill_er11: bb.StraightShankColletExtension = (
        bb.StraightShankColletExtension.get(dia=12.0, length=100.0)
    )
    quill: QuillAssemblyStandardMk1 = QuillAssemblyStandardMk1(
        er11=quill_er11,
        bearing_type=bb.Bearing6001ZZ,
        explode=exploded_view
    )
    quill_holder: QuillHolderAssembly = QuillHolderAssembly(
        quill=quill,
        explode=exploded_view,
    )
    quill_joint: QuillHolderJointAli = QuillHolderJointAli()
    mast: MastAssembly = MastAssembly(quill=quill_holder, quill_joint=quill_joint)
    mast_joint: FrameMastJointSmoothRodRails = FrameMastJointSmoothRodRails()
    frame: FrameAssembly = FrameAssembly(lap=lap, mast=mast, mast_joint=mast_joint)

    def validate(self) -> None:
        self.frame.validate()

    def make_assembly(self) -> cq.Assembly | None:
        """Create the entire machine assembly."""
        return self.frame.get_assembly()

    def get_BOM(self) -> bpd.BOM:
        bom = bpd.BOM()
        bom.merge(self.frame.get_BOM())
        return bom
    def export_everything(self, folder: str = "export") -> None:
        """Export all printable parts and the BOM."""
        bom = self.get_BOM()
        bom.export_parts(os.path.join(folder, "parts"))
        bom.export_text(os.path.join(folder, "BOM.txt"))
        print(f"Exported to {folder}")


if __name__ == "__cq_main__":
    import time
    t0 = time.perf_counter()

    machine = MachineAssembly()
    t1 = time.perf_counter()
    machine.validate()
    result = machine.make_assembly()
    t2 = time.perf_counter()
    show_object(result)  # type: ignore[name-defined]  # noqa: F821
    machine.export_everything()
    t3 = time.perf_counter()
    print(machine.get_BOM().tostring())
    print("\n=== Grouped ===")
    print(machine.get_BOM().tostring_grouped())

    print(f"\nTiming: init={t1-t0:.2f}s  assembly={t2-t1:.2f}s  export={t3-t2:.2f}s  total={t3-t0:.2f}s")
    print("done")
