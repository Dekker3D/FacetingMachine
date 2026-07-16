from __future__ import annotations
import cadquery as cq


class QuillJointBase:
    """Abstract base for the quill's hinge joint — the nubs/shoulders that
    fit into the quill holder's U-slot. Different quills may have different
    nub sizes."""

    def get_object(self) -> cq.Workplane:
        raise NotImplementedError()
