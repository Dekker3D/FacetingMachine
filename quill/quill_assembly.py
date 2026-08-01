from __future__ import annotations
import math
import cadquery as cq
from cadquery import Location, Vector
import bom_part_data as bpd
import bought_bits as bb
from printed_fasteners import SideLoadedCaptiveNutHole
import quill.quill_abstract as quill_abstract
from quill.quill_joint import QuillAngleIndicator, QuillJointAli

from cadquery.func import text, offset


def gear_tooth_profile_polar_points(
    tooth_indices: range,
    angular_pitch: float,
    root_radius: float,
    tip_radius: float,
    valley_angle_offset: float,
) -> list[tuple[float, float]]:
    """Return alternating valley/tip polar points for a triangular gear tooth profile."""
    points: list[tuple[float, float]] = []
    for tooth_index in tooth_indices:
        valley_angle = (tooth_index + valley_angle_offset) * angular_pitch
        points.append((valley_angle, root_radius))
        points.append((valley_angle + angular_pitch / 2, tip_radius))
    return points


# ═══════════════════════════════════════════════════════════════════════
# Assembly — owns all dimensions, injects into parts
# ═══════════════════════════════════════════════════════════════════════


class QuillAssemblyStandardMk1(quill_abstract.QuillAssemblyBase):
    """Standard Mk1 quill: joint with angled nubs, main block with top-loading
    6001ZZ bearings, ER11 collet shank, and 96-tooth index gear.

    Geometry and sub-parts are built once during __init__ and cached.
    Use ``get_assembly()`` and ``get_BOM()`` from the base class."""

    # ── Joint (fits into quill holder's U-slot) ─────────────────
    joint_shoulder_dia: float = 12.0
    joint_shoulder_gap: float = 47.5
    joint_shoulder_thickness: float = 3.0
    joint_user_nub_dia: float = 6.5
    joint_user_nub_length: float = 8.0
    joint_away_nub_dia: float = 5.5
    joint_away_nub_length: float = 5.0
    joint_hinge_height: float = 17.0
    joint_angle_indicator_height: float = 40.0
    joint_angle_indicator_width_x: float = 10.0
    joint_angle_indicator_thickness: float = 10.0
    joint_angle_indicator_corner_margin: float = 2.0
    joint_angle_indicator_screw_size: float = 3.0
    joint_angle_indicator_screw_length: float = 16.0
    joint_angle_indicator_screw_head: str = "countersunk"
    joint_body_positive_x: float = 8.0
    joint_body_top_z: float = 35.0
    joint_magnet_pocket_dia: float = 3.7
    # 4.75 mm from the nub's top puts the midpoint of a 3.0 mm magnet stack
    # on the nub's Z centreline while keeping the pocket close to the Y end.
    joint_magnet_pocket_depth: float = 4.75

    # Joint-related defaults remain here temporarily. See
    # docs/joint-resolution.md for the deferred ownership refactor.

    # ── Base plate ──────────────────────────────────────────────
    base_plate_thickness: float = 8.0
    base_plate_positive_x: float = 88.0
    base_plate_shoulder_inset_y: float = 0.5
    body_index_gear_radial_clearance: float = 2.0
    body_index_gear_axial_clearance: float = 10.0
    body_reinforcement_block_overlap_x: float = 4.0

    # ── User-selected quill design settings ────────────────────
    bearing_radial_tolerance: float = 0.0
    bearing_axial_tolerance: float = 0.5
    bearing_retaining_lip_depth: float = 1.0
    bearing_retaining_lip_overlap: float = 1.0
    shank_bore_radial_tolerance: float = 1.0

    bearing_axis_height_above_base_plate: float = 25.0
    block_material_above_bearing: float = 5.0
    block_x_offset: float = 45.0

    bearing_holder_length_x: float = 16.0
    bearing_holder_screw_x_from_end: float = 8.0
    bearing_holder_split_gap: float = 2.0
    bearing_to_screw_clearance: float = 6.4
    screw_to_outer_wall: float = 4.4
    bearing_holder_screw_nominal_dia: float = 3.0
    body_screw_clearance: float = 0.2
    holder_screw_clearance: float = 0.4

    index_gear_od: float = 41.3
    index_gear_teeth_width: float = 5.0
    index_gear_numbers_width: float = 8.0
    index_gear_spacer_width: float = 2.0
    index_gear_spacer_od: float = 18.0
    index_gear_num_teeth: int = 96
    index_gear_tick_interval_teeth: int = 3
    index_gear_number_interval_teeth: int = 12
    index_gear_tooth_depth: float = 0.8
    index_side_shank_exposure: float = 10.0
    index_gear_clamp_screw_size: float = 3.0
    index_gear_clamp_screw_length: float = 8.0
    index_gear_clamp_screw_clearance: float = 0.2
    index_gear_clamp_nut_clearance: float = 0.3
    index_gear_clamp_nut_depth_clearance: float = 0.6
    index_gear_clamp_screw_adjustment_target: float = 3.0
    index_gear_clamp_nut_bore_wall_min: float = 2.0

    # ── Cheater bearing top ─────────────────────────────────────
    cheater_bearing_type: type[bb.BearingGeneric] = bb.Bearing624ZZ
    cheater_bearing_radial_tolerance: float = 0.1
    cheater_bearing_inner_lip: float = 2.0
    cheater_bearing_radial_material: float = 5.0
    cheater_axle_clearance: float = 0.4
    cheater_rocker_width_y: float = 20.0
    cheater_rocker_side_clearance_y: float = 4.0
    cheater_pivot_above_block: float = 10.0
    cheater_pivot_from_tooth_face_x: float = 40.0
    cheater_top_screw_x_margin: float = 8.0
    cheater_screwdriver_shaft_diameter: float = 6.0
    cheater_screwdriver_radial_clearance: float = 0.5
    block_end_vertical_edge_fillet: float = 2.0
    block_top_edge_fillet: float = 2.0
    cheater_top_screw_clearance_dia: float = 3.4
    removable_top_screw_size: float = 3.0
    removable_top_screw_length: float = 35.0
    removable_top_screw_head: str = "pan"
    removable_top_nut_clearance: float = 0.2
    removable_top_nut_depth_clearance: float = 0.2
    removable_top_nut_drop: float = 8.0
    removable_top_nut_bridge_thickness: float = 0.5
    cheater_pivot_bolt_size: float = 4.0
    cheater_wheel_diameter: float = 30.0
    cheater_wheel_radial_clearance: float = 2.0
    cheater_wheel_outboard_extension: float = 5.0
    cheater_pivot_bolt_thread_protrusion: float = 4.0
    cheater_wheel_hex_clearance: float = 0.2
    cheater_wheel_head_depth_clearance: float = 0.2
    cheater_wheel_grip_notch_radius: float = 1.5
    cheater_wheel_grip_notch_count: int = 12
    cheater_positive_y_shelf_edge_bevel: float = 2.0
    cheater_wall_max_print_angle: float = 45.0
    cheater_rocker_positive_x_length: float = 50.0
    cheater_rocker_arm_thickness_z: float = 8.0
    cheater_rocker_pivot_outer_diameter: float = 12.0
    cheater_rocker_pivot_pilot_diameter: float = 3.4
    cheater_rocker_gear_mount_positive_x: float = 10.0

    cheater_gear_section_screw_size: float = 3.0
    cheater_gear_section_screw_length: float = 12.0
    cheater_gear_section_screw_head: str = "countersunk"
    cheater_gear_section_screw_clearance_dia: float = 3.4
    cheater_gear_section_screw_pilot_dia: float = 2.2
    cheater_gear_section_screw_spacing_y: float = 10.0
    cheater_gear_section_neutral_clearance: float = 0.0
    gear_tooth_root_relief_tangential_width: float = 0.5
    gear_tooth_root_relief_radial_depth: float = 1.0
    cheater_gear_section_negative_x_extension: float = 2.0
    # Match the index gear's proven 5 mm text size.  Its 1 mm engraving is
    # intentionally shallower than the index gear's 2 mm text because this
    # removable section has only a 5 mm axial thickness.
    cheater_gear_section_tooth_count_engraving_size: float = 5.0
    cheater_gear_section_tooth_count_engraving_depth: float = 1.0
    cheater_gear_section_tooth_count_engraving_margin_z: float = 0.5

    cheater_spring_wire_diameter: float = 0.5
    cheater_spring_outside_diameter: float = 8.0
    cheater_spring_free_length: float = 15.0
    cheater_spring_coil_count: int = 8
    cheater_spring_pocket_diameter_clearance: float = 0.5
    cheater_spring_pocket_depth_top: float = 1.5
    cheater_spring_pocket_depth_rocker: float = 1.5
    cheater_spring_edge_clearance_x: float = 1.0
    cheater_spring_target_from_pivot_x: float = 16.0

    def index_gear_width(self) -> float:
        """Axial width outside the block; excludes spacer reach into the lip."""
        return (
            self.index_gear_teeth_width
            + self.index_gear_numbers_width
            + self.index_gear_spacer_width
        )

    def index_gear_modeled_spacer_width(self) -> float:
        return self.index_gear_spacer_width + self.bearing_retaining_lip_depth

    def index_gear_clamp_screw(self) -> bb.SetScrew:
        return bb.SetScrew.get(
            size=self.index_gear_clamp_screw_size,
            length=self.index_gear_clamp_screw_length,
        )

    def index_gear_clamp_nut(self) -> bb.Nut:
        return bb.Nut.get(size=self.index_gear_clamp_screw_size)

    def index_gear_clamp_screw_hole_dia(self) -> float:
        return (
            self.index_gear_clamp_screw().diameter()
            + self.index_gear_clamp_screw_clearance
        )

    def index_gear_clamp_nut_pocket_width(self) -> float:
        return (
            self.index_gear_clamp_nut().width_across_flats()
            + self.index_gear_clamp_nut_clearance
        )

    def index_gear_clamp_nut_pocket_corner_dia(self) -> float:
        return self.index_gear_clamp_nut_pocket_width() / math.cos(
            math.radians(30)
        )

    def index_gear_clamp_nut_pocket_depth(self) -> float:
        return (
            self.index_gear_clamp_nut().height()
            + self.index_gear_clamp_nut_depth_clearance
        )

    def index_gear_clamp_angle(self) -> float:
        tooth_pitch = 360.0 / self.index_gear_num_teeth
        return tooth_pitch * self.index_gear_number_interval_teeth / 2

    def index_gear_clamp_nut_inner_radius(self) -> float:
        return (
            self.index_gear_clamp_screw_outer_radius()
            - self.index_gear_clamp_nut().height()
            - self.index_gear_clamp_screw_adjustment_target
        )

    def index_gear_clamp_screw_adjustment_available(self) -> float:
        return (
            self.index_gear_clamp_screw_outer_radius()
            - self.index_gear_clamp_nut_inner_radius()
            - self.index_gear_clamp_nut().height()
        )

    def index_gear_clamp_nut_bore_wall(self) -> float:
        return (
            self.index_gear_clamp_nut_inner_radius()
            - self.index_gear_bore_dia() / 2
        )

    def index_gear_clamp_screw_outer_radius(self) -> float:
        return (
            self.index_gear_bore_dia() / 2
            + self.index_gear_clamp_screw().shaft_length()
        )

    def index_gear_clamp_hardware_local_objects(
        self,
    ) -> tuple[cq.Workplane, cq.Workplane]:
        """Return clamp set screw/nut in the gear's local print coordinates."""
        numbers_mid_z = self.index_gear_numbers_width / 2
        screw_object = (
            self.index_gear_clamp_screw()
            .get_object()
            .rotate((0, 0, 0), (0, 1, 0), -90)
            .translate(
                (
                    self.index_gear_clamp_screw_outer_radius(),
                    0,
                    numbers_mid_z,
                )
            )
            .rotate((0, 0, 0), (0, 0, 1), -self.index_gear_clamp_angle())
        )
        nut_object = (
            self.index_gear_clamp_nut()
            .get_object()
            .rotate((0, 0, 0), (0, 1, 0), 90)
            .translate(
                (
                    self.index_gear_clamp_nut_inner_radius(),
                    0,
                    numbers_mid_z,
                )
            )
            .rotate((0, 0, 0), (0, 0, 1), -self.index_gear_clamp_angle())
        )
        return screw_object, nut_object

    def _validate_index_gear_configuration(self) -> None:
        if not isinstance(self.index_gear_num_teeth, int) or self.index_gear_num_teeth <= 0:
            raise ValueError("index_gear_num_teeth must be a positive integer")
        intervals = {
            "index_gear_tick_interval_teeth": self.index_gear_tick_interval_teeth,
            "index_gear_number_interval_teeth": (
                self.index_gear_number_interval_teeth
            ),
        }
        for label, value in intervals.items():
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{label} must be a positive integer")
            if self.index_gear_num_teeth % value != 0:
                raise ValueError(
                    f"index_gear_num_teeth must be divisible by {label}"
                )
        if (
            self.index_gear_number_interval_teeth
            % self.index_gear_tick_interval_teeth
            != 0
        ):
            raise ValueError(
                "index_gear_number_interval_teeth must be divisible by "
                "index_gear_tick_interval_teeth"
            )

        screw = self.index_gear_clamp_screw()
        minimum_screw_length = (
            self.index_gear_clamp_nut_bore_wall_min
            + self.index_gear_clamp_nut().height()
            + self.index_gear_clamp_screw_adjustment_target
        )
        if screw.shaft_length() < minimum_screw_length:
            raise ValueError(
                "Index-gear clamp set screw cannot provide the requested "
                f"{self.index_gear_clamp_screw_adjustment_target:g} mm adjustment "
                "while retaining the minimum bore wall; "
                f"M{screw.size:g}×{screw.shaft_length():g} mm is shorter than "
                f"the required {minimum_screw_length:g} mm"
            )
        nut_pocket_width = self.index_gear_clamp_nut_pocket_width()
        nut_pocket_depth = self.index_gear_clamp_nut_pocket_depth()
        finite_positive = {
            "index_gear_clamp_screw_clearance": (
                self.index_gear_clamp_screw_clearance
            ),
            "index_gear_clamp_nut_clearance": self.index_gear_clamp_nut_clearance,
            "index_gear_clamp_nut_depth_clearance": (
                self.index_gear_clamp_nut_depth_clearance
            ),
            "index_gear_clamp_screw_adjustment_target": (
                self.index_gear_clamp_screw_adjustment_target
            ),
            "index_gear_clamp_nut_bore_wall_min": (
                self.index_gear_clamp_nut_bore_wall_min
            ),
            "body_index_gear_axial_clearance": self.body_index_gear_axial_clearance,
        }
        for label, value in finite_positive.items():
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{label} must be finite and greater than 0 mm")
        nut_pocket_corner_dia = nut_pocket_width / math.cos(math.radians(30))
        if nut_pocket_corner_dia >= self.index_gear_numbers_width:
            raise ValueError(
                "Index-gear clamp nut-pocket corners must fit within the numbered "
                f"gear section ({nut_pocket_corner_dia:g} mm corner diameter, "
                f"{self.index_gear_numbers_width:g} mm section)"
            )
        nut_inner_radius = self.index_gear_clamp_nut_inner_radius()
        nut_bore_wall = self.index_gear_clamp_nut_bore_wall()
        if nut_bore_wall < self.index_gear_clamp_nut_bore_wall_min:
            raise ValueError(
                "Index-gear clamp nut pocket leaves too little material around "
                f"the shank bore ({nut_bore_wall:g} mm available, "
                f"{self.index_gear_clamp_nut_bore_wall_min:g} mm required)"
            )
        if nut_inner_radius + nut_pocket_depth >= self.index_gear_od / 2:
            raise ValueError(
                "Index-gear clamp nut pocket must leave material at the gear rim"
            )
        nut_outer_radius = nut_inner_radius + self.index_gear_clamp_nut().height()
        screw_outer_radius = self.index_gear_clamp_screw_outer_radius()
        if screw_outer_radius < nut_outer_radius:
            raise ValueError(
                "Index-gear clamp set screw cannot reach the ER11 shank while "
                "spanning the full captive nut; "
                f"M{screw.size:g}×{screw.shaft_length():g} mm is "
                f"{nut_outer_radius - screw_outer_radius:g} mm too short"
            )
        if screw_outer_radius >= self.index_gear_od / 2:
            raise ValueError(
                "Index-gear clamp set screw would protrude beyond the gear rim "
                "when tightened against the ER11 shank"
            )

    def joint_angle_indicator_screw(self) -> bb.WoodScrew:
        return bb.WoodScrew.get(
            size=self.joint_angle_indicator_screw_size,
            length=self.joint_angle_indicator_screw_length,
            head=self.joint_angle_indicator_screw_head,
        )

    def base_plate_y(self) -> float:
        return self.joint_shoulder_gap - self.base_plate_shoulder_inset_y * 2

    def joint_body_negative_x(self) -> float:
        return -self.joint_angle_indicator_width_x

    def joint_angle_indicator_corner_radius(self) -> float:
        return (
            self.joint_angle_indicator_width_x
            - self.joint_angle_indicator_corner_margin
        )

    def base_plate_x(self) -> float:
        return self.base_plate_positive_x - self.joint_body_negative_x()

    def base_plate_center_x(self) -> float:
        return (
            self.base_plate_positive_x + self.joint_body_negative_x()
        ) / 2

    def joint_support_length_x(self) -> float:
        return self.joint_body_positive_x - self.joint_body_negative_x()

    def body_reinforcement_start_x(self) -> float:
        return self.joint_body_positive_x

    def body_reinforcement_end_x(self) -> float:
        return self.block_x_offset + self.body_reinforcement_block_overlap_x

    def body_reinforcement_top_z(self) -> float:
        shank_bottom_z = self.block_center_z() - self.er11.dia / 2
        return shank_bottom_z - 1.0

    def index_gear_tip_radius(self) -> float:
        return self.index_gear_od / 2 + self.index_gear_tooth_depth

    def body_index_gear_clearance_radius(self) -> float:
        return self.index_gear_tip_radius() + self.body_index_gear_radial_clearance

    def block_length_x(self) -> float:
        return (
            self.er11.length
            - self.index_gear_width()
            - self.index_side_shank_exposure
        )

    def index_side_bearing_x(self) -> float:
        return self.bearing_retaining_lip_depth

    def collet_side_bearing_x(self) -> float:
        return (
            self.block_length_x()
            - self.bearing_retaining_lip_depth
            - self.bearing_type.WIDTH
        )

    def bearing_pocket_dia(self) -> float:
        return self.bearing_type.OD + self.bearing_radial_tolerance * 2

    def bearing_pocket_depth(self) -> float:
        return self.bearing_type.WIDTH + self.bearing_axial_tolerance

    def bearing_retaining_lip_opening_dia(self) -> float:
        return self.bearing_type.OD - self.bearing_retaining_lip_overlap * 2

    def _validate_bearing_configuration(self) -> None:
        if not math.isclose(self.er11.dia, self.bearing_type.ID, abs_tol=1e-6):
            raise ValueError(
                "ER11 shank diameter must match the main bearing ID "
                f"({self.er11.dia:g} mm shank, {self.bearing_type.ID:g} mm ID); "
                "select a matching bearing or collet extension"
            )
        if self.bearing_axial_tolerance < 0:
            raise ValueError("bearing_axial_tolerance cannot be negative")
        if not 0 < self.bearing_retaining_lip_depth < self.bearing_type.WIDTH:
            raise ValueError(
                "bearing_retaining_lip_depth must be greater than 0 and less "
                f"than the {self.bearing_type.WIDTH:g} mm bearing width"
            )
        outer_race_radial_width = (
            self.bearing_type.OD - self.bearing_type.ID
        ) / 2
        if not 0 < self.bearing_retaining_lip_overlap < outer_race_radial_width:
            raise ValueError(
                "bearing_retaining_lip_overlap must touch only the outer race; "
                f"use a value between 0 and {outer_race_radial_width:g} mm"
            )
        lip_opening = self.bearing_retaining_lip_opening_dia()
        required_opening = max(self.shank_bore_dia(), self.index_gear_spacer_od)
        if lip_opening <= required_opening:
            raise ValueError(
                "Bearing retaining-lip opening must clear both the shank bore "
                f"and index-gear spacer ({lip_opening:g} mm opening, "
                f"{required_opening:g} mm required)"
            )
        if self.index_gear_spacer_od <= self.index_gear_bore_dia():
            raise ValueError(
                "index_gear_spacer_od must exceed the index-gear bore diameter"
            )

    def shank_bore_dia(self) -> float:
        return self.er11.dia + self.shank_bore_radial_tolerance * 2

    def index_gear_bore_dia(self) -> float:
        return self.er11.dia

    def block_center_z(self) -> float:
        return self.bearing_axis_height_above_base_plate

    def block_height_z(self) -> float:
        return (
            self.block_center_z()
            + self.bearing_pocket_dia() / 2
            + self.block_material_above_bearing
        )

    def body_screw_hole_dia(self) -> float:
        return (
            self.bearing_holder_screw_nominal_dia
            + self.body_screw_clearance
        )

    def holder_screw_hole_dia(self) -> float:
        return (
            self.bearing_holder_screw_nominal_dia
            + self.holder_screw_clearance
        )

    def bearing_holder_screw_spacing_y(self) -> float:
        screw_center_y = (
            self.bearing_pocket_dia() / 2
            + self.bearing_to_screw_clearance
            + self.body_screw_hole_dia() / 2
        )
        return screw_center_y * 2

    def block_width_y(self) -> float:
        screw_center_to_edge = (
            self.body_screw_hole_dia() / 2
            + self.screw_to_outer_wall
        )
        bearing_holder_half_width = (
            self.bearing_holder_screw_spacing_y() / 2
            + screw_center_to_edge
        )
        cheater_top_half_width = (
            self.cheater_wall_outer_y()
            + self.cheater_screwdriver_keepout_radius()
            + screw_center_to_edge
        )
        return 2 * max(bearing_holder_half_width, cheater_top_half_width)

    def cheater_top_start_x(self) -> float:
        return self.bearing_holder_length_x

    def cheater_top_length_x(self) -> float:
        return self.block_length_x() - self.bearing_holder_length_x * 2

    def cheater_bearing_pocket_dia(self) -> float:
        return (
            self.cheater_bearing_type.OD
            + self.cheater_bearing_radial_tolerance * 2
        )

    def cheater_wall_thickness_y(self) -> float:
        return self.cheater_bearing_type.WIDTH + self.cheater_bearing_inner_lip

    def cheater_wall_inner_y(self) -> float:
        return (
            self.cheater_rocker_width_y / 2
            + self.cheater_rocker_side_clearance_y
        )

    def cheater_structure_width_y(self) -> float:
        return (
            self.cheater_rocker_width_y
            + self.cheater_rocker_side_clearance_y * 2
            + self.cheater_wall_thickness_y() * 2
        )

    def index_teeth_positive_x(self) -> float:
        # Relative to the block's index-side face. The spacer occupies the
        # final +X portion between the teeth and the bearing.
        return -self.index_gear_spacer_width

    def cheater_gear_section_negative_x(self) -> float:
        return self.index_teeth_positive_x() - self.index_gear_teeth_width

    def cheater_gear_mount_bottom_z(self) -> float:
        tooth_count = self.cheater_gear_section_tooth_count()
        half_angle = (
            tooth_count // 2 + 0.5
        ) * 2 * math.pi / self.index_gear_num_teeth
        curve_radius = self.index_gear_tip_radius()
        curve_center_z = (
            self.block_center_z()
            + self.cheater_gear_section_tooth_tip_radius()
            + curve_radius
        )
        root_radius = curve_radius - self.index_gear_tooth_depth
        return curve_center_z - math.cos(half_angle) * root_radius


    def cheater_gear_section_tooth_tip_radius(self) -> float:
        return (
            self.index_gear_tip_radius()
            + self.cheater_gear_section_neutral_clearance
        )

    def cheater_gear_section_screw(self) -> bb.WoodScrew:
        return bb.WoodScrew.get(
            size=self.cheater_gear_section_screw_size,
            length=self.cheater_gear_section_screw_length,
            head=self.cheater_gear_section_screw_head,
        )

    def cheater_gear_section_tooth_pitch(self) -> float:
        return math.pi * self.index_gear_od / self.index_gear_num_teeth

    def cheater_gear_section_tooth_count(self) -> int:
        count = max(
            3,
            int(
                self.cheater_rocker_width_y
                / self.cheater_gear_section_tooth_pitch()
            ),
        )
        return count - 1 if count % 2 == 0 else count

    def cheater_gear_section_screw_z(self) -> float:
        return (
            self.cheater_gear_mount_bottom_z()
            + self.cheater_pivot_z()
            + self.cheater_rocker_arm_thickness_z
        ) / 2

    def cheater_gear_section_backing_top_z(self) -> float:
        return self.cheater_pivot_z() + self.cheater_rocker_arm_thickness_z

    def cheater_pivot_x(self) -> float:
        return (
            self.index_teeth_positive_x()
            + self.cheater_pivot_from_tooth_face_x
        )

    def cheater_pivot_z(self) -> float:
        return self.block_height_z() + self.cheater_pivot_above_block

    def cheater_wall_outer_radius(self) -> float:
        return (
            self.cheater_bearing_pocket_dia() / 2
            + self.cheater_bearing_radial_material
        )

    def cheater_axle_hole_dia(self) -> float:
        return self.cheater_bearing_type.ID + self.cheater_axle_clearance

    def cheater_wheel_clearance_radius(self) -> float:
        return self.cheater_wheel_diameter / 2 + self.cheater_wheel_radial_clearance

    def cheater_wall_outer_y(self) -> float:
        return self.cheater_wall_inner_y() + self.cheater_wall_thickness_y()

    def cheater_screwdriver_keepout_radius(self) -> float:
        return (
            self.cheater_screwdriver_shaft_diameter / 2
            + self.cheater_screwdriver_radial_clearance
        )

    def cheater_top_screw_y(self) -> float:
        """Keep the established screw-to-edge material around the middle top."""
        return (
            self.block_width_y() / 2
            - self.body_screw_hole_dia() / 2
            - self.screw_to_outer_wall
        )

    def block_end_corner_chamfer(self) -> float:
        """Start each end chamfer at the bearing-holder screw axis."""
        shoulder_screw_y = self.bearing_holder_screw_spacing_y() / 2
        return self.block_width_y() / 2 - shoulder_screw_y

    def cheater_wheel_width(self) -> float:
        return (
            self.block_width_y() / 2
            - self.cheater_wall_outer_y()
            + self.cheater_wheel_outboard_extension
        )

    def cheater_positive_y_shelf_top_z(self) -> float:
        """Highest shelf that keeps both pan heads 2 mm from the wheel."""
        bolt = self.removable_top_bolt()
        keepout_radius = self.cheater_wheel_clearance_radius()
        head_radius = bolt.head_diameter() / 2
        screw_x_positions = (
            self.cheater_top_start_x() + self.cheater_top_screw_x_margin,
            self.cheater_top_start_x()
            + self.cheater_top_length_x()
            - self.cheater_top_screw_x_margin,
        )
        allowed_shelf_tops = []
        for screw_x in screw_x_positions:
            nearest_head_x = max(
                0.0,
                abs(screw_x - self.cheater_pivot_x()) - head_radius,
            )
            if nearest_head_x >= keepout_radius:
                continue
            clearance_floor_z = self.cheater_pivot_z() - math.sqrt(
                keepout_radius * keepout_radius
                - nearest_head_x * nearest_head_x
            )
            allowed_shelf_tops.append(
                clearance_floor_z - bolt.head_height()
            )
        if not allowed_shelf_tops:
            return self.block_height_z()
        return min(self.block_height_z(), *allowed_shelf_tops)

    def cheater_positive_y_shelf_drop(self) -> float:
        return self.block_height_z() - self.cheater_positive_y_shelf_top_z()

    def cheater_spring(self) -> bb.CompressionSpring:
        return bb.CompressionSpring.get(
            wire_diameter=self.cheater_spring_wire_diameter,
            outside_diameter=self.cheater_spring_outside_diameter,
            free_length=self.cheater_spring_free_length,
            coil_count=self.cheater_spring_coil_count,
        )

    def cheater_spring_pocket_diameter(self) -> float:
        return (
            self.cheater_spring_outside_diameter
            + self.cheater_spring_pocket_diameter_clearance
        )

    def cheater_spring_center_x(self) -> float:
        maximum_center_x = (
            self.cheater_top_start_x()
            + self.cheater_top_length_x()
            - self.cheater_spring_pocket_diameter() / 2
            - self.cheater_spring_edge_clearance_x
        )
        return min(
            self.cheater_pivot_x() + self.cheater_spring_target_from_pivot_x,
            maximum_center_x,
        )

    def cheater_spring_installed_length(self) -> float:
        lower_seat_z = (
            self.block_height_z() - self.cheater_spring_pocket_depth_top
        )
        upper_seat_z = (
            self.cheater_pivot_z()
            + self.cheater_spring_pocket_depth_rocker
        )
        return upper_seat_z - lower_seat_z

    def _validate_spring_configuration(self) -> None:
        """Reject spring choices that cannot work in the current mechanism."""
        wire_diameter = self.cheater_spring_wire_diameter
        outside_diameter = self.cheater_spring_outside_diameter
        installed_length = self.cheater_spring_installed_length()
        pocket_diameter = self.cheater_spring_pocket_diameter()
        spring_center_x = self.cheater_spring_center_x()
        dimensions = {
            "wire diameter": wire_diameter,
            "outside diameter": outside_diameter,
            "free length": self.cheater_spring_free_length,
            "installed length": installed_length,
            "pocket diameter": pocket_diameter,
            "pocket center X": spring_center_x,
            "pocket diameter clearance": (
                self.cheater_spring_pocket_diameter_clearance
            ),
            "X-edge clearance": self.cheater_spring_edge_clearance_x,
        }
        for label, value in dimensions.items():
            if not math.isfinite(value):
                raise ValueError(f"Cheater spring {label} must be finite")
        if (
            type(self.cheater_spring_coil_count) is not int
            or self.cheater_spring_coil_count < 1
        ):
            raise ValueError("Cheater spring coil count must be a positive integer")
        if wire_diameter <= 0:
            raise ValueError("Cheater spring wire diameter must be greater than 0 mm")
        if outside_diameter <= wire_diameter:
            raise ValueError(
                "Cheater spring outside diameter must be greater than its wire "
                f"diameter ({outside_diameter:g} mm OD, {wire_diameter:g} mm wire)"
            )
        if self.cheater_spring_pocket_diameter_clearance < 0:
            raise ValueError(
                "Cheater spring pocket diameter clearance cannot be negative"
            )
        if self.cheater_spring_edge_clearance_x < 0:
            raise ValueError("Cheater spring X-edge clearance cannot be negative")
        if not 0 < self.cheater_spring_pocket_depth_top < (
            self.block_height_z() - self.block_center_z()
        ):
            raise ValueError(
                "Cheater top spring-pocket depth must be positive and shallower "
                "than the removable top"
            )
        if not 0 < self.cheater_spring_pocket_depth_rocker < (
            self.cheater_rocker_arm_thickness_z
        ):
            raise ValueError(
                "Cheater rocker spring-pocket depth must be positive and shallower "
                "than the rocker arm"
            )
        modeled_solid_length = (
            self.cheater_spring_coil_count + 1
        ) * wire_diameter
        if installed_length < modeled_solid_length:
            raise ValueError(
                "Cheater spring installed length is shorter than the modeled solid "
                f"height ({installed_length:g} mm installed, "
                f"{modeled_solid_length:g} mm solid for "
                f"{self.cheater_spring_coil_count} coils)"
            )
        if self.cheater_spring_free_length <= installed_length:
            raise ValueError(
                "Cheater spring free length must exceed the installed seat gap to "
                f"provide preload ({self.cheater_spring_free_length:g} mm free, "
                f"{installed_length:g} mm installed)"
            )
        if pocket_diameter >= self.cheater_rocker_width_y:
            raise ValueError(
                "Cheater spring pocket must be narrower than the rocker so the "
                f"spring remains laterally captured ({pocket_diameter:g} mm pocket, "
                f"{self.cheater_rocker_width_y:g} mm rocker); use a narrower spring "
                "or increase cheater_rocker_width_y"
            )

        top_start_x = self.cheater_top_start_x()
        top_end_x = top_start_x + self.cheater_top_length_x()
        pocket_radius = pocket_diameter / 2
        required_edge_clearance = self.cheater_spring_edge_clearance_x
        pocket_left_x = spring_center_x - pocket_radius
        pocket_right_x = spring_center_x + pocket_radius
        if (
            pocket_left_x < top_start_x + required_edge_clearance
            or pocket_right_x > top_end_x - required_edge_clearance
        ):
            raise ValueError(
                "Cheater spring pocket does not fit within the removable top with "
                f"the requested {required_edge_clearance:g} mm X-edge clearance"
            )

        rocker_start_x = self.index_teeth_positive_x()
        rocker_end_x = (
            self.cheater_pivot_x() + self.cheater_rocker_positive_x_length
        )
        if (
            pocket_left_x < rocker_start_x + required_edge_clearance
            or pocket_right_x > rocker_end_x - required_edge_clearance
        ):
            raise ValueError(
                "Cheater spring pocket does not fit within the rocker arm with "
                f"the requested {required_edge_clearance:g} mm X-edge clearance; "
                "increase cheater_rocker_positive_x_length or use a narrower spring"
            )
        if spring_center_x <= self.cheater_pivot_x():
            raise ValueError(
                "Cheater spring center must be on the +X side of the rocker pivot "
                "so it presses the gear section toward the index gear"
            )

    def removable_top_bolt(self) -> bb.Bolt:
        return bb.Bolt.get(
            size=self.removable_top_screw_size,
            length=self.removable_top_screw_length,
            head=self.removable_top_screw_head,
        )

    def removable_top_nut(self) -> bb.Nut:
        return bb.Nut.get(size=self.removable_top_screw_size)

    def removable_top_nut_width(self) -> float:
        return (
            self.removable_top_nut().width_across_flats()
            + self.removable_top_nut_clearance * 2
        )

    def removable_top_nut_depth(self) -> float:
        return (
            self.removable_top_nut().height()
            + self.removable_top_nut_depth_clearance
        )

    def cheater_pivot_bolt(self) -> bb.Bolt:
        head_reference = bb.Bolt.get(
            size=self.cheater_pivot_bolt_size,
            length=1.0,
            head="hex",
        )
        nyloc = self.cheater_pivot_nyloc()
        minimum_shaft_length = (
            self.cheater_wall_outer_y()
            + self.cheater_wheel_width()
            - head_reference.head_height()
            + self.cheater_wall_outer_y()
            + nyloc.height()
            + self.cheater_pivot_bolt_thread_protrusion
        )
        shaft_length = math.ceil(minimum_shaft_length / 5.0) * 5.0
        return bb.Bolt.get(
            size=self.cheater_pivot_bolt_size,
            length=shaft_length,
            head="hex",
        )

    def cheater_pivot_nyloc(self) -> bb.NylocNut:
        return bb.NylocNut.get(size=self.cheater_pivot_bolt_size)

    def __init__(
        self,
        er11: bb.StraightShankColletExtension | None = None,
        bearing_type: type[bb.BearingGeneric] = bb.Bearing6001ZZ,
        explode: bool = False,
    ) -> None:
        super().__init__(name="Quill Assembly")
        self.er11 = er11 or bb.StraightShankColletExtension.get(
            dia=12.0,
            length=100.0,
        )
        self.bearing_type = bearing_type
        self.explode = explode
        self._current_group = self.name  # group sub-parts under this assembly
        self._validate_bearing_configuration()
        self._validate_index_gear_configuration()
        self._validate_spring_configuration()

        # Sub-parts (cached via create() → get())
        joint = QuillJointAli.create(
            shoulder_dia=self.joint_shoulder_dia,
            shoulder_gap=self.joint_shoulder_gap,
            shoulder_thickness=self.joint_shoulder_thickness,
            user_nub_dia=self.joint_user_nub_dia,
            user_nub_length=self.joint_user_nub_length,
            away_nub_dia=self.joint_away_nub_dia,
            away_nub_length=self.joint_away_nub_length,
            hinge_height=self.joint_hinge_height,
            angle_indicator_height=self.joint_angle_indicator_height,
            angle_indicator_thickness=self.joint_angle_indicator_thickness,
            body_negative_x=self.joint_body_negative_x(),
            body_positive_x=self.joint_body_positive_x,
            body_top_z=self.joint_body_top_z,
            magnet_pocket_dia=self.joint_magnet_pocket_dia,
            magnet_pocket_depth=self.joint_magnet_pocket_depth,
            base_plate_thickness=self.base_plate_thickness,
            base_plate_x=self.base_plate_x(),
            base_plate_center_x=self.base_plate_center_x(),
            base_plate_y=self.base_plate_y(),
        )
        angle_indicator = QuillAngleIndicator.create(
            shoulder_dia=self.joint_shoulder_dia,
            away_nub_dia=self.joint_away_nub_dia,
            hinge_z=self.base_plate_thickness + self.joint_hinge_height,
            height=self.joint_angle_indicator_height,
            width_x=self.joint_angle_indicator_width_x,
            thickness=self.joint_angle_indicator_thickness,
            corner_radius=self.joint_angle_indicator_corner_radius(),
        )
        angle_indicator_screw = self.joint_angle_indicator_screw()
        block = QuillMainBlock.create(
            length_x=self.block_length_x(),
            width_y=self.block_width_y(),
            height_z=self.block_height_z(),
            split_height=self.block_center_z(),
            collet_side_bearing_x=self.collet_side_bearing_x(),
            index_side_bearing_x=self.index_side_bearing_x(),
            bearing_type=self.bearing_type,
            bearing_pocket_dia=self.bearing_pocket_dia(),
            bearing_pocket_depth=self.bearing_pocket_depth(),
            bearing_retaining_lip_depth=self.bearing_retaining_lip_depth,
            bearing_retaining_lip_opening_dia=(
                self.bearing_retaining_lip_opening_dia()
            ),
            shank_bore_dia=self.shank_bore_dia(),
            holder_length_x=self.bearing_holder_length_x,
            holder_split_gap=self.bearing_holder_split_gap,
            bearing_holder_screw_x_from_end=(
                self.bearing_holder_screw_x_from_end
            ),
            bearing_holder_screw_spacing_y=self.bearing_holder_screw_spacing_y(),
            body_screw_hole_dia=self.body_screw_hole_dia(),
            holder_screw_hole_dia=self.holder_screw_hole_dia(),
            cheater_top_screw_x_margin=self.cheater_top_screw_x_margin,
            cheater_top_screw_y=self.cheater_top_screw_y(),
            cheater_top_screw_clearance_dia=self.cheater_top_screw_clearance_dia,
            cheater_top_body_clearance_depth=self.block_center_z(),
            end_corner_chamfer=self.block_end_corner_chamfer(),
            end_vertical_edge_fillet=self.block_end_vertical_edge_fillet,
            top_edge_fillet=self.block_top_edge_fillet,
            removable_top_nut_width=self.removable_top_nut_width(),
            removable_top_nut_depth=self.removable_top_nut_depth(),
            removable_top_nut_drop=self.removable_top_nut_drop,
            removable_top_nut_bridge_thickness=(
                self.removable_top_nut_bridge_thickness
            ),
        )
        away_shoulder_inner_y = (
            # Repeated AI mistake: using shoulder_joint_thickness instead of
            # joint_angle_indicator_thickness.
            -self.joint_shoulder_gap / 2 + self.joint_angle_indicator_thickness
        )
        body = QuillBody(
            main_block=block,
            joint=joint,
            angle_indicator=angle_indicator,
            block_x=self.block_x_offset,
            indicator_y=away_shoulder_inner_y,
            reinforcement_start_x=self.body_reinforcement_start_x(),
            reinforcement_end_x=self.body_reinforcement_end_x(),
            reinforcement_width_y=self.base_plate_y(),
            reinforcement_bottom_z=self.base_plate_thickness,
            reinforcement_top_z=self.body_reinforcement_top_z(),
            index_gear_start_x=self.block_x_offset - self.index_gear_width(),
            index_gear_width_x=self.index_gear_width(),
            index_gear_axis_z=self.block_center_z(),
            index_gear_clearance_radius=self.body_index_gear_clearance_radius(),
            index_gear_axial_clearance=self.body_index_gear_axial_clearance,
        )
        bearing_holder = QuillBearingHolder.create(
            quill_block=block,
            holder_length_x=self.bearing_holder_length_x,
            holder_split_gap=self.bearing_holder_split_gap,
            screw_spacing_y=self.bearing_holder_screw_spacing_y(),
        )
        cheater_top = QuillCheaterBearingTop.create(
            quill_block=block,
            pivot_x=self.cheater_pivot_x(),
            pivot_z=self.cheater_pivot_z(),
            wall_inner_y=self.cheater_wall_inner_y(),
            wall_thickness_y=self.cheater_wall_thickness_y(),
            wall_outer_radius=self.cheater_wall_outer_radius(),
            bearing_pocket_dia=self.cheater_bearing_pocket_dia(),
            bearing_width=self.cheater_bearing_type.WIDTH,
            axle_hole_dia=self.cheater_axle_hole_dia(),
            positive_y_shelf_top_z=self.cheater_positive_y_shelf_top_z(),
            wheel_clearance_radius=self.cheater_wheel_clearance_radius(),
            positive_y_shelf_edge_bevel=(
                self.cheater_positive_y_shelf_edge_bevel
            ),
            max_print_angle=self.cheater_wall_max_print_angle,
            spring_center_x=self.cheater_spring_center_x(),
            spring_pocket_diameter=self.cheater_spring_pocket_diameter(),
            spring_pocket_depth=self.cheater_spring_pocket_depth_top,
        )
        cheater_rocker = QuillCheaterRocker.create(
            negative_x=self.index_teeth_positive_x(),
            positive_x=(
                self.cheater_pivot_x()
                + self.cheater_rocker_positive_x_length
            ),
            pivot_x=self.cheater_pivot_x(),
            pivot_z=self.cheater_pivot_z(),
            width_y=self.cheater_rocker_width_y,
            arm_thickness_z=self.cheater_rocker_arm_thickness_z,
            pivot_outer_diameter=self.cheater_rocker_pivot_outer_diameter,
            pivot_pilot_diameter=self.cheater_rocker_pivot_pilot_diameter,
            gear_mount_bottom_z=self.cheater_gear_mount_bottom_z(),
            gear_mount_positive_x=self.cheater_rocker_gear_mount_positive_x,
            gear_screw_z=self.cheater_gear_section_screw_z(),
            gear_screw_spacing_y=self.cheater_gear_section_screw_spacing_y,
            gear_screw_pilot_diameter=(
                self.cheater_gear_section_screw_pilot_dia
            ),
            spring_center_x=self.cheater_spring_center_x(),
            spring_pocket_diameter=self.cheater_spring_pocket_diameter(),
            spring_pocket_depth=self.cheater_spring_pocket_depth_rocker,
        )
        gear_section_screw = self.cheater_gear_section_screw()
        cheater_gear_section = QuillCheaterGearSection.create(
            negative_x=self.cheater_gear_section_negative_x(),
            positive_x=self.index_teeth_positive_x(),
            tooth_contact_z=(
                self.block_center_z()
                + self.cheater_gear_section_tooth_tip_radius()
            ),
            curve_radius=self.index_gear_tip_radius(),
            tooth_depth=self.index_gear_tooth_depth,
            backing_width_y=self.cheater_rocker_width_y,
            backing_bottom_z=self.cheater_gear_mount_bottom_z(),
            backing_top_z=self.cheater_gear_section_backing_top_z(),
            angular_pitch=2 * math.pi / self.index_gear_num_teeth,
            tooth_count=self.cheater_gear_section_tooth_count(),
            screw_spacing_y=self.cheater_gear_section_screw_spacing_y,
            screw_z=self.cheater_gear_section_screw_z(),
            screw_clearance_diameter=(
                self.cheater_gear_section_screw_clearance_dia
            ),
            screw_head_diameter=gear_section_screw.head_diameter(),
            screw_head_height=gear_section_screw.head_height(),
            tooth_root_relief_tangential_width=(
                self.gear_tooth_root_relief_tangential_width
            ),
            tooth_root_relief_radial_depth=self.gear_tooth_root_relief_radial_depth,
            negative_x_extension=self.cheater_gear_section_negative_x_extension,
            mating_index_gear_tooth_count=self.index_gear_num_teeth,
            tooth_count_engraving_size=(
                self.cheater_gear_section_tooth_count_engraving_size
            ),
            tooth_count_engraving_depth=(
                self.cheater_gear_section_tooth_count_engraving_depth
            ),
            tooth_count_engraving_z=(
                self.cheater_gear_section_screw_z()
                + self.cheater_gear_section_tooth_count_engraving_size / 2
                + self.cheater_gear_section_tooth_count_engraving_margin_z
            ),
        )
        cheater_spring = self.cheater_spring()
        pivot_bolt = self.cheater_pivot_bolt()
        pivot_nyloc = self.cheater_pivot_nyloc()
        cheater_wheel = QuillCheaterAdjustmentWheel.create(
            outside_diameter=self.cheater_wheel_diameter,
            width=self.cheater_wheel_width(),
            hex_across_flats=(
                pivot_bolt.head_diameter()
                + self.cheater_wheel_hex_clearance * 2
            ),
            hex_depth=(
                pivot_bolt.head_height()
                + self.cheater_wheel_head_depth_clearance
            ),
            shaft_hole_diameter=self.cheater_axle_hole_dia(),
            grip_notch_radius=self.cheater_wheel_grip_notch_radius,
            grip_notch_count=self.cheater_wheel_grip_notch_count,
        )
        gear = IndexGearStandardMk1.create(
            od=self.index_gear_od,
            bore_dia=self.index_gear_bore_dia(),
            teeth_width=self.index_gear_teeth_width,
            tooth_depth=self.index_gear_tooth_depth,
            numbers_width=self.index_gear_numbers_width,
            spacer_width=self.index_gear_modeled_spacer_width(),
            spacer_od=self.index_gear_spacer_od,
            num_teeth=self.index_gear_num_teeth,
            tick_interval_teeth=self.index_gear_tick_interval_teeth,
            number_interval_teeth=self.index_gear_number_interval_teeth,
            clamp_screw_hole_dia=self.index_gear_clamp_screw_hole_dia(),
            clamp_nut_width_across_flats=(
                self.index_gear_clamp_nut_pocket_width()
            ),
            clamp_nut_depth=self.index_gear_clamp_nut_pocket_depth(),
            clamp_nut_inner_radius=self.index_gear_clamp_nut_inner_radius(),
            clamp_angle=self.index_gear_clamp_angle(),
            tooth_root_relief_tangential_width=(
                self.gear_tooth_root_relief_tangential_width
            ),
            tooth_root_relief_radial_depth=self.gear_tooth_root_relief_radial_depth,
        )
        er11 = self.er11

        # ── Assemble ────────────────────────────────────────────
        # Subtract block_center_z from each part's Z placement to align it with
        # the joint hinge axis.
        block_x = self.block_x_offset
        shank_start_x = block_x + self.block_length_x() - self.er11.length
        gear_x = block_x - self.index_gear_width()

        self._add(body, loc=Location(0, 0, -self.block_center_z()))
        # Exploded display placement does not affect the true cutout position.
        indicator_display_y = away_shoulder_inner_y - (
            20.0 if self.explode else 0.0
        )
        self._add(
            angle_indicator,
            obj=angle_indicator.get_object(),
            loc=Location(
                0.0,
                indicator_display_y,
                -self.block_center_z(),
                90,
                0,
                0,
            ),
            name="angle_indicator",
            color="blue",
        )
        indicator_outer_y = (
            indicator_display_y - self.joint_angle_indicator_thickness
        )
        indicator_hinge_z = self.base_plate_thickness + self.joint_hinge_height
        for index, z in enumerate(
            (indicator_hinge_z - 6.0, indicator_hinge_z + 6.0)
        ):
            screw_obj = (
                angle_indicator_screw.get_object()
                .rotate((0, 0, 0), (1, 0, 0), -90)
                .translate((-6.0, indicator_outer_y, z))
            )
            self._add(
                angle_indicator_screw,
                obj=screw_obj,
                loc=Location(0, 0, -self.block_center_z()),
                name=f"angle_indicator_screw_{index}",
                color="gray",
            )
        self._add(er11, loc=Location(Vector(shank_start_x, 0, 0), Vector(0, 1, 0), 90),
                  color="gray")
        self._add(
            bearing_holder,
            obj=bearing_holder.get_assembled_object(),
            loc=Location(block_x, 0, -self.block_center_z()),
            name="bearing_holder_index",
            color="green",
        )
        far_holder_obj = bearing_holder.get_assembled_object()
        if not isinstance(far_holder_obj, cq.Workplane):
            raise TypeError("QuillBearingHolder must provide Workplane geometry")
        far_holder_obj = far_holder_obj.rotate((0, 0, 0), (0, 0, 1), 180)
        self._add(
            bearing_holder,
            obj=far_holder_obj,
            loc=Location(block_x + self.block_length_x(), 0, -self.block_center_z()),
            name="bearing_holder_collet",
            color="green",
        )
        self._add(
            cheater_top,
            obj=cheater_top.get_assembled_object(),
            loc=Location(block_x, 0, -self.block_center_z()),
            name="cheater_bearing_top",
            color="blue",
        )
        cheater_bearing = self.cheater_bearing_type.get(
            name=self.cheater_bearing_type.name,
        )
        positive_bearing_obj = (
            cheater_bearing.get_object()
            .rotate((0, 0, 0), (1, 0, 0), -90)
            .translate(
                (
                    self.cheater_pivot_x(),
                    self.cheater_wall_inner_y() + self.cheater_bearing_inner_lip,
                    self.cheater_pivot_z(),
                )
            )
        )
        negative_bearing_obj = (
            cheater_bearing.get_object()
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate(
                (
                    self.cheater_pivot_x(),
                    -self.cheater_wall_inner_y() - self.cheater_bearing_inner_lip,
                    self.cheater_pivot_z(),
                )
            )
        )
        self._add(
            cheater_bearing,
            obj=positive_bearing_obj,
            loc=Location(block_x, 0, -self.block_center_z()),
            name="cheater_bearing_positive_y",
            color="gray",
        )
        self._add(
            cheater_bearing,
            obj=negative_bearing_obj,
            loc=Location(block_x, 0, -self.block_center_z()),
            name="cheater_bearing_negative_y",
            color="gray",
        )
        self._add(
            cheater_rocker,
            obj=cheater_rocker.get_assembled_object(),
            loc=Location(block_x, 0, -self.block_center_z()),
            name="cheater_rocker",
            color="yellow",
        )
        self._add(
            cheater_gear_section,
            obj=cheater_gear_section.get_assembled_object(),
            loc=Location(block_x, 0, -self.block_center_z()),
            name="cheater_gear_section",
            color="red",
        )
        for index, y in enumerate(
            (
                -self.cheater_gear_section_screw_spacing_y / 2,
                self.cheater_gear_section_screw_spacing_y / 2,
            )
        ):
            screw_obj = (
                gear_section_screw.get_object()
                .rotate((0, 0, 0), (0, 1, 0), 90)
                .translate(
                    (
                        self.cheater_gear_section_negative_x(),
                        y,
                        self.cheater_gear_section_screw_z(),
                    )
                )
            )
            self._add(
                gear_section_screw,
                obj=screw_obj,
                loc=Location(block_x, 0, -self.block_center_z()),
                name=f"cheater_gear_section_screw_{index}",
                color="gray",
            )
        spring_lower_seat_z = (
            self.block_height_z() - self.cheater_spring_pocket_depth_top
        )
        spring_obj = cheater_spring.object_at_length(
            self.cheater_spring_installed_length()
        ).translate(
            (
                block_x + self.cheater_spring_center_x(),
                0,
                spring_lower_seat_z - self.block_center_z(),
            )
        )
        self._add(
            cheater_spring,
            obj=spring_obj,
            name="cheater_rocker_spring",
            color="gray",
        )
        cheater_wall_outer_y = (
            self.cheater_wall_inner_y() + self.cheater_wall_thickness_y()
        )
        pivot_location = (
            block_x + self.cheater_pivot_x(),
            0.0,
            self.cheater_pivot_z() - self.block_center_z(),
        )
        pivot_bolt_obj = (
            pivot_bolt.get_object()
            .rotate((0, 0, 0), (1, 0, 0), -90)
            .translate(
                (
                    pivot_location[0],
                    cheater_wall_outer_y
                    + self.cheater_wheel_width()
                    - pivot_bolt.head_height(),
                    pivot_location[2],
                )
            )
        )
        cheater_wheel_printable_obj = cheater_wheel.get_object()
        if not isinstance(cheater_wheel_printable_obj, cq.Workplane):
            raise TypeError("Cheater adjustment wheel must provide Workplane geometry")
        cheater_wheel_obj = (
            cheater_wheel_printable_obj
            .rotate((0, 0, 0), (1, 0, 0), -90)
            .translate(
                (
                    pivot_location[0],
                    cheater_wall_outer_y,
                    pivot_location[2],
                )
            )
        )
        self._add(
            pivot_bolt,
            obj=pivot_bolt_obj,
            name="cheater_pivot_bolt",
            color="gray",
        )
        pivot_nyloc_metal_obj = (
            pivot_nyloc.metal_object()
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate(
                (
                    pivot_location[0],
                    -cheater_wall_outer_y,
                    pivot_location[2],
                )
            )
        )
        pivot_nyloc_insert_obj = (
            pivot_nyloc.nylon_insert_object()
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate(
                (
                    pivot_location[0],
                    -cheater_wall_outer_y,
                    pivot_location[2],
                )
            )
        )
        self._add(
            pivot_nyloc,
            obj=pivot_nyloc_metal_obj,
            name="cheater_pivot_nyloc",
            color="gray",
        )
        self._assembly.add(
            pivot_nyloc_insert_obj,
            name="cheater_pivot_nyloc_insert",
            color=cq.Color("black"),
        )
        self._add(
            cheater_wheel,
            obj=cheater_wheel_obj,
            name="cheater_adjustment_wheel",
            color="red",
        )
        top_bolt = self.removable_top_bolt()
        lowered_top_bolt = bb.Bolt.get(
            size=self.removable_top_screw_size,
            length=(
                self.removable_top_screw_length
                - math.floor(self.cheater_positive_y_shelf_drop())
            ),
            head=self.removable_top_screw_head,
        )
        top_nut = self.removable_top_nut()
        hardware_positions = (
            tuple(
                (
                    x,
                    y,
                    self.block_center_z()
                    - self.bearing_holder_split_gap / 2
                    - self.removable_top_nut_drop,
                    "bearing_holder",
                )
                for x, y in block.bearing_holder_screw_positions()
            )
            + tuple(
                (
                    x,
                    y,
                    self.block_center_z() - self.removable_top_nut_drop,
                    "cheater_top",
                )
                for x, y in block.cheater_top_screw_positions()
            )
        )
        for index, (x, y, nut_top_z, label) in enumerate(hardware_positions):
            is_lowered_shelf_screw = label == "cheater_top" and y > 0
            displayed_bolt = lowered_top_bolt if is_lowered_shelf_screw else top_bolt
            bolt_top_z = self.block_height_z() - (
                self.cheater_positive_y_shelf_drop()
                if is_lowered_shelf_screw
                else 0.0
            )
            bolt_obj = displayed_bolt.get_object().translate(
                (block_x + x, y, bolt_top_z - self.block_center_z())
            )
            nut_obj = (
                top_nut.get_object()
                .rotate((0, 0, 0), (1, 0, 0), 180)
                .rotate((0, 0, 0), (0, 0, 1), 30)
                .translate((block_x + x, y, nut_top_z - self.block_center_z()))
            )
            self._add(
                displayed_bolt,
                obj=bolt_obj,
                name=f"{label}_bolt_{index}",
                color="gray",
            )
            self._add(
                top_nut,
                obj=nut_obj,
                name=f"{label}_nut_{index}",
                color="gray",
            )
        def gear_local_to_assembly(obj: cq.Workplane) -> cq.Workplane:
            return obj.rotate(
                (0, 0, 0), (0, 0, 1), 180
            ).rotate(
                (0, 0, 0), (0, 1, 0), 90
            )

        gear_object = gear.get_object()
        if not isinstance(gear_object, cq.Workplane):
            raise TypeError("Index gear must provide Workplane geometry")
        gear_obj = gear_local_to_assembly(gear_object)
        self._add(
            gear,
            obj=gear_obj,
            loc=Location(gear_x, 0, 0),
            color="blue",
        )
        clamp_screw_local, clamp_nut_local = (
            self.index_gear_clamp_hardware_local_objects()
        )
        self._add(
            self.index_gear_clamp_screw(),
            obj=gear_local_to_assembly(clamp_screw_local),
            loc=Location(gear_x, 0, 0),
            name="index_gear_clamp_set_screw",
            color="gray",
        )
        self._add(
            self.index_gear_clamp_nut(),
            obj=gear_local_to_assembly(clamp_nut_local),
            loc=Location(gear_x, 0, 0),
            name="index_gear_clamp_nut",
            color="gray",
        )


