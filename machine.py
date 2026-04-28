import math
import bought_bits as bb


class MachineConfig:
    """Configuration for the machine."""

    # General config.
    # 3D printer smallest dimension.
    PRINTER_SIZE = 200.0

    @classmethod
    def printer_safe_size(cls):
        return cls.PRINTER_SIZE - 10.0  # Leave margin for brim, etc.

    # Quill holder
    # Diameter of the swing joint.
    QH_SWING_DIA = 15.0
    # Height of the swing joint.
    QH_SWING_HEIGHT = 50.0
    # Thickness of the swing joint.
    QH_SWING_JOINT_THICKNESS = 5.0
    # Thickness of the pitch joint.
    QH_PITCH_JOINT_THICKNESS = 8.0

    # Mast
    # Leadscrew diameter
    LEADSCREW_DIA = 8.0
    # 20x20mm aluminum t-slot extrusion
    MAST_EXT_WIDTH = 20.0
    MAST_EXT_THICKNESS = 20.0

    # Frame
    # 20x20mm aluminum t-slot extrusion
    FRAME_EXT_WIDTH = 20.0
    FRAME_EXT_HEIGHT = 20.0
    # Rails for the mast. Smooth rods, really.
    FRAME_RAIL_DIA = 8.0
    # Space between frame and rail.
    FRAME_RAIL_SPACING = 10.0
    MAST_VIS_X = 100.0
    MAST_CARRIAGE_LENGTH = 80.0
    MAST_CARRIAGE_CLEARANCE = 2.0
    MAST_CARRIAGE_THICKNESS = 10.0
    # Desired space for mast and its horizontal travel.
    MAST_DESIRED_SPACE = 250.0
    MAST_DESIRED_VERTICAL_TRAVEL = 300.0
    # The piece holding the mast to the mast-carriage.
    MAST_HOLDER_THICKNESS = 12.0
    MAST_HOLDER_HEIGHT = 60.0

    MAST_RAIL_LENGTH = 400.0
    LEADSCREW_LENGTH = 450.0
    MAST_SPINE_LENGTH = 450.0

    # Quill carriage
    QC_JOINT_DIA = 25
    QC_JOINT_LENGTH = 80
