import quill_joint_abstract
import bought_bits as bb
import cadquery as cq

class QuillHolderJointStandard(quill_joint_abstract.QuillHolderJointBase):
    carriage_joint_thickness_radial = 5.0
    carriage_joint_clearance_radial = 2.0
    carriage_joint_thickness_below = 8.0
    carriage_joint_length = 50.0

    def space_needed_carriage_x(self):
        return self.carriage_joint_radius() + self.carriage_joint_clearance_radial

    def offset_carriage_z(self):
        return self.carriage_joint_thickness_below
    
    def carriage_joint_radius(self):
        return bb.Bearing608ZZ.OD / 2 + self.carriage_joint_clearance_radial
    
    def carriage_joint_clearance(self):
        return self.carriage_joint_radius() + self.carriage_joint_clearance_radial


    def add_shape(self, base_width, base_length):
        shape = (
            cq.Workplane("XY")
            .cylinder(self.carriage_joint_thickness_below * 2 + self.carriage_joint_length, self.carriage_joint_radius(), centered=(True, True, False))
            .translate((0, 0, -self.carriage_joint_thickness_below))
        )
        return shape

    def cut_shape(self, base_width, base_length):
        shape = (
            cq.Workplane("XY")
            .cylinder(self.carriage_joint_length, self.carriage_joint_clearance(), centered=(True, True, False))
        )
        return shape

class QuillHolderJointAli(QuillHolderJointStandard):
    # Measured dimensions: 46.6 mm tall, 24.6 mm hinge OD, 15.0 mm hinge ID, mast is 14.5 mm.
    
    carriage_joint_length = 46.6
    carriage_joint_measured_OD = 24.6
    carriage_joint_thickness_radial = (15.0 - carriage_joint_measured_OD) / 2
    
    def carriage_joint_radius(self):
        return 24.6 / 2