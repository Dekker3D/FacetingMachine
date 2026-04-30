# This allows easier type-hinting.
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mast.mast_abstract import MastAssemblyBase

class FrameMastJointBase:
    mast: MastAssemblyBase = None
    
    def set_mast(self, mast: MastAssemblyBase):
        self.mast = mast
