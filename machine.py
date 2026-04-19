class MachineConfig:
    """Configuration for the machine."""

    # Dimensions for the lap
    LAP_HOLE_DIA = 12.7  # Diameter of the hole
    LAP_AXLE_DIA = 8.0  # Diameter of the axle
    LAP_DIA = 152.4  # Diameter of the lap, 6 inches
    LAP_THICKNESS = 2.0  # Thickness of the lap

    SPLASH_GUARD_DIA = min(LAP_DIA + 40.0, 195.0)
