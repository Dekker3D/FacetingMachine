from __future__ import annotations
import cadquery as cq
import bought_bits as bb
import quill_joint.quill_joint_abstract as quill_joint_abstract


class QuillHolderJointStandard(quill_joint_abstract.QuillHolderJointBase):
    carriage_joint_thickness_radial: float = 5.0
    carriage_joint_clearance_radial: float = 2.0
    carriage_joint_thickness_below: float = 8.0
    carriage_joint_length: float = 50.0

    def space_needed_carriage_x(self) -> float:
        return self.carriage_joint_radius() + self.carriage_joint_clearance_radial

    def offset_carriage_z(self) -> float:
        return self.carriage_joint_thickness_below

    def carriage_joint_radius(self) -> float:
        return bb.Bearing608ZZ.OD / 2 + self.carriage_joint_clearance_radial

    def carriage_joint_clearance(self) -> float:
        return self.carriage_joint_radius() + self.carriage_joint_clearance_radial

    def add_shape(
        self, base_width: float, base_length: float
    ) -> cq.Workplane:
        return (
            cq.Workplane("XY")
            .cylinder(
                self.carriage_joint_thickness_below * 2
                + self.carriage_joint_length,
                self.carriage_joint_radius(),
                centered=(True, True, False),
            )
            .translate((0, 0, -self.carriage_joint_thickness_below))
        )

    def cut_shape(
        self, base_width: float, base_length: float
    ) -> cq.Workplane:
        return cq.Workplane("XY").cylinder(
            self.carriage_joint_length,
            self.carriage_joint_clearance(),
            centered=(True, True, False),
        )


class QuillHolderJointAli(QuillHolderJointStandard):
    # Measured dimensions: 46.6 mm tall, 24.6 mm hinge OD,
    # 15.0 mm hinge ID, mast is 14.5 mm.

    carriage_joint_length: float = 46.6
    carriage_joint_measured_OD: float = 24.6
    carriage_joint_thickness_radial: float = (
        (15.0 - 24.6) / 2  # negative — indicates the Ali part is undersized
    )

    def carriage_joint_radius(self) -> float:
        return 24.6 / 2
