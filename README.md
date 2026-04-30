# Gem Faceting Machine - Open Hardware CAD Project

This project aims to create open-source CAD designs for a gem faceting machine, with inspiration from various existing machines.

## Project Structure

```
- README.md           # This file
- TODO.md             # Just a to-do list.
- OFF_THE_SHELF.md    # Dimensions for off-the-shelf parts, for reference.
- BOM_ESTIMATE.md     # Estimated Bill of Materials.
```

## Getting Started

### Previewing:
Just download CQ-Editor from https://github.com/CadQuery/CQ-editor/releases, open it, and open machine_assembly.py. Run it, and it should preview the entire machine.

### Exporting:
- First, make sure you have Python installed.
- Then, create a virtual environment (venv), by opening the command prompt, going to this project's folder, and typing "python -m venv venv". This creates the virtual environment in the "venv" folder in this project.
- Third... uh, well, exporting currently is only sorta-kinda supported by mast_design.py, so... >_> TBD.

## Current Status

See TODO.md

## Other Relevant Projects (for inspiration)

- https://www.thingiverse.com/thing:6505241: Gem Creator, a failed Kickstarter that's already solved most of the problems I had in designing this.
- https://www.thingiverse.com/thing:6010663: Diagonal flat lap. Honestly kinda does the same things, still useful to compare & contrast.

## Contributing

This is intended to be an open hardware project. Contributions are welcome!

Ways that you can contribute:

### Reorganize the code to be cleaner
It's all Python code, and designed to be modular and clean, but I (Dekker3D) am no Python programmer, and this programming language is mildly alien to me.

### Design/fix parts
I guess this one's obvious. It's made to be modular: you should be able to design alternative versions of parts if you want to make big changes, without negatively affecting anyone who wants to use another version. If you find yourself running into issues with that, the design isn't modular enough, and you can point it out, for discussion.

### Build this stuff yourself and test it
Best way to get feedback, probably. It's a good way to contribute if you can't do anything else on this project. Make sure to fill out issues (check the "issues" tab on this GitHub repo) or start discussions about any issue you come across, or any idea you have.
