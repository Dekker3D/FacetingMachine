import cadquery as cq
import math
from cadquery import Location, Color
from quill_assembly import QuillAssembly
from machine import MachineConfig as cfg
import bought_bits as bb

# REMINDER: +X is right, +Y is forwards, +Z is up!
# The mast faces left (+X), the lap is to the left of the mast.

# Distance from mast surface to center of leadscrew, includes clearance
SCREW_DISTANCE_FROM_MAST = bb.RailMGN9H.total_height() + bb.LeadScrewT8.NUT_DIA / 2 + 5.0

RAIL_X = cfg.MAST_EXT_THICKNESS / 2
RAIL_SURFACE_X = bb.RailMGN9H.total_height() + RAIL_X
LEADSCREW_RAIL_SPACING = bb.LeadScrewT8.NUT_DIA / 2 + 5.0
LEADSCREW_X = LEADSCREW_RAIL_SPACING + RAIL_SURFACE_X
QUILL_HOLDER_X = LEADSCREW_X + bb.LeadScrewT8.NUT_DIA / 2 + cfg.QC_JOINT_DIA / 2 + 5.0

DESIRED_TRAVEL_HEIGHT = 300.0  # Desired vertical travel of the quill holder.

LEADSCREW_BEARING_HEIGHT = 15.0
RAIL_START_Y = LEADSCREW_BEARING_HEIGHT

QUILL_CARRIAGE_NUT_DEPTH = bb.LeadScrewT8.NUT_THICKNESS + 1.5
RAIL_CARRIAGE_Y_OFFSET = 10.0 + QUILL_CARRIAGE_NUT_DEPTH

QUILL_CARRIAGE_DISPLAY_HEIGHT = RAIL_START_Y + 100.0  # Height of the quill carriage for visualization.


def make_mast_spine(length=cfg.MAST_SPINE_LENGTH):
    """20x20 T-slot profile.

    Aligned to +Z, starting at origin.
    """

    shell = cq.Workplane("XY").box(
        cfg.MAST_EXT_THICKNESS, cfg.MAST_EXT_WIDTH, length, centered=(True, True, False)
    )
    profile = shell.edges("|Z").chamfer(3)
    profile.faces(">X").tag("SpineFront")
    return profile


def make_mgn9_rail(length=cfg.MAST_RAIL_LENGTH, orient_for_assembly=True):
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


def make_mgn9_carriage(orient_for_assembly=True):
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


