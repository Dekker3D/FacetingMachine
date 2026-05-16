import bom_part_data as bom

class LapAssemblyBase(bom.PartAssembly):
    def required_frame_width():
        raise NotImplementedError()