# ═══════════════════════════════════════════════════════════════════════
# Printed parts
# ═══════════════════════════════════════════════════════════════════════


class QuillMainBlock:
    """Geometry helper shared by the printable quill body and bearing holders."""

    @classmethod
    def create(
        cls,
        length_x: float,
        width_y: float,
        height_z: float,
        split_height: float,
        collet_side_bearing_x: float,
        index_side_bearing_x: float,
        bearing_type: type[bb.BearingGeneric],
        bearing_pocket_dia: float,
        bearing_pocket_depth: float,
        bearing_retaining_lip_depth: float,
        bearing_retaining_lip_opening_dia: float,
        shank_bore_dia: float,
        holder_length_x: float,
        holder_split_gap: float,
        bearing_holder_screw_x_from_end: float,
        bearing_holder_screw_spacing_y: float,
        body_screw_hole_dia: float,
        holder_screw_hole_dia: float,
        cheater_top_screw_x_margin: float,
        cheater_top_screw_y: float,
        cheater_top_screw_clearance_dia: float,
        cheater_top_body_clearance_depth: float,
        end_corner_chamfer: float,
        end_vertical_edge_fillet: float,
        top_edge_fillet: float,
        removable_top_nut_width: float,
        removable_top_nut_depth: float,
        removable_top_nut_drop: float,
        removable_top_nut_bridge_thickness: float,
    ) -> QuillMainBlock:
        return cls(
            length_x=length_x,
            width_y=width_y,
            height_z=height_z,
            split_height=split_height,
            collet_side_bearing_x=collet_side_bearing_x,
            index_side_bearing_x=index_side_bearing_x,
            bearing_type=bearing_type,
            bearing_pocket_dia=bearing_pocket_dia,
            bearing_pocket_depth=bearing_pocket_depth,
            bearing_retaining_lip_depth=bearing_retaining_lip_depth,
            bearing_retaining_lip_opening_dia=(
                bearing_retaining_lip_opening_dia
            ),
            shank_bore_dia=shank_bore_dia,
            holder_length_x=holder_length_x,
            holder_split_gap=holder_split_gap,
            bearing_holder_screw_x_from_end=bearing_holder_screw_x_from_end,
            bearing_holder_screw_spacing_y=bearing_holder_screw_spacing_y,
            body_screw_hole_dia=body_screw_hole_dia,
            holder_screw_hole_dia=holder_screw_hole_dia,
            cheater_top_screw_x_margin=cheater_top_screw_x_margin,
            cheater_top_screw_y=cheater_top_screw_y,
            cheater_top_screw_clearance_dia=cheater_top_screw_clearance_dia,

            cheater_top_body_clearance_depth=cheater_top_body_clearance_depth,
            end_corner_chamfer=end_corner_chamfer,
            end_vertical_edge_fillet=end_vertical_edge_fillet,
            top_edge_fillet=top_edge_fillet,
            removable_top_nut_width=removable_top_nut_width,
            removable_top_nut_depth=removable_top_nut_depth,
            removable_top_nut_drop=removable_top_nut_drop,
            removable_top_nut_bridge_thickness=(
                removable_top_nut_bridge_thickness
            ),
        )

    def __init__(
        self,
        length_x: float,
        width_y: float,
        height_z: float,
        split_height: float,
        collet_side_bearing_x: float,
        index_side_bearing_x: float,
        bearing_type: type[bb.BearingGeneric],
        bearing_pocket_dia: float,
        bearing_pocket_depth: float,
        bearing_retaining_lip_depth: float,
        bearing_retaining_lip_opening_dia: float,
        shank_bore_dia: float,
        holder_length_x: float,
        holder_split_gap: float,
        bearing_holder_screw_x_from_end: float,
        bearing_holder_screw_spacing_y: float,
        body_screw_hole_dia: float,
        holder_screw_hole_dia: float,
        cheater_top_screw_x_margin: float,
        cheater_top_screw_y: float,
        cheater_top_screw_clearance_dia: float,
        cheater_top_body_clearance_depth: float,
        end_corner_chamfer: float,
        end_vertical_edge_fillet: float,
        top_edge_fillet: float,
        removable_top_nut_width: float,
        removable_top_nut_depth: float,
        removable_top_nut_drop: float,
        removable_top_nut_bridge_thickness: float,
    ) -> None:
        self.length = length_x
        self.width = width_y
        self.height = height_z
        self.split_height = split_height
        self.collet_side_bearing_x = collet_side_bearing_x
        self.index_side_bearing_x = index_side_bearing_x
        self.bearing_type = bearing_type
        self.bearing_pocket_dia = bearing_pocket_dia
        self.bearing_pocket_depth = bearing_pocket_depth
        self.bearing_retaining_lip_depth = bearing_retaining_lip_depth
        self.bearing_retaining_lip_opening_dia = (
            bearing_retaining_lip_opening_dia
        )
        self.shank_bore_dia = shank_bore_dia
        self.holder_length_x = holder_length_x
        self.holder_split_gap = holder_split_gap
        self.bearing_holder_screw_x_from_end = bearing_holder_screw_x_from_end
        self.bearing_holder_screw_spacing_y = bearing_holder_screw_spacing_y
        self.body_screw_hole_dia = body_screw_hole_dia
        self.holder_screw_hole_dia = holder_screw_hole_dia
        self.cheater_top_screw_x_margin = cheater_top_screw_x_margin
        self.cheater_top_screw_y = cheater_top_screw_y
        self.cheater_top_screw_clearance_dia = cheater_top_screw_clearance_dia

        self.cheater_top_body_clearance_depth = cheater_top_body_clearance_depth
        self.end_corner_chamfer = end_corner_chamfer
        self.end_vertical_edge_fillet = end_vertical_edge_fillet
        self.top_edge_fillet = top_edge_fillet
        self.removable_top_nut_width = removable_top_nut_width
        self.removable_top_nut_depth = removable_top_nut_depth
        self.removable_top_nut_drop = removable_top_nut_drop
        self.removable_top_nut_bridge_thickness = (
            removable_top_nut_bridge_thickness
        )

        self._object = (
            self.get_base_shape()
            .cut(self.bearing_holder_cut_boxes())
            .cut(self.cheater_top_cut_box())
            .cut(self.removable_top_fastener_cutouts())
        )

    def get_outer_shape(self) -> cq.Workplane:
        """Complete uncut block envelope used for pre-cut structural fusing."""
        return (
            cq.Workplane("XY")
            .box(
                self.length,
                self.width,
                self.height,
                centered=(False, True, False),
            )
            .edges("|Z")
            .chamfer(self.end_corner_chamfer)
            .edges("|Z")
            .fillet(self.end_vertical_edge_fillet)
            .faces(">Z")
            .edges()
            .fillet(self.top_edge_fillet)
        )

    def get_base_shape(self) -> cq.Workplane:
        """Complete block with the shared stepped bearing/shank cavity."""
        block = self.get_outer_shape()
        index_pocket = (
            cq.Workplane("YZ")
            .cylinder(
                self.bearing_pocket_depth,
                self.bearing_pocket_dia / 2,
                centered=(True, True, False),
            )
            .translate(
                (self.bearing_retaining_lip_depth, 0, self.split_height)
            )
        )
        collet_pocket = index_pocket.translate(
            (
                self.length
                - self.bearing_retaining_lip_depth * 2
                - self.bearing_pocket_depth,
                0,
                0,
            )
        )
        index_lip_opening = (
            cq.Workplane("YZ")
            .cylinder(
                self.bearing_retaining_lip_depth,
                self.bearing_retaining_lip_opening_dia / 2,
                centered=(True, True, False),
            )
            .translate((0, 0, self.split_height))
        )
        collet_lip_opening = index_lip_opening.translate(
            (self.length - self.bearing_retaining_lip_depth, 0, 0)
        )
        shank_bore = (
            cq.Workplane("YZ")
            .cylinder(
                self.length,
                self.shank_bore_dia / 2,
                centered=(True, True, False),
            )
            .translate((0, 0, self.split_height))
        )
        block_cut = (
            index_pocket
            .union(collet_pocket)
            .union(index_lip_opening)
            .union(collet_lip_opening)
            .union(shank_bore)
        )
        return block.cut(block_cut)

    def bearing_holder_box(self, z_offset: float = 0.0) -> cq.Workplane:
        """Cube at the -X end; the +X end uses a translated copy."""
        box_bottom_z = self.split_height + z_offset
        box_height = self.height - box_bottom_z
        return (
            cq.Workplane("XY")
            .box(
                self.holder_length_x,
                self.width,
                box_height,
                centered=(False, True, False),
            )
            .translate((0, 0, box_bottom_z))
        )

    def bearing_holder_cut_boxes(self) -> cq.Workplane:
        near_box = self.bearing_holder_box(-self.holder_split_gap / 2)
        far_box = near_box.translate((self.length - self.holder_length_x, 0, 0))
        return near_box.union(far_box)

    def cheater_top_box(self, z_offset: float = 0.0) -> cq.Workplane:
        """Central removable top between the two end bearing holders."""
        box_bottom_z = self.split_height + z_offset
        box_height = self.height - box_bottom_z
        top_length = self.length - self.holder_length_x * 2
        return (
            cq.Workplane("XY")
            .box(
                top_length,
                self.width,
                box_height,
                centered=(False, True, False),
            )
            .translate((self.holder_length_x, 0, box_bottom_z))
        )

    def cheater_top_cut_box(self) -> cq.Workplane:
        # Unlike the bearing holders, this top does not clamp a bearing.
        # Its underside and the body's cut plane meet directly at split_height.
        return self.cheater_top_box()

    def cheater_top_screw_positions(self) -> tuple[tuple[float, float], ...]:
        near_x = self.holder_length_x + self.cheater_top_screw_x_margin
        far_x = (
            self.length
            - self.holder_length_x
            - self.cheater_top_screw_x_margin
        )
        return tuple(
            (x, y)
            for x in (near_x, far_x)
            for y in (-self.cheater_top_screw_y, self.cheater_top_screw_y)
        )

    def bearing_holder_screw_positions(self) -> tuple[tuple[float, float], ...]:
        screw_y = self.bearing_holder_screw_spacing_y / 2
        return tuple(
            (x, y)
            for x in (
                self.bearing_holder_screw_x_from_end,
                self.length - self.bearing_holder_screw_x_from_end,
            )
            for y in (-screw_y, screw_y)
        )

    def _captive_nut_fastener_cutout(
        self,
        x: float,
        y: float,
        interface_z: float,
        shaft_diameter: float,
        shaft_depth: float,
    ) -> cq.Workplane:
        outside_y = math.copysign(self.width / 2, y)
        local_cutout = SideLoadedCaptiveNutHole(
            shaft_diameter=shaft_diameter,
            shaft_depth=shaft_depth,
            nut_width_across_flats=self.removable_top_nut_width,
            nut_depth=self.removable_top_nut_depth,
            nut_drop_from_interface=self.removable_top_nut_drop,
            channel_length=abs(outside_y - y),
            bridge_thickness=self.removable_top_nut_bridge_thickness,
            bridge_side="above_nut",
        ).make_cutout()
        if y < 0:
            local_cutout = local_cutout.rotate((0, 0, 0), (0, 0, 1), 180)
        return local_cutout.translate((x, y, interface_z))

    def removable_top_fastener_cutouts(self) -> cq.Workplane:
        """Body-side bolt paths, captive-nut traps, and loading channels."""
        cutouts = cq.Workplane("XY")
        bearing_holder_interface_z = (
            self.split_height - self.holder_split_gap / 2
        )
        for x, y in self.bearing_holder_screw_positions():
            cutouts = cutouts.union(
                self._captive_nut_fastener_cutout(
                    x,
                    y,
                    bearing_holder_interface_z,
                    self.body_screw_hole_dia,
                    bearing_holder_interface_z,
                )
            )
        for x, y in self.cheater_top_screw_positions():
            cutouts = cutouts.union(
                self._captive_nut_fastener_cutout(
                    x,
                    y,
                    self.split_height,
                    self.cheater_top_screw_clearance_dia,
                    self.cheater_top_body_clearance_depth,
                )
            )
        return cutouts

    def get_cheater_top_base_shape(self) -> cq.Workplane:
        top = self.get_base_shape().intersect(
            self.cheater_top_box()
        )
        clearance = cq.Workplane("XY")
        for x, y in self.cheater_top_screw_positions():
            clearance = clearance.union(
                cq.Workplane("XY")
                .center(x, y)
                .circle(self.cheater_top_screw_clearance_dia / 2)
                .extrude(self.height)
            )
        return top.cut(clearance)

    def get_bearing_holder_shape(self) -> cq.Workplane:
        """Holder derived from the block above the centered split gap."""
        holder = self.get_base_shape().intersect(
            self.bearing_holder_box(self.holder_split_gap / 2)
        )
        screw_y = self.bearing_holder_screw_spacing_y / 2
        screw_x = self.bearing_holder_screw_x_from_end
        return (
            holder.faces(">Z")
            .workplane()
            .pushPoints([(screw_x, -screw_y), (screw_x, screw_y)])
            .hole(self.holder_screw_hole_dia, self.height)
        )

    def get_object(self) -> cq.Workplane:
        return self._object

    def get_cutouts(self) -> cq.Workplane:
        """Block-local cuts to apply after the body structure is fused."""
        return self.get_outer_shape().cut(self._object)

    def dimensions(self) -> tuple[object, ...]:
        return (
            self.length,
            self.width,
            self.height,
            self.split_height,
            self.collet_side_bearing_x,
            self.index_side_bearing_x,
            self.bearing_pocket_dia,
            self.bearing_pocket_depth,
            self.bearing_retaining_lip_depth,
            self.bearing_retaining_lip_opening_dia,
            self.shank_bore_dia,
            self.holder_length_x,
            self.holder_split_gap,
            self.bearing_holder_screw_x_from_end,
            self.bearing_holder_screw_spacing_y,
            self.body_screw_hole_dia,
            self.holder_screw_hole_dia,
            self.cheater_top_screw_x_margin,
            self.cheater_top_screw_y,
            self.cheater_top_screw_clearance_dia,
            self.cheater_top_body_clearance_depth,
            self.end_corner_chamfer,
            self.end_vertical_edge_fillet,
            self.top_edge_fillet,
            self.removable_top_nut_width,
            self.removable_top_nut_depth,
            self.removable_top_nut_drop,
            self.removable_top_nut_bridge_thickness,
            self.bearing_type,
        )


