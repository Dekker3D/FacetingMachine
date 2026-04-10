import cadquery as cq
import math
from cadquery import Location, Color

# Design Parameters based on actual specifications
T_SLOT_SIZE = 20.0  # 20x20mm aluminum t-slot extrusion
LEADSCREW_DIA = 8.0  # T8 leadscrew diameter
LEADSCREW_PITCH = 2.0  # 2mm pitch

# MGN9H Linear Rail Specifications
RAIL_WIDTH = 9.0
RAIL_HEIGHT = 6.5
CARRIAGE_WIDTH = 20.0
CARRIAGE_LENGTH = 39.9
CARRIAGE_HEIGHT = 8.0
RAIL_TOTAL_HEIGHT = 10.0  # Total rail+carriage height
CARRIAGE_CLEARANCE = 2.0  # Below carriage
BALL_DIA = 3.0
MOUNTING_HOLE_LR_SPACING = 15.0  # Left/right spacing
MOUNTING_HOLE_UD_SPACING = 16.0  # Up/down spacing

# Leadscrew Nut Specifications
NUT_DIA = 22.0
NUT_THICKNESS = 3.5
NUT_HOLE_DIA = 3.5
NUT_HOLE_RADIUS = 8.0  # Distance from center to hole

# Bearing Specifications
BEARING_OD = 15.0  # For hinge system
BEARING_ID = 8.0   # Inner diameter
BEARING_WIDTH = 7.0

# New realistic dimensions
RAIL_LENGTH = 250.0
LEADSCREW_LENGTH = 400.0
T_SLOT_LENGTH = 450.0

def make_t_slot_extrusion(length=T_SLOT_LENGTH):
    '''Accurate 20x20 T-slot profile with slots on all sides - fixed co-planar'''
    shell = cq.Workplane("XZ").box(T_SLOT_SIZE, length, T_SLOT_SIZE)
    # Top slot
    shell = shell.faces(">Z").workplane().rect(10, 6).cutBlind(-1.5)
    # Bottom slot
    shell = shell.faces("<Z").workplane().rect(10, 6).cutBlind(-1.5)
    # Right side slot
    shell = shell.faces(">Y").workplane().rect(6, 10).cutBlind(-1.5)
    # Left side slot
    shell = shell.faces("<Y").workplane().rect(6, 10).cutBlind(-1.5)
    profile = shell.edges("|Z or |X or |Y").fillet(0.1)
    return profile

def make_mgn9_rail(length=RAIL_LENGTH):
    '''MGN9 rail profile with mounting holes'''
    rail = cq.Workplane("XY").box(RAIL_WIDTH, length, RAIL_HEIGHT)
    rail = rail.edges(">Z").fillet(0.8)
    # Mounting holes every 30mm
    num_holes = int(length / 30) + 1
    hole_positions = [(RAIL_WIDTH/2 + i*30, 0) for i in range(num_holes)]
    rail = rail.faces(">Z").workplane().pushPoints(hole_positions).circle(3.2/2).cutThruAll()
    return rail

def make_mgn9_carriage():
    '''MGN9H carriage'''
    carriage = cq.Workplane("XY").box(CARRIAGE_WIDTH, CARRIAGE_LENGTH, CARRIAGE_HEIGHT).translate((0, 0, RAIL_HEIGHT/2 + CARRIAGE_HEIGHT/2 - CARRIAGE_CLEARANCE))
    carriage = carriage.edges("|Z").fillet(0.1)
    return carriage

def make_pillow_block():
    '''Pillow block bearing mount for T8 leadscrew (608ZZ recess)'''
    block = cq.Workplane("XY").box(28, 32, 16)
    # Shaft hole
    block = block.faces("<Z").workplane().circle(LEADSCREW_DIA/2 + 0.2).cutThruAll()
    # Bearing recess
    block = block.faces(">Z").workplane(offset=8).circle(BEARING_OD/2).cutBlind(-14)
    # Mounting tabs with M4 holes
    tabs = (cq.Workplane("XY").box(22, 12, 6).translate((0, -16, -5))
            .faces(">Z").workplane().pushPoints([(-9, 0), (9, 0)]).circle(4.2/2).cutThruAll())
    block = block.union(tabs)
    block = block.edges().fillet(0.1)
    return block

def make_t8_shaft(length=LEADSCREW_LENGTH):
    '''T8 leadscrew shaft visualization'''
    shaft = cq.Workplane("XY").cylinder(length, LEADSCREW_DIA/2).translate((0, -15, 225))
    return shaft

