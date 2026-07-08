from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Color
import bought_bits as bb
import bom_part_data as bpd
import lap.lap_abstract as lap_abstract


class LapAssembly(lap_abstract.LapAssemblyBase):
    """Class representing the entire faceting lap assembly."""

    # Lap
    LAP_HOLE_DIA: float = 12.7  # 0.5" arbor
    LAP_AXLE_DIA: float = 8.0   # 8mm shaft
    LAP_DIA: float = 152.4       # 6"
    LAP_THICKNESS: float = 2.0

    # Splash guard
    SG_EXTRA_SPACE: float = 10.0
    SG_HEIGHT: float = 30.0
    SG_THICKNESS: float = 2.0
    SG_SLOPE: float = 0.04
    SG_DRAIN_ID: float = 6.0
    SG_DRAIN_OD: float = 10.0

    # Central tower (rises above splash guard floor to keep water out)
    SG_TOWER_HEIGHT: float = 15.0
    SG_TOWER_WALL: float = 3.0
    SG_TOWER_ID: float = 50.0  # clears lap holder top cone (40mm) + adapter

    # Master lap (rigid disc under the working lap — shorter holder needed)
    USE_MASTER_LAP: bool = True
    MASTER_LAP_THICKNESS: float = 10.0

    # Drain socket
    SG_DRAIN_TUBE_ID: float = 8.0
    SG_DRAIN_TUBE_OD: float = 12.0

    _ready: bool = False
    _lhb: LapHolderBottom | None = None
    _lht: LapHolderTop | None = None
    _sg: SplashGuard | None = None
    _sgb: SplashGuardBottom | None = None

    @classmethod
    def sg_tower_OD(cls) -> float:
        return cls.SG_TOWER_ID + cls.SG_TOWER_WALL * 2

    def sg_screw_spacing(self) -> float:
        return math.ceil(self.sg_OD() * math.sqrt(0.5) / 20) * 20

    def sg_ID(self) -> float:
        return self.LAP_DIA + self.SG_EXTRA_SPACE * 2

    def sg_OD(self) -> float:
        return self.sg_ID() + self.SG_THICKNESS * 2

    def sg_tower_screw_radius(self) -> float:
        """Bolt circle radius for screws attaching SGB to tower."""
        return self.SG_TOWER_ID / 2 + self.SG_TOWER_WALL / 2

    def sg_drain_offset(self) -> float:
        """Radial distance of drain hole from center."""
        # Position the drain between the tower and the inner wall
        tower_clearance = self.sg_tower_OD() / 2 + 5
        return max(tower_clearance, 30.0)

    def required_frame_width(self) -> float:
        return self.sg_screw_spacing() + 20.0

    def ready(self) -> None:
        if not self._ready:
            self._lhb = LapHolderBottom(
                axle_dia=self.LAP_AXLE_DIA,
                lap_thickness=self.LAP_THICKNESS,
                bore_dia=self.LAP_HOLE_DIA,
                master_lap=self.USE_MASTER_LAP,
                master_lap_thickness=self.MASTER_LAP_THICKNESS,
            )
            self._lht = LapHolderTop(self.LAP_AXLE_DIA)
            self._sg = SplashGuard(self)
            self._sgb = SplashGuardBottom(self)
            self._ready = True

    def make_assembly(self) -> cq.Assembly:
        """Assemble the faceting lap components."""
        self.ready()
        assert self._lhb is not None
        assert self._lht is not None
        assert self._sg is not None
        assert self._sgb is not None

        assembly = (
            cq.Assembly()
            .add(
                self._lhb.make(),
                name="lap_holder_bottom",
                loc=Location((0, 0, self.SG_THICKNESS)),
                color=Color("red"),
            )
            .add(
                self._lht.make(),
                name="lap_holder_top",
                loc=Location((0, 0, self.SG_THICKNESS + self._lhb.top_height())),
                color=Color("yellow"),
            )
            .add(
                self._sg.make(self),
                name="splash_guard",
                loc=Location((0, 0, 0)),
                color=Color("blue"),
            )
            .add(
                self._sgb.make(self),
                name="splash_guard_bottom",
                loc=Location((0, 0, 0)),
                color=Color("green"),
            )
        )

        return assembly

    def get_BOM(self) -> bpd.BOM:
        self.ready()
        bom = bpd.BOM()
        if self._lhb:
            bom.add(self._lhb)
        if self._lht:
            bom.add(self._lht)
        if self._sg:
            bom.add(self._sg)
        if self._sgb:
            bom.add(self._sgb)
        bom.add(bb.Bearing608ZZ(name="608ZZ Bearing"), 2)  # axle bearings
        bom.add(bpd.PartWithMetadata(
            name=f"Lap Disc {self.LAP_DIA:.0f}mm",
            description="6-inch diamond grinding lap",
        ))
        if self.USE_MASTER_LAP:
            bom.add(bpd.PartWithMetadata(
                name="Master Lap 6-inch",
                description="Rigid master lap for support",
            ))
        bom.add(LapAdapter(
            shaft_dia=self.LAP_AXLE_DIA,
            arbor_dia=self.LAP_HOLE_DIA,
        ))
        return bom


