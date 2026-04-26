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
    # Slope of splash guard interior.
    SG_SLOPE = 0.04
    # The ID and OD of the drain hole.
    SG_DRAIN_ID = 6.0
    SG_DRAIN_OD = 10.0

    # Spacing. Basically attach at 4 points around the lap.
    # Round to 20 mm increments for ease with 2020 extrusions.
    @classmethod
    def sg_screw_spacing(cls):
        return math.ceil(cls.sg_OD() * math.sqrt(0.5) / 20) * 20

    # Inner diameter.
    @classmethod
    def sg_ID(cls):
        return cls.LAP_DIA + cls.SG_EXTRA_SPACE * 2

    @classmethod
    def sg_OD(cls):
        return cls.sg_ID() + cls.SG_THICKNESS * 2

    @classmethod
    def sg_bottom_dia(cls):
        return bb.Bearing608ZZ.OD + 10

    @classmethod
    def sg_drain_offset(cls):
        return cls.sg_bottom_dia() / 2 + 3 + cls.SG_DRAIN_OD / 2

    # Screw hole spacing for bottom part.
    @classmethod
    def sg_bottom_screw_spacing(cls):
        print(cls.sg_bottom_dia())
        print(cls.sg_bottom_dia() / 2 + 6.0)
        return cls.sg_bottom_dia() / 2 + 6.0

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

    @classmethod
    def frame_width(cls):
        return cls.sg_screw_spacing() + 20.0  # So that the middle of the 2020 matches the screw spacing.

    @classmethod
    def frame_width_internal(cls):
        return cls.frame_width() - 40.0

    @classmethod
    def frame_rail_width(cls):
        return cls.frame_width_internal() - cls.FRAME_RAIL_DIA - cls.FRAME_RAIL_SPACING * 2

    @classmethod
    def mast_space(cls):
        return cls.frame_length() - cls.lap_space_from_left() - 20

    @classmethod
    def frame_length(cls):
        return math.ceil((cls.frame_width() / 2 + cls.sg_OD() / 2 + cls.MAST_DESIRED_SPACE + 20) / 20) * 20

    @classmethod
    def lap_pos_from_left(cls):
        return cls.frame_width() / 2

    @classmethod
    def lap_space_from_left(cls):
        return cls.lap_pos_from_left() + cls.sg_OD() / 2

    @classmethod
    def validate(cls):
        """Validate the configuration."""
        assert cls.sg_OD() < cls.printer_safe_size(), "Splash guard diameter exceeds 3D printer size!"
