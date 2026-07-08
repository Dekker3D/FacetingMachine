from __future__ import annotations
import bom_part_data as bpd


class LapAssemblyBase(bpd.PartAssembly):
    def required_frame_width(self) -> float:
        raise NotImplementedError()
