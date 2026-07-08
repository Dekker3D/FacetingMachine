from __future__ import annotations
import cadquery as cq


class MastAssemblyBase:
    spine_ext_width: float = 20.0
    spine_ext_thickness: float = 20.0
    frame_joint: object | None = None

    def set_frame_joint(self, frame_joint: object) -> None:
        self.frame_joint = frame_joint

    def make_assembly(self) -> cq.Assembly:
        raise NotImplementedError()
