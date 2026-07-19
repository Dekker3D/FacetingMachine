from __future__ import annotations
from dataclasses import dataclass, field
from typing import Self
import cadquery as cq
import os


# ═══════════════════════════════════════════════════════════════════════
# Global part cache — same kwargs → same instance, across all files
# ═══════════════════════════════════════════════════════════════════════

_cache: dict[tuple[type, tuple[tuple[str, object], ...]], PartWithMetadata] = {}


# ═══════════════════════════════════════════════════════════════════════
# PartWithMetadata — single base for parts AND assemblies
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class PartWithMetadata:
    """Base class for every part and assembly in the project.

    Parts set ``self._assembly`` in ``__init__`` to their geometry
    (a single-shape assembly for simple parts, multi-shape for
    assemblies).  ``get_assembly()`` and ``get_BOM()`` return what
    was stored — geometry is built once, at construction time.

    Use ``PartWithMetadata.get(**kwargs)`` to get-or-create a cached
    instance.  Two call-sites with the same kwargs get the same object.
    """

    name: str = ""
    description: str = ""
    price: float = 0.0

    # Non-dataclass fields — set in __post_init__ or subclass __init__
    _object: cq.Workplane | cq.Shape | None = field(default=None, repr=False, compare=False)
    _assembly: cq.Assembly | None = field(default=None, repr=False, compare=False)
    _bom: BOM | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        # Every part starts with empty assembly and BOM.
        # Simple parts overwrite these after super().__init__().
        # Assemblies populate them with _add().
        self._assembly = cq.Assembly(name=self.name)
        self._bom = BOM()

    # ── cache ──────────────────────────────────────────────────────

    @classmethod
    def get(cls, **kwargs: object) -> Self:
        """Get or create: same kwargs → same instance, globally cached."""
        key = (cls, tuple(sorted(kwargs.items())))
        if key not in _cache:
            _cache[key] = cls(**kwargs)  # type: ignore[arg-type]
        return _cache[key]  # type: ignore[return-value]

    # ── assembly / BOM ─────────────────────────────────────────────

    def get_assembly(self) -> cq.Assembly | None:
        """Return the pre-built assembly.  Subclass __init__ must set
        ``self._assembly``."""
        return self._assembly

    def get_BOM(self) -> BOM:
        """Return the BOM.  If nothing was added (simple part), default
        to a BOM containing only this part."""
        if self._bom is not None:
            items = list(self._bom.items())
            if len(items) > 0:
                return self._bom
        return BOM(self)

    # ── assembly helper ─────────────────────────────────────────────

    def _add(
        self,
        part: PartWithMetadata,
        *,
        loc: cq.Location | tuple[float, float, float] | None = None,
        obj: cq.Workplane | cq.Shape | None = None,
        color: str | None = None,
        name: str | None = None,
    ) -> None:
        """Add a sub-part to both the assembly and the BOM.

        ``loc`` is a ``cq.Location`` (position + rotation in one object).
        ``Location(x, y, z)`` for translation only,
        ``Location(x, y, z, rx, ry, rz)`` for Euler rotation, or
        ``Location(Vector, Vector, angle)`` for axis-angle.
        A plain ``(x, y, z)`` tuple is also accepted (no rotation).
        Pass ``obj`` to supply a pre-rotated shape (bypasses
        ``get_object()``).  ``name`` defaults to the part's own name,
        lowercased.
        """
        assert self._assembly is not None, "_assembly not initialized"
        assert self._bom is not None, "_bom not initialized"
        self._bom.merge(part.get_BOM())

        # Resolve location
        if loc is None:
            loc = cq.Location()
        elif isinstance(loc, tuple):
            loc = cq.Location(cq.Vector(*loc))

        # Explicit shape override
        if obj is not None:
            self._assembly.add(
                obj,
                name=name or part.name.lower().replace(" ", "_"),
                loc=loc,
                color=cq.Color(color) if color else None,
            )
            return

        # Try the part's display assembly (preserves sub-parts, colors)
        asm = part.get_assembly()
        if asm is not None and (asm.obj is not None or len(asm.children) > 0):
            self._assembly.add(
                asm,
                name=name or part.name.lower().replace(" ", "_"),
                loc=loc,
                color=cq.Color(color) if color else None,
            )
            return

        # Fall back to raw export shape
        obj = part.get_object()
        if obj is None:
            return  # non-geometric part, BOM-only
        self._assembly.add(
            obj,
            name=name or part.name.lower().replace(" ", "_"),
            loc=loc,
            color=cq.Color(color) if color else None,
        )

    # ── geometry / identity ────────────────────────────────────────

    def get_object(self) -> cq.Workplane | cq.Shape | None:
        """Returns the exportable shape for this part.
        Set ``self._object`` in ``__init__``; return ``None`` for
        non-printable parts (assemblies, off-the-shelf without models)."""
        return self._object

    def _comparables(self) -> tuple[object, ...]:
        """Override in subclasses to include all dimension fields.

        The BOM uses __eq__/__hash__ to deduplicate parts. Override this
        to return a tuple of every field that defines the part's identity.
        Defaults to (name,).
        """
        return (self.name,)

    def __hash__(self) -> int:
        return hash(self._comparables())

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self._comparables() == other._comparables()  # type: ignore[attr-defined]


