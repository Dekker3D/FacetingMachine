from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mast.mast_abstract import MastAssemblyBase


class FrameMastJointBase:
    mast: MastAssemblyBase | None = None

    def set_mast(self, mast: MastAssemblyBase) -> None:
        self.mast = mast
