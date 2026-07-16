from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Vector
import bom_part_data as bpd
import bought_bits as bb
import quill.quill_abstract as quill_abstract
from quill.quill_joint import QuillJointAli


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
    block_x_offset: float = 15.0
    block_center_z: float = 25.0       # matches hinge center Z

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
    cap_screw_spacing_y: float = 44.0   # M3 holes outside bearing OD

    # ── Index gear ─────────────────────────────────────────────
    index_gear_od: float = 41.3
    index_gear_thickness: float = 10.0
    index_gear_bore: float = 12.2
    index_gear_num_teeth: int = 96
    index_gear_slot_angle: float = 30.0
    index_gear_slot_depth: float = 3.0
    index_gear_slot_width: float = 1.5
    index_gear_x_offset: float = 5.0

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
            thickness=self.index_gear_thickness,
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
            dia=self.er11_shank_dia, length=self.er11_shank_length,
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
        cap_loc_collet = Location(Vector(
            block_x + self.collet_side_bearing_x, 0, cap_z,
        ))
        cap_loc_index = Location(Vector(
            block_x + self.index_side_bearing_x, 0, cap_z,
        ))

        # Index gear: printed flat (bore along Z), displayed facing +X.
        # Rotate 90° around Y so bore aligns with X axis.
        gear_obj = gear.get_object().rotate((0, 0, 0), (0, 1, 0), 90)
        gear_x = block_x - self.index_gear_x_offset
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
        bom.add(bb.StraightShankColletExtension(
            dia=self.er11_shank_dia, length=self.er11_shank_length,
        ))
        return bom


# ═══════════════════════════════════════════════════════════════════════
# Printed parts
# ═══════════════════════════════════════════════════════════════════════


