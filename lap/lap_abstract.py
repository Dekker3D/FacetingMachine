from __future__ import annotations
import cadquery as cq
import bom_part_data as bpd


class LapAssemblyBase(bpd.PartWithMetadata):
    def required_frame_width(self) -> float:
        raise NotImplementedError()

    def sg_OD(self) -> float:
        raise NotImplementedError()

    def make_assembly(self) -> cq.Assembly:
        raise NotImplementedError()