# ═══════════════════════════════════════════════════════════════════════
# PrintedPart — a PartWithMetadata that can export STL/STEP
# ═══════════════════════════════════════════════════════════════════════


class PrintedPart(PartWithMetadata):
    """A printed part with metadata."""

    def export(self, folder_path: str, formats: list[str] | None = None) -> None:
        """Export the part to various 3D formats."""
        if formats is None:
            formats = ["stl", "step"]

        obj = self.get_object()
        # Fallback: if get_object() wasn't overridden but _assembly
        # has a single shape, extract it for export.
        if obj is None and self._assembly is not None:
            shapes: list[cq.Shape] = []
            for _, child in self._assembly.traverse():
                if child.shape is not None:
                    shapes.append(child.shape)  # type: ignore[arg-type]
            if len(shapes) == 1:
                obj = shapes[0]  # type: ignore[assignment]
        if obj is None:
            print(f"Warning: No object found for printed part {self.name}")
            return

        os.makedirs(folder_path, exist_ok=True)

        safe_name = (
            "".join(c for c in self.name if c.isalnum() or c in (" ", "_", "-"))
            .rstrip()
            .replace(" ", "_")
            .lower()
        )

        for fmt in formats:
            file_path = os.path.join(folder_path, f"{safe_name}.{fmt}")
            if fmt.lower() == "stl":
                cq.exporters.export(obj, file_path)
            elif fmt.lower() == "step":
                cq.exporters.export(obj, file_path)
            else:
                print(f"Warning: Unsupported format {fmt} for {self.name}")


# ═══════════════════════════════════════════════════════════════════════
# BOM — bill of materials
# ═══════════════════════════════════════════════════════════════════════


class BOM:
    def __init__(self, singlePart: PartWithMetadata | None = None) -> None:
        self._items: dict[PartWithMetadata, int] = {}
        if singlePart is not None:
            self._items[singlePart] = 1

    def add(self, part: PartWithMetadata, qty: int = 1) -> None:
        self._items[part] = self._items.get(part, 0) + qty

    def merge(self, other: BOM, qty: int = 1) -> None:
        for part, part_qty in other._items.items():
            self.add(part, part_qty * qty)

    def items(self):
        return self._items.items()

    def tostring(self) -> str:
        """Returns a formatted string of the BOM items."""
        lines = [f"{'Name':<40} | {'Qty':<5} | {'Price':<8}"]
        lines.append("-" * 60)

        total_price = 0.0
        for part, qty in self._items.items():
            line = f"{part.name:<40} | {qty:<5}"
            if part.price != 0:
                line += f" | {part.price:<8.2f}"
                total_price += part.price * qty
            lines.append(line)

        if total_price > 0:
            lines.append("-" * 60)
            lines.append(f"{'Total':<40} | {'':<5} | {total_price:<8.2f}")

        return "\n".join(lines)

    def export_text(self, filename: str) -> None:
        """Export BOM to a text file."""
        with open(filename, "w") as f:
            f.write(self.tostring())

    def export_parts(self, folder: str, formats: list[str] | None = None) -> None:
        """Export all printed parts in the BOM."""
        for part, _qty in self._items.items():
            if isinstance(part, PrintedPart):
                part.export(folder, formats)
