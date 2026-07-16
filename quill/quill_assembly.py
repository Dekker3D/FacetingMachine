from __future__ import annotations
import cadquery as cq
from cadquery import Location
import bom_part_data as bpd
import bought_bits as bb
import quill.quill_abstract as quill_abstract


class QuillAssembly(quill_abstract.QuillAssemblyBase):
    """Class representing the entire quill assembly. Swappable — owns quill dimensions."""

    # Pitch joint interface (matches quill holder's pitch joint)
    pitch_axle_dia: float = 8.0  # Fits through 608ZZ bearings (ID=8mm)
    pitch_axle_length: float = 64.0  # quill_width + 2 * bearing_width
    pitch_shoulder_dia: float = 24.0  # Wider than bearing OD to constrain axially
    pitch_shoulder_thickness: float = 3.0

    # Quill arm
    quill_arm_length: float = 180.0  # Extends toward lap (+X)
    quill_arm_width: float = 40.0
    quill_arm_height: float = 15.0

    # Dop chuck (placeholder at the tip)
    chuck_dia: float = 12.0
    chuck_length: float = 30.0

    @classmethod
    def make_assembly(cls) -> cq.Assembly:
        """Create the entire quill assembly."""
        assembly = (
            cq.Assembly()
            .add(
                QuillPitchJoint(
                    axle_dia=cls.pitch_axle_dia,
                    axle_length=cls.pitch_axle_length,
                    shoulder_dia=cls.pitch_shoulder_dia,
                    shoulder_thickness=cls.pitch_shoulder_thickness,
                ).get_object(),
                name="pitch_joint",
                loc=Location((0, 0, 0)),
                color=cq.Color("blue"),
            )
            .add(
                QuillArm(
                    length=cls.quill_arm_length,
                    width=cls.quill_arm_width,
                    height=cls.quill_arm_height,
                ).get_object(),
                name="quill_arm",
                loc=Location((0, 0, 0)),
                color=cq.Color("cyan"),
            )
            .add(
                DopChuck(
                    dia=cls.chuck_dia,
                    length=cls.chuck_length,
                ).get_object(),
                name="dop_chuck",
                loc=Location((cls.quill_arm_length - cls.chuck_length / 2, 0, 0)),
                color=cq.Color("gray"),
            )
        )
        return assembly

    def get_BOM(self) -> bpd.BOM:
        bom = bpd.BOM()
        bom.add(QuillPitchJoint(
            axle_dia=self.pitch_axle_dia,
            axle_length=self.pitch_axle_length,
            shoulder_dia=self.pitch_shoulder_dia,
            shoulder_thickness=self.pitch_shoulder_thickness,
        ))
        bom.add(QuillArm(
            length=self.quill_arm_length,
            width=self.quill_arm_width,
            height=self.quill_arm_height,
        ))
        bom.add(DopChuck(
            dia=self.chuck_dia,
            length=self.chuck_length,
        ))
        return bom


class QuillPitchJoint(bpd.PrintedPart):
    """Printed part: axle that sits in the quill holder's pitch joint bearings.
    Two 608ZZ bearings support this axle, allowing the quill to pitch up/down."""

    def __init__(
        self,
        axle_dia: float,
        axle_length: float,
        shoulder_dia: float,
        shoulder_thickness: float,
    ) -> None:
        self.axle_dia = axle_dia
        self.axle_length = axle_length
        self.shoulder_dia = shoulder_dia
        self.shoulder_thickness = shoulder_thickness
        super().__init__(name="Quill Pitch Joint")

    def _comparables(self) -> tuple[object, ...]:
        return (
            self.name, self.axle_dia, self.axle_length,
            self.shoulder_dia, self.shoulder_thickness,
        )

    def get_object(self) -> cq.Workplane:
        """Create the pitch joint axle with bearing shoulders."""
        # Main axle shaft (along Y axis)
        axle = cq.Workplane("XZ").cylinder(
            self.axle_length, self.axle_dia / 2,
            centered=(True, True, True),
        )

        # Shoulder rings on each end to constrain bearings axially
        half_length = self.axle_length / 2
        shoulder_offset = half_length - self.shoulder_thickness / 2

        axle = axle.union(
            cq.Workplane("XZ").cylinder(
                self.shoulder_thickness, self.shoulder_dia / 2,
                centered=(True, True, True),
            ).translate((0, shoulder_offset, 0))
        )
        axle = axle.union(
            cq.Workplane("XZ").cylinder(
                self.shoulder_thickness, self.shoulder_dia / 2,
                centered=(True, True, True),
            ).translate((0, -shoulder_offset, 0))
        )

        # Quill arm mounting block (connects axle to the quill arm)
        axle = axle.union(
            cq.Workplane("XY").box(
                20, self.axle_length, self.shoulder_dia,
                centered=(True, True, True),
            )
        )

        return axle


class QuillArm(bpd.PrintedPart):
    """Printed part: the main arm of the quill, extending from the pitch joint
    toward the lap. Carries the dop chuck at its tip."""

    def __init__(
        self,
        length: float,
        width: float,
        height: float,
    ) -> None:
        self.length = length
        self.width = width
        self.height = height
        super().__init__(name="Quill Arm")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.length, self.width, self.height)

    def get_object(self) -> cq.Workplane:
        """Create the quill arm body extending in +X."""
        arm = (
            cq.Workplane("YZ")
            .box(self.height, self.width, self.length, centered=(True, True, False))
        )
        # Taper the tip
        arm = (
            arm
            .faces(">X").workplane()
            .rect(self.height * 0.6, self.width * 0.6)
            .extrude(-self.length * 0.15, combine="cut")
        )
        return arm


class DopChuck(bpd.PrintedPart):
    """Printed part: placeholder for the dop/gem-holding mechanism at the quill tip."""

    def __init__(
        self,
        dia: float,
        length: float,
    ) -> None:
        self.dia = dia
        self.length = length
        super().__init__(name="Dop Chuck")

    def _comparables(self) -> tuple[object, ...]:
        return (self.name, self.dia, self.length)

    def get_object(self) -> cq.Workplane:
        """Create a placeholder chuck body."""
        chuck = cq.Workplane("YZ").cylinder(
            self.length, self.dia / 2,
            centered=(True, True, True),
        )
        # Dop hole at the tip
        chuck = (
            chuck
            .faces("<X").workplane()
            .hole(self.dia * 0.5, self.length * 0.7)
        )
        return chuck
