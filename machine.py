from __future__ import annotations


class MachineConfig:
    """Configuration for the machine."""

    # General config.
    # 3D printer smallest dimension.
    PRINTER_SIZE: float = 200.0

    @classmethod
    def printer_safe_size(cls) -> float:
        return cls.PRINTER_SIZE - 10.0  # Leave margin for brim, etc.

    # Quill holder
    QH_SWING_DIA: float = 15.0
    QH_SWING_HEIGHT: float = 50.0
    QH_SWING_JOINT_THICKNESS: float = 5.0
    QH_PITCH_JOINT_THICKNESS: float = 8.0

    # Frame
    FRAME_EXT_WIDTH: float = 20.0
    FRAME_EXT_HEIGHT: float = 20.0
    FRAME_RAIL_DIA: float = 8.0
    FRAME_RAIL_SPACING: float = 10.0
    MAST_CARRIAGE_LENGTH: float = 80.0
    MAST_CARRIAGE_CLEARANCE: float = 2.0
    MAST_CARRIAGE_THICKNESS: float = 10.0
    MAST_DESIRED_SPACE: float = 250.0
    MAST_HOLDER_THICKNESS: float = 12.0
    MAST_HOLDER_HEIGHT: float = 60.0
