from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mast.mast_abstract import MastAssemblyBase


class FrameAssemblyBase:
    lap: object = None
    mast: MastAssemblyBase | None = None

    def frame_width(self) -> float:
        raise NotImplementedError()

    def frame_width_internal(self) -> float:
        raise NotImplementedError()

    def frame_rail_width(self) -> float:
        raise NotImplementedError()

    def mast_space(self) -> float:
        raise NotImplementedError()

    def frame_length(self) -> float:
        raise NotImplementedError()

    def lap_pos_from_left(self) -> float:
        raise NotImplementedError()

    def lap_space_from_left(self) -> float:
        raise NotImplementedError()

    def validate(self) -> None:
        raise NotImplementedError()
