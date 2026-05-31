import cadquery as cq
import math
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

    quill: quill_abstract.QuillAssemblyBase = None
    quill_joint: quill_joint_abstract.QuillHolderJointBase = None

    desired_vertical_travel = 300.0

    rail_length = 400.0

    leadscrew_dia = 8.0
    def leadscrew_length(self):
        return math.ceil((self.rail_length + self.bh_total_height() + self.bh_cylinder_height() + self.handwheel_height) / 50.0) * 50.0

    def spine_length(self):
        return math.ceil((self.bh_total_height() * 2 + self.rail_length) / 20.0) * 20.0

    handwheel_height = 10.0

    # 20x20mm aluminum t-slot extrusion
    spine_ext_width = 20.0
    spine_ext_thickness = 20.0

    def rail_x(self):
        return self.spine_ext_thickness / 2

    def rail_surface_x(self):
        return bb.RailMGN15H.total_height() + self.rail_x()

    def leadscrew_rail_spacing(self):
        return bb.LeadScrewT8.NUT_DIA / 2 + 5.0

    def leadscrew_x(self):
        return self.leadscrew_rail_spacing() + self.rail_surface_x()

    def quill_holder_x(self):
        return self.leadscrew_x() + bb.LeadScrewT8.NUT_DIA / 2 + 3.0 + self.quill_joint.space_needed_carriage_x()
    
    def quill_holder_z(self):
        return self.quill_joint.offset_carriage_z()

    def rail_start_y(self):
        return self.bh_total_height()

    QUILL_CARRIAGE_NUT_DEPTH = bb.LeadScrewT8.NUT_THICKNESS + 1.5
    RAIL_CARRIAGE_Y_OFFSET = 10.0 + QUILL_CARRIAGE_NUT_DEPTH

    def quill_carriage_display_height(self):
        # Height of the quill carriage for visualization.
        return self.rail_start_y() + 100.0

    def screw_distance_from_mast(self):
        # Distance from mast surface to center of leadscrew, includes clearance
        return bb.RailMGN15H.total_height() + bb.LeadScrewT8.NUT_DIA / 2 + 5.0

    # Quill carriage
    qc_joint_dia = 25
    qc_joint_length = 80

    def leadscrew_dist_from_spine(self):
        return self.leadscrew_x() - self.rail_x()

    def leadscrew_dist_from_rail(self):
        return self.leadscrew_x() - self.rail_surface_x()
    
    def quill_holder_distance(self):
        return self.quill_holder_x() - self.rail_surface_x()
    
    # Bearing-holder stuff
    BH_LEADSCREW_HOLE_SPACE = 4.0
    BH_BOLT_HOLE_LENGTH = 8.0
    BH_BOLT_HOLE_DIA = 5.0
    BH_BOLT_HEAD_DIA = 10.0
    
    def bh_bolt_head_height(self):
        return self.BH_BOLT_HEAD_DIA / 2 + 5.0

    def bh_diagonal_length(self):
        # Don't need to go diagonal all the way to the mast.
        return self.leadscrew_dist_from_spine() - self.BH_BOLT_HOLE_LENGTH

    def bh_diagonal_height(self):
        # Keep some space for bolt head.
        return max(self.bh_diagonal_length(), self.bh_bolt_head_height() + self.BH_BOLT_HEAD_DIA / 2)

    def bh_cylinder_height(self):
        return bb.Bearing608ZZ.WIDTH + 5.0

    def bh_total_height(self):
        return self.bh_diagonal_height() + self.bh_cylinder_height()

    def make_assembly(self):
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
                color=Color("green"))
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
                loc=Location((10, 0, self.quill_carriage_display_height() + self.RAIL_CARRIAGE_Y_OFFSET)),
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
                loc=Location((self.leadscrew_x(), 0, self.quill_carriage_display_height() + self.QUILL_CARRIAGE_NUT_DEPTH)),
                color=Color("orange"),
            )
            .add(
                self.make_quill_carriage(),
                name="hinge",
                loc=Location((self.rail_surface_x(), 0, self.quill_carriage_display_height())),
                color=Color("purple"),
            )
            .add(
                hw.make(),
                name="handwheel",
                loc=Location(self.leadscrew_x(), 0, self.rail_start_y() + self.rail_length + self.bh_total_height()),
                color=Color("orange")
            )
        )
        
        if self.quill != None:
            assembly = assembly.add(
                self.quill.make_assembly(),
                name="quill_assembly",
                loc=Location((self.quill_holder_x(), 0, self.quill_carriage_display_height() + self.quill_holder_z())),
            )

        return assembly

    def make_bearing_holder(self):
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

    def export_all_parts(self):
        """Export all parts and assembly"""
        print("Exporting improved parts...")
        try:
            cq.exporters.export(self.make_bearing_holder(), "pillow_block.stl")
            print("Pillow block exported")
            cq.exporters.export(self.make_quill_carriage(), "quill_hinge.stl")
            print("Quill hinge exported")
            assembly = self.quill.make_assembly()
            cq.exporters.export(assembly.toCompound(), "mast_assembly.stl")
            print("Improved assembly exported")
            print("All parts exported successfully!")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def make_mast_spine(self, length):
        """20x20 T-slot profile.

        Aligned to +Z, starting at origin.
        """

        shell = cq.Workplane("XY").box(
            self.spine_ext_thickness, self.spine_ext_width, length, centered=(True, True, False)
        )
        profile = shell.edges("|Z").chamfer(3)
        profile.faces(">X").tag("SpineFront")
        return profile

    def make_mgn9_rail(self, length, orient_for_assembly=True):
        """MGN9 rail profile

        Created from origin, going to +Y. Reorient in assembly.
        """

        num_holes = int(length / 30) + 1
        hole_positions = [(0, -i * 30) for i in range(num_holes)]

        rail = (
            cq.Workplane("XY")
            .box(bb.RailMGN15H.RAIL_WIDTH, length, bb.RailMGN15H.RAIL_HEIGHT, centered=(True, False, False))
            .edges(">Z")
            .fillet(0.8)
            .faces("<Z")
            .workplane()
            .pushPoints(hole_positions)
            .circle(3.2 / 2)
            .cutThruAll()
        )
        rail.faces(">Z").tag("RailTop")
        rail.faces("<Z").tag("RailBottom")
        print(F"Rail length: {length}")

        if orient_for_assembly:
            return (rail
                    .rotate((0, 0, 0), (1, 0, 0), 90)
                    .rotate((0, 0, 0), (0, 0, 1), 90))
        else:
            return rail

    def make_mgn9_carriage(self, orient_for_assembly=True):
        """MGN15H carriage

        Created from origin, going to +Y, top is +Z.
        Raised by clearance, assuming rail is at Z0.
        """
        carriage = (
            cq.Workplane("XY")
            .box(
                bb.RailMGN15H.CARRIAGE_WIDTH,
                bb.RailMGN15H.CARRIAGE_LENGTH,
                bb.RailMGN15H.CARRIAGE_HEIGHT,
                centered=(True, False, False),
            )
            .translate((0, 0, bb.RailMGN15H.CARRIAGE_CLEARANCE))
            .edges("|Z")
            .fillet(1.0)
        )
        if orient_for_assembly:
            return (
                carriage
                .rotate((0, 0, 0), (1, 0, 0), 90)
                .rotate((0, 0, 0), (0, 0, 1), 90)
            )
        else:
            return carriage

    def make_t8_shaft(self):
        """T8 leadscrew shaft visualization"""
        shaft = cq.Workplane("XY").cylinder(
            self.leadscrew_length(), self.leadscrew_dia / 2, centered=(True, True, False)
        )
        print(F"Leadscrew length: {self.leadscrew_length()}")
        return shaft

    def make_t8_nut(self):
        """T8 leadscrew nut with flange and mounting holes"""
        nut_body = (cq.Workplane("XY")
                    .cylinder(15, 5.1, centered=(True, True, False))
                    .translate((0, 0, -(1.5 + bb.LeadScrewT8.NUT_THICKNESS)))
                    .chamfer(0.25))
        flange = (cq.Workplane("XY")
                  .circle(11)
                  .extrude(bb.LeadScrewT8.NUT_THICKNESS)
                  .translate((0, 0, -bb.LeadScrewT8.NUT_THICKNESS))
                  .chamfer(0.5))
        angles = [0, 90, 180, 270]
        hole_positions = [
            (
                bb.LeadScrewT8.NUT_HOLE_RADIUS * math.cos(math.radians(a)),
                bb.LeadScrewT8.NUT_HOLE_RADIUS * math.sin(math.radians(a)),
            )
            for a in angles
        ]
        flange = (
            flange.faces(">Z")
            .workplane()
            .pushPoints(hole_positions)
            .circle(bb.LeadScrewT8.NUT_HOLE_DIA / 2)
            .cutThruAll()
        )
        nut = nut_body.union(flange)
        return nut


    def make_quill_carriage(self, orient_for_assembly=True):
        """
        Vertical carriage with bearing hinge for quill holder.
        Designed to fit on MGN9 carriage.
        """
        hinge = (cq.Workplane("XY")
                 .box(bb.RailMGN15H.CARRIAGE_WIDTH, self.quill_holder_distance(), bb.RailMGN15H.CARRIAGE_LENGTH + self.RAIL_CARRIAGE_Y_OFFSET, centered=(True, False, False))
                 .translate((0, 0, 0)))
        hinge = (
            hinge.faces("<Z")
            .workplane(offset=0)
            .move(0, -self.leadscrew_dist_from_rail())
            .hole(10.2 + 1.0)

            .faces("<Z")
            .workplane(offset=0)
            .move(0, -self.leadscrew_dist_from_rail())
            .hole(bb.LeadScrewT8.NUT_DIA + 1.0, 1.5 + bb.LeadScrewT8.NUT_THICKNESS)

            .union(
                self.quill_joint.add_shape(bb.RailMGN15H.CARRIAGE_WIDTH, self.quill_holder_distance() + 5.0)
                .rotate((0, 0, 0), (0, 0, 1), -90)
                .translate((0, self.quill_holder_distance(), self.quill_joint.offset_carriage_z()))
                )

            .cut(
                self.quill_joint.cut_shape(bb.RailMGN15H.CARRIAGE_WIDTH, self.quill_holder_distance() + 5.0)
                .rotate((0, 0, 0), (0, 0, 1), -90)
                .translate((0, self.quill_holder_distance(), self.quill_joint.offset_carriage_z()))
            )
        )
        if orient_for_assembly:
            return (hinge
                    .rotate((0, 0, 0), (0, 0, 1), -90))
        else:
            return hinge


