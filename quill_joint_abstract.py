# This allows type-hinting despite circular references.
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mast_abstract import MastAssemblyBase
    from quill_abstract import QuillAssemblyBase

class QuillHolderJointBase:
    mast: MastAssemblyBase = None
    quill: QuillAssemblyBase = None

    def space_needed_carriage_x(self):
        raise NotImplementedError()

    def offset_carriage_z(self):
        raise NotImplementedError()

    def add_shape(self, base_width, base_length):
        raise NotImplementedError()

    def cut_shape(self, base_width, base_length):
        raise NotImplementedError()