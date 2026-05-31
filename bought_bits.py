import bom_part_data as bom
import cadquery as cq


class BoughtPartWithModel(bom.PartWithMetadata):
    """Base class for all parts."""
    _cached_obj: cq.Workplane = None

    def get_object(self) -> cq.Workplane:
        """Returns a cadquery object representing this part."""
        if self._cached_obj is None:
            self._cached_obj = self._create_object()
        return self._cached_obj

    def _create_object(self) -> cq.Workplane:
        """Creates a cadquery object representing this part."""
        raise NotImplementedError()


class BearingGeneric(BoughtPartWithModel):
    WIDTH = 0.0
    ID = 0.0
    OD = 0.0

    def _create_object(self):
        return (
            cq.Workplane("XY")
            .circle(self.OD / 2)
            .extrude(self.WIDTH)
            .edges()
            .fillet(1.0)
        )


class Bearing608ZZ(BearingGeneric):
    name = "608ZZ Bearing"
    WIDTH = 7.0
    ID = 8.0
    OD = 22.0


class Bearing624ZZ(BearingGeneric):
    name = "624ZZ Bearing"
    WIDTH = 5.0
    ID = 4.0
    OD = 13.0


class Bearing6001ZZ(BearingGeneric):
    name = "6001ZZ Bearing"
    WIDTH = 8.0
    ID = 12.0
    OD = 28.0


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


class StraightShankColletExtension(BoughtPartWithModel):
    def __init__(self, dia: float = 12.0, collet: float = 11, type: str = "M", length: float = 150):
        self.name = F"C{dia}-ER{collet}{type}-{length}L"
        self.dia = dia
        self.collet = collet
        self.type = type
        self.length = length

    def _create_object(self):
        obj = (
            cq.Workplane("XZ")
            .cylinder(self.dia, self.length, centered=(True, True, False))
        )

        return obj