class QuillBody(bpd.PrintedPart):
    """Single printable body containing both the hinge joint and main block."""

    def __init__(
        self,
        main_block: QuillMainBlock,
        joint: QuillJointAli,
        angle_indicator: QuillAngleIndicator,
        block_x: float,
        indicator_y: float,
        reinforcement_start_x: float,
        reinforcement_end_x: float,
        reinforcement_width_y: float,
        reinforcement_bottom_z: float,
        reinforcement_top_z: float,
        index_gear_start_x: float,
        index_gear_width_x: float,
        index_gear_axis_z: float,
        index_gear_clearance_radius: float,
        index_gear_axial_clearance: float,
    ) -> None:
        self.main_block = main_block
        self.joint_dimensions = joint.dimensions()
        self.angle_indicator = angle_indicator
        self.block_x = block_x
        self.indicator_y = indicator_y
        self.reinforcement_dimensions = (
            reinforcement_start_x,
            reinforcement_end_x,
            reinforcement_width_y,
            reinforcement_bottom_z,
            reinforcement_top_z,
        )
        self.index_gear_clearance_dimensions = (
            index_gear_start_x,
            index_gear_width_x,
            index_gear_axis_z,
            index_gear_clearance_radius,
            index_gear_axial_clearance,
        )
        super().__init__(name="Quill Body")

        # Fuse the raw hinge, base, reinforcement, and block first. This lets
        # every later bearing, fastener, indicator, and gear-clearance cut pass
        # through the completed structural envelope cleanly.
        reinforcement = (
            cq.Workplane("XY")
            .box(
                reinforcement_end_x - reinforcement_start_x,
                reinforcement_width_y,
                reinforcement_top_z - reinforcement_bottom_z,
                centered=(False, True, False),
            )
            .translate(
                (
                    reinforcement_start_x,
                    0.0,
                    reinforcement_bottom_z,
                )
            )
        )
        raw_block = main_block.get_outer_shape().translate((block_x, 0, 0))
        obj = joint.get_raw_object().union(reinforcement).union(raw_block)

        block_cutouts = main_block.get_cutouts().translate((block_x, 0, 0))
        obj = obj.cut(joint.get_cutouts()).cut(block_cutouts)

        indicator_cutout = (
            angle_indicator.make(cutout=True)
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((0, indicator_y, 0))
        )
        gear_clearance = (
            cq.Workplane("YZ")
            .circle(index_gear_clearance_radius)
            # Clearance is needed outside the index gear, not behind the
            # block face. End the cylinder exactly where the block begins so
            # the bearing-holder shoulder retains the same rear profile.
            .extrude(index_gear_width_x + index_gear_axial_clearance)
            .translate(
                (
                    index_gear_start_x - index_gear_axial_clearance,
                    0.0,
                    index_gear_axis_z,
                )
            )
        )
        obj = obj.cut(indicator_cutout).cut(gear_clearance)

        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("red"))

        # Bearings belong to the merged quill body. QuillMainBlock is now a
        # geometry helper and is no longer added as a separate printed part.
        bearing = main_block.bearing_type.get(
            name=main_block.bearing_type.name,
        )
        bearing_positions = (
            main_block.collet_side_bearing_x,
            main_block.index_side_bearing_x,
        )
        for bearing_x in bearing_positions:
            self._add(
                bearing,
                loc=Location(
                    Vector(block_x + bearing_x, 0, main_block.split_height),
                    Vector(0, 1, 0),
                    90,
                ),
                color="gray",
                name=f"bearing_{bearing_x:.0f}",
            )

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.main_block.dimensions(),
            self.joint_dimensions,
            self.angle_indicator,
            self.block_x,
            self.indicator_y,
            self.reinforcement_dimensions,
            self.index_gear_clearance_dimensions,
        )