class LeadscrewBearingHolder:
    """Bearing holder for T8 leadscrew (608ZZ recess)"""

    LEADSCREW_HOLE_SPACE = 4.0
    BOLT_HOLE_LENGTH = 8.0
    BOLT_HOLE_DIA = 5.0
    BOLT_HEAD_DIA = 10.0
    BOLT_HEAD_HEIGHT = BOLT_HEAD_DIA / 2 + 5.0

    def leadscrew_dist(self):
        return LEADSCREW_X - RAIL_X

    def diagonal_length(self):
        # Don't need to go diagonal all the way to the mast.
        return self.leadscrew_dist() - self.BOLT_HOLE_LENGTH

    def diagonal_height(self):
        # Keep some space for bolt head.
        return max(self.diagonal_length(), self.BOLT_HEAD_HEIGHT + self.BOLT_HEAD_DIA / 2)

    def cylinder_height(self):
        return bb.Bearing608ZZ.WIDTH + 5.0

    def total_height(self):
        return self.diagonal_height() + self.cylinder_height()

    def make(self, orient_for_assembly=True):
        ls_dist = LEADSCREW_X - RAIL_X
        b_w = bb.Bearing608ZZ.WIDTH
        b_od = bb.Bearing608ZZ.OD

        block_shape_pts = [
            (0, 0),
            (ls_dist - self.diagonal_length(), 0),
            (ls_dist, self.diagonal_height()),
            (ls_dist, self.diagonal_height() + self.cylinder_height()),
            (0, self.diagonal_height() + self.cylinder_height()),
        ]

        block = (
            cq.Workplane("YZ", origin=(-cfg.MAST_EXT_WIDTH / 2, 0, 0))
            .polyline(block_shape_pts)
            .close()
            .extrude(cfg.MAST_EXT_WIDTH)
        )

        block = (
            block
            .faces(">Z")
            .workplane(offset=-(self.cylinder_height()), origin=(0, 0, 0))
            .move(0, ls_dist)
            .cylinder(self.cylinder_height(), b_od / 2 + 4, centered=(True, True, False))
            # Shaft hole
            .faces(">Z")
            .workplane()
            .move(0, ls_dist)
            .hole(cfg.LEADSCREW_DIA + self.LEADSCREW_HOLE_SPACE)
            # Bearing recess
            .faces(">Z")
            .workplane()
            .move(0, ls_dist)
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


def make_t8_shaft(length=cfg.LEADSCREW_LENGTH):
    """T8 leadscrew shaft visualization"""
    shaft = cq.Workplane("XY").cylinder(
        length, cfg.LEADSCREW_DIA / 2, centered=(True, True, False)
    )
    return shaft


def make_t8_nut():
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


class QuillCarriage:
    """Class representing the quill carriage with hinge for the quill holder."""

    @classmethod
    def make(cls, orient_for_assembly=True):
        """
        Vertical carriage with bearing hinge for quill holder.
        Designed to fit on MGN9 carriage.
        """
        hinge = (cq.Workplane("XY")
                 .box(bb.RailMGN9H.CARRIAGE_WIDTH, QUILL_HOLDER_X - RAIL_SURFACE_X, bb.RailMGN9H.CARRIAGE_LENGTH + RAIL_CARRIAGE_Y_OFFSET, centered=(True, False, False))
                 .translate((0, 0, 0)))
        hinge = (
            hinge.faces("<Z")
            .workplane(offset=0)
            .move(0, -(LEADSCREW_X - RAIL_SURFACE_X))
            .hole(10.2 + 1.0)

            .faces("<Z")
            .workplane(offset=0)
            .move(0, -(LEADSCREW_X - RAIL_SURFACE_X))
            .hole(bb.LeadScrewT8.NUT_DIA + 1.0, 1.5 + bb.LeadScrewT8.NUT_THICKNESS)
        )
        if orient_for_assembly:
            return (hinge
                    .rotate((0, 0, 0), (0, 0, 1), -90))
        else:
            return hinge


class MastAssembly:
    """Class representing the entire mast assembly with all components."""

    @classmethod
    def make_assembly(cls):
        """Assemble the mast components with colors for visualization."""
        assembly = (
            cq.Assembly()
            .add(
                make_mast_spine(),
                name="extrusion",
                loc=Location((0, 0, 0)),
                color=Color("lightgray"),
            )
            .add(
                make_mgn9_rail(),
                name="rail",
                loc=Location((RAIL_X, 0, RAIL_START_Y)),
                color=Color("green"))
            .add(
                LeadscrewBearingHolder().make(),
                name="bottom_bearing",
                loc=Location((10, 0, 0)),
                color=Color("red"),
            )
            .add(
                LeadscrewBearingHolder().make(),
                name="top_bearing",
                loc=Location((10, 0, 400)),
                color=Color("red"),
            )
            .add(
                make_mgn9_carriage(True),
                name="carriage1",
                loc=Location((10, 0, QUILL_CARRIAGE_DISPLAY_HEIGHT + RAIL_CARRIAGE_Y_OFFSET)),
                color=Color("yellow"),
            )
            .add(
                make_t8_shaft(),
                name="leadscrew",
                loc=Location((LEADSCREW_X, 0, 0)),
                color=Color("blue"),
            )
            .add(
                make_t8_nut(),
                name="nut",
                loc=Location((LEADSCREW_X, 0, QUILL_CARRIAGE_DISPLAY_HEIGHT + QUILL_CARRIAGE_NUT_DEPTH)),
                color=Color("orange"),
            )
            .add(
                QuillCarriage.make(),
                name="hinge",
                loc=Location((RAIL_SURFACE_X, 0, QUILL_CARRIAGE_DISPLAY_HEIGHT)),
                color=Color("purple"),
            )
            .add(
                QuillAssembly.make_assembly(),
                name="quill_assembly",
                loc=Location((QUILL_HOLDER_X, 0, QUILL_CARRIAGE_DISPLAY_HEIGHT)),
            )
        )

        return assembly


def export_all_parts():
    """Export all parts and assembly"""
    print("Exporting improved parts...")
    try:
        cq.exporters.export(LeadscrewBearingHolder().make(), "pillow_block.stl")
        print("Pillow block exported")
        cq.exporters.export(QuillCarriage.make(), "quill_hinge.stl")
        print("Quill hinge exported")
        assembly = QuillAssembly.make_assembly()
        cq.exporters.export(assembly.toCompound(), "mast_assembly.stl")
        print("Improved assembly exported")
        print("All parts exported successfully!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    cfg.validate()  # Validate the configuration before building.
    success = export_all_parts()
    if success:
        print("Design complete!")
    else:
        print("Design failed - need different approach")
elif __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    cfg.validate()  # Validate the configuration before building.
    result = QuillAssembly.make_assembly()
    show_object(result)
