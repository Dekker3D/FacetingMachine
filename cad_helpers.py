"""
CadQuery spatial helpers: Transforms and boolean-based spatial assertions.

Transforms: declarative placement with named reference frames.
Assertions: use native CadQuery boolean ops (intersect/cut) for exact tests.

Test patterns:
    - assert_no_overlap(a, b)           → a.intersect(b).IsNull()
    - assert_contained(part, bounds)    → part.cut(bounds).IsNull()
    - assert_clearance(part, zone)      → part.intersect(zone).IsNull()
    - assert_fits_printer(part)         → part exceeds 190x190 bed?
"""

from __future__ import annotations
from collections.abc import Callable
import cadquery as cq


# ═══════════════════════════════════════════════════════════════════════
# Boolean-based spatial assertions
# ═══════════════════════════════════════════════════════════════════════

CadQueryObj = cq.Workplane | cq.Assembly | cq.Shape


def _resolve(obj: CadQueryObj) -> cq.Shape:
    """Get a cq.Shape from various CadQuery types."""
    if isinstance(obj, cq.Assembly):
        shapes: list[cq.Shape] = []
        for _name, child in obj.traverse():
            if child.obj is not None:
                shapes.append(child.obj)
            if child.shape is not None:
                shapes.append(child.shape)
        if not shapes:
            return cq.Shape()
        result = shapes[0]
        for s in shapes[1:]:
            result = result.fuse(s)
        return result
    if hasattr(obj, 'val'):
        return obj.val()  # type: ignore[no-any-return]
    return obj  # type: ignore[return-value]


def has_volume(obj: cq.Workplane | cq.Shape, tolerance: float = 0.001) -> bool:
    """True if the shape has measurable volume (> tolerance mm³)."""
    shape = _resolve(obj)
    # CadQuery/OCP uses isNull() (lowercase) on some shape types
    is_null = shape.isNull() if hasattr(shape, 'isNull') else shape.IsNull()
    if is_null:
        return False
    try:
        return shape.Volume() > tolerance
    except Exception:
        return False


def assert_no_overlap(
    a: CadQueryObj,
    b: CadQueryObj,
    *,
    msg: str = "",
    tolerance: float = 0.001,
) -> bool:
    """Fail if parts A and B share any significant volume."""
    sa = _resolve(a)
    sb = _resolve(b)
    overlap = sa.intersect(sb)
    if has_volume(overlap, tolerance):
        vol = overlap.Volume()
        prefix = f"{msg}: " if msg else ""
        raise AssertionError(
            f"{prefix}Parts overlap by {vol:.3f} mm³. "
            f"They should not share any volume."
        )
    return True


def assert_contained(
    part: CadQueryObj,
    container: CadQueryObj,
    *,
    msg: str = "",
    tolerance: float = 0.001,
) -> bool:
    """Fail if any of 'part' extends outside 'container'."""
    sp = _resolve(part)
    sc = _resolve(container)
    outside = sp.cut(sc)
    if has_volume(outside, tolerance):
        vol = outside.Volume()
        prefix = f"{msg}: " if msg else ""
        raise AssertionError(
            f"{prefix}Part extends outside container by {vol:.3f} mm³."
        )
    return True


def assert_clearance(
    part: CadQueryObj,
    clearance_zone: CadQueryObj,
    *,
    msg: str = "",
    tolerance: float = 0.001,
) -> bool:
    """Fail if 'part' intrudes into a clearance zone."""
    sp = _resolve(part)
    sc = _resolve(clearance_zone)
    intrusion = sp.intersect(sc)
    if has_volume(intrusion, tolerance):
        vol = intrusion.Volume()
        prefix = f"{msg}: " if msg else ""
        raise AssertionError(
            f"{prefix}Part intrudes into clearance zone by {vol:.3f} mm³."
        )
    return True


def assert_fits_printer(
    part: CadQueryObj,
    *,
    bed_x: float = 200,
    bed_y: float = 200,
    margin: float = 10,
    msg: str = "",
) -> bool:
    """Fail if any part exceeds the 3D printer bed dimensions."""
    sp = _resolve(part)
    bb = sp.BoundingBox()
    max_dim = max(bed_x, bed_y) - margin

    if bb.xmax - bb.xmin > max_dim:
        prefix = f"{msg}: " if msg else ""
        raise AssertionError(
            f"{prefix}Part X span ({bb.xmax - bb.xmin:.1f}mm) exceeds "
            f"printer bed ({max_dim:.0f}mm with {margin:.0f}mm margin)."
        )
    if bb.ymax - bb.ymin > max_dim:
        prefix = f"{msg}: " if msg else ""
        raise AssertionError(
            f"{prefix}Part Y span ({bb.ymax - bb.ymin:.1f}mm) exceeds "
            f"printer bed ({max_dim:.0f}mm with {margin:.0f}mm margin)."
        )
    return True


# ═══════════════════════════════════════════════════════════════════════
# Shape factories for clearance zones
# ═══════════════════════════════════════════════════════════════════════

def clearance_cylinder(
    center: tuple[float, float, float] = (0, 0, 0),
    axis: str = "Z",
    radius: float = 5.0,
    height: float = 50.0,
) -> cq.Workplane:
    """Create a cylinder for bolt-hole or shaft clearance checking."""
    axes = {"X": "YZ", "Y": "XZ", "Z": "XY"}
    wp = axes.get(axis.upper(), "XY")
    return (
        cq.Workplane(wp)
        .cylinder(height, radius, centered=(True, True, False))
        .translate(center)
    )


