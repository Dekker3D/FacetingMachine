import cadquery as cq
import math
from cadquery import Location, Color

# REMINDER: +X is right, +Y is forwards, +Z is up!
# The mast faces left (+X), the lap is to the left of the mast.

# Design Parameters based on actual specifications
T_SLOT_SIZE = 20.0  # 20x20mm aluminum t-slot extrusion
LEADSCREW_DIA = 8.0  # T8 leadscrew diameter

# MGN9H Linear Rail Specifications
RAIL_WIDTH = 9.0
RAIL_HEIGHT = 6.5
RAIL_CARRIAGE_WIDTH = 20.0
RAIL_CARRIAGE_LENGTH = 39.9
RAIL_CARRIAGE_HEIGHT = 8.0
RAIL_TOTAL_HEIGHT = 10.0  # Total rail+carriage height
RAIL_CARRIAGE_CLEARANCE = 2.0  # Below carriage
MOUNTING_HOLE_LR_SPACING = 15.0  # Left/right spacing
MOUNTING_HOLE_UD_SPACING = 16.0  # Up/down spacing

# Leadscrew Specifications
NUT_DIA = 22.0
NUT_THICKNESS = 3.5
NUT_HOLE_DIA = 3.5
NUT_HOLE_RADIUS = 8.0  # Distance from center to hole
# Distance from mast surface to center of leadscrew, includes clearance
SCREW_DISTANCE_FROM_MAST = RAIL_TOTAL_HEIGHT + NUT_DIA / 2 + 5.0

# Bearing Specifications
# Standard bearings in 15 mm OD don't exist.
# Use 624 bearings (4x13x5 mm) with a sleeve to get to 15 mm diameter.
BEARING_OD = 13.0  # For hinge system
BEARING_ID = 4.0  # Inner diameter
BEARING_WIDTH = 5.0

# New realistic dimensions
RAIL_LENGTH = 400.0
LEADSCREW_LENGTH = 450.0
T_SLOT_LENGTH = 450.0

QUILL_CARRIAGE_JOINT_DIA = 25
QUILL_CARRIAGE_JOINT_LENGTH = 80

RAIL_X = T_SLOT_SIZE / 2
RAIL_SURFACE_X = RAIL_TOTAL_HEIGHT + RAIL_X
LEADSCREW_RAIL_SPACING = NUT_DIA / 2 + 5.0
LEADSCREW_X = LEADSCREW_RAIL_SPACING + RAIL_SURFACE_X
QUILL_HOLDER_X = LEADSCREW_X + NUT_DIA / 2 + QUILL_CARRIAGE_JOINT_DIA / 2 + 5.0


DESIRED_TRAVEL_HEIGHT = 300.0  # Desired vertical travel of the quill holder.

LEADSCREW_BEARING_HEIGHT = 15.0
RAIL_START_Y = LEADSCREW_BEARING_HEIGHT

QUILL_CARRIAGE_NUT_DEPTH = NUT_THICKNESS + 1.5
RAIL_CARRIAGE_Y_OFFSET = 10.0 + QUILL_CARRIAGE_NUT_DEPTH

QUILL_CARRIAGE_DISPLAY_HEIGHT = RAIL_START_Y + 100.0  # Height of the quill carriage for visualization.


def make_t_slot_extrusion(length=T_SLOT_LENGTH):
    """20x20 T-slot profile.

    Aligned to +Z, starting at origin.
    """

    shell = cq.Workplane("XY").box(
        T_SLOT_SIZE, T_SLOT_SIZE, length, centered=(True, True, False)
    )
    profile = shell.edges("|Z").chamfer(3)
    profile.faces(">X").tag("SpineFront")
    return profile


def make_mgn9_rail(length=RAIL_LENGTH, orient_for_assembly=True):
    """MGN9 rail profile

    Created from origin, going to +Y. Reorient in assembly.
    """

    num_holes = int(length / 30) + 1
    hole_positions = [(0, -i * 30) for i in range(num_holes)]

    rail = (
        cq.Workplane("XY")
        .box(RAIL_WIDTH, length, RAIL_HEIGHT, centered=(True, False, False))
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
            RAIL_CARRIAGE_WIDTH,
            RAIL_CARRIAGE_LENGTH,
            RAIL_CARRIAGE_HEIGHT,
            centered=(True, False, False),
        )
        .translate((0, 0, RAIL_CARRIAGE_CLEARANCE))
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


def make_pillow_block(orient_for_assembly=True):
    """Pillow block bearing mount for T8 leadscrew (608ZZ recess)"""
    block = (
        cq.Workplane("XY")
        .box(20, LEADSCREW_X - RAIL_X, BEARING_WIDTH + 5.0 + 10.0, centered=(True, False, False))
        .faces(">Z")
        .workplane(offset=-(BEARING_WIDTH + 5.0))
        .move(0, LEADSCREW_X - RAIL_X)
        .cylinder(BEARING_WIDTH + 5.0, BEARING_OD / 2 + 4, centered=(True, True, False))
        # Shaft hole
        .faces(">Z")
        .workplane()
        .move(0, LEADSCREW_X - RAIL_X)
        .hole(LEADSCREW_DIA + 0.4)
        # Bearing recess
        .faces(">Z")
        .workplane()
        .move(0, LEADSCREW_X - RAIL_X)
        .hole(BEARING_OD, BEARING_WIDTH)
    )
    if orient_for_assembly:
        return (block
                .rotate((0, 0, 0), (0, 0, 1), -90))
    else:
        return block


