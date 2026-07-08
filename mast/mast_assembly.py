from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Color

import bought_bits as bb
import bom_part_data as bpd
import mast.mast_abstract as mast_abstract
import quill.quill_abstract as quill_abstract
import quill_joint.quill_joint_abstract as quill_joint_abstract
import mast.handwheel as handwheel

# REMINDER: +X is left, +Y is forwards, +Z is up!
# The mast faces left (+X), the lap is to the left of the mast.


class MastAssembly(mast_abstract.MastAssemblyBase):
    """Class representing the entire mast assembly with all components."""

    quill: quill_abstract.QuillAssemblyBase | None = None
    quill_joint: quill_joint_abstract.QuillHolderJointBase | None = None

    desired_vertical_travel: float = 300.0
    rail_length: float = 400.0
    leadscrew_dia: float = 8.0
    handwheel_height: float = 10.0

    spine_ext_width: float = 20.0
    spine_ext_thickness: float = 20.0

    QUILL_CARRIAGE_NUT_DEPTH: float = bb.LeadScrewT8.NUT_THICKNESS + 1.5
    RAIL_CARRIAGE_Y_OFFSET: float = 10.0 + QUILL_CARRIAGE_NUT_DEPTH

    qc_joint_dia: float = 25.0
    qc_joint_length: float = 80.0

    BH_LEADSCREW_HOLE_SPACE: float = 4.0
    BH_BOLT_HOLE_LENGTH: float = 8.0
    BH_BOLT_HOLE_DIA: float = 5.0
    BH_BOLT_HEAD_DIA: float = 10.0

    def leadscrew_length(self) -> float:
        return (
            math.ceil(
                (self.rail_length
                 + self.bh_total_height()
                 + self.bh_cylinder_height()
                 + self.handwheel_height)
                / 50.0
            )
            * 50.0
        )

    def spine_length(self) -> float:
        return (
            math.ceil(
                (self.bh_total_height() * 2 + self.rail_length) / 20.0
            )
            * 20.0
        )

    def rail_x(self) -> float:
        return self.spine_ext_thickness / 2

    def rail_surface_x(self) -> float:
        return bb.RailMGN15H.total_height() + self.rail_x()

    def leadscrew_rail_spacing(self) -> float:
        return bb.LeadScrewT8.NUT_DIA / 2 + 5.0

    def leadscrew_x(self) -> float:
        return self.leadscrew_rail_spacing() + self.rail_surface_x()

    def quill_holder_x(self) -> float:
        assert self.quill_joint is not None
        return (
            self.leadscrew_x()
            + bb.LeadScrewT8.NUT_DIA / 2
            + 3.0
            + self.quill_joint.space_needed_carriage_x()
        )

    def quill_holder_z(self) -> float:
        assert self.quill_joint is not None
        return self.quill_joint.offset_carriage_z()

    def rail_start_y(self) -> float:
        return self.bh_total_height()

    def quill_carriage_display_height(self) -> float:
        """Height of the quill carriage for visualization."""
        return self.rail_start_y() + 100.0

    def screw_distance_from_mast(self) -> float:
        return (
            bb.RailMGN15H.total_height()
            + bb.LeadScrewT8.NUT_DIA / 2
            + 5.0
        )

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

    def make_assembly(self) -> cq.Assembly:
        """Assemble the mast components with colors for visualization."""
        hw = handwheel.HandWheel()

        assembly = (
            cq.Assembly()
            .add(
                self.make_mast_spine(self.spine_length()),
                name="extrusion",
                loc=Location((0, 0, 0)),
                color=Color("lightgray"),
            )
            .add(
                self.make_mgn9_rail(self.rail_length),
                name="rail",
                loc=Location((self.rail_x(), 0, self.rail_start_y())),
                color=Color("green"),
            )
            .add(
                self.make_bearing_holder(),
                name="bottom_bearing",
                loc=Location((10, 0, 0)),
                color=Color("red"),
            )
            .add(
                self.make_bearing_holder(),
                name="top_bearing",
                loc=Location((10, 0, self.rail_start_y() + self.rail_length)),
                color=Color("red"),
            )
            .add(
                self.make_mgn9_carriage(True),
                name="carriage1",
                loc=Location((
                    10, 0,
                    self.quill_carriage_display_height()
                    + self.RAIL_CARRIAGE_Y_OFFSET,
                )),
                color=Color("yellow"),
            )
            .add(
                self.make_t8_shaft(),
                name="leadscrew",
                loc=Location((self.leadscrew_x(), 0, 0)),
                color=Color("blue"),
            )
            .add(
                self.make_t8_nut(),
                name="nut",
                loc=Location((
                    self.leadscrew_x(), 0,
                    self.quill_carriage_display_height()
                    + self.QUILL_CARRIAGE_NUT_DEPTH,
                )),
                color=Color("orange"),
            )
            .add(
                self.make_quill_carriage(),
                name="hinge",
                loc=Location((
                    self.rail_surface_x(), 0,
                    self.quill_carriage_display_height(),
                )),
                color=Color("purple"),
            )
            .add(
                hw.get_object(),
                name="handwheel",
                loc=Location(
                    self.leadscrew_x(), 0,
                    self.rail_start_y() + self.rail_length
                    + self.bh_total_height(),
                ),
                color=Color("orange"),
            )
        )

        if self.quill is not None:
            assembly = assembly.add(
                self.quill.make_assembly(),
                name="quill_assembly",
                loc=Location((
                    self.quill_holder_x(), 0,
                    self.quill_carriage_display_height()
                    + self.quill_holder_z(),
                )),
            )

        return assembly

    def make_bearing_holder(self) -> cq.Workplane:
        """Create a bearing holder instance for the current mast config."""
        return BearingHolder(
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
        ).get_object()

    def make_mast_spine(self, length: float) -> cq.Workplane:
        """20x20 T-slot profile. Delegates to bought_bits."""
        return bb.TslotExtrusion2020(length).get_object()

    def make_mgn9_rail(
        self, length: float, orient_for_assembly: bool = True
    ) -> cq.Workplane:
        """MGN15H rail profile. Delegates to bought_bits."""
        rail = bb.RailMGN15H(length).get_object()
        if orient_for_assembly:
            return (
                rail
                .rotate((0, 0, 0), (1, 0, 0), 90)
                .rotate((0, 0, 0), (0, 0, 1), 90)
            )
        return rail

    def make_mgn9_carriage(
        self, orient_for_assembly: bool = True
    ) -> cq.Workplane:
        """MGN15H carriage. Delegates to bought_bits."""
        carriage = bb.RailMGN15H.make_carriage()
        if orient_for_assembly:
            return (
                carriage
                .rotate((0, 0, 0), (1, 0, 0), 90)
                .rotate((0, 0, 0), (0, 0, 1), 90)
            )
        return carriage

    def make_t8_shaft(self) -> cq.Workplane:
        """T8 leadscrew shaft. Delegates to bought_bits."""
        return bb.LeadScrewT8(self.leadscrew_length()).get_object()

    def make_t8_nut(self) -> cq.Workplane:
        """T8 leadscrew nut. Delegates to bought_bits."""
        return bb.LeadScrewT8.make_nut()

    def make_quill_carriage(
        self, orient_for_assembly: bool = True
    ) -> cq.Workplane:
        """Vertical carriage with bearing hinge for quill holder."""
        assert self.quill_joint is not None

        hinge = (
            cq.Workplane("XY")
            .box(
                bb.RailMGN15H.CARRIAGE_WIDTH,
                self.quill_holder_distance(),
                bb.RailMGN15H.CARRIAGE_LENGTH + self.RAIL_CARRIAGE_Y_OFFSET,
                centered=(True, False, False),
            )
            .translate((0, 0, 0))
        )
        hinge = (
            hinge.faces("<Z")
            .workplane(offset=0)
            .move(0, -self.leadscrew_dist_from_rail())
            .hole(10.2 + 1.0)

            .faces("<Z")
            .workplane(offset=0)
            .move(0, -self.leadscrew_dist_from_rail())
            .hole(
                bb.LeadScrewT8.NUT_DIA + 1.0,
                1.5 + bb.LeadScrewT8.NUT_THICKNESS,
            )

            .union(
                self.quill_joint.add_shape(
                    bb.RailMGN15H.CARRIAGE_WIDTH,
                    self.quill_holder_distance() + 5.0,
                )
                .rotate((0, 0, 0), (0, 0, 1), -90)
                .translate((
                    0,
                    self.quill_holder_distance(),
                    self.quill_joint.offset_carriage_z(),
                ))
            )

            .cut(
                self.quill_joint.cut_shape(
                    bb.RailMGN15H.CARRIAGE_WIDTH,
                    self.quill_holder_distance() + 5.0,
                )
                .rotate((0, 0, 0), (0, 0, 1), -90)
                .translate((
                    0,
                    self.quill_holder_distance(),
                    self.quill_joint.offset_carriage_z(),
                ))
            )
        )
        if orient_for_assembly:
            return hinge.rotate((0, 0, 0), (0, 0, 1), -90)
        else:
            return hinge

    def get_BOM(self) -> bpd.BOM:
        bom = bpd.BOM()
        # Printed parts
        bom.add(BearingHolder(
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
        ), 2)  # top and bottom
        bom.add(handwheel.HandWheel())
        # Off-the-shelf
        bom.add(bb.TslotExtrusion2020(self.spine_length()))
        bom.add(bb.RailMGN15H(self.rail_length))
        bom.add(bb.LeadScrewT8(self.leadscrew_length()))
        bom.add(bb.Bearing608ZZ(name="608ZZ Bearing"), 2)  # bearings for leadscrew
        return bom


