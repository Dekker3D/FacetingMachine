from __future__ import annotations
import cadquery as cq
import bom_part_data as bpd


class QuillAssemblyBase:
    @classmethod
    def make_assembly(cls) -> cq.Assembly:
        raise NotImplementedError()

    def get_BOM(self) -> bpd.BOM:
        raise NotImplementedError()
