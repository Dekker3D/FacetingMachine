from __future__ import annotations
import math
import cadquery as cq
import bom_part_data as bom


class BoughtPartWithModel(bom.PartWithMetadata):
    """Base class for off-the-shelf parts with a 3D model."""

    _cached_obj: cq.Workplane | None = None

    def get_object(self) -> cq.Workplane:
        """Returns a cadquery object representing this part."""
        if self._cached_obj is None:
            self._cached_obj = self._create_object()
        return self._cached_obj

    def _create_object(self) -> cq.Workplane:
        """Creates a cadquery object representing this part."""
        raise NotImplementedError()


class BearingGeneric(BoughtPartWithModel):
    WIDTH: float = 0.0
    ID: float = 0.0
    OD: float = 0.0

    def _create_object(self) -> cq.Workplane:
        return (
            cq.Workplane("XY")
            .circle(self.OD / 2)
            .extrude(self.WIDTH)
            .edges()
            .fillet(1.0)
            .faces(">Z")
            .hole(self.ID)
            .edges()
            .fillet(0.5)
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


class RailGeneric(BoughtPartWithModel):
    RAIL_WIDTH: float = 0.0
    RAIL_HEIGHT: float = 0.0
    CARRIAGE_WIDTH: float = 0.0
    CARRIAGE_LENGTH: float = 0.0
    CARRIAGE_HEIGHT: float = 0.0
    CARRIAGE_CLEARANCE: float = 0.0
    MOUNTING_HOLE_LR_SPACING: float = 0.0
    MOUNTING_HOLE_UD_SPACING: float = 0.0

    def __init__(self, length: float, name: str) -> None:
        self.length: float = length
        super().__init__(name)

    @classmethod
    def total_height(cls) -> float:
        return cls.CARRIAGE_HEIGHT + cls.CARRIAGE_CLEARANCE

    def _create_object(self) -> cq.Workplane:
        """Rail profile in canonical orientation (along +Y, top at +Z)."""
        num_holes = int(self.length / 30) + 1
        hole_positions = [(0, -i * 30) for i in range(num_holes)]
        return (
            cq.Workplane("XY")
            .box(self.RAIL_WIDTH, self.length, self.RAIL_HEIGHT,
                 centered=(True, False, False))
            .edges(">Z").fillet(0.8)
            .faces("<Z").workplane()
            .pushPoints(hole_positions)
            .circle(3.2 / 2)
            .cutThruAll()
        )

    @classmethod
    def make_carriage(cls) -> cq.Workplane:
        """Carriage in canonical orientation."""
        return (
            cq.Workplane("XY")
            .box(cls.CARRIAGE_WIDTH, cls.CARRIAGE_LENGTH, cls.CARRIAGE_HEIGHT,
                 centered=(True, False, False))
            .translate((0, 0, cls.CARRIAGE_CLEARANCE))
            .edges("|Z").fillet(1.0)
        )


class RailMGN9H(RailGeneric):
    RAIL_WIDTH = 9.0
    RAIL_HEIGHT = 6.5
    CARRIAGE_WIDTH = 20.0
    CARRIAGE_LENGTH = 39.9
    CARRIAGE_HEIGHT = 8.0
    CARRIAGE_CLEARANCE = 2.0
    MOUNTING_HOLE_LR_SPACING = 15.0
    MOUNTING_HOLE_UD_SPACING = 16.0

    def __init__(self, length: float) -> None:
        super().__init__(length, f"MGN9H Rail {length}mm")


class RailMGN15H(RailGeneric):
    RAIL_WIDTH = 15.0
    RAIL_HEIGHT = 10.0
    CARRIAGE_WIDTH = 32.0
    CARRIAGE_LENGTH = 58.8
    CARRIAGE_HEIGHT = 12.0
    CARRIAGE_CLEARANCE = 4.0
    MOUNTING_HOLE_LR_SPACING = 25.0
    MOUNTING_HOLE_UD_SPACING = 25.0

    def __init__(self, length: float) -> None:
        super().__init__(length, f"MGN15H Rail {length}mm")


class LeadScrewGeneric(BoughtPartWithModel):
    SCREW_DIA: float = 0.0
    NUT_DIA: float = 0.0
    NUT_THICKNESS: float = 0.0
    NUT_HOLE_DIA: float = 0.0
    NUT_HOLE_RADIUS: float = 0.0

    def __init__(self, length: float, name: str) -> None:
        self.length: float = length
        super().__init__(name)

    def _create_object(self) -> cq.Workplane:
        """Leadscrew shaft along +Z, starting at origin."""
        return cq.Workplane("XY").cylinder(
            self.length, self.SCREW_DIA / 2,
            centered=(True, True, False)
        )

    @classmethod
    def make_nut(cls) -> cq.Workplane:
        """T8 nut with flange and mounting holes, centered on origin."""
        nut_body = (
            cq.Workplane("XY")
            .cylinder(15, 5.1, centered=(True, True, False))
            .translate((0, 0, -(1.5 + cls.NUT_THICKNESS)))
            .chamfer(0.25)
        )
        flange = (
            cq.Workplane("XY")
            .circle(11)
            .extrude(cls.NUT_THICKNESS)
            .translate((0, 0, -cls.NUT_THICKNESS))
            .chamfer(0.5)
        )
        angles = [0, 90, 180, 270]
        hole_positions = [
            (cls.NUT_HOLE_RADIUS * math.cos(math.radians(a)),
             cls.NUT_HOLE_RADIUS * math.sin(math.radians(a)))
            for a in angles
        ]
        flange = (
            flange.faces(">Z").workplane()
            .pushPoints(hole_positions)
            .circle(cls.NUT_HOLE_DIA / 2)
            .cutThruAll()
        )
        return nut_body.union(flange)


class LeadScrewT8(LeadScrewGeneric):
    SCREW_DIA = 8.0
    NUT_DIA = 22.0
    NUT_THICKNESS = 3.5
    NUT_HOLE_DIA = 3.5
    NUT_HOLE_RADIUS = 8.0

    def __init__(self, length: float) -> None:
        super().__init__(length, f"T8 Leadscrew {length}mm")


class TslotExtrusionGeneric(BoughtPartWithModel):
    """Generic T-slot aluminum extrusion profile."""

    WIDTH: float = 0.0
    HEIGHT: float = 0.0

    def __init__(self, length: float, name: str) -> None:
        self.length: float = length
        super().__init__(name)

    def _create_object(self) -> cq.Workplane:
        """Extrusion along +Z, starting at origin."""
        return (
            cq.Workplane("XY")
            .box(self.WIDTH, self.HEIGHT, self.length,
                 centered=(True, True, False))
            .edges("|Z").chamfer(3)
        )


class TslotExtrusion2020(TslotExtrusionGeneric):
    WIDTH = 20.0
    HEIGHT = 20.0

    def __init__(self, length: float) -> None:
        super().__init__(length, f"2020 T-slot Extrusion {length}mm")


class StraightShankColletExtension(BoughtPartWithModel):
    def __init__(self, dia: float = 12.0, collet: float = 11,
                 type: str = "M", length: float = 150) -> None:
        self.name = f"C{dia}-ER{collet}{type}-{length}L"
        self.dia: float = dia
        self.collet: float = collet
        self.type: str = type
        self.length: float = length
        super().__init__(name=self.name)

    def _create_object(self) -> cq.Workplane:
        return cq.Workplane("XY").cylinder(
            self.length, self.dia / 2, centered=(True, True, False)
        )


class SmoothRod(bom.PartWithMetadata):
    """A smooth rod (off-the-shelf). No geometry, just metadata for BOM."""

    def __init__(self, diameter: float, length: float) -> None:
        self.diameter = diameter
        self.length = length
        super().__init__(name=f"Smooth Rod {diameter}x{length}mm")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.diameter, self.length)
