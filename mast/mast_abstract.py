from __future__ import annotations


class MastAssemblyBase:
    frame_joint: object | None = None

    def set_frame_joint(self, frame_joint: object) -> None:
        self.frame_joint = frame_joint
