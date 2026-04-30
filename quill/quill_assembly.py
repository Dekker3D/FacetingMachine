import cadquery as cq
from cadquery import Location
from machine import MachineConfig as cfg
import bought_bits as bb
import quill.quill_abstract as quill_abstract


class QuillAssembly(quill_abstract.QuillAssemblyBase):
    """Class representing the entire quill assembly."""

    @classmethod
    def make_assembly(cls):
        """Create the entire quill assembly."""

        qh = QuillHolder()
        qt_X = qh.pitch_joint_X_offset()
        qt_Z = qh.pitch_joint_Z_offset()

        assembly = (
            cq.Assembly()
            .add(
                qh.make(),
                name="quill_holder",
                loc=Location((0, 0, 0)),
                color=cq.Color("orange")
            )
            .add(
                QuillTilt().make(),
                name="quill_tilt",
                loc=Location((qt_X, 0, qt_Z)),
                color=cq.Color("green")
            )
        )

        return assembly


class QuillTilt:
    """Represents the part of the quill that tilts up and down."""

    def make(self):
        """Create the quill tilt."""

        tilt = (
            cq.Workplane("XY")
            .box(10, 10, 10)
            )

        return tilt


class QuillHolder:
    """
    Class representing the quill holder.
    This holds the quill and allows it to pitch up/down.
    The holder swings left/right on the quill carriage.
    """

    QUILL_WIDTH = 50.0

    def swing_joint_OD(self):
        return cfg.QH_SWING_DIA + cfg.QH_SWING_JOINT_THICKNESS * 2

    def pitch_joint_OD(self):
        return bb.Bearing608ZZ.OD + cfg.QH_PITCH_JOINT_THICKNESS * 2

    def pitch_joint_X_offset(self):
        return self.swing_joint_OD() / 2 + self.pitch_joint_OD() / 2

    def pitch_joint_Z_offset(self):
        return self.pitch_joint_OD() / 2

    def make(self):
        """Create the quill holder."""

        holder = (
            cq.Workplane("XY")
            .cylinder(
                cfg.QH_SWING_HEIGHT,
                self.swing_joint_OD() / 2,
                centered=(True, True, False)
            )
        )

        holder = holder.cut(
            cq.Workplane("XY")
            .cylinder(
                cfg.QH_SWING_HEIGHT,
                cfg.QH_SWING_DIA / 2,
                centered=(True, True, False)
            )
        )

        # Pitch joint bearing holders
        holder = holder.union(
            cq.Workplane("XZ")
            .move(self.pitch_joint_X_offset(), self.pitch_joint_Z_offset())
            .cylinder(self.QUILL_WIDTH + bb.Bearing608ZZ.WIDTH * 2, self.pitch_joint_OD() / 2)
            .faces(">Z")
            .hole(bb.Bearing608ZZ.OD)
        )

        holder = holder.cut(
            cq.Workplane("XZ")
            .move(self.pitch_joint_X_offset(), self.pitch_joint_Z_offset())
            .box(self.pitch_joint_OD(), 100, self.QUILL_WIDTH)
        )

        return holder
