from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Vector
import bom_part_data as bpd
import bought_bits as bb
import quill.quill_abstract as quill_abstract
from quill.quill_joint import QuillJointAli
from cadquery.func import text, compound, offset

# ═══════════════════════════════════════════════════════════════════════
# Assembly — owns all dimensions, injects into parts
# ═══════════════════════════════════════════════════════════════════════


class QuillAssemblyStandardMk1(quill_abstract.QuillAssemblyBase):
    """Standard Mk1 quill: joint with angled nubs, main block with top-loading
    6001ZZ bearings, ER11 collet shank, and 96-tooth index gear."""

    # ── Joint (fits into quill holder's U-slot) ─────────────────
    joint_shoulder_dia: float = 12.0
    joint_shoulder_gap: float = 47.5
    joint_user_nub_dia: float = 6.5
    joint_user_nub_length: float = 8.0
    joint_away_nub_dia: float = 5.5
    joint_away_nub_length: float = 5.0
    joint_hinge_height: float = 20.0
    joint_angle_indicator_height: float = 40.0
    joint_angle_indicator_thickness: float = 2.5

    # ── Base plate ──────────────────────────────────────────────
    base_plate_thickness: float = 5.0
    base_plate_x: float = 110.0
    base_plate_y: float = 70.0

    # ── Main block ─────────────────────────────────────────────
    block_length_x: float = 70.0
    block_width_y: float = 56.0
    block_height_z: float = 40.0
    block_x_offset: float = 45.0
    block_center_z: float = 25.0  # matches hinge center Z

    # ── Bearing positions (from collet end = +X end of block) ──
    collet_side_bearing_x: float = 18.0
    index_side_bearing_x: float = 52.0
    bearing_pocket_dia: float = 28.2
    bearing_pocket_depth: float = 8.5
    shank_bore_dia: float = 12.2

    # ── Bearing caps ───────────────────────────────────────────
    cap_length_x: float = 34.0
    cap_width_y: float = 28.0
    cap_thickness: float = 4.0
    cap_screw_spacing_y: float = 44.0  # M3 holes outside bearing OD

    # ── Index gear ─────────────────────────────────────────────
    index_gear_od: float = 41.3
    index_gear_teeth_width: float = 5.0
    index_gear_numbers_width: float = 8.0
    index_gear_bore: float = 12.2
    index_gear_num_teeth: int = 96
    index_gear_slot_angle: float = 30.0
    index_gear_slot_depth: float = 3.0
    index_gear_slot_width: float = 1.5

    # ── ER11 collet extension ──────────────────────────────────
    er11_shank_dia: float = 12.0
    er11_shank_length: float = 100.0

    # ═══════════════════════════════════════════════════════════
    # Assembly
    # ═══════════════════════════════════════════════════════════

    def _joint(self) -> QuillJointAli:
        return QuillJointAli(
            shoulder_dia=self.joint_shoulder_dia,
            shoulder_gap=self.joint_shoulder_gap,
            user_nub_dia=self.joint_user_nub_dia,
            user_nub_length=self.joint_user_nub_length,
            away_nub_dia=self.joint_away_nub_dia,
            away_nub_length=self.joint_away_nub_length,
            hinge_height=self.joint_hinge_height,
            angle_indicator_height=self.joint_angle_indicator_height,
            angle_indicator_thickness=self.joint_angle_indicator_thickness,
            base_plate_thickness=self.base_plate_thickness,
            base_plate_x=self.base_plate_x,
            base_plate_y=self.base_plate_y,
        )

    def _block(self) -> QuillMainBlock:
        return QuillMainBlock(
            length_x=self.block_length_x,
            width_y=self.block_width_y,
            height_z=self.block_height_z,
            center_z=self.block_center_z,
            collet_side_bearing_x=self.collet_side_bearing_x,
            index_side_bearing_x=self.index_side_bearing_x,
            bearing_pocket_dia=self.bearing_pocket_dia,
            bearing_pocket_depth=self.bearing_pocket_depth,
            shank_bore_dia=self.shank_bore_dia,
            cap_screw_spacing_y=self.cap_screw_spacing_y,
        )

    def _bearing_cap(self) -> BearingCap:
        return BearingCap(
            length_x=self.cap_length_x,
            width_y=self.cap_width_y,
            thickness=self.cap_thickness,
            screw_spacing_y=self.cap_screw_spacing_y,
            bearing_pocket_dia=self.bearing_pocket_dia,
        )

    def _index_gear(self) -> IndexGearStandardMk1:
        return IndexGearStandardMk1(
            od=self.index_gear_od,
            bore_dia=self.index_gear_bore,
            teeth_width=self.index_gear_teeth_width,
            numbers_width=self.index_gear_numbers_width,
            num_teeth=self.index_gear_num_teeth,
            slot_angle=self.index_gear_slot_angle,
            slot_depth=self.index_gear_slot_depth,
            slot_width=self.index_gear_slot_width,
        )

    def make_assembly(self) -> cq.Assembly:
        block_x = self.block_x_offset
        block = self._block()
        cap = self._bearing_cap()
        gear = self._index_gear()
        er11 = bb.StraightShankColletExtension(
            dia=self.er11_shank_dia,
            length=self.er11_shank_length,
        )

        # ER11 shank: bought_bits creates it along Z (XY workplane).
        # Rotate 90° around Y so it extends along +X (toward lap).
        er11_obj = er11.get_object().rotate((0, 0, 0), (0, 1, 0), 90)

        # Block placed +X from hinge center
        block_loc = Location(Vector(block_x, 0, 0))

        # ER11 shank: collet end at +X, shank passes through block.
        # Shank spans from (block_x + block_len - shank_len) to (block_x + block_len).
        shank_start_x = block_x + self.block_length_x - self.er11_shank_length
        er11_loc = Location(Vector(shank_start_x, 0, self.block_center_z))

        # Bearing caps sit on top of the block
        cap_z = self.block_center_z + self.block_height_z / 2
        cap_loc_collet = Location(
            Vector(
                block_x + self.collet_side_bearing_x,
                0,
                cap_z,
            )
        )
        cap_loc_index = Location(
            Vector(
                block_x + self.index_side_bearing_x,
                0,
                cap_z,
            )
        )

        # Index gear: printed flat (bore along Z), displayed facing +X.
        # Rotate 90° around Y so bore aligns with X axis.
        gear_obj = (
            gear.get_object()
            .rotate((0, 0, 0), (0, 0, 1), 180)
            .rotate((0, 0, 0), (0, 1, 0), 90)
        )
        gear_x = (
            block_x - self.index_gear_teeth_width - self.index_gear_numbers_width - 2
        )
        gear_loc = Location(Vector(gear_x, 0, self.block_center_z))

        assembly = (
            cq.Assembly()
            .add(
                self._joint().get_object(),
                name="quill_joint",
                loc=Location(Vector(0, 0, 0)),
                color=cq.Color("orange"),
            )
            .add(
                block.get_object(),
                name="main_block",
                loc=block_loc,
                color=cq.Color("blue"),
            )
            .add(
                er11_obj,
                name="er11_shank",
                loc=er11_loc,
                color=cq.Color("gray"),
            )
            .add(
                cap.get_object(),
                name="bearing_cap_collet",
                loc=cap_loc_collet,
                color=cq.Color("green"),
            )
            .add(
                cap.get_object(),
                name="bearing_cap_index",
                loc=cap_loc_index,
                color=cq.Color("green"),
            )
            .add(
                gear_obj,
                name="index_gear",
                loc=gear_loc,
                color=cq.Color("red"),
            )
        )
        return assembly

    def get_BOM(self) -> bpd.BOM:
        bom = bpd.BOM()
        bom.add(self._joint())
        bom.add(self._block())
        bom.add(self._bearing_cap(), 2)
        bom.add(self._index_gear())
        bom.add(bb.Bearing6001ZZ(name="6001ZZ Bearing"), 2)
        bom.add(
            bb.StraightShankColletExtension(
                dia=self.er11_shank_dia,
                length=self.er11_shank_length,
            )
        )
        return bom


