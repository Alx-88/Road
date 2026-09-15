# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tools to Datum Plane commands."""

import FreeCAD, FreeCADGui
import os
from .. import ICONPATH
from ..make import make_datum_plane
from ..tasks.task_selection import SingleSelection
from ..utils.trackers import ViewTracker


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
        self.alignment_selector.combo_box.currentTextChanged.connect(self.region_update)

        self.region_selector = SingleSelection()
        self.region_update()

        self.form = [self.alignment_selector, self.region_selector]
        FreeCADGui.Control.showDialog(self)

    def region_update(self):
        """Update region selector when alignment changes."""
        alignment = self.alignment_selector.selected_object
        if alignment:
            for item in alignment.Group:
                if hasattr(item, 'Proxy') and item.Proxy.Type == "Road::Regions":
                    self.region_selector.set_group(item)
                    break

    def accept(self):
        """Create datum plane at selected position."""
        FreeCAD.Console.PrintWarning("Select Datum Plane position on screen")
        view = FreeCADGui.ActiveDocument.ActiveView
        self.tracker = ViewTracker(view, "Mouse", key="Left", function=self.set_placement)
        self.tracker.start()

    def set_placement(self, callback):
        """Set the placement of the datum plane based on mouse position."""
        alignment = self.alignment_selector.selected_object
        region = self.region_selector.selected_object

        if not alignment or not region:
            FreeCAD.Console.PrintError("No alignment or region selected\n")
            self.tracker.stop()
            return

        # Find or create DatumPlanes group
        datum_planes_group = None
        for item in region.Group:
            if hasattr(item, 'Proxy') and item.Proxy.Type == "Road::DatumPlanes":
                datum_planes_group = item
                break

        if not datum_planes_group:
            datum_planes_group = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup", "DatumPlanes")
            # Set a property to identify the group type
            datum_planes_group.addProperty("App::PropertyString", "Type").Type = "Road::DatumPlanes"
            region.addObject(datum_planes_group)

        # Create datum plane
        datum_plane = make_datum_plane.create()

        # Get position from mouse
        event = callback.getEvent()
        position = event.getPosition()
        view = FreeCADGui.ActiveDocument.ActiveView
        coordinate = view.getPoint(tuple(position.getValue()))

        # Calculate station and offset from alignment
        # Convert from mm to m (FreeCAD uses mm, alignment uses m)
        point_relative = coordinate.sub(alignment.Placement.Base).multiply(0.001)
        
        try:
            station, offset = alignment.Model.get_station_offset(
                [point_relative.x, point_relative.y]
            )
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error getting station: {str(e)}\n")
            station = 0
            offset = 0

        # Set properties
        datum_plane.Station = station if station is not None else 0
        datum_plane.Offset = offset if offset is not None else 0
        datum_plane.Elevation = coordinate.z * 0.001  # Convert mm to m
        datum_plane.Placement.Base = coordinate

        # Add to group
        datum_planes_group.addObject(datum_plane)

        self.tracker.stop()
        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()


FreeCADGui.addCommand("Datum Plane Create", DatumPlaneCreate())
