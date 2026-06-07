# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides GUI tool to create a working plane perpendicular to an alignment."""

import FreeCAD, FreeCADGui

from ..variables import icons_path


class WorkingPlaneCreate:
    """Command to create a working plane at a specified station of an alignment."""

    def __init__(self):
        """Constructor"""
        pass

    def GetResources(self):
        """Return the command resources dictionary"""
        return {
            "Pixmap": icons_path + "/WorkingPlane.svg",
            "MenuText": "Create Working Plane at Station",
            "ToolTip": "Create a working plane perpendicular to alignment at specified station."}

    def IsActive(self):
        """Define tool button activation situation"""
        return bool(FreeCADGui.ActiveDocument)

    def Activated(self):
        """Command activation method"""
        doc = FreeCAD.ActiveDocument
        if not doc:
            FreeCAD.Console.PrintError("No active document!")
            return

        alignment_obj = self._get_alignment_object()
        if not alignment_obj:
            return

        if not hasattr(alignment_obj, 'Model') or alignment_obj.Model is None:
            FreeCAD.Console.PrintError("Alignment has no geometry model.")
            return

        station, ok = self._get_station_input(
            alignment_obj.Model.get_sta_start(),
            alignment_obj.Model.get_sta_end()
        )
        
        if not ok:
            return

        self.create_working_plane(alignment_obj, station)

    def _get_alignment_object(self):
        """Get alignment object from selection or find in document."""
        selection = FreeCADGui.Selection.getSelection()
        if selection:
            for obj in selection:
                if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, 'Type'):
                    if obj.Proxy.Type == 'Road::Alignment':
                        return obj

        doc = FreeCAD.ActiveDocument
        alignments = []
        for obj in doc.Objects:
            if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, 'Type'):
                if obj.Proxy.Type == 'Road::Alignment':
                    alignments.append(obj)
        
        if not alignments:
            FreeCAD.Console.PrintError("No Road Alignment objects found in document.")
            return None
        
        if len(alignments) == 1:
            return alignments[0]
        
        FreeCAD.Console.PrintMessage(f"Found {len(alignments)} alignments. Using first one: {alignments[0].Name}")
        return alignments[0]

    def _get_station_input(self, start_sta, end_sta):
        """Show dialog to input station value."""
        try:
            from PySide.QtGui import QInputDialog
            station, ok = QInputDialog.getDouble(
                FreeCADGui.getMainWindow(),
                "Station Input",
                f"Enter station (between {start_sta:.2f} and {end_sta:.2f}):",
                (start_sta + end_sta) / 2,
                start_sta,
                end_sta,
                2
            )
            return station, ok
        except ImportError:
            from PySide2.QtWidgets import QInputDialog
            station, ok = QInputDialog.getDouble(
                FreeCADGui.getMainWindow(),
                "Station Input",
                f"Enter station (between {start_sta:.2f} and {end_sta:.2f}):",
                (start_sta + end_sta) / 2,
                start_sta,
                end_sta,
                2
            )
            return station, ok

    def create_working_plane(self, alignment_obj, station):
        """
        Create a working plane perpendicular to alignment at given station.
        """
        doc = FreeCAD.ActiveDocument
        
        try:
            point_2d, ortho_vector_2d = alignment_obj.Model.get_orthogonal_at_station(
                station, 'left'
            )
            
            tangent_2d = (ortho_vector_2d[1], -ortho_vector_2d[0])
            
            scale = 1000.0
            point_3d = FreeCAD.Vector(point_2d[0] * scale, point_2d[1] * scale, 0)
            ortho_vec_3d = FreeCAD.Vector(ortho_vector_2d[0] * scale, ortho_vector_2d[1] * scale, 0)
            tangent_vec_3d = FreeCAD.Vector(tangent_2d[0] * scale, tangent_2d[1] * scale, 0)
            
            ortho_vec_3d.normalize()
            tangent_vec_3d.normalize()
            
            y_axis_3d = tangent_vec_3d.cross(ortho_vec_3d)
            
            wp_name = f'WP_{alignment_obj.Name}_Sta{station:.2f}'
            wp = doc.addObject('PartDesign::Workplane', wp_name)
            wp.Label = f'WP at {alignment_obj.Name} Sta{station:.2f}'
            
            wp.Origin = point_3d
            wp.XAxis = ortho_vec_3d
            wp.YAxis = y_axis_3d
            
            wp.Visibility = True
            
            wp.addProperty("App::PropertyString", "Alignment", "Base").Alignment = alignment_obj.Name
            wp.addProperty("App::PropertyFloat", "Station", "Base").Station = station
            
            if hasattr(alignment_obj, 'Group') and alignment_obj.Group:
                alignment_obj.Group.addObject(wp)
            
            doc.recompute()
            FreeCAD.Console.PrintMessage(f"Created working plane: {wp.Name}")
            return wp
            
        except ValueError as e:
            FreeCAD.Console.PrintError(f"Error: {str(e)}")
            return None
        except Exception as e:
            FreeCAD.Console.PrintError(f"Unexpected error: {str(e)}")
            return None


FreeCADGui.addCommand("Working Plane Create", WorkingPlaneCreate())