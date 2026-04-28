class FrameAssemblyBase:
    def frame_width(self):
        raise NotImplementedError()

    def frame_width_internal(self):
        raise NotImplementedError()

    def frame_rail_width(self):
        raise NotImplementedError()

    def mast_space(self):
        raise NotImplementedError()

    def frame_length(self):
        raise NotImplementedError()

    def lap_pos_from_left(self):
        raise NotImplementedError()

    def lap_space_from_left(self):
        raise NotImplementedError()

    def validate(self):
        raise NotImplementedError()
