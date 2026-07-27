from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Vector
import bom_part_data as bpd
import bought_bits as bb
import quill.quill_abstract as quill_abstract
from quill.quill_joint import QuillAngleIndicator, QuillJointAli
from cadquery.func import text, compound, offset


# ═══════════════════════════════════════════════════════════════════════
# Assembly — owns all dimensions, injects into parts
# ═══════════════════════════════════════════════════════════════════════


class QuillAssemblyStandardMk1(quill_abstract.QuillAssemblyBase):
    """Standard Mk1 quill: joint with angled nubs, main block with top-loading
    6001ZZ bearings, ER11 collet shank, and 96-tooth index gear.

    Geometry and sub-parts are built once during __init__ and cached.
    Use ``get_assembly()`` and ``get_BOM()`` from the base class."""

    # ── Joint (fits into quill holder's U-slot) ─────────────────
    joint_shoulder_dia: float = 12.0
    joint_shoulder_gap: float = 47.5
    joint_shoulder_thickness: float = 3.0
    joint_user_nub_dia: float = 6.5
    joint_user_nub_length: float = 8.0
    joint_away_nub_dia: float = 5.5
    joint_away_nub_length: float = 5.0
    joint_hinge_height: float = 20.0
    joint_angle_indicator_height: float = 40.0
    joint_angle_indicator_thickness: float = 8.0
    joint_magnet_pocket_dia: float = 3.7
    # 4.75 mm from the nub's top puts the midpoint of a 3.0 mm magnet stack
    # on the nub's Z centreline while keeping the pocket close to the Y end.
    joint_magnet_pocket_depth: float = 4.75

    # ── Base plate ──────────────────────────────────────────────
    base_plate_thickness: float = 5.0
    base_plate_x: float = 110.0
    base_plate_y: float = 70.0

    # ── Main block ─────────────────────────────────────────────
    block_width_y: float = 56.0
    # Bearing centre is at Z=25; 39.2 leaves 0.1 mm radial clearance above
    # a 28 mm bearing when the cap closes the top-loading pocket.
    block_height_z: float = 39.2
    block_x_offset: float = 45.0
    block_center_z: float = 25.0

    # ── Bearing geometry ───────────────────────────────────────
    bearing_pocket_dia: float = 28.2
    bearing_pocket_depth: float = 8.5
    shank_bore_dia: float = 12.2

    # ── Bearing holders ─────────────────────────────────────────
    bearing_holder_length_x: float = 16.0
    bearing_holder_split_gap: float = 2.0
    bearing_holder_screw_spacing_y: float = 44.0

    # ── Index gear ─────────────────────────────────────────────
    index_gear_od: float = 41.3
    index_gear_teeth_width: float = 5.0
    index_gear_numbers_width: float = 8.0
    index_gear_spacer_width: float = 2.0
    index_gear_bore: float = 12.2
    index_gear_num_teeth: int = 96
    index_gear_slot_angle: float = 30.0
    index_gear_slot_depth: float = 3.0
    index_gear_slot_width: float = 1.5

    # ── ER11 collet extension ──────────────────────────────────
    er11_shank_dia: float = 12.0
    er11_shank_length: float = 100.0
    index_side_shank_exposure: float = 10.0

    @classmethod
    def index_gear_width(cls) -> float:
        return (
            cls.index_gear_teeth_width
            + cls.index_gear_numbers_width
            + cls.index_gear_spacer_width
        )

    @classmethod
    def block_length_x(cls) -> float:
        return (
            cls.er11_shank_length
            - cls.index_gear_width()
            - cls.index_side_shank_exposure
        )

    @classmethod
    def index_side_bearing_x(cls) -> float:
        # Bearing models start at their local origin and extend toward +X.
        return 0.0

    @classmethod
    def collet_side_bearing_x(cls) -> float:
        return cls.block_length_x() - bb.Bearing6001ZZ.WIDTH

    def __init__(self, explode: bool = False) -> None:
        super().__init__(name="Quill Assembly")
        self.explode = explode
        self._current_group = self.name  # group sub-parts under this assembly

        # Sub-parts (cached via create() → get())
        joint = QuillJointAli.create(
            shoulder_dia=self.joint_shoulder_dia,
            shoulder_gap=self.joint_shoulder_gap,
            shoulder_thickness=self.joint_shoulder_thickness,
            user_nub_dia=self.joint_user_nub_dia,
            user_nub_length=self.joint_user_nub_length,
            away_nub_dia=self.joint_away_nub_dia,
            away_nub_length=self.joint_away_nub_length,
            hinge_height=self.joint_hinge_height,
            angle_indicator_height=self.joint_angle_indicator_height,
            angle_indicator_thickness=self.joint_angle_indicator_thickness,
            magnet_pocket_dia=self.joint_magnet_pocket_dia,
            magnet_pocket_depth=self.joint_magnet_pocket_depth,
            base_plate_thickness=self.base_plate_thickness,
            base_plate_x=self.base_plate_x,
            base_plate_y=self.base_plate_y,
        )
        angle_indicator = QuillAngleIndicator.create(
            shoulder_dia=self.joint_shoulder_dia,
            away_nub_dia=self.joint_away_nub_dia,
            hinge_z=self.base_plate_thickness + self.joint_hinge_height,
            height=self.joint_angle_indicator_height,
            thickness=self.joint_angle_indicator_thickness,
        )
        block = QuillMainBlock.create(
            length_x=self.block_length_x(),
            width_y=self.block_width_y,
            height_z=self.block_height_z,
            split_height=self.block_center_z,
            collet_side_bearing_x=self.collet_side_bearing_x(),
            index_side_bearing_x=self.index_side_bearing_x(),
            bearing_pocket_dia=self.bearing_pocket_dia,
            bearing_pocket_depth=self.bearing_pocket_depth,
            shank_bore_dia=self.shank_bore_dia,
            holder_length_x=self.bearing_holder_length_x,
            holder_split_gap=self.bearing_holder_split_gap,
            bearing_holder_screw_spacing_y=self.bearing_holder_screw_spacing_y,
        )
        away_shoulder_inner_y = (
            # Repeated AI mistake: using shoulder_joint_thickness instead of
            # joint_angle_indicator_thickness.
            -self.joint_shoulder_gap / 2 + self.joint_angle_indicator_thickness
        )
        body = QuillBody(
            main_block=block,
            joint=joint,
            angle_indicator=angle_indicator,
            block_x=self.block_x_offset,
            indicator_y=away_shoulder_inner_y,
        )
        bearing_holder = QuillBearingHolder.create(
            quill_block=block,
            holder_length_x=self.bearing_holder_length_x,
            holder_split_gap=self.bearing_holder_split_gap,
            screw_spacing_y=self.bearing_holder_screw_spacing_y,
        )
        gear = IndexGearStandardMk1.create(
            od=self.index_gear_od,
            bore_dia=self.index_gear_bore,
            teeth_width=self.index_gear_teeth_width,
            numbers_width=self.index_gear_numbers_width,
            spacer_width=self.index_gear_spacer_width,
            num_teeth=self.index_gear_num_teeth,
            slot_angle=self.index_gear_slot_angle,
            slot_depth=self.index_gear_slot_depth,
            slot_width=self.index_gear_slot_width,
        )
        er11 = bb.StraightShankColletExtension.get(
            dia=self.er11_shank_dia,
            length=self.er11_shank_length,
        )

        # ── Assemble ────────────────────────────────────────────
        # Reminder: we're subtracing self.block_center_z from the Z of all parts, to line up with the joint.
        block_x = self.block_x_offset
        shank_start_x = block_x + self.block_length_x() - self.er11_shank_length
        gear_x = block_x - self.index_gear_width()

        self._add(body, loc=Location(0, 0, -self.block_center_z))
        # Exploded display placement does not affect the true cutout position.
        indicator_display_y = away_shoulder_inner_y - (
            20.0 if self.explode else 0.0
        )
        self._add(
            angle_indicator,
            loc=Location(
                0.0,
                indicator_display_y,
                -self.block_center_z,
                90,
                0,
                0,
            ),
            name="angle_indicator",
        )
        self._add(er11, loc=Location(Vector(shank_start_x, 0, 0), Vector(0, 1, 0), 90),
                  color="gray")
        self._add(
            bearing_holder,
            loc=Location(block_x, 0, -self.block_center_z),
            name="bearing_holder_index",
        )
        far_holder_obj = bearing_holder.get_object()
        if not isinstance(far_holder_obj, cq.Workplane):
            raise TypeError("QuillBearingHolder must provide Workplane geometry")
        far_holder_obj = far_holder_obj.rotate((0, 0, 0), (0, 0, 1), 180)
        self._add(
            bearing_holder,
            obj=far_holder_obj,
            loc=Location(block_x + self.block_length_x(), 0, -self.block_center_z),
            name="bearing_holder_collet",
        )
        gear_obj = (
            gear.get_object()
            .rotate((0, 0, 0), (0, 0, 1), 180)  # type: ignore[union-attr]
            .rotate((0, 0, 0), (0, 1, 0), 90)    # type: ignore[union-attr]
        )
        self._add(gear, obj=gear_obj,
                  loc=Location(gear_x, 0, 0))