class BearingHolder(bpd.PrintedPart):
    """Leadscrew bearing holder (pillow block).

    Printed part that mounts to the mast spine and holds a 608ZZ bearing
    for the leadscrew. All dimensions come from the assembly — this class
    just builds geometry.
    """

    def __init__(self, *,
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
                 bearing_type,
                 ):
        # spine_span = width of the mast spine in Y (this part spans that full width)
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

    def __eq__(self, other):
        if not isinstance(other, BearingHolder):
            return False
        return (self.name == other.name
                and self.spine_span == other.spine_span
                and self.leadscrew_dist == other.leadscrew_dist
                and self.diagonal_length == other.diagonal_length
                and self.diagonal_height == other.diagonal_height
                and self.cylinder_height == other.cylinder_height
                and self.leadscrew_dia == other.leadscrew_dia)

    def __hash__(self):
        return hash((self.name, self.spine_span,
                     self.leadscrew_dist, self.diagonal_length,
                     self.diagonal_height, self.cylinder_height,
                     self.leadscrew_dia))

    def total_height(self):
        return self.diagonal_height + self.cylinder_height

    def get_object(self):
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
            .cylinder(self.cylinder_height, self.bearing_type.OD / 2 + 4, centered=(True, True, False))
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
            .cylinder(self.bolt_hole_length, self.bolt_hole_dia / 2, centered=(True, True, False))
            .faces(">Y")
            .workplane()
            .cylinder(100, self.bolt_head_dia / 2, centered=(True, True, False))
        )

        # Rotate into display orientation (assembly will place it).
        return block.rotate((0, 0, 0), (0, 0, 1), -90)