# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to Datum Plane commands."""

import FreeCAD, FreeCADGui
import os
from PySide.QtWidgets import QInputDialog
from .. import ICONPATH
from ..make import make_datum_plane
from ..tasks.task_selection import SingleSelection


class DatumPlaneCreate:
    """Command to create a new Datum Plane object along an alignment."""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "DatumPlane.svg"),
            "MenuText": "Create Datum Plane",
            "ToolTip": "Create Datum Plane at station along an alignment"
        }

    def IsActive(self):
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        alignments = FreeCAD.ActiveDocument.getObject("Alignments")
        self.alignment_selector = SingleSelection(alignments)

        self.form = [self.alignment_selector]
        FreeCADGui.Control.showDialog(self)

    def accept(self):
        """Create datum plane at specified station."""
        alignment = self.alignment_selector.selected_object

        if not alignment:
            FreeCAD.Console.PrintError("No alignment selected\n")
            return

        # Check if alignment has a model
        if not hasattr(alignment, 'Model') or alignment.Model is None:
            FreeCAD.Console.PrintError("Selected alignment has no model\n")
            return

        # Get available profiles from alignment
        profile_names = []
        if alignment.Model.profiles and alignment.Model.profiles.design_profiles:
            profile_names = [p.name for p in alignment.Model.profiles.design_profiles]
        if alignment.Model.profiles and alignment.Model.profiles.surface_profiles:
            profile_names.extend([p.name for p in alignment.Model.profiles.surface_profiles])

        # If no profiles exist, warn user
        if not profile_names:
            FreeCAD.Console.PrintWarning("No profiles found in alignment. Using elevation 0.\n")
            profile_name = None
        else:
            # Show profile selection dialog
            if len(profile_names) == 1:
                profile_name = profile_names[0]
            else:
                profile_name, ok = QInputDialog.getItem(
                    FreeCADGui.getMainWindow(),
                    "Select Profile",
                    "Select profile for elevation:",
                    profile_names,
                    0,
                    False
                )
                if not ok:
                    return
                profile_name = str(profile_name)

        # Ask user for station
        station, ok = QInputDialog.getDouble(
            FreeCADGui.getMainWindow(),
            "Station Input",
            "Enter station (m):",
            0.0,
            -999999.0,
            999999.0,
            2
        )
        if not ok:
            return

        # Find or create DatumPlanes group directly under alignment
        datum_planes_group = None
        for item in alignment.Group:
            if hasattr(item, 'Proxy') and hasattr(item.Proxy, 'Type') and item.Proxy.Type == "Road::DatumPlanes":
                datum_planes_group = item
                break

        if not datum_planes_group:
            datum_planes_group = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup", "DatumPlanes")
            datum_planes_group.addProperty("App::PropertyString", "Type").Type = "Road::DatumPlanes"
            alignment.addObject(datum_planes_group)

        # Create datum plane
        datum_plane = make_datum_plane.create()

        # Get 3D point from alignment at station
        try:
            if profile_name:
                point_3d = alignment.Model.get_3d_point_at_station(profile_name, station)
            else:
                # Get horizontal position only
                x, y = alignment.Model.get_point_at_station(station)
                point_3d = (x, y, 0.0)

            if point_3d is None:
                FreeCAD.Console.PrintError(f"Could not get position at station {station}\n")
                return

            # Convert from alignment coordinates (m) to FreeCAD coordinates (mm)
            # Using zero_referance for proper coordinate transformation
            from ..utils.support import zero_referance
            coord = zero_referance(alignment.Model.get_start_point(), [point_3d[:2]])
            center = coord[0]

            # Set elevation (convert from m to mm)
            elevation_mm = point_3d[2] * 1000

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error getting position at station {station}: {str(e)}\n")
            return

        # Set properties
        datum_plane.Station = station
        datum_plane.Offset = 0  # Centered on alignment
        datum_plane.Elevation = point_3d[2]  # In meters
        datum_plane.ProfileName = profile_name if profile_name else ""

        # Position the plane at the calculated point
        center.z = elevation_mm
        datum_plane.Placement.Base = center

        # Add to group
        datum_planes_group.addObject(datum_plane)

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Datum Plane Create", DatumPlaneCreate())
