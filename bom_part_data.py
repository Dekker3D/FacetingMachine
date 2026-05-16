from dataclasses import dataclass
from typing import Optional


@dataclass
class PartWithMetadata:
    """Holds metadata for a single type of part."""
    name: str
    description: Optional[str] = ""
    price: float = 0.0  # Can be overridden.


class PrintedPart(PartWithMetadata):
    """A printed part with metadata."""

    def export(folderPath: str):
        raise NotImplementedError()


class PartAssembly:
    def get_BOM(self) -> 'BOM':
        raise NotImplementedError()


class BOM:
    def __init__(self, singlePart: PartWithMetadata = None):
        self._items: dict[PartWithMetadata, int] = {}  # part -> quantity
        if singlePart is not None:
            self._items[singlePart] = 1

    def add(self, part: PartWithMetadata, qty: int=1):
        self._items[part] = self._items.get(PrintedPart, 0) + qty

    def merge(self, other: 'BOM', qty: int = 1):
        for part, part_qty in other._items.items():
            self.add(part, part_qty * qty)
    
    def items(self):
        return self._items.items()

    def tostring(self) -> str:
        """Returns a formatted string of the BOM items."""
        price: float = 0.0
        lines = [
            f"{part.name:<40} | {qty:<10}" + (f" | {part.price:<10.2f}" if part.price != 0 else "")
            for part, qty in self._items.items()
        ]
        return "\n".join(lines)