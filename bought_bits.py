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


class RailGeneric:
    RAIL_WIDTH = 0
    RAIL_HEIGHT = 0
    CARRIAGE_WIDTH = 0
    CARRIAGE_LENGTH = 0
    CARRIAGE_HEIGHT = 0
    CARRIAGE_CLEARANCE = 0  # Below carriage
    MOUNTING_HOLE_LR_SPACING = 0  # Left/right spacing
    MOUNTING_HOLE_UD_SPACING = 0  # Up/down spacing

    @classmethod
    def total_height(cls):
        return cls.CARRIAGE_HEIGHT + cls.CARRIAGE_CLEARANCE


class RailMGN9H(RailGeneric):
    RAIL_WIDTH = 9.0
    RAIL_HEIGHT = 6.5
    CARRIAGE_WIDTH = 20.0
    CARRIAGE_LENGTH = 39.9
    CARRIAGE_HEIGHT = 8.0
    CARRIAGE_CLEARANCE = 2.0
    MOUNTING_HOLE_LR_SPACING = 15.0
    MOUNTING_HOLE_UD_SPACING = 16.0


class RailMGN15H(RailGeneric):
    RAIL_WIDTH = 15.0
    RAIL_HEIGHT = 10.0
    CARRIAGE_WIDTH = 32.0
    CARRIAGE_LENGTH = 58.8
    CARRIAGE_HEIGHT = 12.0
    CARRIAGE_CLEARANCE = 4.0
    MOUNTING_HOLE_LR_SPACING = 25.0
    MOUNTING_HOLE_UD_SPACING = 25.0


class LeadScrewGeneric:
    SCREW_DIA = 0
    NUT_DIA = 0
    NUT_THICKNESS = 0
    NUT_HOLE_DIA = 0
    NUT_HOLE_RADIUS = 0  # Distance from center to hole


class LeadScrewT8(LeadScrewGeneric):
    SCREW_DIA = 8.0
    NUT_DIA = 22.0
    NUT_THICKNESS = 3.5
    NUT_HOLE_DIA = 3.5
    NUT_HOLE_RADIUS = 8.0