# ═══════════════════════════════════════════════════════════════════════
# Printed parts
# ═══════════════════════════════════════════════════════════════════════


class QuillBlockBase(bpd.PrintedPart):
    """Base class for quill main blocks. Creates a rectangular block with
    a stepped cylindrical cavity: wide at both ends for bearings, narrow
    in the middle for the collet shank. Subclasses add screw holes,
    mounting features, etc."""

    def __init__(
        self,
        length: float,
        width: float,
        height: float,
        split_height: float,
        split_space: float,
        bearing_type: type[bb.BearingGeneric],
        collet_shank: bb.StraightShankColletExtension,
        name: str = "Quill Block",
    ) -> None:
        self.length = length
        self.width = width
        self.height = height
        self.split_height = split_height
        self.split_space = split_space
        self.bearing_type = bearing_type
        self.collet_shank = collet_shank
        super().__init__(name=name)

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.length, self.width, self.height,
            self.split_height, self.split_space,
            self.bearing_type, self.collet_shank,
        )

    def get_base_shape(self) -> cq.Workplane:
        """Solid block minus the bearing + shank cavity."""
        internal_length = self.length - self.bearing_type.WIDTH * 2
        block_cut = (
            cq.Workplane("YZ")
            .cylinder(
                self.bearing_type.WIDTH,
                self.bearing_type.OD / 2,
                centered=(True, True, False),
            )
            .faces(">X")
            .cylinder(
                internal_length, self.collet_shank.dia / 2 + 1, centered=(True, True, False)
            )
            .faces(">X")
            .cylinder(
                self.bearing_type.WIDTH,
                self.bearing_type.OD / 2,
                centered=(True, True, False),
            )
            .translate((0, 0, self.split_height))
        )

        block = (
            cq.Workplane("XY")
            .box(self.length, self.width, self.height, centered=(False, True, False))
            .cut(block_cut)
        )

        return block


