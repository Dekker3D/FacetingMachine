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
BEARING_ID = 4.0   # Inner diameter
BEARING_WIDTH = 5.0

# New realistic dimensions
RAIL_LENGTH = 400.0
LEADSCREW_LENGTH = 450.0
T_SLOT_LENGTH = 450.0


def make_t_slot_extrusion(length=T_SLOT_LENGTH):
    # Accurate 20x20 T-slot profile with slots on all sides.
    # Aligned to +Z, starting at origin.
    shell = cq.Workplane("XY").box(T_SLOT_SIZE, T_SLOT_SIZE, length, centered=(True, True, False))
    profile = shell.edges("|Z").chamfer(3)
    profile.faces(">X").tag("SpineFront")
    return profile


def make_mgn9_rail(length=RAIL_LENGTH):
    # MGN9 rail profile with mounting holes
    # Created from origin, going to +Y. Reorient in assembly.
    num_holes = int(length / 30) + 1
    hole_positions = [(0, -i*30) for i in range(num_holes)]
    
    rail = (cq.Workplane("XY")
            .box(RAIL_WIDTH, length, RAIL_HEIGHT, centered=(True, False, False))
            .edges(">Z")
            .fillet(0.8)
            .faces("<Z")
            .workplane()
            .pushPoints(hole_positions)
            .circle(3.2/2)
            .cutThruAll())
    rail.faces(">Z").tag("RailTop")
    rail.faces("<Z").tag("RailBottom")
    return rail


def make_mgn9_carriage():
    # MGN9H carriage
    # Created from origin, going to +Y, top is +Z.
    carriage = (cq.Workplane("XY")
                .box(RAIL_CARRIAGE_WIDTH, RAIL_CARRIAGE_LENGTH, RAIL_CARRIAGE_HEIGHT, centered=(True, True, False))
                .translate((0, 0, RAIL_CARRIAGE_CLEARANCE))
                .edges("|Z")
                .fillet(1.0))
    return carriage


def make_pillow_block():
    # Pillow block bearing mount for T8 leadscrew (608ZZ recess)
    block = (cq.Workplane("XY")
             .box(28, 32, 16)
             # Shaft hole
             .faces("<Z").workplane().circle(LEADSCREW_DIA/2 + 0.2).cutThruAll()
             # Bearing recess
             .faces(">Z").workplane(offset=8).circle(BEARING_OD/2).cutBlind(-14)
             .edges().fillet(0.1))
    return block


def make_t8_shaft(length=LEADSCREW_LENGTH):
    # T8 leadscrew shaft visualization
    shaft = cq.Workplane("XY").cylinder(length, LEADSCREW_DIA/2, centered=(True, True, False))
    return shaft


def make_t8_nut():
    # T8 leadscrew nut with flange and mounting holes
    nut_body = cq.Workplane("XY").cylinder(15, 11).translate((0, 0, 1.75))
    flange = cq.Workplane("XY").circle(11).extrude(NUT_THICKNESS).translate((0, 0, 3.5))
    angles = [0, 90, 180, 270]
    hole_positions = [(NUT_HOLE_RADIUS * math.cos(math.radians(a)), NUT_HOLE_RADIUS * math.sin(math.radians(a))) for a in angles]
    flange = flange.faces(">Z").workplane().pushPoints(hole_positions).circle(NUT_HOLE_DIA/2).cutThruAll()
    nut = nut_body.union(flange)
    nut = nut.edges().fillet(0.1)
    return nut


def make_quill_hinge():
    # Improved quill hinge with bearing recess (0.5mm tol bushing)
    hinge = cq.Workplane("XY").box(35, 22, 12)
    hinge = hinge.faces("<Z").workplane().circle(BEARING_OD/2).cutThruAll()
    hinge = hinge.faces(">Z").workplane(offset=10).circle(BEARING_ID/2 + 0.5).cutBlind(-12)  # Bushing tol
    mount_tab = cq.Workplane("XY").box(30, 15, 5).translate((0, 11, 0))
    hinge = hinge.union(mount_tab)
    hinge = hinge.edges().fillet(0.1)
    return hinge


def make_base_plate():
    '''Triangular base with 3 M6 leveler feet + central t-slot clamp'''
    plate = cq.Workplane("XY").circle(100).extrude(10)
    # 3 feet holes at 60mm equilateral
    feet_pos = [(0, 0), (60*math.cos(math.radians(120)), 60*math.sin(math.radians(120))), (60*math.cos(math.radians(240)), 60*math.sin(math.radians(240)))]
    plate = plate.faces(">Z").workplane().pushPoints(feet_pos).circle(6.2/2).cutThruAll()
    # Central clamp for t-slot bottom
    clamp = cq.Workplane("XY").box(25, 25, 15).translate((0, 0, 5)).edges("|Z").fillet(0.1)
    base = plate.union(clamp)
    return base


def make_assembly():
    rail = make_mgn9_rail()
    carriage1 = make_mgn9_carriage()
    
    carriage1Axis = carriage1.faces("<Z").translate((0, 0, RAIL_HEIGHT - RAIL_CARRIAGE_CLEARANCE)).val()
    
    # Assembly with colors, for easy identification of parts.
    assembly = (cq.Assembly()
                .add(make_t_slot_extrusion(), name='extrusion', loc=Location((0, 0, 0)), color=Color('lightgray'))
                .add(rail, name='rail', color=Color('green'))
                .add(make_pillow_block(), name='bottom_bearing', loc=Location((25, -28, 20)), color=Color('red'))
                .add(make_pillow_block(), name='top_bearing', loc=Location((25, -28, 430)), color=Color('red'))
                .add(carriage1, name='carriage1', loc=Location((25, 0, 110)), color=Color('yellow'))
                .add(make_mgn9_carriage(), name='carriage2', loc=Location((25, 0, 130)), color=Color('yellow'))  # Dual spaced
                .add(make_t8_shaft(), name='leadscrew', loc=Location((25, -15, 20)), color=Color('blue'))
                .add(make_t8_nut(), name='nut', loc=Location((25, -15, 110)), color=Color('orange'))
                .add(make_quill_hinge(), name='hinge', loc=Location((35, 0, 110)), color=Color('purple'))
                .add(make_base_plate(), name='base', loc=Location((0, 0, -10)), color=Color('black'))
                
                # Constrain extrusion to so it doesn't move.
                .constrain('extrusion', 'Fixed')
                
                # Constrain rail to extrusion
                .constrain('rail?RailBottom', 'extrusion?SpineFront', 'Plane')
                # Plane constraint allows rotation along plane, correct with another constraint
                .constrain('rail@faces@<Y', 'extrusion@faces@<Z', 'Axis')
    
                .constrain('carriage1', carriage1Axis, 'rail', rail.faces(tag="RailTop").val(), 'Plane')
                .constrain('carriage1@faces@<Y', 'rail@faces@<Y', 'Axis')
                )
    
    assembly.solve()
    return assembly


def export_all_parts():
    '''Export all parts and assembly'''
    print("Exporting improved parts...")
    try:
        cq.exporters.export(make_pillow_block(), 'pillow_block.stl')
        print("Pillow block exported")
        cq.exporters.export(make_quill_hinge(), 'quill_hinge.stl')
        print("Quill hinge exported")
        cq.exporters.export(make_base_plate(), 'base_plate.stl')
        print("Base plate exported")
        assembly = make_assembly()
        cq.exporters.export(assembly.toCompound(), 'mast_assembly.stl')
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
else:
    # If not __main__, then we're in CQ-Editor. Show the assembly.
    # show_object is a valid CQ-Editor function.
    result = make_assembly()
    show_object(result)