class QuillCheaterBearingTop(bpd.PrintedPart):
    """Removable block top with sloped walls for the cheater pivot bearings.

    The exported object is rotated so its assembled +X face is on the print
    bed. ``get_assembled_object()`` returns the orientation used by the quill.
    """

    @classmethod
    def create(
        cls,
        quill_block: QuillMainBlock,
        pivot_x: float,
        pivot_z: float,
        wall_inner_y: float,
        wall_thickness_y: float,
        wall_outer_radius: float,
        bearing_pocket_dia: float,
        bearing_width: float,
        axle_hole_dia: float,
        positive_y_shelf_top_z: float,
        wheel_clearance_radius: float,
        positive_y_shelf_edge_bevel: float,
        max_print_angle: float,
        spring_center_x: float,
        spring_pocket_diameter: float,
        spring_pocket_depth: float,
    ) -> QuillCheaterBearingTop:
        return cls.get(
            quill_block=quill_block,
            pivot_x=pivot_x,
            pivot_z=pivot_z,
            wall_inner_y=wall_inner_y,
            wall_thickness_y=wall_thickness_y,
            wall_outer_radius=wall_outer_radius,
            bearing_pocket_dia=bearing_pocket_dia,
            bearing_width=bearing_width,
            axle_hole_dia=axle_hole_dia,
            positive_y_shelf_top_z=positive_y_shelf_top_z,
            wheel_clearance_radius=wheel_clearance_radius,
            positive_y_shelf_edge_bevel=positive_y_shelf_edge_bevel,
            max_print_angle=max_print_angle,
            spring_center_x=spring_center_x,
            spring_pocket_diameter=spring_pocket_diameter,
            spring_pocket_depth=spring_pocket_depth,
        )

    def __init__(
        self,
        quill_block: QuillMainBlock,
        pivot_x: float,
        pivot_z: float,
        wall_inner_y: float,
        wall_thickness_y: float,
        wall_outer_radius: float,
        bearing_pocket_dia: float,
        bearing_width: float,
        axle_hole_dia: float,
        positive_y_shelf_top_z: float,
        wheel_clearance_radius: float,
        positive_y_shelf_edge_bevel: float,
        max_print_angle: float,
        spring_center_x: float,
        spring_pocket_diameter: float,
        spring_pocket_depth: float,
    ) -> None:
        self.quill_block_dimensions = quill_block.dimensions()
        self.pivot_x = pivot_x
        self.pivot_z = pivot_z
        self.wall_inner_y = wall_inner_y
        self.wall_thickness_y = wall_thickness_y
        self.wall_outer_radius = wall_outer_radius
        self.bearing_pocket_dia = bearing_pocket_dia
        self.bearing_width = bearing_width
        self.axle_hole_dia = axle_hole_dia
        self.positive_y_shelf_top_z = positive_y_shelf_top_z
        self.wheel_clearance_radius = wheel_clearance_radius
        self.positive_y_shelf_edge_bevel = positive_y_shelf_edge_bevel
        self.max_print_angle = max_print_angle
        self.spring_center_x = spring_center_x
        self.spring_pocket_diameter = spring_pocket_diameter
        self.spring_pocket_depth = spring_pocket_depth
        super().__init__(name="Quill Cheater Bearing Top")

        assembled = quill_block.get_cheater_top_base_shape().cut(
            self._make_positive_y_shelf_cut(quill_block)
        )
        assembled = assembled.union(self._make_wall_rails(quill_block))
        wall = self._make_positive_y_wall(quill_block)
        assembled = assembled.union(wall).union(
            wall.mirror("XZ")
        )
        assembled = assembled.cut(self._make_wheel_clearance_cut(quill_block))
        assembled = self._fillet_wheel_shelf_edges(assembled, quill_block)
        assembled = assembled.cut(self._make_spring_pocket(quill_block))
        assembled = assembled.cut(self._make_bearing_pockets())
        assembled = assembled.cut(self._make_axle_hole())
        self._assembled_object = assembled

        # +X is the print-bed face: after this rotation the maximum assembled
        # X plane is at print Z=0 and the rest of the part rises in +Z.
        assembled_shape = assembled.val()
        if not isinstance(assembled_shape, cq.Shape):
            raise TypeError("Cheater bearing top must provide solid geometry")
        max_x = assembled_shape.BoundingBox().xmax
        printable = (
            assembled
            .rotate((0, 0, 0), (0, 1, 0), 90)
            .translate((0, 0, max_x))
        )
        self._object = printable
        self._assembly.add(printable, name="body", color=cq.Color("blue"))

    def _make_positive_y_shelf_cut(
        self,
        quill_block: QuillMainBlock,
    ) -> cq.Workplane:
        wall_outer_y = self.wall_inner_y + self.wall_thickness_y
        outboard_width = quill_block.width / 2 - wall_outer_y
        shelf_drop = quill_block.height - self.positive_y_shelf_top_z
        return (
            cq.Workplane("XY")
            .box(
                quill_block.length,
                outboard_width,
                shelf_drop,
                centered=(False, False, False),
            )
            .translate((0, wall_outer_y, self.positive_y_shelf_top_z))
        )

    def _make_wheel_clearance_cut(
        self,
        quill_block: QuillMainBlock,
    ) -> cq.Workplane:
        wall_outer_y = self.wall_inner_y + self.wall_thickness_y
        outboard_width = quill_block.width / 2 - wall_outer_y
        return (
            cq.Workplane("XZ")
            .center(self.pivot_x, self.pivot_z)
            .circle(self.wheel_clearance_radius)
            .extrude(-outboard_width)
            .translate((0, wall_outer_y, 0))
        )

    def _make_spring_pocket(
        self,
        quill_block: QuillMainBlock,
    ) -> cq.Workplane:
        return (
            cq.Workplane("XY")
            .center(self.spring_center_x, 0)
            .circle(self.spring_pocket_diameter / 2)
            .extrude(-self.spring_pocket_depth)
            .translate((0, 0, quill_block.height))
        )

    def _fillet_wheel_shelf_edges(
        self,
        assembled: cq.Workplane,
        quill_block: QuillMainBlock,
    ) -> cq.Workplane:
        """Fillet all five user-facing shelf/relief edges together."""
        vertical_offset = self.pivot_z - self.positive_y_shelf_top_z
        if vertical_offset >= self.wheel_clearance_radius:
            # The cylindrical cut does not reach the shelf plane.
            return assembled

        x_extent = math.sqrt(
            self.wheel_clearance_radius * self.wheel_clearance_radius
            - vertical_offset * vertical_offset
        )
        wall_outer_y = self.wall_inner_y + self.wall_thickness_y
        block_outer_y = quill_block.width / 2
        tolerance = 0.01
        relief_box = cq.selectors.BoxSelector(
            (
                self.pivot_x - x_extent - tolerance,
                wall_outer_y - tolerance,
                self.pivot_z - self.wheel_clearance_radius - tolerance,
            ),
            (
                self.pivot_x + x_extent + tolerance,
                block_outer_y + tolerance,
                self.positive_y_shelf_top_z + tolerance,
            ),
        )
        outer_shelf_box = cq.selectors.BoxSelector(
            (
                quill_block.holder_length_x - tolerance,
                block_outer_y - tolerance,
                self.positive_y_shelf_top_z - tolerance,
            ),
            (
                quill_block.length - quill_block.holder_length_x + tolerance,
                block_outer_y + tolerance,
                self.positive_y_shelf_top_z + tolerance,
            ),
        )
        combined_selector = cq.selectors.SumSelector(
            relief_box,
            outer_shelf_box,
        )
        boxed_edges = assembled.edges(combined_selector).vals()
        if not all(isinstance(edge, cq.Edge) for edge in boxed_edges):
            raise TypeError("Wheel-relief selector returned a non-edge shape")
        relief_edges = []
        for edge in boxed_edges:
            if not isinstance(edge, cq.Edge):
                continue
            bounds = edge.BoundingBox()
            is_x_side = (
                edge.geomType() == "LINE"
                and bounds.xlen < tolerance
                and bounds.zlen < tolerance
            )
            is_user_side_arc = (
                edge.geomType() in ("CIRCLE", "ELLIPSE")
                and abs(bounds.ymin - block_outer_y) < tolerance
                and abs(bounds.ymax - block_outer_y) < tolerance
            )
            is_outer_x_segment = (
                edge.geomType() == "LINE"
                and bounds.ylen < tolerance
                and bounds.zlen < tolerance
                and abs(bounds.ymin - block_outer_y) < tolerance
                and abs(bounds.zmin - self.positive_y_shelf_top_z) < tolerance
                and (
                    bounds.xmax <= self.pivot_x - x_extent + tolerance
                    or bounds.xmin >= self.pivot_x + x_extent - tolerance
                )
            )
            if is_x_side or is_user_side_arc or is_outer_x_segment:
                relief_edges.append(edge)
        if len(relief_edges) != 5:
            raise ValueError(
                "Expected the relief arc, two Y-side edges, and two "
                "outer X-aligned shelf edges, "
                f"found {len(relief_edges)}"
            )
        return assembled.newObject(relief_edges).fillet(
            self.positive_y_shelf_edge_bevel
        )

    def _wall_root_z(self, quill_block: QuillMainBlock) -> float:
        """Rail height required to keep both tangent slopes printable."""
        angle = math.radians(self.max_print_angle)
        tangent = math.tan(angle)
        secant = 1.0 / math.cos(angle)
        root_x_positions = (
            quill_block.holder_length_x,
            quill_block.length - quill_block.holder_length_x,
        )
        required_roots = tuple(
            self.pivot_z
            - tangent * abs(root_x - self.pivot_x)
            + self.wall_outer_radius * secant
            for root_x in root_x_positions
        )
        return max(quill_block.height, *required_roots)

    def _make_wall_rails(
        self,
        quill_block: QuillMainBlock,
    ) -> cq.Workplane:
        start_x = quill_block.holder_length_x
        end_x = quill_block.length - quill_block.holder_length_x
        root_z = self._wall_root_z(quill_block)
        rail_height = root_z - quill_block.height
        if rail_height <= 0:
            return cq.Workplane("XY")

        positive_rail = (
            cq.Workplane("XY")
            .box(
                end_x - start_x,
                self.wall_thickness_y,
                rail_height,
                centered=(False, False, False),
            )
            .translate((start_x, self.wall_inner_y, quill_block.height))
        )
        return positive_rail.union(positive_rail.mirror("XZ"))

    def _make_positive_y_wall(
        self,
        quill_block: QuillMainBlock,
    ) -> cq.Workplane:
        top_start_x = quill_block.holder_length_x
        top_end_x = quill_block.length - quill_block.holder_length_x
        root_z = self._wall_root_z(quill_block)
        left_tangent = self._upper_tangent_point(
            top_start_x,
            root_z,
        )
        right_tangent = self._upper_tangent_point(
            top_end_x,
            root_z,
        )
        # XZ's negative extrusion points toward +Y.
        wall = (
            cq.Workplane("XZ")
            .moveTo(top_start_x, root_z)
            .lineTo(*left_tangent)
            .threePointArc(
                (self.pivot_x, self.pivot_z + self.wall_outer_radius),
                right_tangent,
            )
            .lineTo(top_end_x, root_z)
            .close()
            .extrude(-self.wall_thickness_y)
            .translate((0, self.wall_inner_y, 0))
        )
        return wall

    def _upper_tangent_point(
        self,
        root_x: float,
        root_z: float,
    ) -> tuple[float, float]:
        """Upper external tangent from a wall root to the bearing boss."""
        dx = root_x - self.pivot_x
        dz = root_z - self.pivot_z
        distance_squared = dx * dx + dz * dz
        radius_squared = self.wall_outer_radius * self.wall_outer_radius
        if distance_squared <= radius_squared:
            raise ValueError("Wall root must lie outside the bearing boss")

        base_x = self.pivot_x + radius_squared * dx / distance_squared
        base_z = self.pivot_z + radius_squared * dz / distance_squared
        factor = (
            self.wall_outer_radius
            * math.sqrt(distance_squared - radius_squared)
            / distance_squared
        )
        perpendicular_x = -dz
        perpendicular_z = dx
        first = (
            base_x + factor * perpendicular_x,
            base_z + factor * perpendicular_z,
        )
        second = (
            base_x - factor * perpendicular_x,
            base_z - factor * perpendicular_z,
        )
        return first if first[1] > second[1] else second

    def _make_bearing_pockets(self) -> cq.Workplane:
        outside_y = self.wall_inner_y + self.wall_thickness_y
        positive = (
            cq.Workplane("XZ")
            .center(self.pivot_x, self.pivot_z)
            .circle(self.bearing_pocket_dia / 2)
            .extrude(self.bearing_width)
            .translate((0, outside_y, 0))
        )
        negative = positive.mirror("XZ")
        return positive.union(negative)

    def _make_axle_hole(self) -> cq.Workplane:
        outside_y = self.wall_inner_y + self.wall_thickness_y
        return (
            cq.Workplane("XZ")
            .center(self.pivot_x, self.pivot_z)
            .circle(self.axle_hole_dia / 2)
            .extrude(outside_y * 2)
            .translate((0, outside_y, 0))
        )

    def get_assembled_object(self) -> cq.Workplane:
        return self._assembled_object

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.quill_block_dimensions,
            self.pivot_x,
            self.pivot_z,
            self.wall_inner_y,
            self.wall_thickness_y,
            self.wall_outer_radius,
            self.bearing_pocket_dia,
            self.bearing_width,
            self.axle_hole_dia,
            self.positive_y_shelf_top_z,
            self.wheel_clearance_radius,
            self.positive_y_shelf_edge_bevel,
            self.max_print_angle,
            self.spring_center_x,
            self.spring_pocket_diameter,
            self.spring_pocket_depth,
        )


