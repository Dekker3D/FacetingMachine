# Gem Faceting Machine - Open Hardware Project

## Overview
Open-source CAD design for a gem faceting machine, starting with a replacement mast for a Vevor imitation machine. Goal is to eventually replace the entire machine while maintaining compatibility with existing components.

## Current Machine
- **Type**: Cheap Vevor imitation (AliExpress)
- **Lap size**: 6 inch
- **Gem sizes**: 8-30mm range
- **Target**: Personal use initially, potentially open-source later

## Key Requirements
1. **Mechanical components**: Either off-the-shelf (bearings, linear rails) or fully detailed for 3D printing/production
2. **Electronics**: Space for RPM control of faceting lap (to be integrated later)
3. **Compatibility**: Maintain vague compatibility with existing machine during transition
4. **Precision**: Suitable for gem faceting applications

## Project Phases
### Phase 1: Mast Replacement
- Design replacement mast that interfaces with existing base
- Ensure proper alignment and stability for faceting operations
- Include mounting points for existing components

### Phase 2: Component-by-Component Replacement
- Replace individual mechanical parts as designs are finalized
- Maintain compatibility during transition period

### Phase 3: Full Integration
- Complete redesign with integrated electronic control
- Optimize for manufacturing and assembly

## Technical Details
- **CAD**: CadQuery (Python-based)
- **Design philosophy**: Open hardware, collaborative development
- **Target output**: 3D printable components + off-the-shelf hardware specs

## Known Limitations
- Sparse documentation on existing designs
- No image references available due to platform constraints
- Working within WSL2 Ubuntu environment (Windows CadQuery installation not directly accessible)