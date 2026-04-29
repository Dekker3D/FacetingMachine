class QuillHolderJointBase:
    def space_needed_carriage_x(self):
        raise NotImplementedError()

    def offset_carriage_z(self):
        raise NotImplementedError()

    def add_shape(self, base_width, base_length):
        raise NotImplementedError()

    def cut_shape(self, base_width, base_length):
        raise NotImplementedError()