class QuillMainBlock(bpd.PrintedPart):
    """Printed part: main body of the quill. Houses two 6001ZZ bearings
    in top-loading pockets, has a through-bore for the ER11 shank, and
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
        self.length_x = length_x
        self.width_y = width_y
        self.height_z = height_z
        self.center_z = center_z
        self.collet_side_bearing_x = collet_side_bearing_x
        self.index_side_bearing_x = index_side_bearing_x
        self.bearing_pocket_dia = bearing_pocket_dia
        self.bearing_pocket_depth = bearing_pocket_depth
        self.shank_bore_dia = shank_bore_dia
        self.cap_screw_spacing_y = cap_screw_spacing_y
        super().__init__(name="Quill Main Block")

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.length_x, self.width_y, self.height_z,
            self.center_z, self.collet_side_bearing_x,
            self.index_side_bearing_x, self.bearing_pocket_dia,
            self.bearing_pocket_depth, self.shank_bore_dia,
            self.cap_screw_spacing_y,
        )

    def _block_bottom_z(self) -> float:
        return self.center_z - self.height_z / 2

    def _block_top_z(self) -> float:
        return self.center_z + self.height_z / 2

    def get_object(self) -> cq.Workplane:
        block = (
            cq.Workplane("XY")
            .box(self.length_x, self.width_y, self.height_z,
                 centered=(True, True, False))
            .translate((self.length_x / 2, 0, self._block_bottom_z()))
        )

        # Shank bore through entire block along X
        block = (
            block
            .faces(">X").workplane()
            .circle(self.shank_bore_dia / 2)
            .cutThruAll()
        )

        # Bearing pockets — open upward
        block = self._cut_bearing_pocket(block, self.collet_side_bearing_x)
        block = self._cut_bearing_pocket(block, self.index_side_bearing_x)

        # M3 screw holes — one on each Y side of each bearing
        screw_y = self.cap_screw_spacing_y / 2
        for bx in (self.collet_side_bearing_x, self.index_side_bearing_x):
            for sy in (-screw_y, screw_y):
                block = (
                    block
                    .faces(">Z").workplane()
                    .center(bx - self.length_x / 2, sy)
                    .hole(3.2, self.height_z)
                )

        return block

    def _cut_bearing_pocket(
        self, block: cq.Workplane, x_center: float,
    ) -> cq.Workplane:
        """Cut a blind bearing pocket from the top face, open upward."""
        return (
            block
            .faces(">Z").workplane()
            .center(x_center - self.length_x / 2, 0)
            .hole(self.bearing_pocket_dia, self.bearing_pocket_depth)
        )


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
        return (self.name, self.length_x, self.width_y, self.thickness,
                self.screw_spacing_y, self.bearing_pocket_dia)

    def get_object(self) -> cq.Workplane:
        # Flat plate centered on bearing
        cap = (
            cq.Workplane("XY")
            .box(self.length_x, self.width_y, self.thickness,
                 centered=(True, True, False))
        )

        # Semi-circular cutout on the bottom to cradle the bearing
        # Cut a cylinder from below, leaving the sides as screw tabs
        bearing_r = self.bearing_pocket_dia / 2 + 0.5
        cradle = (
            cq.Workplane("XY")
            .cylinder(self.thickness + 2, bearing_r,
                      centered=(True, True, False))
            .translate((0, 0, -1))
        )
        cap = cap.cut(cradle)

        # M3 clearance holes on either Y side
        screw_y = self.screw_spacing_y / 2
        for sy in (-screw_y, screw_y):
            cap = (
                cap
                .faces(">Z").workplane()
                .center(0, sy)
                .hole(3.4, self.thickness)
            )

        return cap


class IndexGearStandardMk1(bpd.PrintedPart):
    """Printed part: 96-tooth index gear. Clamps onto the ER11 shank with
    a captive M3 set-screw. V-notches around perimeter for a detent pin.
    Printed flat — numbers on bottom, teeth on top. Displayed edge-on."""

    def __init__(
        self,
        od: float,
        bore_dia: float,
        thickness: float,
        num_teeth: int,
        slot_angle: float,
        slot_depth: float,
        slot_width: float,
    ) -> None:
        self.od = od
        self.bore_dia = bore_dia
        self.thickness = thickness
        self.num_teeth = num_teeth
        self.slot_angle = slot_angle
        self.slot_depth = slot_depth
        self.slot_width = slot_width
        super().__init__(name="Index Gear")

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.od, self.bore_dia, self.thickness,
            self.num_teeth, self.slot_angle, self.slot_depth,
            self.slot_width,
        )

    def get_object(self) -> cq.Workplane:
        gear = (
            cq.Workplane("XY")
            .cylinder(self.thickness, self.od / 2,
                      centered=(True, True, False))
        )

        # Central bore
        gear = gear.faces(">Z").workplane().hole(self.bore_dia)

        # Slots around perimeter
        gear = self._cut_slots(gear)

        # Captive M3 nut pocket + radial set-screw hole
        gear = self._add_nut_pocket(gear)

        # Tick marks on bottom face
        gear = self._add_tick_marks(gear)

        return gear

    def _cut_slots(self, gear: cq.Workplane) -> cq.Workplane:
        """Cut 96 angled V-notches into the outer perimeter."""
        radius = self.od / 2
        angle_per_tooth = 360.0 / self.num_teeth
        slot_rad = math.radians(self.slot_angle)

        # Build a wedge cutter that bites into the perimeter.
        # The cutter is a thin triangular prism at the correct angle.
        cutter_inner = radius - self.slot_depth
        cutter_hw = self.slot_width / 2
        cutter_pts = [
            (cutter_inner, -cutter_hw),
            (cutter_inner, cutter_hw),
            (radius + 1, cutter_hw * 0.3),
            (radius + 1, -cutter_hw * 0.3),
        ]

        # Rotate the profile by slot_angle
        cos_a = math.cos(slot_rad)
        sin_a = math.sin(slot_rad)
        rotated_pts = [
            (x * cos_a - y * sin_a, x * sin_a + y * cos_a)
            for x, y in cutter_pts
        ]

        slot_cutter = (
            cq.Workplane("XY")
            .polyline(rotated_pts)
            .close()
            .extrude(self.thickness + 2)
            .translate((0, 0, -1))
        )

        for i in range(self.num_teeth):
            angle = angle_per_tooth * i
            rotated = slot_cutter.rotate((0, 0, 0), (0, 0, 1), angle)
            gear = gear.cut(rotated)

        return gear

    def _add_nut_pocket(self, gear: cq.Workplane) -> cq.Workplane:
        """Hex pocket for captive M3 nut + radial hole to bore."""
        radius = self.od / 2
        mid_z = self.thickness / 2
        nut_flat = 5.8   # M3 nut across flats + clearance
        nut_depth = 3.0

        # Hex pocket cut into the outer surface
        pocket = (
            cq.Workplane("XY")
            .circle(nut_flat / 2)
            .extrude(nut_depth)
            .translate((radius - nut_depth / 2, 0, mid_z))
        )
        gear = gear.cut(pocket)

        # Radial hole from pocket bottom to central bore
        radial = (
            cq.Workplane("YZ")
            .circle(3.2 / 2)
            .extrude(radius)
            .translate((0, 0, mid_z))
        )
        gear = gear.cut(radial)

        return gear

    def _add_tick_marks(self, gear: cq.Workplane) -> cq.Workplane:
        """Engraved tick marks on the bottom face."""
        angle_per_tooth = 360.0 / self.num_teeth
        radius = self.od / 2
        mark_depth = 0.4

        for i in range(0, self.num_teeth, 3):
            angle = angle_per_tooth * i
            rad = math.radians(angle)
            is_major = (i % 12 == 0)
            line_len = 4.0 if is_major else 2.5
            inner_r = radius - 1.0
            outer_r = inner_r - line_len
            mid_r = (inner_r + outer_r) / 2
            x = mid_r * math.cos(rad)
            y = mid_r * math.sin(rad)

            mark = (
                cq.Workplane("XY")
                .box(line_len, 0.6, mark_depth + 0.1,
                     centered=(True, True, False))
                .translate((x, y, -0.05))
                .rotate((0, 0, 0), (0, 0, 1), angle)
            )
            gear = gear.cut(mark)

        return gear
