from __future__ import annotations

import cadquery as cq

import bom_part_data as bpd
from quill.quill_joint_abstract import QuillJointBase


class QuillJointAli(QuillJointBase):
    """AliExpress-holder-compatible hinge for the replacement quill.

    The measured ``shoulder_gap`` is the distance between the two outer
    shoulder faces.  The unequal nubs start at those faces and run along the
    pitch axis (+/-Y).  The base plate is printed flat and supports both the
    hinge and the quill main block.
    """

    @classmethod
    def create(
        cls,
        shoulder_dia: float,
        shoulder_gap: float,
        shoulder_thickness: float,
        user_nub_dia: float,
        user_nub_length: float,
        away_nub_dia: float,
        away_nub_length: float,
        hinge_height: float,
        angle_indicator_height: float,
        angle_indicator_thickness: float,
        body_negative_x: float,
        body_positive_x: float,
        body_top_z: float,
        magnet_pocket_dia: float,
        magnet_pocket_depth: float,
        base_plate_thickness: float,
        base_plate_x: float,
        base_plate_center_x: float,
        base_plate_y: float,
    ) -> QuillJointAli:
        return cls(
            shoulder_dia=shoulder_dia,
            shoulder_gap=shoulder_gap,
            shoulder_thickness=shoulder_thickness,
            user_nub_dia=user_nub_dia,
            user_nub_length=user_nub_length,
            away_nub_dia=away_nub_dia,
            away_nub_length=away_nub_length,
            hinge_height=hinge_height,
            angle_indicator_height=angle_indicator_height,
            angle_indicator_thickness=angle_indicator_thickness,
            body_negative_x=body_negative_x,
            body_positive_x=body_positive_x,
            body_top_z=body_top_z,
            magnet_pocket_dia=magnet_pocket_dia,
            magnet_pocket_depth=magnet_pocket_depth,
            base_plate_thickness=base_plate_thickness,
            base_plate_x=base_plate_x,
            base_plate_center_x=base_plate_center_x,
            base_plate_y=base_plate_y,
        )

    def __init__(
        self,
        shoulder_dia: float,
        shoulder_gap: float,
        shoulder_thickness: float,
        user_nub_dia: float,
        user_nub_length: float,
        away_nub_dia: float,
        away_nub_length: float,
        hinge_height: float,
        angle_indicator_height: float,
        angle_indicator_thickness: float,
        body_negative_x: float,
        body_positive_x: float,
        body_top_z: float,
        magnet_pocket_dia: float,
        magnet_pocket_depth: float,
        base_plate_thickness: float,
        base_plate_x: float,
        base_plate_center_x: float,
        base_plate_y: float,
    ) -> None:
        self.shoulder_dia = shoulder_dia
        self.shoulder_gap = shoulder_gap
        self.shoulder_thickness = shoulder_thickness
        self.user_nub_dia = user_nub_dia
        self.user_nub_length = user_nub_length
        self.away_nub_dia = away_nub_dia
        self.away_nub_length = away_nub_length
        self.hinge_height = hinge_height
        self.angle_indicator_height = angle_indicator_height
        self.angle_indicator_thickness = angle_indicator_thickness
        self.body_negative_x = body_negative_x
        self.body_positive_x = body_positive_x
        self.body_top_z = body_top_z
        self.magnet_pocket_dia = magnet_pocket_dia
        self.magnet_pocket_depth = magnet_pocket_depth
        self.base_plate_thickness = base_plate_thickness
        self.base_plate_x = base_plate_x
        self.base_plate_center_x = base_plate_center_x
        self.base_plate_y = base_plate_y
        raw_obj = (
            self._make_base_plate()
            .union(self._make_support_block())
            .union(self._make_hinge_barrel())
            .union(self._make_shoulder(+1))
            .union(self._make_shoulder(-1))
            .union(self._make_user_nub())
            .union(self._make_away_nub())
        )
        self._raw_object = raw_obj
        obj = raw_obj.cut(self._make_indicator_screw_pilots())
        obj = obj.cut(self._make_magnet_pocket())
        self._object = obj

    def get_object(self) -> cq.Workplane:
        return self._object

    def get_raw_object(self) -> cq.Workplane:
        """Uncut structure for fusing into the complete quill body."""
        return self._raw_object

    def get_cutouts(self) -> cq.Workplane:
        """Joint-local cuts to apply after all structural unions."""
        return self._raw_object.cut(self._object)

    def dimensions(self) -> tuple[object, ...]:
        return (
            self.shoulder_dia,
            self.shoulder_gap,
            self.shoulder_thickness,
            self.user_nub_dia,
            self.user_nub_length,
            self.away_nub_dia,
            self.away_nub_length,
            self.hinge_height,
            self.angle_indicator_height,
            self.angle_indicator_thickness,
            self.body_negative_x,
            self.body_positive_x,
            self.body_top_z,
            self.magnet_pocket_dia,
            self.magnet_pocket_depth,
            self.base_plate_thickness,
            self.base_plate_x,
            self.base_plate_center_x,
            self.base_plate_y,
        )

    def _hinge_z(self) -> float:
        return self.base_plate_thickness + self.hinge_height

    def _shoulder_center_y(self, side: int) -> float:
        return side * (self.shoulder_gap - self.shoulder_thickness) / 2

    def _make_base_plate(self) -> cq.Workplane:
        return (
            cq.Workplane("XY")
            .box(
                self.base_plate_x,
                self.base_plate_y,
                self.base_plate_thickness,
                centered=(True, True, False),
            )
            .translate((self.base_plate_center_x, 0, 0))
        )

    def _make_support_block(self) -> cq.Workplane:
        """Large printable hinge body supporting the indicator screws."""
        return (
            cq.Workplane("XY")
            .box(
                self.body_positive_x - self.body_negative_x,
                self.shoulder_gap,
                self.body_top_z - self.base_plate_thickness,
                centered=(False, True, False),
            )
            .translate(
                (self.body_negative_x, 0, self.base_plate_thickness)
            )
        )

    def _make_shoulder(self, side: int) -> cq.Workplane:
        return (
            cq.Workplane("XZ")
            .cylinder(
                self.shoulder_thickness,
                self.shoulder_dia / 2,
                centered=(True, True, True),
            )
            .translate((0, self._shoulder_center_y(side), self._hinge_z()))
        )

    def _make_hinge_barrel(self) -> cq.Workplane:
        """Solid core between the two outer shoulder faces."""
        return (
            cq.Workplane("XZ")
            .circle(self.shoulder_dia / 2)
            .extrude(self.shoulder_gap)
            .translate((0, self.shoulder_gap / 2, self._hinge_z()))
        )


    def _make_user_nub(self) -> cq.Workplane:
        # XZ's positive normal points toward -Y, so a negative extrusion
        # sends this +Y/user-side nub outward from the shoulder face.
        return (
            cq.Workplane("XZ")
            .circle(self.user_nub_dia / 2)
            .extrude(-self.user_nub_length)
            .translate((0, self.shoulder_gap / 2, self._hinge_z()))
        )

    def _make_away_nub(self) -> cq.Workplane:
        # Positive XZ extrusion points toward -Y, outward on the away side.
        return (
            cq.Workplane("XZ")
            .circle(self.away_nub_dia / 2)
            .extrude(self.away_nub_length)
            .translate((0, -self.shoulder_gap / 2, self._hinge_z()))
        )

    def _indicator_mount_centers(self) -> tuple[tuple[float, float], ...]:
        hinge_z = self._hinge_z()
        return ((-6.0, hinge_z - 6.0), (-6.0, hinge_z + 6.0))


    def _make_indicator_screw_pilots(self) -> cq.Workplane:
        """Blind 2.2 mm pilot holes for nominal 3 mm wood screws."""
        away_inner_y = -self.shoulder_gap / 2 + self.shoulder_thickness
        pilots = cq.Workplane("XZ")
        for x, z in self._indicator_mount_centers():
            pilots = pilots.union(
                cq.Workplane("XZ")
                .center(x, z)
                .circle(2.2 / 2)
                .extrude(-8.0)
                .translate((0, away_inner_y, 0))
            )
        return pilots

    def _make_magnet_pocket(self) -> cq.Workplane:
        """Radial magnet pocket opening upward (+Z) near the user nub end."""
        pocket_y = (
            self.shoulder_gap / 2
            + self.user_nub_length
            - self.magnet_pocket_dia / 2
            - 0.4
        )
        nub_top_z = self._hinge_z() + self.user_nub_dia / 2
        return (
            cq.Workplane("XY")
            .circle(self.magnet_pocket_dia / 2)
            .extrude(-self.magnet_pocket_depth)
            .translate((0, pocket_y, nub_top_z))
        )


