# Gem Faceting Machine - Open Hardware CAD Project

This project aims to create open-source CAD designs for a gem faceting machine, starting with a replacement mast for a Vevor imitation machine.

## Project Structure

```
FacetingMachine/
├── PROJECT.md          # Project overview and goals
├── TODO.md             # Detailed task list and milestones
├── SPECIFICATIONS.md   # Technical requirements and constraints
├── README.md           # This file
├── mast_design.py      # Initial mast replacement design
├── FacetingMachine.py   # Original template file (smart speaker design)
└── ...                 # Future component designs
```

## Getting Started

1. **Review Requirements**: Check `SPECIFICATIONS.md` for technical constraints
2. **Check Tasks**: See `TODO.md` for current progress and next steps
3. **Run Designs**: Execute Python files with CadQuery to generate STL files
4. **Modify Parameters**: Adjust values in Python files to match specific requirements

## Current Status

- ✅ Project documentation setup
- ✅ Initial mast design structure
- 🔄 Need to verify actual machine dimensions
- 🔄 Need to validate design constraints

## Environment Notes

- Working in WSL2 Ubuntu environment
- CadQuery installation may differ from Windows setup
- Designs are exportable to STL format for 3D printing
- Focus on open-source, manufacturable components

## Contributing

This is intended to be an open hardware project. Contributions are welcome!

## Next Steps

1. Measure existing machine to get accurate dimensions
2. Test and refine the mast design
3. Design mounting interfaces for existing components
4. Create assembly documentation