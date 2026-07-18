from __future__ import annotations
import bom_part_data as bpd


class QuillAssemblyBase(bpd.PartWithMetadata):
    """Abstract base for quill assemblies. Extends PartWithMetadata so
    all quills inherit get_assembly() and get_BOM() with caching."""
    pass
