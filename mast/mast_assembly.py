from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Vector

import bought_bits as bb
import bom_part_data as bpd
import mast.mast_abstract as mast_abstract
import quill_holder.quill_holder_abstract as quill_holder_abstract
import quill_holder_joint.quill_holder_joint_abstract as quill_holder_joint_abstract
from mast.handwheel import HandWheel

# REMINDER: +X is left, +Y is forwards, +Z is up!
# The mast faces left (+X), the lap is to the left of the mast.


class MastAssembly(mast_abstract.MastAssemblyBase):
    """Mast assembly: spine extrusion, linear rail, leadscrew, carriage,
    bearing holders, handwheel, and optional quill holder + quill."""

    # ── Dimensions ──────────────────────────────────────────────
    desired_vertical_travel: float = 300.0
    rail_length: float = 400.0
    leadscrew_dia: float = 8.0
    handwheel_height: float = 10.0

    spine_ext_width: float = 20.0
    spine_ext_thickness: float = 20.0

    QUILL_CARRIAGE_NUT_DEPTH: float = bb.LeadScrewT8.NUT_THICKNESS + 1.5
    RAIL_CARRIAGE_Y_OFFSET: float = 10.0 + QUILL_CARRIAGE_NUT_DEPTH

    BH_LEADSCREW_HOLE_SPACE: float = 4.0
    BH_BOLT_HOLE_LENGTH: float = 8.0
    BH_BOLT_HOLE_DIA: float = 5.0
    BH_BOLT_HEAD_DIA: float = 10.0

    # ── Derived dimensions ──────────────────────────────────────

    def leadscrew_length(self) -> float:
        return math.ceil(
            (self.rail_length + self.bh_total_height()
             + self.bh_cylinder_height() + self.handwheel_height) / 50.0
        ) * 50.0

    def spine_length(self) -> float:
        return math.ceil(
            (self.bh_total_height() * 2 + self.rail_length) / 20.0
        ) * 20.0

    def rail_x(self) -> float:
        return self.spine_ext_thickness / 2

    def rail_surface_x(self) -> float:
        return bb.RailMGN15H.total_height() + self.rail_x()

    def leadscrew_rail_spacing(self) -> float:
        return bb.LeadScrewT8.NUT_DIA / 2 + 5.0

    def leadscrew_x(self) -> float:
        return self.leadscrew_rail_spacing() + self.rail_surface_x()

    def quill_holder_x(self) -> float:
        assert self._quill_joint is not None
        return (
            self.leadscrew_x() + bb.LeadScrewT8.NUT_DIA / 2 + 3.0
            + self._quill_joint.space_needed_carriage_x()
        )

    def quill_holder_z(self) -> float:
        assert self._quill_joint is not None
        return self._quill_joint.offset_carriage_z()

    def rail_start_y(self) -> float:
        return self.bh_total_height()

    def quill_carriage_display_height(self) -> float:
        return self.rail_start_y() + 100.0

    def leadscrew_dist_from_spine(self) -> float:
        return self.leadscrew_x() - self.rail_x()

    def leadscrew_dist_from_rail(self) -> float:
        return self.leadscrew_x() - self.rail_surface_x()

    def quill_holder_distance(self) -> float:
        return self.quill_holder_x() - self.rail_surface_x()

    def bh_bolt_head_height(self) -> float:
        return self.BH_BOLT_HEAD_DIA / 2 + 5.0

    def bh_diagonal_length(self) -> float:
        return self.leadscrew_dist_from_spine() - self.BH_BOLT_HOLE_LENGTH

    def bh_diagonal_height(self) -> float:
        return max(
            self.bh_diagonal_length(),
            self.bh_bolt_head_height() + self.BH_BOLT_HEAD_DIA / 2,
        )

    def bh_cylinder_height(self) -> float:
        return bb.Bearing608ZZ.WIDTH + 5.0

    def bh_total_height(self) -> float:
        return self.bh_diagonal_height() + self.bh_cylinder_height()

    # ═══════════════════════════════════════════════════════════
    # Construction
    # ═══════════════════════════════════════════════════════════

    def __init__(
        self,
        quill: quill_holder_abstract.QuillHolderAssemblyBase | None = None,
        quill_joint: quill_holder_joint_abstract.QuillHolderJointBase | None = None,
    ) -> None:
        super().__init__(name="Mast Assembly")
        self._current_group = self.name
        self._quill_joint = quill_joint

        # Spine extrusion
        spine = bb.TslotExtrusion2020.get(length=self.spine_length())
        self._add(spine, loc=Location(0, 0, 0), color="lightgray",
                  name="extrusion")

        # Rail
        rail = bb.RailMGN15H.get(length=self.rail_length)
        rail_obj = rail.get_object().rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), 90)
        self._add(rail, obj=rail_obj,
                  loc=Location(self.rail_x(), 0, self.rail_start_y()),
                  color="gray", name="rail")

        # Bearing holders (bottom + top)
        bh_bottom = self._make_bearing_holder()
        bh_top = self._make_bearing_holder()
        self._add(bh_bottom, loc=Location(10, 0, 0),
                  name="bottom_bearing")
        self._add(bh_top, loc=Location(10, 0, self.rail_start_y() + self.rail_length),
                  color="red", name="top_bearing")

        # Carriage
        carriage_obj = (
            bb.RailMGN15H.make_carriage()
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .rotate((0, 0, 0), (0, 0, 1), 90)
        )
        self._assembly.add(  # type: ignore[union-attr]
            carriage_obj, name="carriage1",
            loc=Location(10, 0,
                         self.quill_carriage_display_height() + self.RAIL_CARRIAGE_Y_OFFSET),
            color=cq.Color("gray"),
        )

        # Leadscrew
        leadscrew = bb.LeadScrewT8.get(length=self.leadscrew_length())
        self._add(leadscrew, loc=Location(self.leadscrew_x(), 0, 0),
                  color="gray", name="leadscrew")

        # T8 nut
        nut_obj = bb.LeadScrewT8.make_nut()
        self._assembly.add(  # type: ignore[union-attr]
            nut_obj, name="nut",
            loc=Location(self.leadscrew_x(), 0,
                         self.quill_carriage_display_height() + self.QUILL_CARRIAGE_NUT_DEPTH),
            color=cq.Color("gray"),
        )

        # Quill carriage (hinge)
        carriage = self._make_quill_carriage()
        self._add(carriage,
                  loc=Location(self.rail_surface_x(), 0, self.quill_carriage_display_height()),
                  color="purple", name="hinge")

        # Handwheel
        hw = HandWheel.create()
        self._add(hw,
                  loc=Location(self.leadscrew_x(), 0,
                               self.rail_start_y() + self.rail_length + self.bh_total_height()),
                  name="handwheel")

        # Optional quill holder assembly
        if quill is not None:
            self._add(quill,
                      loc=Location(self.quill_holder_x(), 0,
                                   self.quill_carriage_display_height() + self.quill_holder_z()),
                      name="quill_assembly")


    # ── Part factories ──────────────────────────────────────────

    def _make_bearing_holder(self) -> BearingHolder:
        return BearingHolder.create(
            spine_span=self.spine_ext_width,
            leadscrew_dist=self.leadscrew_dist_from_spine(),
            diagonal_length=self.bh_diagonal_length(),
            diagonal_height=self.bh_diagonal_height(),
            cylinder_height=self.bh_cylinder_height(),
            bolt_head_height=self.bh_bolt_head_height(),
            bolt_hole_length=self.BH_BOLT_HOLE_LENGTH,
            bolt_hole_dia=self.BH_BOLT_HOLE_DIA,
            bolt_head_dia=self.BH_BOLT_HEAD_DIA,
            leadscrew_dia=self.leadscrew_dia,
            leadscrew_hole_space=self.BH_LEADSCREW_HOLE_SPACE,
            bearing_type=bb.Bearing608ZZ,
        )

    def _make_quill_carriage(self) -> QuillCarriage:
        assert self._quill_joint is not None
        joint_add = self._quill_joint.add_shape(
            bb.RailMGN15H.CARRIAGE_WIDTH,
            self.quill_holder_distance() + 5.0,
        )
        joint_cut = self._quill_joint.cut_shape(
            bb.RailMGN15H.CARRIAGE_WIDTH,
            self.quill_holder_distance() + 5.0,
        )
        return QuillCarriage.create(
            base_width=bb.RailMGN15H.CARRIAGE_WIDTH,
            base_length=self.quill_holder_distance(),
            rail_carriage_length=bb.RailMGN15H.CARRIAGE_LENGTH,
            rail_carriage_y_offset=self.RAIL_CARRIAGE_Y_OFFSET,
            leadscrew_dist_from_rail=self.leadscrew_dist_from_rail(),
            leadscrew_nut_dia=bb.LeadScrewT8.NUT_DIA,
            leadscrew_nut_thickness=bb.LeadScrewT8.NUT_THICKNESS,
            joint_add_shape=joint_add,
            joint_cut_shape=joint_cut,
            joint_offset_z=self.quill_holder_z(),
        )


