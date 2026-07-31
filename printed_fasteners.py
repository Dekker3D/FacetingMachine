from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

import cadquery as cq


@dataclass(frozen=True)
class SideLoadedCaptiveNutHole:
    """Canonical cutout for a vertical bolt and side-loaded captive hex nut.

    Local ``Z=0`` is the printed-part interface where the bolt enters. The
    shaft and nut trap extend toward ``-Z``. The insertion channel opens from
    the bolt axis toward local ``+Y``. Callers rotate the completed cutout as
    part of placement when another direction is needed. An optional sacrificial
    membrane can interrupt the shaft immediately above or below the nut cavity
    so a horizontal cavity roof prints as a simple bridge; the screw breaks
    through the membrane during assembly.
    """

    shaft_diameter: float
    shaft_depth: float
    nut_width_across_flats: float
    nut_depth: float
    nut_drop_from_interface: float
    channel_length: float
    bridge_thickness: float = 0.0
    bridge_side: Literal["above_nut", "below_nut"] = "above_nut"

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
        if not math.isfinite(self.bridge_thickness):
            raise ValueError("Captive-nut bridge thickness must be finite")
        if self.bridge_thickness < 0:
            raise ValueError("Captive-nut bridge thickness cannot be negative")
        if self.bridge_side not in ("above_nut", "below_nut"):
            raise ValueError(
                "Captive-nut bridge side must be 'above_nut' or 'below_nut'"
            )
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
        if (
            self.bridge_thickness > 0
            and self.bridge_side == "above_nut"
            and self.bridge_thickness >= self.nut_drop_from_interface
        ):
            raise ValueError(
                "Captive-nut bridge above the nut must leave an entry-side shaft"
            )
        nut_bottom = self.nut_drop_from_interface + self.nut_depth
        far_shaft_start = nut_bottom + (
            self.bridge_thickness if self.bridge_side == "below_nut" else 0.0
        )
        if (
            self.bridge_thickness > 0
            and far_shaft_start >= self.shaft_depth
        ):
            raise ValueError(
                "Captive-nut bridge must leave an end-side shaft"
            )

    def _make_shaft_cutout(self) -> cq.Workplane:
        if self.bridge_thickness == 0:
            return (
                cq.Workplane("XY")
                .circle(self.shaft_diameter / 2)
                .extrude(-self.shaft_depth)
            )
        nut_bottom = self.nut_drop_from_interface + self.nut_depth
        if self.bridge_side == "above_nut":
            entry_depth = self.nut_drop_from_interface - self.bridge_thickness
            far_start = nut_bottom
        else:
            entry_depth = nut_bottom
            far_start = nut_bottom + self.bridge_thickness
        far_depth = self.shaft_depth - far_start
        entry_shaft = (
            cq.Workplane("XY")
            .circle(self.shaft_diameter / 2)
            .extrude(-entry_depth)
        )
        far_shaft = (
            cq.Workplane("XY")
            .circle(self.shaft_diameter / 2)
            .extrude(-far_depth)
            .translate((0, 0, -far_start))
        )
        return entry_shaft.union(far_shaft)

    def make_cutout(self) -> cq.Workplane:
        """Return the local bolt-path, nut-trap, and insertion-channel cutout."""
        shaft = self._make_shaft_cutout()
        # CadQuery's polygon diameter is vertex-to-vertex. Converting the
        # requested across-flats width here produces a pocket whose measured
        # local-X width remains exactly nut_width_across_flats.
        polygon_diameter_for_across_flats = (
            self.nut_width_across_flats / math.cos(math.radians(30))
        )
        nut_trap = (
            cq.Workplane("XY")
            .polygon(6, polygon_diameter_for_across_flats)
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