def make_t8_shaft(length=LEADSCREW_LENGTH):
    """T8 leadscrew shaft visualization"""
    shaft = cq.Workplane("XY").cylinder(
        length, LEADSCREW_DIA / 2, centered=(True, True, False)
    )
    return shaft


def make_t8_nut():
    """T8 leadscrew nut with flange and mounting holes"""
    nut_body = (cq.Workplane("XY")
                .cylinder(15, 5.1, centered=(True, True, False))
                .translate((0, 0, -(1.5+NUT_THICKNESS)))
                .chamfer(0.25))
    flange = (cq.Workplane("XY")
              .circle(11)
              .extrude(NUT_THICKNESS)
              .translate((0, 0, -NUT_THICKNESS))
              .chamfer(0.5))
    angles = [0, 90, 180, 270]
    hole_positions = [
        (
            NUT_HOLE_RADIUS * math.cos(math.radians(a)),
            NUT_HOLE_RADIUS * math.sin(math.radians(a)),
        )
        for a in angles
    ]
    flange = (
        flange.faces(">Z")
        .workplane()
        .pushPoints(hole_positions)
        .circle(NUT_HOLE_DIA / 2)
        .cutThruAll()
    )
    nut = nut_body.union(flange)
    return nut


def make_quill_carriage(orient_for_assembly=True):
    """
    Vertical carriage with bearing hinge for quill holder.
    Designed to fit on MGN9 carriage.
    """
    hinge = (cq.Workplane("XY")
             .box(RAIL_CARRIAGE_WIDTH, QUILL_HOLDER_X - RAIL_SURFACE_X, RAIL_CARRIAGE_LENGTH + RAIL_CARRIAGE_Y_OFFSET, centered=(True, False, False))
             .translate((0, 0, 0)))
    hinge = (
        hinge.faces("<Z")
        .workplane(offset=0)
        .move(0, -(LEADSCREW_X - RAIL_SURFACE_X))
        .hole(10.2 + 1.0)

        .faces("<Z")
        .workplane(offset=0)
        .move(0, -(LEADSCREW_X - RAIL_SURFACE_X))
        .hole(NUT_DIA + 1.0, 1.5 + NUT_THICKNESS)
    )
    if orient_for_assembly:
        return (hinge
                .rotate((0, 0, 0), (0, 0, 1), -90))
    else:
        return hinge


def make_base_plate():
    """Triangular base with 3 M6 leveler feet + central t-slot clamp"""
    plate = cq.Workplane("XY").circle(100).extrude(10)
    # 3 feet holes at 60mm equilateral
    feet_pos = [
        (0, 0),
        (60 * math.cos(math.radians(120)), 60 * math.sin(math.radians(120))),
        (60 * math.cos(math.radians(240)), 60 * math.sin(math.radians(240))),
    ]
    plate = (
        plate.faces(">Z").workplane().pushPoints(feet_pos).circle(6.2 / 2).cutThruAll()
    )
    # Central clamp for t-slot bottom
    clamp = (
        cq.Workplane("XY").box(25, 25, 15).translate((0, 0, 5)).edges("|Z").fillet(0.1)
    )
    base = plate.union(clamp)
    return base


def make_assembly():
    """Assemble the mast components with colors for visualization."""
    assembly = (
        cq.Assembly()
        .add(
            make_t_slot_extrusion(),
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
            make_pillow_block(),
            name="bottom_bearing",
            loc=Location((10, 0, 0)),
            color=Color("red"),
        )
        .add(
            make_pillow_block(),
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
            make_quill_carriage(),
            name="hinge",
            loc=Location((RAIL_SURFACE_X, 0, QUILL_CARRIAGE_DISPLAY_HEIGHT)),
            color=Color("purple"),
        )
        .add(
            make_base_plate(),
            name="base",
            loc=Location((0, 0, -10)),
            color=Color("black"),
        )
    )

    return assembly


def export_all_parts():
    """Export all parts and assembly"""
    print("Exporting improved parts...")
    try:
        cq.exporters.export(make_pillow_block(), "pillow_block.stl")
        print("Pillow block exported")
        cq.exporters.export(make_quill_carriage(), "quill_hinge.stl")
        print("Quill hinge exported")
        cq.exporters.export(make_base_plate(), "base_plate.stl")
        print("Base plate exported")
        assembly = make_assembly()
        cq.exporters.export(assembly.toCompound(), "mast_assembly.stl")
        print("Improved assembly exported")
        print("All parts exported successfully!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = export_all_parts()
    if success:
        print("Design complete!")
    else:
        print("Design failed - need different approach")
elif __name__ == "__cq_main__":
    # We're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    result = make_assembly()
    show_object(result)
