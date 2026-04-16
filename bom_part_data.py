from dataclasses import dataclass
from typing import Optional


@dataclass
class PartMetadata:
    """Holds metadata for a single type of part."""
    name: str
    description: Optional[str] = ""
    price: Optional[float] = 0.0