class BearingHolder(bpd.PrintedPart):
    """Leadscrew bearing holder (pillow block).

    Printed part that mounts to the mast spine and holds a 608ZZ bearing
    for the leadscrew. All dimensions come from the assembly — this class
    just builds geometry.
    """

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
        self.spine_span: float = spine_span
        self.leadscrew_dist: float = leadscrew_dist
        self.diagonal_length: float = diagonal_length
        self.diagonal_height: float = diagonal_height
        self.cylinder_height: float = cylinder_height
        self.bolt_head_height: float = bolt_head_height
        self.bolt_hole_length: float = bolt_hole_length
        self.bolt_hole_dia: float = bolt_hole_dia
        self.bolt_head_dia: float = bolt_head_dia
        self.leadscrew_dia: float = leadscrew_dia
        self.leadscrew_hole_space: float = leadscrew_hole_space
        self.bearing_type: type[bb.BearingGeneric] = bearing_type
        super().__init__(name="Bearing Holder")

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

    def get_object(self) -> cq.Workplane:
        block_shape_pts = [
            (0, 0),
            (self.leadscrew_dist - self.diagonal_length, 0),
            (self.leadscrew_dist, self.diagonal_height),
            (self.leadscrew_dist, self.diagonal_height + self.cylinder_height),
            (0, self.diagonal_height + self.cylinder_height),
        ]

        block = (
            cq.Workplane("YZ", origin=(-self.spine_span / 2, 0, 0))
            .polyline(block_shape_pts)
            .close()
            .extrude(self.spine_span)
        )

        block = (
            block
            .faces(">Z")
            .workplane(offset=-(self.cylinder_height), origin=(0, 0, 0))
            .move(0, self.leadscrew_dist)
            .cylinder(
                self.cylinder_height,
                self.bearing_type.OD / 2 + 4,
                centered=(True, True, False),
            )
            # Shaft hole
            .faces(">Z")
            .workplane()
            .move(0, self.leadscrew_dist)
            .hole(self.leadscrew_dia + self.leadscrew_hole_space)
            # Bearing recess
            .faces(">Z")
            .workplane()
            .move(0, self.leadscrew_dist)
            .hole(self.bearing_type.OD + 0.2, self.bearing_type.WIDTH)
        )

        block = block.cut(
            cq.Workplane("top", origin=(0, 0, self.bolt_head_height))
            .cylinder(
                self.bolt_hole_length,
                self.bolt_hole_dia / 2,
                centered=(True, True, False),
            )
            .faces(">Y")
            .workplane()
            .cylinder(
                100, self.bolt_head_dia / 2,
                centered=(True, True, False),
            )
        )

        # Rotate into display orientation (assembly will place it).
        return block.rotate((0, 0, 0), (0, 0, 1), -90)