class QuillCheaterGearSection(bpd.PrintedPart):
    """Replaceable convex gear arc mounted to the rocker's -X face."""

    @classmethod
    def create(
        cls,
        negative_x: float,
        positive_x: float,
        tooth_contact_z: float,
        curve_radius: float,
        tooth_depth: float,
        backing_width_y: float,
        backing_bottom_z: float,
        backing_top_z: float,
        angular_pitch: float,
        tooth_count: int,
        screw_spacing_y: float,
        screw_z: float,
        screw_clearance_diameter: float,
        screw_head_diameter: float,
        screw_head_height: float,
        tooth_root_relief_tangential_width: float,
        tooth_root_relief_radial_depth: float,
        negative_x_extension: float,
        mating_index_gear_tooth_count: int,
        tooth_count_engraving_size: float,
        tooth_count_engraving_depth: float,
        tooth_count_engraving_z: float,
    ) -> QuillCheaterGearSection:
        return cls.get(
            negative_x=negative_x,
            positive_x=positive_x,
            tooth_contact_z=tooth_contact_z,
            curve_radius=curve_radius,
            tooth_depth=tooth_depth,
            backing_width_y=backing_width_y,
            backing_bottom_z=backing_bottom_z,
            backing_top_z=backing_top_z,
            angular_pitch=angular_pitch,
            tooth_count=tooth_count,
            screw_spacing_y=screw_spacing_y,
            screw_z=screw_z,
            screw_clearance_diameter=screw_clearance_diameter,
            screw_head_diameter=screw_head_diameter,
            screw_head_height=screw_head_height,
            tooth_root_relief_tangential_width=tooth_root_relief_tangential_width,
            tooth_root_relief_radial_depth=tooth_root_relief_radial_depth,
            negative_x_extension=negative_x_extension,
            mating_index_gear_tooth_count=mating_index_gear_tooth_count,
            tooth_count_engraving_size=tooth_count_engraving_size,
            tooth_count_engraving_depth=tooth_count_engraving_depth,
            tooth_count_engraving_z=tooth_count_engraving_z,
        )

    def __init__(
        self,
        negative_x: float,
        positive_x: float,
        tooth_contact_z: float,
        curve_radius: float,
        tooth_depth: float,
        backing_width_y: float,
        backing_bottom_z: float,
        backing_top_z: float,
        angular_pitch: float,
        tooth_count: int,
        screw_spacing_y: float,
        screw_z: float,
        screw_clearance_diameter: float,
        screw_head_diameter: float,
        screw_head_height: float,
        tooth_root_relief_tangential_width: float,
        tooth_root_relief_radial_depth: float,
        negative_x_extension: float,
        mating_index_gear_tooth_count: int,
        tooth_count_engraving_size: float,
        tooth_count_engraving_depth: float,
        tooth_count_engraving_z: float,
    ) -> None:
        self.negative_x = negative_x
        self.positive_x = positive_x
        self.tooth_contact_z = tooth_contact_z
        self.curve_radius = curve_radius
        self.tooth_depth = tooth_depth
        self.backing_width_y = backing_width_y
        self.backing_bottom_z = backing_bottom_z
        self.backing_top_z = backing_top_z
        self.angular_pitch = angular_pitch
        self.tooth_count = tooth_count
        self.screw_spacing_y = screw_spacing_y
        self.screw_z = screw_z
        self.screw_clearance_diameter = screw_clearance_diameter
        self.screw_head_diameter = screw_head_diameter
        self.screw_head_height = screw_head_height
        self.tooth_root_relief_tangential_width = tooth_root_relief_tangential_width
        self.tooth_root_relief_radial_depth = tooth_root_relief_radial_depth
        self.negative_x_extension = negative_x_extension
        self.mating_index_gear_tooth_count = mating_index_gear_tooth_count
        self.tooth_count_engraving_size = tooth_count_engraving_size
        self.tooth_count_engraving_depth = tooth_count_engraving_depth
        self.tooth_count_engraving_z = tooth_count_engraving_z
        super().__init__(name="Quill Cheater Gear Section")

        half_count = tooth_count // 2
        root_radius = curve_radius - tooth_depth
        curve_center_z = tooth_contact_z + curve_radius
        half_angle = (half_count + 0.5) * angular_pitch
        tooth_profile = gear_tooth_profile_polar_points(
            range(-half_count, half_count + 1),
            angular_pitch,
            root_radius,
            curve_radius,
            valley_angle_offset=-0.5,
        )
        profile = [
            (math.sin(angle) * radius, curve_center_z - math.cos(angle) * radius)
            for angle, radius in tooth_profile
        ]
        edge_y = math.sin(half_angle) * root_radius
        profile.extend(
            (
                (
                    edge_y,
                    curve_center_z - math.cos(half_angle) * root_radius,
                ),
                (edge_y, backing_top_z),
                (-edge_y, backing_top_z),
            )
        )
        # Extend the entire gear section toward -X, then restore the +Y half,
        # all material above the screw centres, and each screw-head clearance.
        extended_negative_x = negative_x - negative_x_extension

        toothed_section = (
            cq.Workplane("YZ")
            .polyline(profile)
            .close()
            .extrude(positive_x - extended_negative_x)
            .translate((extended_negative_x, 0.0, 0.0))
        )
        backing = (
            cq.Workplane("XY")
            .box(
                positive_x - extended_negative_x,
                backing_width_y,
                backing_top_z - backing_bottom_z,
                centered=(False, True, False),
            )
            .translate((extended_negative_x, 0.0, backing_bottom_z))
        )
        assembled = toothed_section.union(backing)
        positive_y_extension_cut = (
            cq.Workplane("XY")
            .box(
                negative_x_extension + 0.1,
                backing_width_y / 2 + 0.1,
                backing_top_z - backing_bottom_z + curve_radius * 2,
                centered=(False, False, False),
            )
            .translate(
                (
                    extended_negative_x - 0.1,
                    -0.1,
                    backing_bottom_z - curve_radius,
                )
            )
        )
        assembled = assembled.cut(positive_y_extension_cut)
        above_screw_extension_cut = (
            cq.Workplane("XY")
            .box(
                negative_x_extension + 0.1,
                backing_width_y + 0.2,
                backing_top_z - screw_z + curve_radius * 2,
                centered=(False, True, False),
            )
            .translate(
                (
                    extended_negative_x - 0.1,
                    0.0,
                    screw_z,
                )
            )
        )
        assembled = assembled.cut(above_screw_extension_cut)
        screw_head_extension_clearance = cq.Workplane("YZ")
        for y in (-screw_spacing_y / 2, screw_spacing_y / 2):
            screw_head_extension_clearance = screw_head_extension_clearance.union(
                cq.Workplane("YZ")
                .center(y, screw_z)
                .circle(screw_head_diameter / 2 + 1.0)
                .extrude(negative_x_extension + 0.1)
                .translate((extended_negative_x - 0.1, 0.0, 0.0))
            )
        assembled = assembled.cut(screw_head_extension_clearance)
        root_relief = cq.Workplane("YZ")
        for valley_angle, _radius in tooth_profile[::2]:
            tangent_y = math.cos(valley_angle)
            tangent_z = math.sin(valley_angle)
            root_y = math.sin(valley_angle) * root_radius
            root_z = curve_center_z - math.cos(valley_angle) * root_radius
            inward_y = -math.sin(valley_angle)
            inward_z = math.cos(valley_angle)
            outward_y = math.sin(valley_angle)
            outward_z = -math.cos(valley_angle)
            half_width = tooth_root_relief_tangential_width / 2
            depth = tooth_root_relief_radial_depth
            slot = cq.Workplane("YZ").polyline(
                [
                    (root_y - tangent_y * half_width + outward_y * depth, root_z - tangent_z * half_width + outward_z * depth),
                    (root_y + tangent_y * half_width + outward_y * depth, root_z + tangent_z * half_width + outward_z * depth),
                    (root_y + tangent_y * half_width + inward_y * depth, root_z + tangent_z * half_width + inward_z * depth),
                    (root_y - tangent_y * half_width + inward_y * depth, root_z - tangent_z * half_width + inward_z * depth),
                ]
            ).close().extrude(positive_x - extended_negative_x + 0.2).translate(
                (extended_negative_x - 0.1, 0.0, 0.0)
            )
            root_relief = root_relief.union(slot)
        assembled = assembled.cut(root_relief)
        clearance = cq.Workplane("YZ")
        for y in (-screw_spacing_y / 2, screw_spacing_y / 2):
            shaft = (
                cq.Workplane("YZ")
                .center(y, screw_z)
                .circle(screw_clearance_diameter / 2)
                .extrude(positive_x - negative_x + 0.2)
                .translate((negative_x - 0.1, 0.0, 0.0))
            )
            countersink = (
                cq.Workplane("YZ")
                .center(y, screw_z)
                .circle(screw_head_diameter / 2)
                .workplane(offset=screw_head_height)
                .circle(screw_clearance_diameter / 2)
                .loft()
                .translate((negative_x, 0.0, 0.0))
            )
            clearance = clearance.union(shaft).union(countersink)
        assembled = assembled.cut(clearance)
        engraving = (
            cq.Workplane("YZ")
            .center(0.0, tooth_count_engraving_z)
            .text(
                str(mating_index_gear_tooth_count),
                tooth_count_engraving_size,
                tooth_count_engraving_depth,
            )
            .mirror("XZ")
            .translate((negative_x, 0.0, 0.0))
        )
        assembled = assembled.cut(engraving)
        self._assembled_object = assembled

        printable = assembled.rotate((0, 0, 0), (0, 1, 0), 90)
        printable_shape = printable.val()
        if not isinstance(printable_shape, cq.Shape):
            raise TypeError("Cheater gear section must provide solid geometry")
        printable = printable.translate((0.0, 0.0, -printable_shape.BoundingBox().zmin))
        self._object = printable
        self._assembly.add(printable, name="body", color=cq.Color("red"))

    def get_assembled_object(self) -> cq.Workplane:
        return self._assembled_object

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.negative_x,
            self.positive_x,
            self.tooth_contact_z,
            self.curve_radius,
            self.tooth_depth,
            self.backing_width_y,
            self.backing_bottom_z,
            self.backing_top_z,
            self.angular_pitch,
            self.tooth_count,
            self.screw_spacing_y,
            self.screw_z,
            self.screw_clearance_diameter,
            self.screw_head_diameter,
            self.screw_head_height,
            self.tooth_root_relief_tangential_width,
            self.tooth_root_relief_radial_depth,
            self.negative_x_extension,
            self.mating_index_gear_tooth_count,
            self.tooth_count_engraving_size,
            self.tooth_count_engraving_depth,
            self.tooth_count_engraving_z,
        )


