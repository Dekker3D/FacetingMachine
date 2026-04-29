import cadquery as cq
import math
from cadquery import Location, Color
from machine import MachineConfig as cfg
import bought_bits as bb
import mast_abstract
import quill_abstract

# REMINDER: +X is left, +Y is forwards, +Z is up!
# The mast faces left (+X), the lap is to the left of the mast.


class MastAssembly(mast_abstract.MastAssemblyBase):
    """Class representing the entire mast assembly with all components."""

    quill: quill_abstract.QuillAssemblyBase = None
    desired_vertical_travel = 300.0

    rail_length = 400.0

    leadscrew_dia = 8.0
    leadscrew_length = 450.0

    spine_length = 450.0

    # 20x20mm aluminum t-slot extrusion
    spine_ext_width = 20.0
    spine_ext_thickness = 20.0

    def rail_x(self):
        return self.spine_ext_thickness / 2

    def rail_surface_x(self):
        return bb.RailMGN9H.total_height() + self.rail_x()

    def leadscrew_rail_spacing(self):
        return bb.LeadScrewT8.NUT_DIA / 2 + 5.0

    def leadscrew_x(self):
        return self.leadscrew_rail_spacing() + self.rail_surface_x()

    def quill_holder_x(self):
        return self.leadscrew_x() + bb.LeadScrewT8.NUT_DIA / 2 + self.qc_joint_dia / 2 + 5.0

    LEADSCREW_BEARING_HEIGHT = 15.0
    RAIL_START_Y = LEADSCREW_BEARING_HEIGHT

    QUILL_CARRIAGE_NUT_DEPTH = bb.LeadScrewT8.NUT_THICKNESS + 1.5
    RAIL_CARRIAGE_Y_OFFSET = 10.0 + QUILL_CARRIAGE_NUT_DEPTH

    QUILL_CARRIAGE_DISPLAY_HEIGHT = RAIL_START_Y + 100.0  # Height of the quill carriage for visualization.

    def screw_distance_from_mast(self):
        # Distance from mast surface to center of leadscrew, includes clearance
        return bb.RailMGN9H.total_height() + bb.LeadScrewT8.NUT_DIA / 2 + 5.0

    # Quill carriage
    qc_joint_dia = 25
    qc_joint_length = 80

    def leadscrew_dist_from_spine(self):
        return self.leadscrew_x() - self.rail_x()

    def leadscrew_dist_from_rail(self):
        return self.leadscrew_x() - self.rail_surface_x()

    def make_assembly(self):
        """Assemble the mast components with colors for visualization."""

        bearing = LeadscrewBearingHolder()
        bearing.LEADSCREW_DISTANCE = self.leadscrew_dist_from_spine()
        bearing.LEADSCREW_DIA = self.leadscrew_dia

        quill_carriage = QuillCarriage()
        quill_carriage.LEADSCREW_DISTANCE = self.leadscrew_dist_from_rail()
        quill_carriage.QUILL_HOLDER_DISTANCE = self.quill_holder_x() - self.rail_surface_x()
        quill_carriage.RAIL_CARRIAGE_Y_OFFSET = self.RAIL_CARRIAGE_Y_OFFSET

        assembly = (
            cq.Assembly()
            .add(
                self.make_mast_spine(self.spine_length),
                name="extrusion",
                loc=Location((0, 0, 0)),
                color=Color("lightgray"),
            )
            .add(
                self.make_mgn9_rail(self.rail_length),
                name="rail",
                loc=Location((self.rail_x(), 0, self.RAIL_START_Y)),
                color=Color("green"))
            .add(
                bearing.make(),
                name="bottom_bearing",
                loc=Location((10, 0, 0)),
                color=Color("red"),
            )
            .add(
                bearing.make(),
                name="top_bearing",
                loc=Location((10, 0, 400)),
                color=Color("red"),
            )
            .add(
                self.make_mgn9_carriage(True),
                name="carriage1",
                loc=Location((10, 0, self.QUILL_CARRIAGE_DISPLAY_HEIGHT + self.RAIL_CARRIAGE_Y_OFFSET)),
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
                loc=Location((self.leadscrew_x(), 0, self.QUILL_CARRIAGE_DISPLAY_HEIGHT + self.QUILL_CARRIAGE_NUT_DEPTH)),
                color=Color("orange"),
            )
            .add(
                quill_carriage.make(),
                name="hinge",
                loc=Location((self.rail_surface_x(), 0, self.QUILL_CARRIAGE_DISPLAY_HEIGHT)),
                color=Color("purple"),
            )
            .add(
                self.quill.make_assembly(),
                name="quill_assembly",
                loc=Location((self.quill_holder_x(), 0, self.QUILL_CARRIAGE_DISPLAY_HEIGHT)),
            )
        )

        return assembly

    def export_all_parts(self):
        """Export all parts and assembly"""
        print("Exporting improved parts...")
        try:
            cq.exporters.export(LeadscrewBearingHolder().make(), "pillow_block.stl")
            print("Pillow block exported")
            cq.exporters.export(QuillCarriage.make(), "quill_hinge.stl")
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
            .box(bb.RailMGN9H.RAIL_WIDTH, length, bb.RailMGN9H.RAIL_HEIGHT, centered=(True, False, False))
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

        if orient_for_assembly:
            return (rail
                    .rotate((0, 0, 0), (1, 0, 0), 90)
                    .rotate((0, 0, 0), (0, 0, 1), 90))
        else:
            return rail

    def make_mgn9_carriage(self, orient_for_assembly=True):
        """MGN9H carriage

        Created from origin, going to +Y, top is +Z.
        Raised by clearance, assuming rail is at Z0.
        """
        carriage = (
            cq.Workplane("XY")
            .box(
                bb.RailMGN9H.CARRIAGE_WIDTH,
                bb.RailMGN9H.CARRIAGE_LENGTH,
                bb.RailMGN9H.CARRIAGE_HEIGHT,
                centered=(True, False, False),
            )
            .translate((0, 0, bb.RailMGN9H.CARRIAGE_CLEARANCE))
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
            self.leadscrew_length, self.leadscrew_dia / 2, centered=(True, True, False)
        )
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


