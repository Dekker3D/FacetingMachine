from __future__ import annotations
import cadquery as cq
import bom_part_data as bpd


class MastAssemblyBase(bpd.PartWithMetadata):
    """Abstract base for mast assemblies."""
    spine_ext_width: float = 20.0
    spine_ext_thickness: float = 20.0
    frame_joint: object | None = None
