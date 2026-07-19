from __future__ import annotations
import bom_part_data as bpd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mast.mast_abstract import MastAssemblyBase


class FrameMastJointBase(bpd.PartWithMetadata):
    mast: MastAssemblyBase | None = None

    def set_mast(self, mast: MastAssemblyBase) -> None:
        self.mast = mast
