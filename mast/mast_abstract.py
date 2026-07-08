from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mast.mast_abstract import MastAssemblyBase


class MastAssemblyBase:
    frame_joint: object | None = None

    def set_frame_joint(self, frame_joint: object) -> None:
        self.frame_joint = frame_joint
