from __future__ import annotations

from dataclasses import dataclass
import math

import cadquery as cq


@dataclass(frozen=True)
class SideLoadedCaptiveNutHole:
    """Canonical cutout for a vertical bolt and side-loaded captive hex nut.

    Local ``Z=0`` is the printed-part interface where the bolt enters. The
    shaft and nut trap extend toward ``-Z``. The insertion channel opens from
    the bolt axis toward local ``+Y``. Callers rotate the completed cutout as
    part of placement when another direction is needed.
    """

    shaft_diameter: float
    shaft_depth: float
    nut_width_across_flats: float
    nut_depth: float
    nut_drop_from_interface: float
    channel_length: float

    def __post_init__(self) -> None:
        dimensions = {
            "shaft diameter": self.shaft_diameter,
            "shaft depth": self.shaft_depth,
            "nut width across flats": self.nut_width_across_flats,
            "nut depth": self.nut_depth,
            "nut drop from interface": self.nut_drop_from_interface,
            "channel length": self.channel_length,
        }
        for label, value in dimensions.items():
            if not math.isfinite(value):
                raise ValueError(f"Captive-nut {label} must be finite")
        for label, value in dimensions.items():
            if value <= 0:
                raise ValueError(f"Captive-nut {label} must be greater than 0 mm")
        nut_corner_radius = self.nut_width_across_flats / (
            2 * math.cos(math.radians(30))
        )
        if self.channel_length < nut_corner_radius:
            raise ValueError(
                "Captive-nut channel length must reach beyond the nut pocket"
            )
        if self.nut_drop_from_interface + self.nut_depth > self.shaft_depth:
            raise ValueError(
                "Captive-nut trap must fit within the bolt shaft depth"
            )

    def make_cutout(self) -> cq.Workplane:
        """Return the local bolt-path, nut-trap, and insertion-channel cutout."""
        shaft = (
            cq.Workplane("XY")
            .circle(self.shaft_diameter / 2)
            .extrude(-self.shaft_depth)
        )
        nut_width_across_corners = self.nut_width_across_flats / math.cos(
            math.radians(30)
        )
        nut_trap = (
            cq.Workplane("XY")
            .polygon(6, nut_width_across_corners)
            .extrude(-self.nut_depth)
            .rotate((0, 0, 0), (0, 0, 1), 30)
            .translate((0, 0, -self.nut_drop_from_interface))
        )
        insertion_channel = (
            cq.Workplane("XY")
            .box(
                self.nut_width_across_flats,
                self.channel_length,
                self.nut_depth,
                centered=(True, True, False),
            )
            .translate(
                (
                    0,
                    self.channel_length / 2,
                    -self.nut_drop_from_interface - self.nut_depth,
                )
            )
        )
        return shaft.union(nut_trap).union(insertion_channel)