class LeadscrewBearingHolder:
    """Bearing holder for T8 leadscrew (608ZZ recess)"""

    # Bearing-holder stuff
    LEADSCREW_HOLE_SPACE = 4.0
    LEADSCREW_DISTANCE = 20.0
    LEADSCREW_DIA = 8.0
    BOLT_HOLE_LENGTH = 8.0
    BOLT_HOLE_DIA = 5.0
    BOLT_HEAD_DIA = 10.0
    BOLT_HEAD_HEIGHT = BOLT_HEAD_DIA / 2 + 5.0
    BASE_WIDTH = 20.0

    def diagonal_length(self):
        # Don't need to go diagonal all the way to the mast.
        return self.LEADSCREW_DISTANCE - self.BOLT_HOLE_LENGTH

    def diagonal_height(self):
        # Keep some space for bolt head.
        return max(self.diagonal_length(), self.BOLT_HEAD_HEIGHT + self.BOLT_HEAD_DIA / 2)

    def cylinder_height(self):
        return bb.Bearing608ZZ.WIDTH + 5.0

    def total_height(self):
        return self.diagonal_height() + self.cylinder_height()

    def make(self, orient_for_assembly=True):
        b_w = bb.Bearing608ZZ.WIDTH
        b_od = bb.Bearing608ZZ.OD

        block_shape_pts = [
            (0, 0),
            (self.LEADSCREW_DISTANCE - self.diagonal_length(), 0),
            (self.LEADSCREW_DISTANCE, self.diagonal_height()),
            (self.LEADSCREW_DISTANCE, self.diagonal_height() + self.cylinder_height()),
            (0, self.diagonal_height() + self.cylinder_height()),
        ]

        block = (
            cq.Workplane("YZ", origin=(-self.BASE_WIDTH / 2, 0, 0))
            .polyline(block_shape_pts)
            .close()
            .extrude(self.BASE_WIDTH)
        )

        block = (
            block
            .faces(">Z")
            .workplane(offset=-(self.cylinder_height()), origin=(0, 0, 0))
            .move(0, self.LEADSCREW_DISTANCE)
            .cylinder(self.cylinder_height(), b_od / 2 + 4, centered=(True, True, False))
            # Shaft hole
            .faces(">Z")
            .workplane()
            .move(0, self.LEADSCREW_DISTANCE)
            .hole(self.LEADSCREW_DIA + self.LEADSCREW_HOLE_SPACE)
            # Bearing recess
            .faces(">Z")
            .workplane()
            .move(0, self.LEADSCREW_DISTANCE)
            .hole(b_od + 0.2, b_w)
        )

        block = block.cut(
            cq.Workplane("top", origin=(0, 0, self.BOLT_HEAD_HEIGHT))
            .cylinder(self.BOLT_HOLE_LENGTH, self.BOLT_HOLE_DIA / 2, centered=(True, True, False))
            .faces(">Y")
            .workplane()
            .cylinder(100, self.BOLT_HEAD_DIA / 2, centered=(True, True, False))
        )

        if orient_for_assembly:
            return (block
                    .rotate((0, 0, 0), (0, 0, 1), -90))
        else:
            return block


class QuillCarriage:
    """Class representing the quill carriage with hinge for the quill holder."""

    # Placeholders.
    LEADSCREW_DISTANCE = 0.0
    QUILL_HOLDER_DISTANCE = 0.0
    RAIL_CARRIAGE_Y_OFFSET = 0.0

    def make(self, orient_for_assembly=True):
        """
        Vertical carriage with bearing hinge for quill holder.
        Designed to fit on MGN9 carriage.
        """
        hinge = (cq.Workplane("XY")
                 .box(bb.RailMGN9H.CARRIAGE_WIDTH, self.QUILL_HOLDER_DISTANCE, bb.RailMGN9H.CARRIAGE_LENGTH + self.RAIL_CARRIAGE_Y_OFFSET, centered=(True, False, False))
                 .translate((0, 0, 0)))
        hinge = (
            hinge.faces("<Z")
            .workplane(offset=0)
            .move(0, -self.LEADSCREW_DISTANCE)
            .hole(10.2 + 1.0)

            .faces("<Z")
            .workplane(offset=0)
            .move(0, -self.LEADSCREW_DISTANCE)
            .hole(bb.LeadScrewT8.NUT_DIA + 1.0, 1.5 + bb.LeadScrewT8.NUT_THICKNESS)
        )
        if orient_for_assembly:
            return (hinge
                    .rotate((0, 0, 0), (0, 0, 1), -90))
        else:
            return hinge
