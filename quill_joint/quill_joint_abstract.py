from __future__ import annotations
import cadquery as cq
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mast.mast_abstract import MastAssemblyBase


class QuillHolderJointBase:
    mast: MastAssemblyBase | None = None
    quill: object | None = None

    def space_needed_carriage_x(self) -> float:
        raise NotImplementedError()

    def offset_carriage_z(self) -> float:
        raise NotImplementedError()

    def add_shape(
        self, base_width: float, base_length: float
    ) -> cq.Workplane:
        raise NotImplementedError()

    def cut_shape(
        self, base_width: float, base_length: float
    ) -> cq.Workplane:
        raise NotImplementedError()