class QuillMainBlock(QuillBlockBase):
    """Printed part: main body of the quill. Extends QuillBlockBase to add
    M3 screw holes for bearing caps on either side of each bearing."""

    def __init__(
        self,
        length_x: float,
        width_y: float,
        height_z: float,
        center_z: float,
        collet_side_bearing_x: float,
        index_side_bearing_x: float,
        bearing_pocket_dia: float,
        bearing_pocket_depth: float,
        shank_bore_dia: float,
        cap_screw_spacing_y: float,
    ) -> None:
        self.center_z = center_z
        self.collet_side_bearing_x = collet_side_bearing_x
        self.index_side_bearing_x = index_side_bearing_x
        self.bearing_pocket_dia = bearing_pocket_dia
        self.bearing_pocket_depth = bearing_pocket_depth
        self.shank_bore_dia = shank_bore_dia
        self.cap_screw_spacing_y = cap_screw_spacing_y

        # Derive QuillBlockBase params from our own.
        # split_height: Z of the cavity center, relative to block bottom (Z=0).
        # Block bottom = center_z - height_z/2, cavity center = center_z,
        # so split_height = center_z - (center_z - height_z/2) = height_z/2.
        split_height = height_z / 2
        super().__init__(
            length=length_x,
            width=width_y,
            height=height_z,
            split_height=split_height,
            split_space=0.0,
            bearing_type=bb.Bearing6001ZZ,
            collet_shank=bb.StraightShankColletExtension(
                dia=shank_bore_dia, length=length_x,
            ),
            name="Quill Main Block",
        )

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.length, self.width, self.height,
            self.center_z, self.collet_side_bearing_x,
            self.index_side_bearing_x, self.bearing_pocket_dia,
            self.bearing_pocket_depth, self.shank_bore_dia,
            self.cap_screw_spacing_y,
            self.split_height, self.bearing_type, self.collet_shank,
        )

    def _block_bottom_z(self) -> float:
        return self.center_z - self.height / 2

    def _block_top_z(self) -> float:
        return self.center_z + self.height / 2

    def get_object(self) -> cq.Workplane:
        # Start from the base shape (block with bearing + shank cavity)
        block = self.get_base_shape()
        # Translate to the correct Z (block sits on base plate, not bed)
        block = block.translate((0, 0, self._block_bottom_z()))

        # M3 screw holes — one on each Y side of each bearing
        screw_y = self.cap_screw_spacing_y / 2
        for bx in (self.collet_side_bearing_x, self.index_side_bearing_x):
            for sy in (-screw_y, screw_y):
                block = (
                    block.faces(">Z")
                    .workplane()
                    .center(bx - self.length / 2, sy)
                    .hole(3.2, self.height)
                )

        return block