# ═══════════════════════════════════════════════════════════════════════
# Printed parts
# ═══════════════════════════════════════════════════════════════════════


class BearingHolder(bpd.PrintedPart):
    """Leadscrew bearing holder (pillow block)."""

    @classmethod
    def create(
        cls,
        spine_span: float,
        leadscrew_dist: float,
        diagonal_length: float,
        diagonal_height: float,
        cylinder_height: float,
        bolt_head_height: float,
        bolt_hole_length: float,
        bolt_hole_dia: float,
        bolt_head_dia: float,
        leadscrew_dia: float,
        leadscrew_hole_space: float,
        bearing_type: type[bb.BearingGeneric],
    ) -> BearingHolder:
        return cls.get(
            spine_span=spine_span,
            leadscrew_dist=leadscrew_dist,
            diagonal_length=diagonal_length,
            diagonal_height=diagonal_height,
            cylinder_height=cylinder_height,
            bolt_head_height=bolt_head_height,
            bolt_hole_length=bolt_hole_length,
            bolt_hole_dia=bolt_hole_dia,
            bolt_head_dia=bolt_head_dia,
            leadscrew_dia=leadscrew_dia,
            leadscrew_hole_space=leadscrew_hole_space,
            bearing_type=bearing_type,
        )

    def __init__(
        self,
        *,
        spine_span: float,
        leadscrew_dist: float,
        diagonal_length: float,
        diagonal_height: float,
        cylinder_height: float,
        bolt_head_height: float,
        bolt_hole_length: float,
        bolt_hole_dia: float,
        bolt_head_dia: float,
        leadscrew_dia: float,
        leadscrew_hole_space: float,
        bearing_type: type[bb.BearingGeneric],
    ) -> None:
        self.spine_span = spine_span
        self.leadscrew_dist = leadscrew_dist
        self.diagonal_length = diagonal_length
        self.diagonal_height = diagonal_height
        self.cylinder_height = cylinder_height
        self.bolt_head_height = bolt_head_height
        self.bolt_hole_length = bolt_hole_length
        self.bolt_hole_dia = bolt_hole_dia
        self.bolt_head_dia = bolt_head_dia
        self.leadscrew_dia = leadscrew_dia
        self.leadscrew_hole_space = leadscrew_hole_space
        self.bearing_type = bearing_type
        super().__init__(name="Bearing Holder")

        # Build geometry
        block_shape_pts = [
            (0, 0),
            (self.leadscrew_dist - self.diagonal_length, 0),
            (self.leadscrew_dist, self.diagonal_height),
            (self.leadscrew_dist, self.diagonal_height + self.cylinder_height),
            (0, self.diagonal_height + self.cylinder_height),
        ]
        obj = (
            cq.Workplane("YZ", origin=(-self.spine_span / 2, 0, 0))
            .polyline(block_shape_pts)
            .close()
            .extrude(self.spine_span)
        )
        obj = (
            obj
            .faces(">Z")
            .workplane(offset=-(self.cylinder_height), origin=(0, 0, 0))
            .move(0, self.leadscrew_dist)
            .cylinder(self.cylinder_height, self.bearing_type.OD / 2 + 4,
                      centered=(True, True, False))
            .faces(">Z").workplane()
            .move(0, self.leadscrew_dist)
            .hole(self.leadscrew_dia + self.leadscrew_hole_space)
            .faces(">Z").workplane()
            .move(0, self.leadscrew_dist)
            .hole(self.bearing_type.OD + 0.2, self.bearing_type.WIDTH)
        )
        obj = obj.cut(
            cq.Workplane("top", origin=(0, 0, self.bolt_head_height))
            .cylinder(self.bolt_hole_length, self.bolt_hole_dia / 2,
                      centered=(True, True, False))
            .faces(">Y").workplane()
            .cylinder(100, self.bolt_head_dia / 2,
                      centered=(True, True, False))
        )
        obj = obj.rotate((0, 0, 0), (0, 0, 1), -90)
        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("red"))
        # Each holder contains one 608ZZ bearing
        self._add(self.bearing_type.get(name="608ZZ Bearing"),
                  loc=cq.Location((self.leadscrew_dist, 0, self.diagonal_height + self.cylinder_height - self.bearing_type.WIDTH)),
                  name="leadscrew_bearing")

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.spine_span, self.leadscrew_dist,
            self.diagonal_length, self.diagonal_height,
            self.cylinder_height, self.bolt_head_height,
            self.bolt_hole_length, self.bolt_hole_dia,
            self.bolt_head_dia, self.leadscrew_dia,
            self.leadscrew_hole_space, self.bearing_type,
        )

    def total_height(self) -> float:
        return self.diagonal_height + self.cylinder_height