class QuillAngleIndicator(bpd.PrintedPart):
    """Replaceable angle-stop arm, printed flat on its broad XZ face."""

    @classmethod
    def create(
        cls,
        shoulder_dia: float,
        away_nub_dia: float,
        hinge_z: float,
        height: float,
        width_x: float,
        thickness: float,
        corner_radius: float,
    ) -> QuillAngleIndicator:
        return cls.get(
            shoulder_dia=shoulder_dia,
            away_nub_dia=away_nub_dia,
            hinge_z=hinge_z,
            height=height,
            width_x=width_x,
            thickness=thickness,
            corner_radius=corner_radius,
        )

    def __init__(
        self,
        shoulder_dia: float,
        away_nub_dia: float,
        hinge_z: float,
        height: float,
        width_x: float,
        thickness: float,
        corner_radius: float,
    ) -> None:
        self.shoulder_dia = shoulder_dia
        self.away_nub_dia = away_nub_dia
        self.hinge_z = hinge_z
        self.height = height
        self.width_x = width_x
        self.thickness = thickness
        self.corner_radius = corner_radius
        super().__init__(name="Quill Angle Indicator")

        obj = self.make(cutout=False)

        self._object = obj
        self._assembly.add(obj, name="body", color=cq.Color("blue"))
    
    def make(self, cutout: bool = False) -> cq.Workplane:
        mount_centers = self._mount_centers()
        # Thick flat-printable cuboid. Its X=0 edge is the stop surface and
        # lies directly above the -Y nub's X centreline.
        gap = 0.0 if cutout else 0.2
        obj = (
            cq.Workplane("XY")
            .box(
                self.width_x,
                self.height + 10.0 - gap,
                self.thickness,
                centered=(False, False, False),
            )
            .translate((-self.width_x, self.hinge_z - 10.0 + gap, 0))
        )
        nub_cutout = (
            cq.Workplane("XY")
            .cylinder(self.thickness + 2.0, self.away_nub_dia / 2 + gap, centered=(True, True, False))
            .translate((0, self.hinge_z, -1.0))
        )
        obj = obj.cut(nub_cutout)

        # In print coordinates this is the +Y/-X vertical edge. After the
        # assembly's X-axis rotation it becomes the requested +Z/-X edge.
        top_y = self.hinge_z + self.height
        rounded_edge = obj.edges("|Z").filter(
            lambda edge: (
                isinstance(edge, cq.Edge)
                and abs(edge.Center().x + self.width_x) < 1e-6
                and abs(edge.Center().y - top_y) < 1e-6
            )
        )
        if rounded_edge.size() != 1:
            raise ValueError("Expected one angle-indicator outer top edge")
        obj = rounded_edge.fillet(self.corner_radius)

        if cutout:
            return obj

        # Countersunk clearance holes enter from the exposed outer face. The
        # full 8 mm thickness leaves room for varying conical head profiles.
        obj = (
            obj.faces(">Z")
            .workplane()
            .pushPoints(mount_centers)
            .cskHole(3.4, 6.5, 82.0)
        )
        
        return obj

    def _mount_centers(self) -> tuple[tuple[float, float], ...]:
        return ((-6.0, self.hinge_z - 6.0), (-6.0, self.hinge_z + 6.0))

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name,
            self.shoulder_dia,
            self.away_nub_dia,
            self.hinge_z,
            self.height,
            self.width_x,
            self.thickness,
            self.corner_radius,
        )