# ═══════════════════════════════════════════════════════════════════════
# Lap holder
# ═══════════════════════════════════════════════════════════════════════

class LapHolderBottom(bpd.PrintedPart):
    """Conic lap holder bottom. Shorter when using a master lap."""

    def __init__(
        self,
        axle_dia: float,
        lap_thickness: float,
        bore_dia: float,
        master_lap: bool = True,
        master_lap_thickness: float = 10.0,
    ) -> None:
        self.axle_dia = axle_dia
        self.lap_thickness = lap_thickness
        self.bore_dia = bore_dia
        self.master_lap = master_lap
        self.master_lap_thickness = master_lap_thickness
        super().__init__(name="Lap Holder Bottom")

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.axle_dia, self.lap_thickness, self.bore_dia,
            self.master_lap, self.master_lap_thickness,
        )

    def cone_height(self) -> float:
        return 10.0 if self.master_lap else 20.0

    def get_object(self) -> cq.Workplane:
        """Create the bottom part of the faceting lap holder."""
        ch = self.cone_height()
        bump_height = ch + self.master_lap_thickness + self.lap_thickness / 2.0
        cone_points = [
            (self.axle_dia / 2, 0),
            (self.axle_dia / 2 + 2.0, 0),
            (self.axle_dia / 2 + 2.0 + ch, ch),
            (self.bore_dia / 2, ch),
            (self.bore_dia / 2 - 0.1, bump_height),
            (self.axle_dia / 2, bump_height),
        ]
        holder = (
            cq.Workplane("XZ")
            .polyline(cone_points)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )
        return holder

    def make(self) -> cq.Workplane:
        return self.get_object()

    def top_height(self) -> float:
        return self.cone_height() + self.master_lap_thickness + self.lap_thickness


class LapHolderTop(bpd.PrintedPart):
    """Top part of the faceting lap holder."""

    def __init__(self, axle_dia: float) -> None:
        self.axle_dia = axle_dia
        super().__init__(name="Lap Holder Top")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.axle_dia)

    def cone_height(self) -> float:
        return 6.0

    def cone_dia(self) -> float:
        return 40.0

    def get_object(self) -> cq.Workplane:
        """Create the top part of the faceting lap holder."""
        cone_points = [
            (self.axle_dia / 2, 0),
            (self.axle_dia / 2, self.cone_height()),
            (self.axle_dia / 2 + 4.0, self.cone_height()),
            (self.cone_dia() / 2, 1.0),
            (self.cone_dia() / 2, 0.0),
        ]
        holder = (
            cq.Workplane("XZ")
            .polyline(cone_points)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )
        return holder

    def make(self) -> cq.Workplane:
        return self.get_object()


class LapAdapter(bpd.PrintedPart):
    """Adapter bushing: 0.5\" lap arbor to 8mm shaft."""

    def __init__(self, shaft_dia: float = 8.0, arbor_dia: float = 12.7) -> None:
        self.shaft_dia = shaft_dia
        self.arbor_dia = arbor_dia
        super().__init__(name="Lap Arbor Adapter")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.shaft_dia, self.arbor_dia)

    def get_object(self) -> cq.Workplane:
        """Cylindrical bushing with flange."""
        flange_dia = self.arbor_dia + 6.0
        flange_thickness = 2.0
        body_length = 8.0

        adapter = (
            cq.Workplane("XY")
            # Body (goes into lap arbor)
            .cylinder(body_length, self.arbor_dia / 2 - 0.1,
                      centered=(True, True, False))
            # Flange
            .faces("<Z")
            .workplane()
            .circle(flange_dia / 2)
            .extrude(flange_thickness)
            # Shaft hole
            .faces(">Z")
            .workplane()
            .hole(self.shaft_dia)
        )
        return adapter


# ═══════════════════════════════════════════════════════════════════════
# Splash guard top
# ═══════════════════════════════════════════════════════════════════════