def make_t8_nut():
    '''T8 leadscrew nut with flange and mounting holes'''
    nut_body = cq.Workplane("XY").cylinder(15, 11).translate((0, 0, 1.75))
    flange = cq.Workplane("XY").circle(11).extrude(NUT_THICKNESS).translate((0, 0, 3.5))
    angles = [0, 90, 180, 270]
    hole_positions = [(NUT_HOLE_RADIUS * math.cos(math.radians(a)), NUT_HOLE_RADIUS * math.sin(math.radians(a))) for a in angles]
    flange = flange.faces(">Z").workplane().pushPoints(hole_positions).circle(NUT_HOLE_DIA/2).cutThruAll()
    nut = nut_body.union(flange)
    nut = nut.edges().fillet(0.1)
    return nut

def make_quill_hinge():
    '''Improved quill hinge with bearing recess (0.5mm tol bushing)'''
    hinge = cq.Workplane("XY").box(35, 22, 12)
    hinge = hinge.faces("<Z").workplane().circle(BEARING_OD/2).cutThruAll()
    hinge = hinge.faces(">Z").workplane(offset=10).circle(BEARING_ID/2 + 0.5).cutBlind(-12)  # Bushing tol
    mount_tab = cq.Workplane("XY").box(30, 15, 5).translate((0, 11, 0))
    hinge = hinge.union(mount_tab)
    hinge = hinge.edges().fillet(0.1)
    return hinge

def make_linear_rail_mount():
    '''Updated rail mount with fillets'''
    result = cq.Workplane("XY").box(60, 30, 8)
    result = result.faces("<Z").workplane(offset=-4).rect(RAIL_WIDTH + 2, RAIL_HEIGHT + 2).cutBlind(-8)
    hole_positions = [(-7.5, 0), (7.5, 0), (0, -8), (0, 8)]
    result = result.faces(">Z").workplane().pushPoints(hole_positions).circle(1.65).cutBlind(-8)
    result = result.edges().fillet(0.1)
    return result

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
    '''Improved realistic assembly with colors'''
    assembly = cq.Assembly()
    assembly.add(make_t_slot_extrusion(), name='extrusion', loc=Location((0, 0, 0)), color=Color('lightgray'))
    assembly.add(make_linear_rail_mount(), name='rail_mount', loc=Location((0, 0, 0)), color=Color('gray'))
    assembly.add(make_mgn9_rail(), name='rail', loc=Location((0, 1, 6)), color=Color('green'))
    assembly.add(make_pillow_block(), name='bottom_bearing', loc=Location((0, -28, 5)), color=Color('red'))
    assembly.add(make_pillow_block(), name='top_bearing', loc=Location((0, -28, 220)), color=Color('red'))
    assembly.add(make_mgn9_carriage(), name='carriage1', loc=Location((0, 12, 110)), color=Color('yellow'))
    assembly.add(make_mgn9_carriage(), name='carriage2', loc=Location((0, 12, 110 + 8)), color=Color('yellow'))  # Dual UD
    assembly.add(make_t8_shaft(), name='leadscrew', loc=Location((0, 0, 0)), color=Color('blue'))
    assembly.add(make_t8_nut(), name='nut', loc=Location((0, -15, 110)), color=Color('orange'))
    assembly.add(make_quill_hinge(), name='hinge', loc=Location((0, 25, 110)), color=Color('purple'))
    assembly.add(make_base_plate(), name='base', loc=Location((0, 0, -10)), color=Color('black'))
    return assembly

def export_all_parts():
    '''Export all parts and assembly'''
    print("Exporting improved parts...")
    try:
        cq.exporters.export(make_t_slot_extrusion().translate((100, 0, 0)), 't_slot_extrusion.stl')
        print("T-slot extrusion exported")
        cq.exporters.export(make_mgn9_rail(), 'mgn9_rail.stl')
        print("MGN9 rail exported")
        cq.exporters.export(make_mgn9_carriage(), 'mgn9_carriage.stl')
        print("MGN9 carriage exported")
        cq.exporters.export(make_pillow_block(), 'pillow_block.stl')
        print("Pillow block exported")
        cq.exporters.export(make_t8_shaft(100), 't8_shaft.stl')  # Short for export
        print("T8 shaft exported")
        cq.exporters.export(make_t8_nut(), 't8_nut.stl')
        print("T8 nut exported")
        cq.exporters.export(make_quill_hinge(), 'quill_hinge.stl')
        print("Quill hinge exported")
        cq.exporters.export(make_linear_rail_mount(), 'linear_rail_mount.stl')
        print("Linear rail mount exported")
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