class BearingCap(bpd.PrintedPart):
    """Printed part: U-shaped cap that screws onto the main block over
    a bearing. Two M3 screw holes on either side of the bearing."""

    def __init__(
        self,
        length_x: float,
        width_y: float,
        thickness: float,
        screw_spacing_y: float,
        bearing_pocket_dia: float,
    ) -> None:
        self.length_x = length_x
        self.width_y = width_y
        self.thickness = thickness
        self.screw_spacing_y = screw_spacing_y
        self.bearing_pocket_dia = bearing_pocket_dia
        super().__init__(name="Bearing Cap")

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.length_x,
            self.width_y,
            self.thickness,
            self.screw_spacing_y,
            self.bearing_pocket_dia,
        )

    def get_object(self) -> cq.Workplane:
        # Flat plate centered on bearing
        cap = cq.Workplane("XY").box(
            self.length_x, self.width_y, self.thickness, centered=(True, True, False)
        )

        # Semi-circular cutout on the bottom to cradle the bearing
        # Cut a cylinder from below, leaving the sides as screw tabs
        bearing_r = self.bearing_pocket_dia / 2 + 0.5
        cradle = (
            cq.Workplane("XY")
            .cylinder(self.thickness + 2, bearing_r, centered=(True, True, False))
            .translate((0, 0, -1))
        )
        cap = cap.cut(cradle)

        # M3 clearance holes on either Y side
        screw_y = self.screw_spacing_y / 2
        for sy in (-screw_y, screw_y):
            cap = cap.faces(">Z").workplane().center(0, sy).hole(3.4, self.thickness)

        return cap


