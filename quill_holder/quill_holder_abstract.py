from __future__ import annotations
import cadquery as cq
import bom_part_data as bpd


class QuillHolderAssemblyBase:
    def make_assembly(self) -> cq.Assembly:
        raise NotImplementedError()

    def get_BOM(self) -> bpd.BOM:
        raise NotImplementedError()
