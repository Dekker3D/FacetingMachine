import cadquery as cq
import math
from cadquery import Location

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

def make_bearing_mount():
    '''Simple bearing mount for leadscrew ends'''
    result = (cq.Workplane("XY")
              .cylinder(20, LEADSCREW_DIA/2 + 5)
              .faces(">Z").workplane()
              .circle(BEARING_OD/2).cutBlind(-BEARING_WIDTH)
              .faces(">Z").workplane()
              .circle(LEADSCREW_DIA/2 + 0.1).cutBlind(-20))
    
    # Mounting tab for t-slot extrusion
    tab = (cq.Workplane("XY")
           .box(15, 8, 8)
           .translate((0, -T_SLOT_SIZE/2 - 4, 0)))
    return result.union(tab)

def make_carriage_adapter():
    '''Adapter for MGN9H carriage to connect to leadscrew nut'''
    result = cq.Workplane("XY").box(50, 30, 20)
    
    # Carriage pocket from bottom
    result = result.faces("<Z").workplane().rect(CARRIAGE_WIDTH + 4, CARRIAGE_LENGTH + 4).cutBlind(20)
    
    # Nut pocket from top
    result = result.faces(">Z").workplane().circle(NUT_DIA/2 + 2).cutBlind(-20)
    
    # Nut mounting holes (batch cut)
    hole_positions = [(NUT_HOLE_RADIUS * math.cos(math.radians(a)), NUT_HOLE_RADIUS * math.sin(math.radians(a))) for a in [0, 90, 180, 270]]
    result = result.faces(">Z").workplane().pushPoints(hole_positions).circle(NUT_HOLE_DIA/2).cutBlind(-20)
    
    return result

def make_hinge():
    '''Hinge system for quill assembly with 15mm OD bearings'''
    result = (cq.Workplane("XY")
              .cylinder(BEARING_WIDTH + 10, BEARING_OD/2 + 2)
              .faces(">Z").workplane()
              .circle(BEARING_OD/2).cutBlind(-BEARING_WIDTH)
              .faces(">Z").workplane()
              .circle(BEARING_ID/2).cutBlind(-BEARING_WIDTH - 10))
    
    # Mounting face
    mount = (cq.Workplane("XY")
             .box(30, 20, 5)
             .translate((0, 0, -BEARING_WIDTH - 2.5)))
    return result.union(mount)

def make_linear_rail_mount():
    '''Mount for MGN9H rail attached to t-slot extrusion'''
    result = cq.Workplane("XY").box(60, 30, 8)
    
    # Rail pocket from bottom
    result = result.faces("<Z").workplane(offset=-4).rect(RAIL_WIDTH + 2, RAIL_HEIGHT + 2).cutBlind(-8)
    
    # Mounting holes (batch cut: LR ±7.5 y=0; UD x=0 ±8)
    hole_positions = [(-7.5, 0), (7.5, 0), (0, -8), (0, 8)]
    result = result.faces(">Z").workplane().pushPoints(hole_positions).circle(1.65).cutBlind(-8)
    
    return result

def make_t_slot_piece():
    '''T-slot extrusion piece for visualization'''
    # Main body (length along Y)
    main = (cq.Workplane("XZ")
            .box(T_SLOT_SIZE, 400, T_SLOT_SIZE, centered=(True, False, True)))  # Longer for assembly
    
    # T-slots
    result = main.faces(">Z").workplane().rect(10, 6).cutBlind(-8)
    result = result.faces("<Z").workplane().rect(10, 6).cutBlind(-8)
    return result

def make_assembly():
    '''Idiomatic CadQuery Assembly'''
    assembly = cq.Assembly()
    
    # Main t-slot extrusion (base, long)
    extrusion = make_t_slot_piece()
    assembly.add(extrusion, name='extrusion', loc=Location((0, 0, 0)))
    
    # Linear rail mount on extrusion
    rail_mount = make_linear_rail_mount()
    assembly.add(rail_mount, name='rail_mount', loc=Location((0, 0, 0)))
    
    # Leadscrew bearing mounts (behind rail)
    top_bearing = make_bearing_mount()
    assembly.add(top_bearing, name='top_bearing', loc=Location((0, -30, 200)))
    
    bottom_bearing = make_bearing_mount()
    assembly.add(bottom_bearing, name='bottom_bearing', loc=Location((0, -30, 0)))
    
    # Carriage adapter (mid-rail height)
    rail_mid = RAIL_HEIGHT/2 + CARRIAGE_HEIGHT/2
    carriage_adapter = make_carriage_adapter()
    assembly.add(carriage_adapter, name='carriage', loc=Location((0, rail_mid, 100)))
    
    # Quill hinge above carriage
    hinge = make_hinge()
    assembly.add(hinge, name='hinge', loc=Location((0, rail_mid + 20, 100)))
    
    return assembly

def export_all_parts():
    '''Export all individual parts + assembly'''
    print("Exporting parts...")
    
    try:
        # Individual parts (translate for separation)
        cq.exporters.export(make_bearing_mount().translate((0, 0, 100)), 'top_bearing_mount.stl')
        print("Top bearing mount exported")
        
        cq.exporters.export(make_bearing_mount(), 'bottom_bearing_mount.stl')
        print("Bottom bearing mount exported")
        
        cq.exporters.export(make_linear_rail_mount(), 'linear_rail_mount.stl')
        print("Linear rail mount exported")
        
        cq.exporters.export(make_carriage_adapter(), 'carriage_adapter.stl')
        print("Carriage adapter exported")
        
        cq.exporters.export(make_hinge(), 'quill_hinge.stl')
        print("Hinge exported")
        
        cq.exporters.export(make_t_slot_piece().translate((0, 0, 20)), 't_slot_piece.stl')
        print("T-slot piece exported")
        
        # Assembly as compound for STL
        assembly = make_assembly()
        cq.exporters.export(assembly.toCompound(), 'mast_assembly.stl')
        print("Assembly exported")
        
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