class SplashGuard(bpd.PrintedPart):
    """Splash guard top: large shell + central tower."""

    def __init__(self, la: LapAssembly) -> None:
        self.la: LapAssembly = la
        super().__init__(name="Splash Guard")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name,)

    def get_object(self) -> cq.Workplane:
        """Create the splash guard with central tower."""
        la = self.la
        floor_z = la.SG_THICKNESS

        # Outer shell
        guard = cq.Workplane("XY").cylinder(
            la.SG_HEIGHT + la.SG_THICKNESS,
            la.sg_ID() / 2 + la.SG_THICKNESS,
            centered=(True, True, False),
        )

        # Interior cutout (hollow with sloped floor)
        cutout = (
            guard.faces(">Z")
            .workplane(invert=True, offset=-50)
            .cylinder(
                la.SG_HEIGHT + 100,
                la.sg_ID() / 2,
                centered=(True, True, False),
                combine=False,
            )
        )

        # Slope toward drain
        conepts = [
            (0, 0),
            (500, la.SG_SLOPE * 500),
            (500, 500),
            (0, 500),
        ]
        cutout = (
            cutout.intersect(
                cq.Workplane(
                    "XZ", origin=(la.sg_drain_offset(), 0, la.SG_THICKNESS)
                )
                .polyline(conepts)
                .close()
                .revolve(360, (0, 0, 0), (0, 1, 0))
            )
            .edges()
            .fillet(5.0)
        )

        # Drain hole
        cutout = (
            cutout.union(
                cq.Workplane(
                    "XY",
                    origin=(la.sg_drain_offset(), 0, la.SG_THICKNESS - 50),
                )
                .cylinder(100, la.SG_DRAIN_ID / 2, centered=(True, True, False))
            )
            .edges()
            .fillet(1.0)
        )

        guard = guard.cut(cutout)

        # --- Central tower ---
        # Filled cylinder with inverted cone cutout. The solid ring between
        # cone and outer wall provides material for screw holes from below.
        tower_od = la.sg_tower_OD()  # e.g. 56mm
        tower_id = la.SG_TOWER_ID    # e.g. 50mm

        # The inverted cone cutout: wider at tower top, narrow at floor.
        # Clears the lap holder bottom's cone profile.
        holder_top_r = la.LAP_HOLE_DIA / 2 + 3  # clears holder + adapter
        tower_top_r = tower_id / 2

        # Cone cutout points (revolved in XZ): from tower top inward to floor
        cone_cut_pts = [
            (tower_top_r, la.SG_TOWER_HEIGHT),        # top outer (tower ID)
            (holder_top_r, la.SG_TOWER_HEIGHT),       # top inner (clears holder)
            (la.LAP_AXLE_DIA / 2 + 0.5, 0),           # floor at shaft
            (tower_top_r, 0),                          # floor outer
        ]
        cone_cutout = (
            cq.Workplane("XZ")
            .polyline(cone_cut_pts)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )

        tower = (
            cq.Workplane("XY")
            .cylinder(la.SG_TOWER_HEIGHT, tower_od / 2,
                      centered=(True, True, False))
            .translate((0, 0, floor_z))
            .cut(cone_cutout.translate((0, 0, floor_z)))
            # Shaft hole through the floor
            .faces("<Z")
            .workplane()
            .hole(la.LAP_AXLE_DIA + 0.5)
        )

        # Screw holes: 4x through the solid ring of the tower, for
        # self-tapping screws coming up from the SGB below.
        screw_r = la.sg_tower_screw_radius()
        screw_positions = [
            (screw_r * math.cos(math.radians(a)),
             screw_r * math.sin(math.radians(a)))
            for a in (45, 135, 225, 315)
        ]
        tower = (
            tower
            .faces(">Z")
            .workplane()
            .pushPoints(screw_positions)
            .hole(2.5, la.SG_TOWER_HEIGHT + 5)
        )

        guard = guard.union(tower)

        return guard

    def make(self, la: LapAssembly) -> cq.Workplane:
        return self.get_object()


# ═══════════════════════════════════════════════════════════════════════
# Splash guard bottom
# ═══════════════════════════════════════════════════════════════════════