# ═══════════════════════════════════════════════════════════════════════
# Printed parts
# ═══════════════════════════════════════════════════════════════════════


class QuillMainBlock:
    """Geometry helper shared by the printable quill body and bearing holders."""

    @classmethod
    def create(
        cls,
        length_x: float,
        width_y: float,
        height_z: float,
        split_height: float,
        collet_side_bearing_x: float,
        index_side_bearing_x: float,
        bearing_pocket_dia: float,
        bearing_pocket_depth: float,
        shank_bore_dia: float,
        holder_length_x: float,
        holder_split_gap: float,
        bearing_holder_screw_spacing_y: float,
    ) -> QuillMainBlock:
        return cls(
            length_x=length_x,
            width_y=width_y,
            height_z=height_z,
            split_height=split_height,
            collet_side_bearing_x=collet_side_bearing_x,
            index_side_bearing_x=index_side_bearing_x,
            bearing_pocket_dia=bearing_pocket_dia,
            bearing_pocket_depth=bearing_pocket_depth,
            shank_bore_dia=shank_bore_dia,
            holder_length_x=holder_length_x,
            holder_split_gap=holder_split_gap,
            bearing_holder_screw_spacing_y=bearing_holder_screw_spacing_y,
        )

    def __init__(
        self,
        length_x: float,
        width_y: float,
        height_z: float,
        split_height: float,
        collet_side_bearing_x: float,
        index_side_bearing_x: float,
        bearing_pocket_dia: float,
        bearing_pocket_depth: float,
        shank_bore_dia: float,
        holder_length_x: float,
        holder_split_gap: float,
        bearing_holder_screw_spacing_y: float,
    ) -> None:
        self.length = length_x
        self.width = width_y
        self.height = height_z
        self.split_height = split_height
        self.collet_side_bearing_x = collet_side_bearing_x
        self.index_side_bearing_x = index_side_bearing_x
        self.bearing_pocket_dia = bearing_pocket_dia
        self.bearing_pocket_depth = bearing_pocket_depth
        self.shank_bore_dia = shank_bore_dia
        self.holder_length_x = holder_length_x
        self.holder_split_gap = holder_split_gap
        self.bearing_holder_screw_spacing_y = bearing_holder_screw_spacing_y
        self.bearing_type = bb.Bearing6001ZZ
        self.collet_shank = bb.StraightShankColletExtension(
            dia=shank_bore_dia,
            length=length_x,
        )

        obj = self.get_base_shape().cut(self.bearing_holder_cut_boxes())
        screw_y = self.bearing_holder_screw_spacing_y / 2
        screw_x_positions = (
            self.collet_side_bearing_x + self.bearing_type.WIDTH / 2,
            self.index_side_bearing_x + self.bearing_type.WIDTH / 2,
        )
        screw_positions = [
            (screw_x, side_y)
            for screw_x in screw_x_positions
            for side_y in (-screw_y, screw_y)
        ]
        self._object = (
            obj.faces(">Z")
            .workplane()
            .pushPoints(screw_positions)
            .hole(3.2, self.height)
        )

    def get_base_shape(self) -> cq.Workplane:
        """Complete block with the shared stepped bearing/shank cavity."""
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
                internal_length,
                self.collet_shank.dia / 2 + 1,
                centered=(True, True, False),
            )
            .faces(">X")
            .cylinder(
                self.bearing_type.WIDTH,
                self.bearing_type.OD / 2,
                centered=(True, True, False),
            )
            .translate((0, 0, self.split_height))
        )
        return (
            cq.Workplane("XY")
            .box(self.length, self.width, self.height, centered=(False, True, False))
            .cut(block_cut)
        )

    def bearing_holder_box(self, z_offset: float = 0.0) -> cq.Workplane:
        """Cube at the -X end; the +X end uses a translated copy."""
        box_bottom_z = self.split_height + z_offset
        box_height = self.height - box_bottom_z
        return (
            cq.Workplane("XY")
            .box(
                self.holder_length_x,
                self.width,
                box_height,
                centered=(False, True, False),
            )
            .translate((0, 0, box_bottom_z))
        )

    def bearing_holder_cut_boxes(self) -> cq.Workplane:
        near_box = self.bearing_holder_box(-self.holder_split_gap / 2)
        far_box = near_box.translate((self.length - self.holder_length_x, 0, 0))
        return near_box.union(far_box)

    def get_bearing_holder_shape(self) -> cq.Workplane:
        """Holder derived from the block above the centered split gap."""
        holder = self.get_base_shape().intersect(
            self.bearing_holder_box(self.holder_split_gap / 2)
        )
        screw_y = self.bearing_holder_screw_spacing_y / 2
        screw_x = self.bearing_type.WIDTH / 2
        return (
            holder.faces(">Z")
            .workplane()
            .pushPoints([(screw_x, -screw_y), (screw_x, screw_y)])
            .hole(3.4, self.height)
        )

    def get_object(self) -> cq.Workplane:
        return self._object

    def dimensions(self) -> tuple[object, ...]:
        return (
            self.length,
            self.width,
            self.height,
            self.split_height,
            self.collet_side_bearing_x,
            self.index_side_bearing_x,
            self.bearing_pocket_dia,
            self.bearing_pocket_depth,
            self.shank_bore_dia,
            self.holder_length_x,
            self.holder_split_gap,
            self.bearing_holder_screw_spacing_y,
            self.bearing_type,
            self.collet_shank,
        )