class QuillCarriage(bpd.PrintedPart):
    """Printed part: vertical carriage that rides on the MGN15H rail and
    carries the quill holder hinge."""

    @classmethod
    def create(
        cls,
        base_width: float,
        base_length: float,
        rail_carriage_length: float,
        rail_carriage_y_offset: float,
        leadscrew_dist_from_rail: float,
        leadscrew_nut_dia: float,
        leadscrew_nut_thickness: float,
        joint_add_shape: cq.Workplane,
        joint_cut_shape: cq.Workplane,
        joint_offset_z: float,
    ) -> QuillCarriage:
        return cls.get(
            base_width=base_width,
            base_length=base_length,
            rail_carriage_length=rail_carriage_length,
            rail_carriage_y_offset=rail_carriage_y_offset,
            leadscrew_dist_from_rail=leadscrew_dist_from_rail,
            leadscrew_nut_dia=leadscrew_nut_dia,
            leadscrew_nut_thickness=leadscrew_nut_thickness,
            joint_add_shape=joint_add_shape,
            joint_cut_shape=joint_cut_shape,
            joint_offset_z=joint_offset_z,
        )

    def __init__(
        self,
        base_width: float,
        base_length: float,
        rail_carriage_length: float,
        rail_carriage_y_offset: float,
        leadscrew_dist_from_rail: float,
        leadscrew_nut_dia: float,
        leadscrew_nut_thickness: float,
        joint_add_shape: cq.Workplane,
        joint_cut_shape: cq.Workplane,
        joint_offset_z: float,
    ) -> None:
        self.base_width = base_width
        self.base_length = base_length
        self.rail_carriage_length = rail_carriage_length
        self.rail_carriage_y_offset = rail_carriage_y_offset
        self.leadscrew_dist_from_rail = leadscrew_dist_from_rail
        self.leadscrew_nut_dia = leadscrew_nut_dia
        self.leadscrew_nut_thickness = leadscrew_nut_thickness
        self._joint_add = joint_add_shape
        self._joint_cut = joint_cut_shape
        self._joint_offset_z = joint_offset_z
        super().__init__(name="Mast Carriage")
        # Build geometry
        obj = self._build()
        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("red"))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.base_width, self.base_length,
            self.rail_carriage_length, self.rail_carriage_y_offset,
            self.leadscrew_dist_from_rail, self.leadscrew_nut_dia,
            self.leadscrew_nut_thickness,
        )

    def _build(self) -> cq.Workplane:
        hinge = (
            cq.Workplane("XY")
            .box(self.base_width, self.base_length,
                 self.rail_carriage_length + self.rail_carriage_y_offset,
                 centered=(True, False, False))
        )
        hinge = (
            hinge
            .faces("<Z").workplane(offset=0)
            .move(0, -self.leadscrew_dist_from_rail)
            .hole(10.2 + 1.0)
            .faces("<Z").workplane(offset=0)
            .move(0, -self.leadscrew_dist_from_rail)
            .hole(self.leadscrew_nut_dia + 1.0,
                  1.5 + self.leadscrew_nut_thickness)
            .union(
                self._joint_add
                .rotate((0, 0, 0), (0, 0, 1), -90)
                .translate((0, self.base_length, self._joint_offset_z))
            )
            .cut(
                self._joint_cut
                .rotate((0, 0, 0), (0, 0, 1), -90)
                .translate((0, self.base_length, self._joint_offset_z))
            )
        )
        return hinge.rotate((0, 0, 0), (0, 0, 1), -90)
