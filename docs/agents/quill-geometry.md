# Quill Geometry — StandardMk1

Confirmed layout for the quill subsystem. Reference before modifying quill code.

## Coordinate System

- **+X**: Left (toward the lap from the mast)
- **+Y**: Forward (away from user? — "toward the user" is ambiguous in current code; most parts are Y-symmetrical)
- **+Z**: Up

## Quill Holder (QuillHolder)

A single piece, candelabra-shaped:

- **Swivel joint**: Vertical cylinder at the **-X** end. Plugs into the quill carriage hinge on the mast. Allows the whole quill to swing left/right.
- **Two arms**: Project **+X** from the swivel joint, one on the **-Y** side (user-facing) and one on the **+Y** side. Parallel.
- **At the tip of each arm**: A 608ZZ bearing (22mm OD, 8mm ID). These hold the pitch rod.

## Pitch Rod

- **8mm diameter** straight rod, runs along the **Y** axis through both 608ZZ bearings in the quill holder arms.
- **Magnet** on the **-Y** end (user-facing side). A Hall-effect sensor reads rotation → pitch angle. The digital readout + sensor share a box on the -Y side.
- The **quill body clamps onto** the pitch rod between the two arms.

## Quill Body (printed part)

Clamped onto the pitch rod. Houses two 6001ZZ bearings (12mm ID, 28mm OD, 8mm wide). The ER11 extension runs through these bearings.

- The **ER11 extension centerline is at the same Z height** as the pitch rod centerline — no vertical offset.
- Bearings spaced as far apart as structurally possible for stiffness.

## ER11 Extension (off-the-shelf)

- **12mm OD, ~100mm long**, hollow rod with ER11 collet nut on one end.
- **Collet faces +X** (toward the lap).
- Holds **6mm dop sticks** (parametrizable — some builders use different sizes).

## Index Gear

- **3D printed**, 96-tooth (3.75° per step). Clamps onto the ER11 extension.
- Located at the **-X** end of the ER11 extension (behind the rear 6001ZZ bearing). Not between the 6001ZZ bearings — makes swapping easier.
- Teeth on the outside circumference (not end-face).

## Cheater Mechanism

- **Function:** Angle adjustments below the 3.75 degrees of the index gear, when a gem facet just isn't hitting the lap right.
- **Rocker** with a small gear section that meshes with the index gear.
- **Side-to-side adjustment** via a bolt threaded into the rocker plastic, and held in place with small bearings on the quill body. 624ZZ seems right, with a 4mm bolt, and a nyloc nut to hold it in place.
- **Spring-loaded disengagement** to switch indices.
- Optional hold-up feature (for cone-section cutting instead of faceting — future enhancement).

## Angle Stop

- Physical stop on the quill body that bumps against the quill holder to prevent the quill from tilting below a set pitch angle.

## Pitch Angle Operation

- **Girdle cutting (0°):** Mast at lowest position, quill horizontal. Dop parallel to lap surface, centerline just above lap surface height (offset determined by the girdle's radius)
- **Crown/pavilion facets (20–60°):** Mast raised, quill tilted down. The mast rise compensates for the tilt so the quill doesn't collide with the lap.
- **Table facet cutting:** Done with a 45 degree angle adapter, as this kind of machine can't easily reach the lap while tilted straight down. The adapter takes the place of the dop.

## Easy Release (future)

Not in StandardMk1. Possible future improvement; some part of the quill or quill holder detaches to let the user inspect the gem more easily while it's still held by the quill.
Whatever mechanism this uses, it will have to be stiff and consistent when attached, and quick/easy to release and re-attach.

## No Thread Tapping Rule

All threaded features use either:
- Heat-set inserts
- Captive nuts
- Wood screws in plastic
- Bolts threaded directly into plastic (rare, mostly cheater mechanism)

No requirement for the builder to tap screw threads.


# Off-the-Shelf Parts Used

| Part | Key Dimensions | Qty |
|------|---------------|-----|
| ER11 straight shank extension | 12mm OD, ~100mm length | 1 |
| ER11 collet (for 6mm dop) | 6mm ID | 1 |
| 6001ZZ bearings | 12mm ID, 28mm OD, 8mm W | 2 |
| 608ZZ bearings | 8mm ID, 22mm OD, 7mm W | 2 |
| 8mm rod (pitch rod) | 8mm diameter | 1 |

## Design Constraints — Applied in Quill

These are requirements that affect how we model this:

- Quill attached to mast carriage, must be held at a height where the dop can **go flat on the lap (on its side)** — so the pitch rod (and ER11) centerline must reach the lap surface height when the quill is horizontal at the lowest mast position.
- The mast provides vertical travel; we don't add extra offset in the quill — that gets handled by mast height.
- The ER11 doesn't go below the pitch rod — it's in-plane. When tilted, the mast rises, keeping the tip at the lap.
- Keying (rotational alignment of the dop) is not used on this machine, so a keyway is not needed.