class QuillCheaterRocker(bpd.PrintedPart):
    """Raised cheater rocker, exported with assembled +Y on the print bed."""

    @classmethod
    def create(
        cls,
        negative_x: float,
        positive_x: float,
        pivot_x: float,
        pivot_z: float,
        width_y: float,
        arm_thickness_z: float,
        pivot_outer_diameter: float,
        pivot_pilot_diameter: float,
        gear_mount_bottom_z: float,
        gear_mount_positive_x: float,
        gear_screw_z: float,
        gear_screw_spacing_y: float,
        gear_screw_pilot_diameter: float,
        spring_center_x: float,
        spring_pocket_diameter: float,
        spring_pocket_depth: float,
    ) -> QuillCheaterRocker:
        return cls.get(
            negative_x=negative_x,
            positive_x=positive_x,
            pivot_x=pivot_x,
            pivot_z=pivot_z,
            width_y=width_y,
            arm_thickness_z=arm_thickness_z,
            pivot_outer_diameter=pivot_outer_diameter,
            pivot_pilot_diameter=pivot_pilot_diameter,
            gear_mount_bottom_z=gear_mount_bottom_z,
            gear_mount_positive_x=gear_mount_positive_x,
            gear_screw_z=gear_screw_z,
            gear_screw_spacing_y=gear_screw_spacing_y,
            gear_screw_pilot_diameter=gear_screw_pilot_diameter,
            spring_center_x=spring_center_x,
            spring_pocket_diameter=spring_pocket_diameter,
            spring_pocket_depth=spring_pocket_depth,
        )

    def __init__(
        self,
        negative_x: float,
        positive_x: float,
        pivot_x: float,
        pivot_z: float,
        width_y: float,
        arm_thickness_z: float,
        pivot_outer_diameter: float,
        pivot_pilot_diameter: float,
        gear_mount_bottom_z: float,
        gear_mount_positive_x: float,
        gear_screw_z: float,
        gear_screw_spacing_y: float,
        gear_screw_pilot_diameter: float,
        spring_center_x: float,
        spring_pocket_diameter: float,
        spring_pocket_depth: float,
    ) -> None:
        self.negative_x = negative_x
        self.positive_x = positive_x
        self.pivot_x = pivot_x
        self.pivot_z = pivot_z
        self.width_y = width_y
        self.arm_thickness_z = arm_thickness_z
        self.pivot_outer_diameter = pivot_outer_diameter
        self.pivot_pilot_diameter = pivot_pilot_diameter
        self.gear_mount_bottom_z = gear_mount_bottom_z
        self.gear_mount_positive_x = gear_mount_positive_x
        self.gear_screw_z = gear_screw_z
        self.gear_screw_spacing_y = gear_screw_spacing_y
        self.gear_screw_pilot_diameter = gear_screw_pilot_diameter
        self.spring_center_x = spring_center_x
        self.spring_pocket_diameter = spring_pocket_diameter
        self.spring_pocket_depth = spring_pocket_depth
        super().__init__(name="Quill Cheater Rocker")

        length_x = positive_x - negative_x
        arm = (
            cq.Workplane("XY")
            .box(length_x, width_y, arm_thickness_z, centered=False)
            .translate((negative_x, -width_y / 2, pivot_z))
        )
        gear_mount = (
            cq.Workplane("XY")
            .box(
                gear_mount_positive_x - negative_x,
                width_y,
                pivot_z + arm_thickness_z - gear_mount_bottom_z,
                centered=(False, True, False),
            )
            .translate((negative_x, 0.0, gear_mount_bottom_z))
        )
        pivot_barrel = (
            cq.Workplane("XZ")
            .center(pivot_x, pivot_z)
            .circle(pivot_outer_diameter / 2)
            .extrude(-width_y)
            .translate((0, -width_y / 2, 0))
        )
        pivot_pilot = (
            cq.Workplane("XZ")
            .center(pivot_x, pivot_z)
            .circle(pivot_pilot_diameter / 2)
            .extrude(-width_y)
            .translate((0, -width_y / 2, 0))
        )
        spring_pocket = (
            cq.Workplane("XY")
            .center(spring_center_x, 0)
            .circle(spring_pocket_diameter / 2)
            .extrude(spring_pocket_depth)
            .translate((0, 0, pivot_z))
        )
        gear_pilots = cq.Workplane("YZ")
        gear_pilot_depth = gear_mount_positive_x - negative_x
        for y in (-gear_screw_spacing_y / 2, gear_screw_spacing_y / 2):
            gear_pilots = gear_pilots.union(
                cq.Workplane("YZ")
                .center(y, gear_screw_z)
                .circle(gear_screw_pilot_diameter / 2)
                .extrude(gear_pilot_depth)
                .translate((negative_x, 0.0, 0.0))
            )
        assembled = (
            arm.union(gear_mount)
            .union(pivot_barrel)
            .cut(pivot_pilot)
            .cut(spring_pocket)
            .cut(gear_pilots)
        )
        self._assembled_object = assembled

        printable = assembled.rotate((0, 0, 0), (1, 0, 0), -90)
        printable_shape = printable.val()
        if not isinstance(printable_shape, cq.Shape):
            raise TypeError("Cheater rocker must provide solid geometry")
        printable = printable.translate(
            (0, 0, -printable_shape.BoundingBox().zmin)
        )
        self._object = printable
        self._assembly.add(printable, name="body", color=cq.Color("yellow"))

    def get_assembled_object(self) -> cq.Workplane:
        return self._assembled_object

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.negative_x,
            self.positive_x,
            self.pivot_x,
            self.pivot_z,
            self.width_y,
            self.arm_thickness_z,
            self.pivot_outer_diameter,
            self.pivot_pilot_diameter,
            self.gear_mount_bottom_z,
            self.gear_mount_positive_x,
            self.gear_screw_z,
            self.gear_screw_spacing_y,
            self.gear_screw_pilot_diameter,
            self.spring_center_x,
            self.spring_pocket_diameter,
            self.spring_pocket_depth,
        )


