# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Datum Plane objects."""

import FreeCAD, Part
from .geo_object import GeoObject


class DatumPlane(GeoObject):
    """This class is about Datum Plane object data features."""

    def __init__(self, obj):
        """Set data properties."""
        super().__init__(obj)

        self.Type = 'Road::DatumPlane'

        obj.addProperty(
            "App::PropertyFloat", "Station", "Base",
            "Station along alignment").Station = 0

        obj.addProperty(
            "App::PropertyFloat", "Offset", "Base",
            "Offset from alignment").Offset = 0

        obj.addProperty(
            "App::PropertyFloat", "Elevation", "Base",
            "Elevation of datum plane").Elevation = 0

        obj.addProperty(
            "App::PropertyFloat", "Width", "Geometry",
            "Width of datum plane").Width = 100

        obj.addProperty(
            "App::PropertyFloat", "Length", "Geometry",
            "Length of datum plane").Length = 100

        obj.addProperty(
            "App::PropertyFloat", "Rotation", "Geometry",
            "Rotation of datum plane around vertical axis").Rotation = 0

        obj.addProperty(
            "App::PropertyBool", "ShowLabel", "Display",
            "Show station label").ShowLabel = True

        obj.addProperty(
            "App::PropertyString", "Name", "Base",
            "Datum plane name").Name = "DatumPlane"

        obj.addProperty(
            "App::PropertyString", "ProfileName", "Base",
            "Profile name for elevation reference").ProfileName = ""

        obj.Proxy = self

    def execute(self, obj):
        """Generate the datum plane shape."""
        # Get parent group (DatumPlanes)
        datum_planes = obj.getParentGroup()
        if not datum_planes:
            return

        # Get alignment from parent of datum_planes group
        alignment = datum_planes.getParentGroup()
        if not alignment or not hasattr(alignment, 'Model'):
            return

        try:
            # Get point at station along alignment with elevation
            if obj.ProfileName and alignment.Model.profiles:
                # Try to get 3D point from profile
                point_3d = alignment.Model.get_3d_point_at_station(obj.ProfileName, obj.Station)
                if point_3d:
                    # Convert to FreeCAD coordinates using zero_referance
                    from ..utils.support import zero_referance
                    coord = zero_referance(alignment.Model.get_start_point(), [point_3d[:2]])
                    center = coord[0]
                    # Set elevation from profile (convert from m to mm)
                    obj.Elevation = point_3d[2]
                    center.z = point_3d[2] * 1000
                else:
                    # Fallback to horizontal only
                    tuple_coord, tuple_vec = alignment.Model.get_orthogonal_at_station(
                        obj.Station, "left"
                    )
                    from ..utils.support import zero_referance
                    coord = zero_referance(alignment.Model.get_start_point(), [tuple_coord])
                    center = coord[0]
            else:
                # No profile specified, use horizontal position only
                tuple_coord, tuple_vec = alignment.Model.get_orthogonal_at_station(
                    obj.Station, "left"
                )
                from ..utils.support import zero_referance
                coord = zero_referance(alignment.Model.get_start_point(), [tuple_coord])
                center = coord[0]

            # Apply rotation to the orthogonal vector
            import math
            angle_rad = math.radians(obj.Rotation)
            vec_x = tuple_vec[0]
            vec_y = tuple_vec[1]

            # Rotate vector
            rotated_vec_x = vec_x * math.cos(angle_rad) - vec_y * math.sin(angle_rad)
            rotated_vec_y = vec_x * math.sin(angle_rad) + vec_y * math.cos(angle_rad)

            # Create plane shape (rectangle)
            half_length = obj.Length * 1000 / 2
            half_width = obj.Width * 1000 / 2

            # Calculate corner points
            # Forward direction (along alignment)
            forward_vec = FreeCAD.Vector(rotated_vec_x, rotated_vec_y, 0).normalized()
            # Right direction (perpendicular)
            right_vec = FreeCAD.Vector(-rotated_vec_y, rotated_vec_x, 0).normalized()

            p1 = center + forward_vec.multiply(-half_length) + right_vec.multiply(-half_width)
            p2 = center + forward_vec.multiply( half_length) + right_vec.multiply(-half_width)
            p3 = center + forward_vec.multiply( half_length) + right_vec.multiply( half_width)
            p4 = center + forward_vec.multiply(-half_length) + right_vec.multiply( half_width)

            # Add elevation (convert from m to mm)
            elevation_mm = obj.Elevation * 1000
            p1.z = elevation_mm
            p2.z = elevation_mm
            p3.z = elevation_mm
            p4.z = elevation_mm

            # Create face
            obj.Shape = Part.makePolygon([p1, p2, p3, p4, p1])

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error creating datum plane shape: {str(e)}\n")
            obj.Shape = Part.Shape()

    def onChanged(self, obj, prop):
        """Do something when a property has changed."""
        super().onChanged(obj, prop)

        # Update label with station if Name is default
        if prop == "Station" and obj.Name == "DatumPlane":
            obj.Name = f"DatumPlane_Sta{obj.Station:.2f}"
