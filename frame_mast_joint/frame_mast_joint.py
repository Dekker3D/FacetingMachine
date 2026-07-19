from __future__ import annotations
import frame_mast_joint.frame_mast_joint_abstract as fmj_abstract


class FrameMastJointSmoothRodRails(fmj_abstract.FrameMastJointBase):
    def __init__(self) -> None:
        super().__init__(name="Frame-Mast Joint (Smooth Rod Rails)")

    @classmethod
    def create(cls) -> FrameMastJointSmoothRodRails:
        return cls.get()