class IndexGearStandardMk1(bpd.PrintedPart):
    """Printed part: 96-tooth index gear. Clamps onto the ER11 shank with
    a captive M3 set-screw. V-notches around perimeter for a detent pin.
    Printed flat — numbers on bottom, teeth on top. Displayed edge-on."""

    def __init__(
        self,
        od: float,
        bore_dia: float,
        teeth_width: float,
        numbers_width: float,
        num_teeth: int,
        slot_angle: float,
        slot_depth: float,
        slot_width: float,
    ) -> None:
        self.od = od
        self.bore_dia = bore_dia
        self.teeth_width = teeth_width
        self.numbers_width = numbers_width
        self.num_teeth = num_teeth
        self.slot_angle = slot_angle
        self.slot_depth = slot_depth
        self.slot_width = slot_width
        super().__init__(name="Index Gear")

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.od,
            self.bore_dia,
            self.teeth_width,
            self.numbers_width,
            self.num_teeth,
            self.slot_angle,
            self.slot_depth,
            self.slot_width,
        )

    def get_object(self) -> cq.Workplane:
        gear = cq.Workplane("XY").cylinder(
            self.teeth_width + self.numbers_width,
            self.od / 2,
            centered=(True, True, False),
        )

        # Central bore
        gear = gear.faces(">Z").workplane().hole(self.bore_dia)

        # Tick marks on bottom face
        gear = self._add_tick_marks(gear)

        # Captive M3 nut pocket + radial set-screw hole
        gear = self._add_nut_pocket(gear)

        # Slots around perimeter
        gear = self._add_teeth(gear)

        return gear

    def _get_nut_hole_angle(self):
        return 360 / 16.0  # between the numbers, and there's 8 numbers.

    def _add_teeth(self, gear: cq.Workplane) -> cq.Workplane:
        verts = []
        for x in range(self.num_teeth * 2):
            angle = math.radians(x * 360.0 / (self.num_teeth * 2))
            dist = self.od / 2 + (x % 2) * 0.8
            verts.append([math.sin(angle) * dist, math.cos(angle) * dist])

        teeth = cq.Workplane("XY").polyline(verts).close().extrude(self.teeth_width)
        return gear.union(teeth.translate((0, 0, self.numbers_width)))

    def _add_nut_pocket(self, gear: cq.Workplane) -> cq.Workplane:
        """Hex pocket for captive M3 nut + radial hole to bore."""
        radius = self.od / 2
        numbers_mid_z = self.numbers_width / 2
        nut_flat = 5.8  # M3 nut across flats + clearance
        nut_depth = 3.0
        nut_distance = radius - 10

        # Hex pocket cut into the outer surface
        pocket = (
            cq.Workplane("YZ")
            .polygon(6, nut_flat, circumscribed=True)
            .extrude(nut_depth)
            .rotate((0, 0, 0), (1, 0, 0), 0)
            .translate((nut_distance, 0, numbers_mid_z))
        )

        pocket_shaft = (
            cq.Workplane("YZ")
            .box(nut_flat, numbers_mid_z * 2, nut_depth, centered=(True, True, False))
            .translate((nut_distance, 0, 0))
        )
        pocket = pocket.union(pocket_shaft)

        # Radial hole from pocket bottom to central bore
        radial = (
            cq.Workplane("YZ")
            .circle(3.2 / 2)
            .extrude(self.od)
            .translate((0, 0, numbers_mid_z))
        )
        pocket = pocket.union(radial).rotate(
            (0, 0, 0), (0, 0, 1), -self._get_nut_hole_angle()
        )
        gear = gear.cut(pocket)

        return gear

    def _add_tick_marks(self, gear: cq.Workplane) -> cq.Workplane:
        """Engraved tick marks on the bottom face."""
        angle_per_tooth = 360.0 / self.num_teeth
        radius = self.od / 2
        mark_depth = 0.4

        for i in range(0, self.num_teeth, 3):
            angle = angle_per_tooth * i
            is_major = i % 12 == 0
            is_mid = i % 3 == 0
            line_len = 4.0 if is_major else 2.5 if is_mid else 1.5

            mark = (
                cq.Workplane("XY")
                .box(mark_depth * 2, 0.6, line_len, centered=(True, True, False))
                .translate((radius - mark_depth, 0, 0))
                .rotate((0, 0, 0), (0, 0, 1), angle)
            )
            gear = gear.cut(mark)

            if is_major:
                print(f"Making numbah {i}!")
                # num = compound(text("15", 5))
                num_mark = (
                    cq.Workplane("XY")
                    .add(offset(text(f"{((i - 1) % self.num_teeth) + 1}", 5), 2))
                    # .extrude(2)
                    # compound(offset(text("15", 3), 3, cap=True, both=True))
                    .rotate((0, 0, 0), (0, 1, 0), 90)
                    .translate((radius - mark_depth, 0, self.numbers_width * 2 / 3))
                    .rotate((0, 0, 0), (0, 0, 1), angle)
                )
                gear = gear.cut(num_mark)

        return gear