class SplashGuardBottom(bpd.PrintedPart):
    """
    Splash guard bottom. Sits below the SGT, holds the lap shaft with
    two 608ZZ bearings, and provides a drain socket.

    Cone-shaped body for printability (printed upside-down: flat top face
    on the print bed, bearing housing and drain pointing upward).
    """

    def __init__(self, la: LapAssembly) -> None:
        self.la: LapAssembly = la
        super().__init__(name="Splash Guard Bottom")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name,)

    def get_object(self) -> cq.Workplane:
        """Create the splash guard bottom."""
        la = self.la
        bearing_od = bb.Bearing608ZZ.OD    # 22mm
        bearing_w = bb.Bearing608ZZ.WIDTH   # 7mm
        spacer_h = 10.0                     # between bearings

        bearing_stack_h = bearing_w * 2 + spacer_h

        # --- Cone body (revolved profile, like original) ---
        # Top disc radius: covers the tower + some extra for screw landings
        top_r = la.sg_tower_OD() / 2 + 5.0   # ~33mm
        # Bottom of cone: bearing housing OD
        cone_bottom_r = bearing_od / 2 + 4.0  # ~15mm
        cone_height = bearing_stack_h + 8.0   # slope down to bearing section

        cone_pts = [
            (0, 0),                     # center bottom
            (top_r, 0),                 # wide flat top (mates with SGT)
            (cone_bottom_r, -cone_height),  # cone slopes inward
            (cone_bottom_r, -(cone_height + bearing_stack_h + 5)),  # bearing section
            (0, -(cone_height + bearing_stack_h + 5)),  # center bottom
        ]

        body = (
            cq.Workplane("XZ")
            .polyline(cone_pts)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )

        # --- Shaft hole ---
        body = (
            body
            .faces("<Z")
            .workplane(origin=(0, 0, 0))
            .hole(la.LAP_AXLE_DIA + 0.3)
        )

        # --- Upper bearing recess (closest to lap, at bottom of cone) ---
        body = (
            body
            .faces("<Z")
            .workplane(origin=(0, 0, 0))
            .hole(bearing_od + 0.2, bearing_w)
        )

        # --- Lower bearing recess (at very bottom) ---
        body = (
            body
            .faces("<Z")
            .workplane(origin=(0, 0, 0))
            .hole(bearing_od + 0.2, bearing_stack_h + 5)
        )

        # --- Spacer cutout between bearings ---
        # Remove material between the two bearing recesses
        spacer_cutout_z = -(cone_height + bearing_w)
        body = (
            body
            .faces("<Z")
            .workplane(origin=(0, 0, spacer_cutout_z))
            .hole(la.LAP_AXLE_DIA + 4.0, spacer_h)
        )

        # --- Screw holes (into SGT tower from below) ---
        screw_r = la.sg_tower_screw_radius()
        screw_positions = [
            (screw_r * math.cos(math.radians(a)),
             screw_r * math.sin(math.radians(a)))
            for a in (45, 135, 225, 315)
        ]
        body = (
            body
            .faces(">Z")
            .workplane(origin=(0, 0, 0))
            .pushPoints(screw_positions)
            .cboreHole(3.2, 6.0, 3.0, top_r)  # through the flat top disc
        )

        # --- Drain: pad + channel + socket ---
        drain_x = la.sg_drain_offset()

        # Pad under the drain hole (provides material for channel)
        pad_r = la.SG_DRAIN_OD / 2 + 5.0
        pad = (
            cq.Workplane("XY")
            .workplane(offset=0)
            .transformed(offset=(drain_x, 0, 0))
            .circle(pad_r)
            .extrude(la.SG_THICKNESS + 2.0)
        )

        # Channel from drain position to +X edge (cut into the pad + body)
        channel_w = la.SG_DRAIN_TUBE_OD + 2
        channel_h = la.SG_DRAIN_TUBE_OD
        edge_x = la.sg_tower_OD() / 2 + 20
        channel = (
            cq.Workplane("XZ")
            .transformed(offset=(drain_x, 0, 0))
            .box(edge_x - drain_x + 10, channel_w, channel_h,
                 centered=(False, True, False))
            .translate((0, 0, -la.SG_THICKNESS))
        )

        # 45° socket at the +X edge
        socket_len = 20.0
        socket_r = la.SG_DRAIN_TUBE_OD / 2 + 1.0
        socket_center_z = -(la.SG_THICKNESS + channel_h / 2)

        # Build socket in its own coordinate system then translate
        socket = (
            cq.Workplane("YZ")
            .transformed(offset=(0, 0, 0))
            .workplane(offset=edge_x - 5)
            .center(0, socket_center_z)
            .circle(socket_r)
            .extrude(socket_len)
        )

        body = body.union(pad).cut(channel).cut(socket)

        return body

    def make(self, la: LapAssembly) -> cq.Workplane:
        return self.get_object()


if __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    result = LapAssembly().make_assembly()
    show_object(result)  # type: ignore[name-defined]  # noqa: F821