class QuillBody(bpd.PrintedPart):
    """Single printable body containing both the hinge joint and main block."""

    def __init__(
        self,
        main_block: QuillMainBlock,
        joint: QuillJointAli,
        angle_indicator: QuillAngleIndicator,
        block_x: float,
        indicator_y: float,
    ) -> None:
        self.main_block = main_block
        self.joint_dimensions = joint.dimensions()
        self.angle_indicator = angle_indicator
        self.block_x = block_x
        self.indicator_y = indicator_y
        super().__init__(name="Quill Body")

        # The indicator is modeled flat for export. Rotate a clearance copy
        # into its assembled orientation and subtract that exact profile from
        # the joint before the joint and bearing block become one solid.
        indicator_cutout = (
            angle_indicator.make(cutout=True)
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((0, indicator_y, 0))
        )
        joint_obj = joint.get_object().cut(indicator_cutout)
        block_obj = main_block.get_object()
        if not isinstance(block_obj, cq.Workplane):
            raise TypeError("QuillMainBlock must provide Workplane geometry")
        obj = joint_obj.union(block_obj.translate((block_x, 0, 0)))

        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("blue"))

        # Bearings belong to the merged quill body. QuillMainBlock is now a
        # geometry helper and is no longer added as a separate printed part.
        bearing = bb.Bearing6001ZZ.get(name="6001ZZ Bearing")
        bearing_positions = (
            main_block.collet_side_bearing_x,
            main_block.index_side_bearing_x,
        )
        for bearing_x in bearing_positions:
            self._add(
                bearing,
                loc=Location(
                    Vector(block_x + bearing_x, 0, main_block.split_height),
                    Vector(0, 1, 0),
                    90,
                ),
                color="gray",
                name=f"bearing_{bearing_x:.0f}",
            )

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.main_block.dimensions(),
            self.joint_dimensions,
            self.angle_indicator,
            self.block_x,
            self.indicator_y,
        )


