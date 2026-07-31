# Quill quality-pass checkpoint

Date: 2026-07-31  
Branch: `quality/quill-robustness`

This note is an agent-facing handoff for continuing the quill robustness pass in small, reviewable checkpoints. It is not a claim that the branch is ready to merge; geometry changes still require CQ-Editor/Blender inspection.

## Completed checkpoints

### Spring validation — `d33d781`

- Validates finite, positive compression-spring dimensions and integral coil count.
- Uses the modeled solid height `(coil_count + 1) * wire_diameter`.
- Rejects displayed lengths below solid height or above free length.
- Rejects quill spring/pocket combinations that cannot provide preload or fit the rocker/top.
- Adds focused configuration tests without relying on face/edge identities.

### Exact metric fasteners — `1f94af5`

- Removes `int(size)` truncation from standard bolt/nut/nyloc/washer lookup.
- Adds exact M2 and M2.5 entries alongside the existing metric sizes.
- Preserves fractional nominal sizes and lengths in names.
- Rejects unsupported standard sizes instead of silently assigning another size's geometry.

### Reusable captive-nut cutout — `ff58998`

- Adds `printed_fasteners.SideLoadedCaptiveNutHole`.
- Migrates the eight quill removable-top fastener paths to the shared cutout.
- Default old/new quill-body geometry compared equal by two-way Boolean subtraction (`0.0 mm³` both ways).
- The canonical cutout opens toward local `+Y`; callers rotate the complete cutout when needed.

#### Across-flats clarification

`nut_width_across_flats` remains the actual transverse width of both the nut pocket and loading slot. For a 5.9 mm setting, the measured local-X width is 5.9 mm.

CadQuery's regular-polygon constructor accepts a vertex-to-vertex diameter, so constructing a hex with a requested 5.9 mm across-flats size requires passing `5.9 / cos(30°)` to `polygon()`. That conversion does **not** make the slot across-corners wide. The corner radius is also used only to ensure the loading channel reaches far enough in local `+Y` to open the pocket.

## Current geometry checkpoint: inset main bearings

The next commit on this branch restores the requested bearing retention:

- Both 6001ZZ bearings are inset 1.0 mm into the main block.
- Each end has a 1.0 mm-deep lip overlapping the bearing's outer race by 1.0 mm radially.
- Default bearing-pocket depth remains derived from hardware:
  `bearing_type.WIDTH + bearing_axial_tolerance` (8.5 mm for the default 8 mm bearing and 0.5 mm tolerance).
- Default lip opening is 26 mm for the 28 mm-OD bearing.
- The index-gear spacer OD is an explicit 18 mm assembly setting.
- The gear's external spacer remains 2 mm, while its modeled ring extends an additional 1 mm through the retaining-lip opening to meet the inset bearing.
- `index_gear_width()` deliberately excludes that internal reach, so block length and the gear's external placement do not move.

Transformed-shape verification for the default configuration:

```text
gear X range:              30.0 .. 46.0 mm
index bearing X range:     46.0 .. 54.0 mm
gear/body overlap:          0.0 mm³
bearing/body overlap:       0.0 mm³
gear/bearing overlap:       0.0 mm³
gear-to-bearing face gap:   0.0 mm
```

Configuration validation rejects:

- Main-bearing ID that does not match the ER11 shank diameter.
- Negative axial tolerance.
- Lip depth outside `(0, bearing width)`.
- Lip overlap that extends beyond the outer-race radial region.
- A lip opening that blocks either the shank bore or index-gear spacer.
- Spacer OD no larger than the index-gear bore.

### Human visual checkpoint still required

Open `machine_assembly.py` in CQ-Editor and inspect both block ends, especially:

1. The 1 mm retaining lips are visible and continuous around the outer race.
2. Bearings are inset rather than flush.
3. The index-gear spacer passes through the lip without touching it.
4. The spacer bears on the bearing's inner race rather than the seal or outer race.
5. The collet-side lip does not obstruct shank/collet installation.
6. Accepted bearing-holder print orientation and split geometry remain unchanged.

Do not regenerate or commit release exports until this visual checkpoint is accepted.

## Planned next work

Continue as separate, reviewable checkpoints in this order. Do not combine all of these into one refactor.

### 1. Index-gear clamp hardware

- Replace the hardcoded M3 nut/shaft dimensions with selected `Bolt`/`Nut` objects and explicit clearances.
- Add the actual clamp screw and nut to the assembly display and BOM.
- Derive the captive-pocket angular position from tooth pitch/number layout instead of a fixed `360 / 16` assumption.
- Validate pocket, channel, bore, and outer-wall material before CadQuery operations.
- Reuse a printed-fastener utility only if the radial gear geometry genuinely matches its coordinate contract; do not force the vertical `SideLoadedCaptiveNutHole` abstraction onto it.

### 2. Assembly preflight validation

Add early, actionable validation for stable physical contracts:

- Bearing OD/pocket fit, bearing width/pocket depth, and available radial/axial material.
- Selected hardware versus clearance, pilot, head, nut, and displayed/BOM dimensions.
- Bearing-holder and cheater-top screw centers versus part bounds and edge material.
- Captive-nut drop versus available body depth.
- Minimum rocker, holder, top, handwheel, and gear-section dimensions.
- Positive gear tooth counts/depths and physically usable gear-section spans.

Keep formula ownership on `QuillAssemblyStandardMk1`; printed parts remain dimension receivers.

### 3. Angle-indicator mount specification

Create one small immutable specification shared by the joint and indicator containing:

- Screw centers.
- Selected screw model.
- Clearance/head geometry.
- Pilot geometry and engagement.
- Required edge margin.

This is an interface-consistency cleanup, not the deferred broad joint redesign.

### 4. Printed-part file split

After the preceding tests are stable, move quill printed-part/helper classes from `quill_assembly.py` to a dedicated module such as `quill/quill_parts.py`.

- Make it a pure move/import cleanup wherever possible.
- Preserve public imports or add explicit re-exports if external callers depend on current paths.
- Do not move assembly dimension formulas into part classes.
- Commit the move separately from behavior changes to keep review straightforward.

### 5. Cache API documentation/TODO

Document rather than refactor immediately:

- Cache identity currently depends on kwargs representation and mutable objects.
- Omitted defaults versus explicitly supplied defaults can produce separate entries.
- Object identity can reduce reuse for helper-containing keys.
- Cache/lifecycle behavior should be addressed project-wide, not in a quill-only patch.

### 6. Explicit build lifecycle design (design pass only)

The user wants class variables to remain convenient configuration that can be changed after object initialization but before geometry construction. Explore an explicit recursive `build()` lifecycle separately:

- Configuration references and joint endpoints are wired first.
- Parent `build()` calls child `build()` methods.
- `get_object()`, `get_assembly()`, exports, and BOM access assert that the object has been built.
- Define whether repeated `build()` calls rebuild, reject, or require an explicit invalidation/reset.
- Define cache identity and mutability rules before implementing.
- Ensure joint objects can receive references to both connected parts before geometry exists.

This is a broad architecture change affecting the whole machine. Write and review a design proposal before changing production code.

## Test philosophy

Keep normal tests focused on stable contracts rather than fragile topology:

- Valid configuration builds a valid single solid per printable part.
- Impossible configurations fail early with useful messages.
- Hardware-derived relationships remain synchronized.
- Boolean overlap/clearance checks cover intentional interfaces.
- Avoid face counts, edge ordering, tessellation details, and selector identities unless they are themselves part of the contract.

Put slow export/reimport, STL manifold analysis, and detailed clearance sweeps in an opt-in geometry-validation suite rather than requiring them on every small commit.
