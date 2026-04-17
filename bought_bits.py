import bom_part_data as bom
import cadquery as cq


class Part:
    """Base class for all parts."""
    _cached_obj: cq.Workplane = None
    metadata: bom.PartMetadata = None

    @classmethod
    def get_object(cls) -> cq.Workplane:
        """Returns a cadquery object representing this part."""
        if cls._cached_obj is None:
            cls._cached_obj = cls._create_object()
        return cls._cached_obj

    @classmethod
    def _create_object(cls) -> cq.Workplane:
        """Creates a cadquery object representing this part."""
        raise NotImplementedError()


class BearingGeneric(Part):
    WIDTH = 0.0
    ID = 0.0
    OD = 0.0

    @classmethod
    def _create_object(cls):
        return (
            cq.Workplane("XY")
            .circle(cls.OD / 2)
            .extrude(cls.WIDTH)
            .edges()
            .fillet(1.0)
        )


class Bearing608ZZ(BearingGeneric):
    metadata = bom.PartMetadata(name="608ZZ Bearing")
    WIDTH = 7.0
    ID = 8.0
    OD = 22.0


class Bearing624ZZ(BearingGeneric):
    metadata = bom.PartMetadata(name="624ZZ Bearing")
    WIDTH = 5.0
    ID = 4.0
    OD = 13.0
