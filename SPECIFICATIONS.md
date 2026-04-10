# Gem Faceting Machine - Component Specifications

## Off-the-Shelf Components

### T8 Leadscrew (AliExpress)
- **Type**: Simple screw thread (not ball screw)
- **Diameter**: 8mm
- **Pitch**: 2mm
- **Length**: 300mm
- **Nut specifications**:
  - Diameter: 22mm
  - Thickness: 3.5mm
  - Flange diameter: 22mm
  - Mounting holes: 4x ø3.5mm
  - Hole spacing: 8mm radius from center (16mm diameter)
  - Mounting: Wood screws into 3D printed part

### MGN9H Linear Rail System
- **Rail dimensions**:
  - Width: 9mm
  - Height: 6.5mm
  - Length: To be determined based on travel needs
- **Carriage dimensions**:
  - Width: 20mm
  - Length: 39.9mm
  - Height: 8mm
  - Overhang: 10mm from rail surface
  - Clearance below carriage: 2mm
- **Mounting holes**:
  - Spacing: 15mm left/right, 16mm along length
  - Fasteners: M3x8 bolts (estimated)
- **Configuration**: Two carriages on single rail for stiffness

### Aluminum Extrusion
- **Type**: 20x20mm T-slot extrusion
- **Function**: Main structural mast replacement
- **T-slot**: 10mm wide, 6mm deep, positioned at ±2mm from center

### Bearing Components
- **Leadscrew bearings**: Standard 8mm ID bearings (to be sourced)
- **Hinge bearings**: 15mm OD bearings for quill assembly interface
- **Quill bushing**: Interface with existing quill assembly

## Design Layout
- **Linear rail**: Mounted directly against 20x20mm extrusion
- **Leadscrew**: Positioned in front of the linear rail
- **Carriage system**: Two carriages on single rail for stability
- **Height adjustment**: Leadscrew with manual knob control
- **Quill interface**: Hinge system with 15mm OD bearings

## Current Machine Reference
- **Original mast**: 14.5mm diameter rod
- **Quill assembly**: Uses 15mm long bushing with 0.5mm tolerance
- **Current issues**: Rough surface, poor sliding/rotation