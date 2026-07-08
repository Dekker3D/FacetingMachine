from __future__ import annotations
from dataclasses import dataclass
import cadquery as cq
import os


@dataclass
class PartWithMetadata:
    """Holds metadata for a single type of part."""

    name: str
    description: str = ""
    price: float = 0.0

    def get_object(self) -> cq.Workplane | None:
        """Returns the CadQuery object for this part, if it has one."""
        return None

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


class PrintedPart(PartWithMetadata):
    """A printed part with metadata."""

    def export(self, folder_path: str, formats: list[str] | None = None) -> None:
        """Export the part to various 3D formats."""
        if formats is None:
            formats = ["stl", "step"]

        obj = self.get_object()
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


class PartAssembly:
    def get_BOM(self) -> BOM:
        raise NotImplementedError()


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
