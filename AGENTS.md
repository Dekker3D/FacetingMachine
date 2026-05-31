# AGENTS.md — Gem Faceting Machine

An open-hardware CAD project for a precision gem faceting machine, built with CadQuery and designed for 3D printing + off-the-shelf parts.

## Project Overview

This project produces parametric, modular CAD models of a gem faceting machine. The goal is a machine anyone can build with a 3D printer, common hardware, and AliExpress-sourced linear motion components.

**Key principles:**
- **Reproducible:** No thread tapping required. All threaded inserts must be heat-set or captive-nut designs. Wood-screws in plastic are also okay. A novice with a 3D printer should be able to build this.
- **Modular:** Every subsystem (frame, mast, quill, lap, joints) is replaceable. Swap a part, swap its assembly class, everything still fits.
- **Parametric:** Key dimensions (dop stick diameter, collet size, bearing sizes) are configurable at the assembly level.

## Repository Structure

```
FacetingMachine/
├── AGENTS.md              # This file
├── README.md              # Human-facing project overview
├── machine_assembly.py    # Top-level: pick your parts here
├── machine.py             # Legacy config (being phased out)
├── bom_part_data.py       # BOM infrastructure (PrintedPart, PartAssembly, BOM)
├── bought_bits.py         # Off-the-shelf components (bearings, rails, leadscrews)
├── frame/                 # Frame subsystem
│   ├── frame_assembly.py  # FrameAssemblyStandardMk1
│   └── frame_abstract.py  # Base class
├── mast/                  # Mast subsystem (vertical carriage + leadscrew)
│   ├── mast_assembly.py   # MastAssemblyStandardMk1
│   ├── mast_abstract.py   # Base class
│   └── handwheel.py       # Leadscrew handwheel
├── quill/                 # Quill subsystem (holds the dop stick)
│   ├── quill_assembly.py  # QuillAssemblyStandardMk1
│   └── quill_abstract.py  # Base class
├── quill_joint/           # Joint connecting quill to mast carriage
│   ├── quill_joint.py     # Specific joint implementations
│   └── quill_joint_abstract.py
├── frame_mast_joint/      # Joint connecting mast to frame rails
│   ├── frame_mast_joint.py
│   └── frame_mast_joint_abstract.py
├── lap/                   # Lap (spinning grinding/polishing disc)
│   ├── lap_assembly.py    # LapAssemblyStandardMk1
│   └── lap_abstract.py
├── docs/                  # Human-facing documentation
│   ├── OFF_THE_SHELF.md   # Dimensions for bought parts
│   ├── BOM_ESTIMATE.md    # Cost estimate
│   └── agents/            # Agent-facing documentation (put new agent-facing files here)
└── export/                # Generated STEP/STL exports and BOM
```

**Rule:** Any agent-oriented documentation besides this file goes into `docs/agents/`. Keep the root clean.

## Architecture: Assembly/Part Pattern

### The Math Rule (CRITICAL)

**All dimensions live on assembly classes as classmethods. They are never stored in instance variables.**

If `dim_a` calls `dim_b` and `dim_b` calls `dim_a`, you get an infinite recursion → instant bug detection. No silent inconsistencies.

```python
class MastAssemblyStandardMk1:
    @classmethod
    def leadscrew_x(cls):
        # References bought_bits and other classmethods on this assembly
        return cls.leadscrew_rail_spacing() + cls.rail_surface_x()

    @classmethod
    def rail_surface_x(cls):
        return bb.RailMGN15H.total_height() + cls.rail_x()
```

### Assemblies Own the Math

An assembly class:
1. Declares all dimensions as classmethods (calling other classmethods or bought_bits)
2. Creates part instances with dimensions injected at construction
3. Provides `make_assembly()` returning a `cq.Assembly`
4. Provides `get_BOM()` returning a `BOM`

### Parts Are Dumb Receivers

A part class:
1. Receives dimensions in `__init__()`
2. Provides `get_object()` returning a `cq.Workplane`
3. Extends `PrintedPart` (for 3D-printed parts) or `BoughtPartWithModel` (for off-the-shelf)
4. **Does not do math.** It builds geometry from what it's given.

