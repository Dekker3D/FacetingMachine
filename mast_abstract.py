# This allows type-hinting despite circular references.
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from frame_joint_abstract import FrameMastJointBase

class MastAssemblyBase:
    frame_joint: FrameMastJointBase = None

    def set_frame_joint(self, frame_joint: FrameMastJointBase):
        self.frame_joint = frame_joint
