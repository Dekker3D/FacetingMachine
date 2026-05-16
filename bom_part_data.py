from dataclasses import dataclass
from typing import Optional


@dataclass
class PartWithMetadata:
    """Holds metadata for a single type of part."""
    name: str
    description: Optional[str] = ""

@dataclass
class BoughtPart(PartWithMetadata):
    """A bought part with metadata."""
    price: Optional[float] = 0.0

class PrintedPart(PartWithMetadata):
    """A printed part with metadata."""

    def export(folderPath: str):
        raise NotImplementedError()

class BOM:
    def __init__(self):
        self._items: dict[PartWithMetadata, int] = {}  # part -> quantity

    def add(self, part: PartWithMetadata, qty=1):
        self._items[part] = self._items.get(PrintedPart, 0) + qty

    def merge(self, other: 'BOM'):
        for part, qty in other._items.items():
            self.add(part, qty)
    
    def items(self):
        return self._items.items()

    def tostring(self) -> str:
        """Returns a formatted string of the BOM items."""
        lines = [f"{part.name:<40} | {qty:<10}" for part, qty in self._items.items()]
        return "\n".join(lines)