class QuillBearingHolder(bpd.PrintedPart):
    """Removable bearing clamp derived from the quill block's own shape."""

    @classmethod
    def create(
        cls,
        quill_block: QuillMainBlock,
        holder_length_x: float,
        holder_split_gap: float,
        screw_spacing_y: float,
    ) -> QuillBearingHolder:
        return cls.get(
            quill_block=quill_block,
            holder_length_x=holder_length_x,
            holder_split_gap=holder_split_gap,
            screw_spacing_y=screw_spacing_y,
        )

    def __init__(
        self,
        quill_block: QuillMainBlock,
        holder_length_x: float,
        holder_split_gap: float,
        screw_spacing_y: float,
    ) -> None:
        self.quill_block_dimensions = quill_block.dimensions()
        self.holder_length_x = holder_length_x
        self.holder_split_gap = holder_split_gap
        self.screw_spacing_y = screw_spacing_y
        super().__init__(name="Quill Bearing Holder")

        obj = quill_block.get_bearing_holder_shape()
        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("red"))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.quill_block_dimensions,
            self.holder_length_x,
            self.holder_split_gap,
            self.screw_spacing_y,
        )


class IndexGearStandardMk1(bpd.PrintedPart):
    """Printed part: 96-tooth index gear. Clamps onto the ER11 shank with
    a captive M3 set-screw. V-notches around perimeter for a detent pin.
    Printed flat — numbers on bottom, teeth on top. Displayed edge-on."""

    @classmethod
    def create(
        cls,
        od: float,
        bore_dia: float,
        teeth_width: float,
        numbers_width: float,
        spacer_width: float,
        num_teeth: int,
        slot_angle: float,
        slot_depth: float,
        slot_width: float,
    ) -> IndexGearStandardMk1:
        return cls.get(
            od=od,
            bore_dia=bore_dia,
            teeth_width=teeth_width,
            numbers_width=numbers_width,
            spacer_width=spacer_width,
            num_teeth=num_teeth,
            slot_angle=slot_angle,
            slot_depth=slot_depth,
            slot_width=slot_width,
        )

    def __init__(
        self,
        od: float,
        bore_dia: float,
        teeth_width: float,
        numbers_width: float,
        spacer_width: float,
        num_teeth: int,
        slot_angle: float,
        slot_depth: float,
        slot_width: float,
    ) -> None:
        self.od = od
        self.bore_dia = bore_dia
        self.teeth_width = teeth_width
        self.numbers_width = numbers_width
        self.spacer_width = spacer_width
        self.num_teeth = num_teeth
        self.slot_angle = slot_angle
        self.slot_depth = slot_depth
        self.slot_width = slot_width
        super().__init__(name="Index Gear")
        # Build geometry once
        obj = cq.Workplane("XY").cylinder(
            self.teeth_width + self.numbers_width,
            self.od / 2,
            centered=(True, True, False),
        )
        obj = obj.faces(">Z").workplane().hole(self.bore_dia)
        obj = self._add_tick_marks(obj)
        obj = self._add_nut_pocket(obj)
        obj = self._add_teeth(obj)
        # After the gear is rotated into the assembly, local +Z becomes +X.
        # This ring fills the old washer gap and bears against the inner
        # race of the adjacent 6001ZZ bearing.
        spacer_ring = (
            cq.Workplane("XY")
            .circle(18.0 / 2)
            .circle(self.bore_dia / 2)
            .extrude(self.spacer_width)
            .translate((0, 0, self.teeth_width + self.numbers_width))
        )
        obj = obj.union(spacer_ring)
        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("red"))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.od,
            self.bore_dia,
            self.teeth_width,
            self.numbers_width,
            self.spacer_width,
            self.num_teeth,
            self.slot_angle,
            self.slot_depth,
            self.slot_width,
        )

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
                    .rotate((0, 0, 0), (0, 0, 1), -angle)
                )
                gear = gear.cut(num_mark)

        return gear