class QuillCheaterAdjustmentWheel(bpd.PrintedPart):
    """Hand wheel that captures the M4 pivot bolt's hex head.

    The wheel is exported flat with its axis along Z. In the assembly it is
    rotated so that axis follows the pivot bolt along Y.
    """

    @classmethod
    def create(
        cls,
        outside_diameter: float,
        width: float,
        hex_across_flats: float,
        hex_depth: float,
        shaft_hole_diameter: float,
        grip_notch_radius: float,
        grip_notch_count: int,
    ) -> QuillCheaterAdjustmentWheel:
        return cls.get(
            outside_diameter=outside_diameter,
            width=width,
            hex_across_flats=hex_across_flats,
            hex_depth=hex_depth,
            shaft_hole_diameter=shaft_hole_diameter,
            grip_notch_radius=grip_notch_radius,
            grip_notch_count=grip_notch_count,
        )

    def __init__(
        self,
        outside_diameter: float,
        width: float,
        hex_across_flats: float,
        hex_depth: float,
        shaft_hole_diameter: float,
        grip_notch_radius: float,
        grip_notch_count: int,
    ) -> None:
        self.outside_diameter = outside_diameter
        self.width = width
        self.hex_across_flats = hex_across_flats
        self.hex_depth = hex_depth
        self.shaft_hole_diameter = shaft_hole_diameter
        self.grip_notch_radius = grip_notch_radius
        self.grip_notch_count = grip_notch_count
        super().__init__(name="Quill Cheater Adjustment Wheel")

        obj = cq.Workplane("XY").circle(outside_diameter / 2).extrude(width)
        notch_radius_from_center = outside_diameter / 2
        for index in range(grip_notch_count):
            angle = math.radians(index * 360 / grip_notch_count)
            notch = (
                cq.Workplane("XY")
                .center(
                    math.cos(angle) * notch_radius_from_center,
                    math.sin(angle) * notch_radius_from_center,
                )
                .circle(grip_notch_radius)
                .extrude(width)
            )
            obj = obj.cut(notch)

        hex_pocket = (
            cq.Workplane("XY")
            .workplane(offset=width - hex_depth)
            .polygon(6, hex_across_flats, circumscribed=True)
            .extrude(hex_depth)
        )
        shaft_hole = (
            cq.Workplane("XY")
            .circle(shaft_hole_diameter / 2)
            .extrude(width)
        )
        obj = obj.cut(hex_pocket.union(shaft_hole))
        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("red"))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.outside_diameter,
            self.width,
            self.hex_across_flats,
            self.hex_depth,
            self.shaft_hole_diameter,
            self.grip_notch_radius,
            self.grip_notch_count,
        )


