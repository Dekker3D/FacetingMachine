import cadquery as cq
import math

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
    """Simple bearing mount for leadscrew ends"""
    result = cq.Workplane("XY")
    
    # Base cylinder
    result = result.cylinder(20, LEADSCREW_DIA/2 + 5)
    
    # Bearing hole - subtract using workplane
    result = result.faces(">Z").workplane().circle(BEARING_OD/2).cutBlind(-BEARING_WIDTH)
    
    # Leadscrew hole with slight clearance
    result = result.faces(">Z").workplane().circle(LEADSCREW_DIA/2 + 0.1).cutBlind(-20)
    
    # Mounting tab for t-slot extrusion
    tab = cq.Workplane("XY").box(15, 8, 8).translate([0, -T_SLOT_SIZE/2 - 4, 0])
    result = result.union(tab)
    
    return result

def make_carriage_adapter():
    """Adapter for MGN9H carriage to connect to leadscrew nut"""
    result = cq.Workplane("XY")
    
    # Main block sized for carriage and nut
    main_block = result.box(50, 30, 20)
    
    # Carriage pocket - exact size for MGN9H carriage
    carriage_pocket = main_block.faces("<Z").workplane(offset=-10).rect(
        CARRIAGE_WIDTH + 4, CARRIAGE_LENGTH + 4
    ).cutBlind(20)
    
    # Nut pocket
    nut_pocket = carriage_pocket.faces(">Z").workplane().circle(NUT_DIA/2 + 2).cutBlind(-20)
    
    # Nut mounting holes for wood screws
    for angle in [0, 90, 180, 270]:
        hole_x = NUT_HOLE_RADIUS * math.cos(math.radians(angle))
        hole_y = NUT_HOLE_RADIUS * math.sin(math.radians(angle))
        screw_hole = nut_pocket.faces(">Z").workplane().circle(NUT_HOLE_DIA/2).cutBlind(-20).translate([hole_x, hole_y, 0])
    
    return screw_hole

def make_hinge():
    """Hinge system for quill assembly with 15mm OD bearings"""
    result = cq.Workplane("XY")
    
    # Main cylinder
    main_cylinder = result.cylinder(BEARING_WIDTH + 10, BEARING_OD/2 + 2)
    
    # Bearing hole
    bearing_hole = main_cylinder.faces(">Z").workplane().circle(BEARING_OD/2).cutBlind(-BEARING_WIDTH)
    
    # Pin hole
    pin_hole = bearing_hole.faces(">Z").workplane().circle(BEARING_ID/2).cutBlind(-BEARING_WIDTH - 10)
    
    # Mounting face
    mount = cq.Workplane("XY").box(30, 20, 5).translate([0, 0, -BEARING_WIDTH - 2.5])
    final_result = pin_hole.union(mount)
    
    return final_result

def make_linear_rail_mount():
    """Mount for MGN9H rail attached to t-slot extrusion"""
    result = cq.Workplane("XY")
    
    # Mounting plate for rail
    plate = result.box(60, 30, 8)
    
    # Rail pocket - exact size for MGN9H rail
    rail_pocket = plate.faces("<Z").workplane(offset=-4).rect(
        RAIL_WIDTH + 2, RAIL_HEIGHT + 2
    ).cutBlind(-8)
    
    # Mounting holes for rail
    # Left/right holes
    for x_offset in [-MOUNTING_HOLE_LR_SPACING/2, MOUNTING_HOLE_LR_SPACING/2]:
        hole = rail_pocket.faces(">Z").workplane().circle(1.65).cutBlind(-8).translate([x_offset, 0, 0])
    
    # Up/down holes
    for y_offset in [-MOUNTING_HOLE_UD_SPACING/2, MOUNTING_HOLE_UD_SPACING/2]:
        hole = rail_pocket.faces(">Z").workplane().circle(1.65).cutBlind(-8).translate([0, y_offset, 0])
    
    return hole

def make_t_slot_piece():
    """T-slot extrusion piece for visualization"""
    # Main body
    main = cq.Workplane("XZ").box(T_SLOT_SIZE, 100, T_SLOT_SIZE, centered=[True, False, True])
    
    # T-slot on top face
    t_slot1 = main.faces(">Z").workplane().rect(10, 6).cutBlind(-8)
    
    # T-slot on bottom face
    t_slot2 = main.faces("<Z").workplane().rect(10, 6).cutBlind(-8)
    
    return t_slot2

def make_assembly():
    """Create complete assembly with proper layout"""
    # Main t-slot extrusion
    extrusion = make_t_slot_piece()
    
    # Linear rail mount (attached to extrusion)
    rail_mount = make_linear_rail_mount().translate([0, 0, 0])
    
    # Leadscrew bearing mounts (behind rail)
    top_bearing = make_bearing_mount().translate([0, -30, 200])
    bottom_bearing = make_bearing_mount().translate([0, -30, 0])
    
    # Carriage adapter (attached to rail)
    # Position: rail_height/2 + carriage_height/2 above rail mount
    rail_height_pos = RAIL_HEIGHT/2 + CARRIAGE_HEIGHT/2
    carriage_adapter = make_carriage_adapter().translate([0, rail_height_pos, 100])
    
    # Quill hinge (attached to carriage adapter)
    hinge = make_hinge().translate([0, rail_height_pos + 20, 100])
    
    # Combine all components
    assembly = extrusion.union(rail_mount).union(top_bearing).union(bottom_bearing).union(carriage_adapter).union(hinge)
    
    return assembly

def export_all_parts():
    """Export all individual parts"""
    print("Exporting parts...")
    
    try:
        # Export bearing mounts (these worked before)
        top_bearing = make_bearing_mount().translate([0, 0, 100])
        cq.exporters.export(top_bearing, 'top_bearing_mount.stl')
        print("Top bearing mount exported")
        
        bottom_bearing = make_bearing_mount().translate([0, 0, 0])
        cq.exporters.export(bottom_bearing, 'bottom_bearing_mount.stl')
        print("Bottom bearing mount exported")
        
        # Export linear rail mount
        rail_mount = make_linear_rail_mount()
        cq.exporters.export(rail_mount, 'linear_rail_mount.stl')
        print("Linear rail mount exported")
        
        # Export carriage adapter
        adapter = make_carriage_adapter()
        cq.exporters.export(adapter, 'carriage_adapter.stl')
        print("Carriage adapter exported")
        
        # Export hinge
        hinge = make_hinge()
        cq.exporters.export(hinge, 'quill_hinge.stl')
        print("Hinge exported")
        
        # Export t-slot piece
        t_slot = make_t_slot_piece()
        cq.exporters.export(t_slot, 't_slot_piece.stl')
        print("T-slot piece exported")
        
        # Export assembly
        assembly = make_assembly()
        cq.exporters.export(assembly, 'mast_assembly.stl')
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
    result = make_assembly()
    show_object(result)