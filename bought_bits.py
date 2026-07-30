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
            self._object = self._cached_obj  # sync with BOM visibility
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


# ═══════════════════════════════════════════════════════════════════════
# Bolts, nuts, washers
# ═══════════════════════════════════════════════════════════════════════

# Standard dimensions for ISO metric fasteners (mm).
# Keys are nominal sizes; values are:
#   (head_dia_across_flats, head_height,
#    nut_width_across_flats, nut_thickness,
#    washer_od, washer_thickness)
_FASTENER_DIMS: dict[int, tuple[float, float, float, float, float, float]] = {
    3:  (5.5, 3.0, 5.5, 2.4, 7.0, 0.5),
    4:  (7.0, 4.0, 7.0, 3.2, 9.0, 0.8),
    5:  (8.0, 5.0, 8.0, 4.0, 10.0, 1.0),
    6:  (10.0, 6.0, 10.0, 5.0, 12.0, 1.6),
    8:  (13.0, 8.0, 13.0, 6.5, 16.0, 1.6),
    10: (17.0, 10.0, 17.0, 8.0, 20.0, 2.0),
    12: (19.0, 12.0, 19.0, 10.0, 24.0, 2.5),
}


# ── Bolt / screw ─────────────────────────────────────────────────────


class Bolt(BoughtPartWithModel):
    """Threaded fastener.  Shaft along +Z, head at origin.
    Use ``Bolt.get(size=3, length=30)`` for hex, or pass ``head``:

    - ``"hex"`` — ISO metric hex-head bolt (default)
    - ``"countersunk"`` — flat countersunk head
    - ``"pan"`` — pan / button head

    Dimension accessors let surrounding geometry query sizes without
    knowing the head type, so you can swap ``head="hex"`` for
    ``head="countersunk"`` and all clearances stay correct."""

    def __init__(self, size: float, length: float, head: str = "hex") -> None:
        self.size = size
        self.length = length
        self.head = head
        hd, hh, *_ = _FASTENER_DIMS.get(
            int(size), (size * 1.8, size, 0, 0, 0, 0),
        )
        if head == "hex":
            self._head_dia = hd
            self._head_h = hh
        elif head == "countersunk":
            self._head_dia = size * 2.0
            self._head_h = size * 0.5
        elif head == "pan":
            self._head_dia = size * 1.8
            self._head_h = size * 0.7
        else:
            raise ValueError(f"Unknown head type: {head}")
        super().__init__(name=f"M{size:.0f}×{length:.0f}mm {head} Bolt")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.size, self.length, self.head)

    # ── dimension accessors ────────────────────────────────────────

    def diameter(self) -> float:
        """Nominal thread diameter (shaft)."""
        return self.size

    def head_diameter(self) -> float:
        """Widest part of the head (across-flats for hex, OD for pan)."""
        return self._head_dia

    def head_height(self) -> float:
        """Height of the head along the shaft axis."""
        return self._head_h

    def shaft_length(self) -> float:
        """Length of the threaded shaft (below the head)."""
        return self.length

    def total_length(self) -> float:
        """Head height + shaft length."""
        return self._head_h + self.length

    # ── geometry ───────────────────────────────────────────────────

    def _create_object(self) -> cq.Workplane:
        if self.head == "hex":
            head_shape = (
                cq.Workplane("XY")
                .polygon(6, self._head_dia / 2, circumscribed=True)
                .extrude(self._head_h)
            )
        elif self.head == "countersunk":
            head_shape = (
                cq.Workplane("XY")
                .circle(self._head_dia / 2)
                .workplane(offset=self._head_h)
                .circle(self.size / 2)
                .loft()
            )
        else:  # pan
            head_shape = (
                cq.Workplane("XY")
                .cylinder(self._head_h, self._head_dia / 2,
                          centered=(True, True, False))
            )
        return head_shape.faces("<Z").workplane().cylinder(
            self.length, self.size / 2,
            centered=(True, True, False),
        )


# ── Nut ──────────────────────────────────────────────────────────────


class Nut(BoughtPartWithModel):
    """ISO metric hex nut.  Flat on XY, bore along Z.
    Use ``Nut.get(size=3)``."""

    def __init__(self, size: float) -> None:
        self.size = size
        _, _, self._width, self._thick, _, _ = _FASTENER_DIMS.get(
            int(size), (0, 0, size * 1.8, size * 0.8, 0, 0),
        )
        super().__init__(name=f"M{size:.0f} Nut")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.size)

    # ── dimension accessors ────────────────────────────────────────

    def diameter(self) -> float:
        """Bore diameter (clearance for shaft)."""
        return self.size + 0.3

    def width_across_flats(self) -> float:
        """Width across opposite flat faces (wrench size)."""
        return self._width

    def width_across_corners(self) -> float:
        """Width across opposite corners (clearance circle)."""
        return self._width / math.cos(math.radians(30))

    def height(self) -> float:
        """Thickness of the nut."""
        return self._thick

    # ── geometry ───────────────────────────────────────────────────

    def _create_object(self) -> cq.Workplane:
        return (
            cq.Workplane("XY")
            .polygon(6, self.width_across_corners())
            .extrude(self._thick)
            .faces(">Z").workplane()
            .hole(self.diameter())
        )


# ── Washer ───────────────────────────────────────────────────────────


class Washer(BoughtPartWithModel):
    """ISO metric flat washer.  Flat on XY, bore along Z.
    Use ``Washer.get(size=3)``."""

    def __init__(self, size: float) -> None:
        self.size = size
        _, _, _, _, self._od, self._thick = _FASTENER_DIMS.get(
            int(size), (0, 0, 0, 0, size * 2.2, size * 0.15),
        )
        super().__init__(name=f"M{size:.0f} Washer")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.size)

    # ── dimension accessors ────────────────────────────────────────

    def diameter(self) -> float:
        """Bore diameter (clearance for shaft)."""
        return self.size + 0.3

    def outer_diameter(self) -> float:
        """Outside diameter of the washer."""
        return self._od

    def height(self) -> float:
        """Thickness of the washer."""
        return self._thick

    # ── geometry ───────────────────────────────────────────────────

    def _create_object(self) -> cq.Workplane:
        return (
            cq.Workplane("XY")
            .cylinder(self._thick, self._od / 2,
                      centered=(True, True, False))
            .faces(">Z").workplane()
            .hole(self.diameter())
        )
