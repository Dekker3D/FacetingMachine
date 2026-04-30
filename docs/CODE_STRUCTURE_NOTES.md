# Code Structure Notes:

## Modular Joints:
Each actual joint class implements two base classes: one for each part it's joining.

FrameAssembly might implement FrameExtMastInterface, which gives the frame-mast joint the information it needs about connecting to a frame based on 2020/2040 extrusions.
MastAssembly might implement MastFootFrameInterface, which does the same for a mast with a 3D-printed foot.

A specific FrameExtMastFootJoint class might implement a similar interface for the frame and mast, if needed.