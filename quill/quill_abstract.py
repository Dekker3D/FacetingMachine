from __future__ import annotations
import cadquery as cq


class QuillAssemblyBase:
    @classmethod
    def make_assembly(cls) -> cq.Assembly:
        raise NotImplementedError()