```python
class BearingHolder(bpd.PrintedPart):
    def __init__(self, bearing_od: float, bearing_width: float, length: float):
        self.bearing_od = bearing_od
        self.bearing_width = bearing_width
        self.length = length
        super().__init__(name="Bearing Holder")

    def get_object(self) -> cq.Workplane:
        # Build geometry using self.bearing_od, etc.
        ...
```

### Naming Convention: Design Versions

All classes for the standard design use the `StandardMk1` suffix:
- `MastAssemblyStandardMk1`
- `QuillAssemblyStandardMk1`
- `FrameAssemblyStandardMk1`

New designs use different prefixes (e.g., `SlimMk1`, `LargeFormatMk1`). Iterations on the same design increment the Mk number. This keeps class names descriptive without being absurdly long.

### Joint Architecture

Joints connect two assemblies. They are pure classmethod classes — no abstract bases, no instance wiring. Assemblies import their specific joint class and call its classmethods directly. Joints only reference `bought_bits` and basic geometry, never assemblies (avoids circular imports).

```python
class QuillHolderJointStandardMk1:
    @classmethod
    def space_needed_carriage_x(cls):
        return ...

    @classmethod
    def offset_carriage_z(cls):
        return ...
```

An assembly that needs a different joint simply imports a different joint class. Python's module system handles the polymorphism.

### The Top-Level Shopping List

`machine_assembly.py` is the configuration file. It wires assemblies together:

```python
class MachineAssemblyStandardMk1(bpd.PartAssembly):
    frame = FrameAssemblyStandardMk1()
    mast = MastAssemblyStandardMk1()
    lap = LapAssemblyStandardMk1()
    
    frame.lap = lap
    frame.mast = mast
    mast.quill_joint = QuillHolderJointStandardMk1()
    mast.quill = QuillAssemblyStandardMk1()
```

## Development Setup

### Previewing
Download [CQ-Editor](https://github.com/CadQuery/CQ-editor/releases), open it, and open `machine_assembly.py`. Run it to preview the entire machine.

### Exporting
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install cadquery
# Export via machine_assembly.py's export_everything()
```

### Coordinate System
- **+X**: Left (toward the lap from the mast)
- **+Y**: Forward
- **+Z**: Up

## Design Constraints

- **Printer bed:** 200×200mm (minus 10mm margin for brim)
- **No thread tapping:** All threaded features use heat-set inserts, captive nuts, or printed threads designed for plastic
- **Off-the-shelf only:** All non-printed parts must be sourceable from AliExpress or standard hardware suppliers
- **Dop stick diameter:** 6mm default, but parametric for alternative sizes
- **Key dimensions:** Bearing sizes, rail types, and extrusion sizes defined in `bought_bits.py`

## BOM (Bill of Materials)

The BOM system (`bom_part_data.py`) tracks all parts with quantities and prices:
- `PartWithMetadata` — base class with name, description, price
- `PrintedPart` — 3D-printed part with export capability (STL, STEP)
- `BoughtPartWithModel` — off-the-shelf part with optional visual model
- `BOM` — dictionary-based collection with merge, text export, and batch part export

Each assembly's `get_BOM()` returns its parts. `machine_assembly.py` merges all BOMs for the full project.

## Contributing

### Adding a New Part Variant
1. Create a new class with the design prefix (e.g., `QuillAssemblySlimMk1`)
2. All math as classmethods, parts as dumb receivers
3. Follow the existing abstract base if one exists
4. Add your assembly to `machine_assembly.py` as an alternative configuration

### Adding New Agent Documentation
Put it in `docs/agents/`. This keeps the root directory clean and separates machine-facing docs from human-facing ones.

### Code Style
- CadQuery uses millimeters throughout
- Classmethods for all dimensions
- No silent defaults — every dimension must have a visible origin (either a classmethod or a parameter)
- Filenames: snake_case, descriptive