def clearance_box(
    center: tuple[float, float, float] = (0, 0, 0),
    size: tuple[float, float, float] = (10, 10, 10),
) -> cq.Workplane:
    """Create a box for clearance checking."""
    return (
        cq.Workplane("XY")
        .box(*size, centered=(True, True, True))
        .translate(center)
    )


def printer_envelope(
    bed_x: float = 200,
    bed_y: float = 200,
    margin: float = 10,
    height: float = 500,
) -> cq.Workplane:
    """Create a box representing the usable printer volume."""
    usable = max(bed_x, bed_y) - margin
    return (
        cq.Workplane("XY")
        .box(usable, usable, height, centered=(True, True, False))
        .translate((0, 0, height / 2))
    )


# ═══════════════════════════════════════════════════════════════════════
# Reference frames (declarative placement)
# ═══════════════════════════════════════════════════════════════════════

class RefFrame:
    """
    A named reference frame with an origin.

    Instead of saying "in front of the mast" (ambiguous), you define a
    frame on the mast's +X face and offset from that. The frame's name
    documents the intent, and the origin provides exact coordinates.
    """

    def __init__(
        self,
        name: str,
        origin: cq.Vector | None = None,
        parent_label: str = "",
    ) -> None:
        self.name: str = name
        self.origin: cq.Vector = origin or cq.Vector(0, 0, 0)
        self.parent_label: str = parent_label

    @classmethod
    def world(cls) -> RefFrame:
        """The global coordinate frame."""
        return cls("world", cq.Vector(0, 0, 0))

    @classmethod
    def on_face(
        cls,
        parent_label: str,
        shape: cq.Workplane | cq.Shape,
        face_selector: str,
        name: str = "",
    ) -> RefFrame:
        """
        Create a frame on a specific face of a shape.

        face_selector: "+X", "-X", "+Y", "-Y", "+Z", or "-Z".
        The frame's origin is the center of that extreme face.
        """
        if hasattr(shape, 'val'):
            shape = shape.val()  # type: ignore[assignment]

        direction = face_selector.upper()
        direction_map: dict[str, tuple[cq.Vector, bool]] = {
            "+X": (cq.Vector(1, 0, 0), True),
            "-X": (cq.Vector(-1, 0, 0), True),
            "+Y": (cq.Vector(0, 1, 0), True),
            "-Y": (cq.Vector(0, -1, 0), True),
            "+Z": (cq.Vector(0, 0, 1), True),
            "-Z": (cq.Vector(0, 0, -1), True),
        }
        if direction not in direction_map:
            raise ValueError(f"Unknown direction: {face_selector}")

        vec, pick_max = direction_map[direction]
        face = shape.faces(cq.DirectionMinMaxSelector(vec, pick_max))
        center = face.Center()

        frame_name = name or f"{parent_label}.{face_selector}"
        return cls(frame_name, center, parent_label)

    def offset(self, x: float = 0, y: float = 0, z: float = 0) -> RefFrame:
        """Return a new frame offset from this one in world coordinates."""
        new_origin = self.origin + cq.Vector(x, y, z)
        return RefFrame(
            f"{self.name}+({x},{y},{z})",
            new_origin, self.parent_label,
        )

    def as_location(self) -> cq.Location:
        """Convert to a CadQuery Location for assembly placement."""
        return cq.Location(self.origin)

    def as_vector(self) -> cq.Vector:
        """Get the origin as a Vector."""
        return self.origin

    def __repr__(self) -> str:
        return (
            f"RefFrame({self.name!r}, "
            f"origin=({self.origin.x:.1f}, {self.origin.y:.1f}, "
            f"{self.origin.z:.1f}), parent={self.parent_label!r})"
        )


def gap_between(a: RefFrame, b: RefFrame, axis: str) -> float:
    """
    Signed gap between two reference frames along a world axis.

    Returns a.origin - b.origin along the given axis.
    """
    axis = axis.upper()
    val_a = getattr(a.origin, {'X': 'x', 'Y': 'y', 'Z': 'z'}[axis])
    val_b = getattr(b.origin, {'X': 'x', 'Y': 'y', 'Z': 'z'}[axis])
    return val_a - val_b


# ═══════════════════════════════════════════════════════════════════════
# Lightweight test runner
# ═══════════════════════════════════════════════════════════════════════

_test_results: dict[str, object] = {"passed": 0, "failed": 0, "errors": []}


def run_tests(test_funcs: list[Callable[[], None]]) -> bool:
    """Run a list of test functions, report results, return True if all pass."""
    global _test_results
    _test_results = {"passed": 0, "failed": 0, "errors": []}

    for fn in test_funcs:
        try:
            fn()
            _test_results["passed"] = int(_test_results["passed"]) + 1
            print(f"  OK  {fn.__name__}")
        except AssertionError as e:
            _test_results["failed"] = int(_test_results["failed"]) + 1
            _test_results["errors"] = list(_test_results["errors"]) + [(fn.__name__, str(e))]  # type: ignore[arg-type]
            print(f"  FAIL  {fn.__name__}: {e}")

    passed = int(_test_results["passed"])
    failed = int(_test_results["failed"])
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0
