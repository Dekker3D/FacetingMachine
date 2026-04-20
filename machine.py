class MachineConfig:
    """Configuration for the machine."""

    # General config.
    # 3D printer smallest dimension.
    PRINTER_SIZE = 200.0

    @classmethod
    def printer_safe_size(cls):
        return cls.PRINTER_SIZE - 10.0  # Leave margin for brim, etc.

    # Lap dimensions.
    # Diameter of the arbor hole.
    LAP_HOLE_DIA = 12.7
    # Diameter of the axle. M8 bolt.
    LAP_AXLE_DIA = 8.0
    # Diameter of the lap, 6 inches.
    LAP_DIA = 152.4
    # Thickness of the lap.
    LAP_THICKNESS = 2.0

    # Splash guard dimensions.
    # Space to reach for stuff that fell under the lap.
    SG_EXTRA_SPACE = 10.0
    # Height, includes lip.
    SG_HEIGHT = 30.0
    # Material thickness.
    SG_THICKNESS = 2.0

    # Inner diameter.
    @classmethod
    def sg_ID(cls):
        return cls.LAP_DIA + cls.SG_EXTRA_SPACE * 2

    @classmethod
    def sg_OD(cls):
        return cls.sg_ID() + cls.SG_THICKNESS * 2

    # Quill holder
    # Diameter of the swing joint.
    QH_SWING_DIA = 15.0
    # Height of the swing joint.
    QH_SWING_HEIGHT = 50.0
    # Thickness of the swing joint.
    QH_SWING_JOINT_THICKNESS = 5.0
    # Thickness of the pitch joint.
    QH_PITCH_JOINT_THICKNESS = 8.0

    @classmethod
    def validate(cls):
        """Validate the configuration."""
        assert cls.sg_OD() < cls.printer_safe_size(), "Splash guard diameter exceeds 3D printer size!"
