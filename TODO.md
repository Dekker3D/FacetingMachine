# Gem Faceting Machine - TODO List

## Design stuff

### Lap:
- [ ] Add drain hole to splash guard.
- [ ] Add bearings for lap-axle to splash guard.
- [ ] Add motor mount.

### Mast:
- [X] Fix leadscrew bearing-holders.
- [ ] Figure out alignment mechanism for leadscrew bearing-holders. (V-slot extrusion?)
- [ ] Fix quill-holder carriage to have swivel joint.
- [ ] Implement quill-holder properly.
- [ ] Implement quill-tilt.
- [ ] Implement quill.
- [ ] Add handwheel to hold leadscrew.
- [ ] Add optional handwheel-brake mechanism, toggled. (Over-under mechanism?)
- Check: Handwheel keeps leadscrew at correct height.
- Check: Handwheel does not run into obstructions.
- Check: Quill-tilt can tilt freely.
- Check: Quill-tilt bearing holders are strong enough. (Print orientation, thickness)

### Frame:
- [ ] Add mast-carriage-rail holders.
- [ ] Add mast-angle calibration mechanism to mast carriage.
- [ ] Add clamp mechanism to mast carriage, to clamp to rails.
- [X] Add legs.
- Check: Free space for 90 degree brackets for 2020 extrusion frame parts.

## Spatial testing

Now verified: `cad_helpers.py` + `test_spatial.py` (7 tests, all pass).
Boolean-based assertions (intersect/cut) work on real CadQuery geometry.
See `branches: spatial-testing`.

- [X] Basic harness: `assert_no_overlap`, `assert_contained`, `assert_clearance`, `assert_fits_printer`
- [X] RefFrame: named reference frames for unambiguous placement
- [X] Test: handwheel doesn't hit bearing holder (was a "Check" item on the old list)
- [X] Test: leadscrew passes through bearing recess
- [X] Test: splash guard and bearing holder fit printer bed
- [ ] Add clearance zone tests for moving parts (quill tilt envelope, mast carriage travel range)
- [ ] Test: lap holder top/bottom alignment, splash guard bottom bearing fit
- [ ] Test: quill swing joint clearance around mast carriage
- [ ] Define clearance zones: dop stick travel path through lap area, user hand space
- [ ] Refactor one assembly to use RefFrame-based placement (instead of raw `Location` tuples)
- [ ] Write `docs/agents/spatial-testing.md` — how-to for LLMs writing new tests
- [ ] Wire `python test_spatial.py` as a pre-export verification step (run before `export_everything()`)

## Off-the-shelf parts
- [ ] Find suitable collet chuck for 6mm dops.