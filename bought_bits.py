import bom_part_data as bom
import cadquery as cq


class part:
    """Base class for all parts."""
    cached_obj: cq.Workplane = None
    part: bom.PartMetadata = None

    def get_object(self) -> cq.Workplane:
        """Returns a cadquery object representing this part."""
        if self.cached_obj is None:
            self.cached_obj = self._create_object()
        return self.cached_obj

    def _create_object(self) -> cq.Workplane:
        """Creates a cadquery object representing this part."""
        raise NotImplementedError()


class bearing_generic(part):
    def width(self):
        raise NotImplementedError()

    def ID(self):
        raise NotImplementedError()

    def OD(self):
        raise NotImplementedError()

    def _create_object(self):
        return cq.Workplane("XY").circle(self.OD()/2).extrude(self.width()).edges().fillet(1.0)


class bearing_608zz(bearing_generic):
    part = bom.PartMetadata(
        name="608ZZ Bearing"
    )

    def width(self):
        return 7.0

    def ID(self):
        return 8.0

    def OD(self):
        return 22.0


class bearing_624zz(bearing_generic):
    part = bom.PartMetadata(
        name="624ZZ Bearing"
    )

    def width(self):
        return 5.0

    def ID(self):
        return 4.0

    def OD(self):
        return 13.0