class QuillBearingHolder(bpd.PrintedPart):
    """Removable bearing clamp derived from the quill block's own shape."""

    @classmethod
    def create(
        cls,
        quill_block: QuillMainBlock,
        holder_length_x: float,
        holder_split_gap: float,
        screw_spacing_y: float,
    ) -> QuillBearingHolder:
        return cls.get(
            quill_block=quill_block,
            holder_length_x=holder_length_x,
            holder_split_gap=holder_split_gap,
            screw_spacing_y=screw_spacing_y,
        )

    def __init__(
        self,
        quill_block: QuillMainBlock,
        holder_length_x: float,
        holder_split_gap: float,
        screw_spacing_y: float,
    ) -> None:
        self.quill_block_dimensions = quill_block.dimensions()
        self.holder_length_x = holder_length_x
        self.holder_split_gap = holder_split_gap
        self.screw_spacing_y = screw_spacing_y
        super().__init__(name="Quill Bearing Holder")

        obj = quill_block.get_bearing_holder_shape()
        self._assembled_object = obj
        printable = obj.rotate((0, 0, 0), (1, 0, 0), 180)
        printable_shape = printable.val()
        if not isinstance(printable_shape, cq.Shape):
            raise TypeError("Quill bearing holder must provide solid geometry")
        printable = printable.translate(
            (0.0, 0.0, -printable_shape.BoundingBox().zmin)
        )
        self._object = printable
        self._assembly.add(printable, name="body", color=cq.Color("green"))

    def get_assembled_object(self) -> cq.Workplane:
        return self._assembled_object

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.quill_block_dimensions,
            self.holder_length_x,
            self.holder_split_gap,
            self.screw_spacing_y,
        )


class IndexGearStandardMk1(bpd.PrintedPart):
    """Printed part: 96-tooth index gear. Clamps onto the ER11 shank with
    a captive M3 set-screw. V-notches around perimeter for a detent pin.
    Printed flat — numbers on bottom, teeth on top. Displayed edge-on."""

    @classmethod
    def create(
        cls,
        od: float,
        bore_dia: float,
        teeth_width: float,
        tooth_depth: float,
        numbers_width: float,
        spacer_width: float,
        spacer_od: float,
        num_teeth: int,
        tick_interval_teeth: int,
        number_interval_teeth: int,
        clamp_screw_hole_dia: float,
        clamp_nut_width_across_flats: float,
        clamp_nut_depth: float,
        clamp_nut_inner_radius: float,
        clamp_angle: float,
        tooth_root_relief_tangential_width: float,
        tooth_root_relief_radial_depth: float,
    ) -> IndexGearStandardMk1:
        return cls.get(
            od=od,
            bore_dia=bore_dia,
            teeth_width=teeth_width,
            tooth_depth=tooth_depth,
            numbers_width=numbers_width,
            spacer_width=spacer_width,
            spacer_od=spacer_od,
            num_teeth=num_teeth,
            tick_interval_teeth=tick_interval_teeth,
            number_interval_teeth=number_interval_teeth,
            clamp_screw_hole_dia=clamp_screw_hole_dia,
            clamp_nut_width_across_flats=clamp_nut_width_across_flats,
            clamp_nut_depth=clamp_nut_depth,
            clamp_nut_inner_radius=clamp_nut_inner_radius,
            clamp_angle=clamp_angle,
            tooth_root_relief_tangential_width=tooth_root_relief_tangential_width,
            tooth_root_relief_radial_depth=tooth_root_relief_radial_depth,
        )

    def __init__(
        self,
        od: float,
        bore_dia: float,
        teeth_width: float,
        tooth_depth: float,
        numbers_width: float,
        spacer_width: float,
        spacer_od: float,
        num_teeth: int,
        tick_interval_teeth: int,
        number_interval_teeth: int,
        clamp_screw_hole_dia: float,
        clamp_nut_width_across_flats: float,
        clamp_nut_depth: float,
        clamp_nut_inner_radius: float,
        clamp_angle: float,
        tooth_root_relief_tangential_width: float,
        tooth_root_relief_radial_depth: float,
    ) -> None:
        self.od = od
        self.bore_dia = bore_dia
        self.teeth_width = teeth_width
        self.tooth_depth = tooth_depth
        self.numbers_width = numbers_width
        self.spacer_width = spacer_width
        self.spacer_od = spacer_od
        self.num_teeth = num_teeth
        self.tick_interval_teeth = tick_interval_teeth
        self.number_interval_teeth = number_interval_teeth
        self.clamp_screw_hole_dia = clamp_screw_hole_dia
        self.clamp_nut_width_across_flats = clamp_nut_width_across_flats
        self.clamp_nut_depth = clamp_nut_depth
        self.clamp_nut_inner_radius = clamp_nut_inner_radius
        self.clamp_angle = clamp_angle
        self.tooth_root_relief_tangential_width = tooth_root_relief_tangential_width
        self.tooth_root_relief_radial_depth = tooth_root_relief_radial_depth
        super().__init__(name="Index Gear")
        # Build geometry once
        obj = cq.Workplane("XY").cylinder(
            self.teeth_width + self.numbers_width,
            self.od / 2,
            centered=(True, True, False),
        )
        obj = obj.faces(">Z").workplane().hole(self.bore_dia)
        obj = self._add_tick_marks(obj)
        obj = self._add_nut_pocket(obj)
        obj = self._add_teeth(obj)
        # After the gear is rotated into the assembly, local +Z becomes +X.
        # This ring fills the old washer gap and bears against the inner
        # race of the adjacent 6001ZZ bearing.
        spacer_ring = (
            cq.Workplane("XY")
            .circle(self.spacer_od / 2)
            .circle(self.bore_dia / 2)
            .extrude(self.spacer_width)
            .translate((0, 0, self.teeth_width + self.numbers_width))
        )
        obj = obj.union(spacer_ring)
        # Teeth are added as a solid polygon and therefore refill the bore.
        # Cut the bore last, after every union, so the exported STL retains a
        # continuous opening through the teeth, numbered body, and spacer.
        obj = obj.faces(">Z").workplane().hole(self.bore_dia)
        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("blue"))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.od,
            self.bore_dia,
            self.teeth_width,
            self.tooth_depth,
            self.numbers_width,
            self.spacer_width,
            self.spacer_od,
            self.num_teeth,
            self.tick_interval_teeth,
            self.number_interval_teeth,
            self.clamp_screw_hole_dia,
            self.clamp_nut_width_across_flats,
            self.clamp_nut_depth,
            self.clamp_nut_inner_radius,
            self.clamp_angle,
            self.tooth_root_relief_tangential_width,
            self.tooth_root_relief_radial_depth,
        )

    def _add_teeth(self, gear: cq.Workplane) -> cq.Workplane:
        angular_pitch = 2 * math.pi / self.num_teeth
        tooth_profile = gear_tooth_profile_polar_points(
            range(self.num_teeth),
            angular_pitch,
            self.od / 2,
            self.od / 2 + self.tooth_depth,
            valley_angle_offset=0.0,
        )
        verts = [
            (math.sin(angle) * radius, math.cos(angle) * radius)
            for angle, radius in tooth_profile
        ]
        teeth = cq.Workplane("XY").polyline(verts).close().extrude(self.teeth_width)
        gear = gear.union(teeth.translate((0, 0, self.numbers_width)))

        root_relief = cq.Workplane("XY")
        for valley_angle, root_radius in tooth_profile[::2]:
            tangent_x = math.cos(valley_angle)
            tangent_y = -math.sin(valley_angle)
            radial_x = math.sin(valley_angle)
            radial_y = math.cos(valley_angle)
            half_width = self.tooth_root_relief_tangential_width / 2
            depth = self.tooth_root_relief_radial_depth
            root_x = radial_x * root_radius
            root_y = radial_y * root_radius
            slot = cq.Workplane("XY").polyline(
                [
                    (root_x - tangent_x * half_width + radial_x * depth, root_y - tangent_y * half_width + radial_y * depth),
                    (root_x + tangent_x * half_width + radial_x * depth, root_y + tangent_y * half_width + radial_y * depth),
                    (root_x + tangent_x * half_width - radial_x * depth, root_y + tangent_y * half_width - radial_y * depth),
                    (root_x - tangent_x * half_width - radial_x * depth, root_y - tangent_y * half_width - radial_y * depth),
                ]
            ).close().extrude(self.teeth_width).translate((0.0, 0.0, self.numbers_width))
            root_relief = root_relief.union(slot)
        return gear.cut(root_relief)

    def _add_nut_pocket(self, gear: cq.Workplane) -> cq.Workplane:
        """Captive-nut pocket, face-loading channel, and radial screw path."""
        numbers_mid_z = self.numbers_width / 2

        pocket = (
            cq.Workplane("YZ")
            .polygon(
                6,
                self.clamp_nut_width_across_flats,
                circumscribed=True,
            )
            .extrude(self.clamp_nut_depth)
            .translate((self.clamp_nut_inner_radius, 0, numbers_mid_z))
        )

        loading_channel = (
            cq.Workplane("YZ")
            .box(
                self.clamp_nut_width_across_flats,
                numbers_mid_z * 2,
                self.clamp_nut_depth,
                centered=(True, True, False),
            )
            .translate((self.clamp_nut_inner_radius, 0, 0))
        )

        radial_screw_path = (
            cq.Workplane("YZ")
            .circle(self.clamp_screw_hole_dia / 2)
            .extrude(self.od)
            .translate((0, 0, numbers_mid_z))
        )
        cutout = pocket.union(loading_channel).union(radial_screw_path).rotate(
            (0, 0, 0),
            (0, 0, 1),
            -self.clamp_angle,
        )
        return gear.cut(cutout)

    def _add_tick_marks(self, gear: cq.Workplane) -> cq.Workplane:
        """Engraved tick marks on the bottom face."""
        angle_per_tooth = 360.0 / self.num_teeth
        radius = self.od / 2
        mark_depth = 0.4

        for i in range(0, self.num_teeth, self.tick_interval_teeth):
            angle = angle_per_tooth * i
            is_major = i % self.number_interval_teeth == 0
            line_len = 4.0 if is_major else 2.5

            mark = (
                cq.Workplane("XY")
                .box(mark_depth * 2, 0.6, line_len, centered=(True, True, False))
                .translate((radius - mark_depth, 0, 0))
                .rotate((0, 0, 0), (0, 0, 1), angle)
            )
            gear = gear.cut(mark)

            if is_major:
                num_mark = (
                    cq.Workplane("XY")
                    .add(offset(text(f"{((i - 1) % self.num_teeth) + 1}", 5), 2))
                    .rotate((0, 0, 0), (0, 1, 0), 90)
                    .translate((radius - mark_depth, 0, self.numbers_width * 2 / 3))
                    .rotate((0, 0, 0), (0, 0, 1), -angle)
                )
                gear = gear.cut(num_mark)

        return gear
