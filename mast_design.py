import cadquery as cq
import math

def make_bearing_mount():
    """Simple bearing mount using basic operations"""
    result = cq.Workplane("XY")
    
    # Base cylinder
    result = result.cylinder(20, LEADSCREW_DIA/2 + 5)
    
    # Bearing hole - subtract using workplane
    result = result.faces(">Z").workplane().circle(BEARING_OD/2).cutBlind(-BEARING_WIDTH)
    
    # Leadscrew hole
    result = result.faces(">Z").workplane().circle(LEADSCREW_DIA/2 + 0.1).cutBlind(-20)
    
    # Mounting tab
    tab = cq.Workplane("XY").box(15, 8, 8).translate([0, -T_SLOT_SIZE/2 - 4, 0])
    result = result.union(tab)
    
    return result

def make_carriage_adapter():
    """Simple carriage adapter"""
    result = cq.Workplane("XY")
    
    # Main block
    result = result.box(40, 25, 15)
    
    # Carriage pocket
    result = result.faces("<Z").workplane(offset=7.5).rect(32, 24).cutBlind(-15)
    
    # Nut pocket
    result = result.faces(">Z").workplane().circle(NUT_DIA/2 + 2).cutBlind(-15)
    
    # Mounting holes
    for angle in [0, 90, 180, 270]:
        hole_x = NUT_HOLE_RADIUS * math.cos(math.radians(angle))
        hole_y = NUT_HOLE_RADIUS * math.sin(math.radians(angle))
        result = result.faces(">Z").workplane().circle(NUT_HOLE_DIA/2).cutBlind(-15).translate([hole_x, hole_y, 0])
    
    return result

def make_hinge():
    """Simple hinge system"""
    result = cq.Workplane("XY")
    
    # Main cylinder
    result = result.cylinder(BEARING_WIDTH + 10, BEARING_OD/2 + 2)
    
    # Bearing hole
    result = result.faces(">Z").workplane().circle(BEARING_OD/2).cutBlind(-BEARING_WIDTH)
    
    # Pin hole
    result = result.faces(">Z").workplane().circle(4).cutBlind(-BEARING_WIDTH - 10)
    
    # Mounting face
    mount = cq.Workplane("XY").box(30, 20, 5).translate([0, 0, -BEARING_WIDTH - 2.5])
    result = result.union(mount)
    
    return result

def export_parts():
    """Export parts using minimal operations"""
    print("Creating parts...")
    
    try:
        # Bearing mounts
        top_bearing = make_bearing_mount().translate([0, 0, 100])
        cq.exporters.export(top_bearing, 'top_bearing_mount.stl')
        print("Top bearing mount exported")
        
        bottom_bearing = make_bearing_mount().translate([0, 0, 0])
        cq.exporters.export(bottom_bearing, 'bottom_bearing_mount.stl')
        print("Bottom bearing mount exported")
        
        # Carriage adapter
        adapter = make_carriage_adapter()
        cq.exporters.export(adapter, 'carriage_adapter.stl')
        print("Carriage adapter exported")
        
        # Hinge
        hinge = make_hinge()
        cq.exporters.export(hinge, 'quill_hinge.stl')
        print("Hinge exported")
        
        print("All parts exported successfully!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Set parameters
    T_SLOT_SIZE = 20.0
    LEADSCREW_DIA = 8.0
    BEARING_OD = 15.0
    BEARING_WIDTH = 7.0
    NUT_DIA = 22.0
    NUT_HOLE_DIA = 3.5
    NUT_HOLE_RADIUS = 8.0
    
    success = export_parts()
    if success:
        print("Design complete!")
    else:
        print("Design failed - need different approach")