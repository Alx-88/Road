# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Datum Plane objects."""

from pivy import coin
from .view_geo_object import ViewProviderGeoObject


class ViewProviderDatumPlane(ViewProviderGeoObject):
    """This class is about Datum Plane Object view features."""

    def __init__(self, vobj):
        """Set view properties."""
        super().__init__(vobj, "DatumPlane")
        vobj.Proxy = self

    def attach(self, vobj):
        """Create Object visuals in 3D view."""
        super().attach(vobj)
        self.Object = vobj.Object
        self.view = vobj

        # Draw style for the plane
        self.draw_style = coin.SoDrawStyle()
        self.draw_style.style = coin.SoDrawStyle.LINES
        self.draw_style.lineWidth = 2

        # Color for the plane (semi-transparent blue)
        self.color = coin.SoBaseColor()
        self.color.rgb = (0.3, 0.6, 0.9)

        # Coordinates and face set for the plane
        self.coords = coin.SoCoordinate3()
        self.face_set = coin.SoIndexedFaceSet()

        # Line set for outline
        self.line_set = coin.SoLineSet()

        # Group for plane visualization
        plane_group = coin.SoGroup()
        plane_group.addChild(self.draw_style)
        plane_group.addChild(self.color)
        plane_group.addChild(self.coords)
        plane_group.addChild(self.face_set)
        plane_group.addChild(self.line_set)

        # Annotation for the plane (so it's always visible)
        self.plane_annotation = coin.SoAnnotation()
        self.plane_annotation.addChild(plane_group)

        # Add to standard group
        self.sel2 = coin.SoType.fromName('SoFCSelection').createInstance()
        self.sel2.style = 'EMISSIVE_DIFFUSE'
        self.sel2.addChild(self.plane_annotation)

        self.drag = coin.SoSeparator()
        self.standard.addChild(self.sel2)
        self.standard.addChild(self.drag)

    def updateData(self, obj, prop):
        """Update Object visuals when a data property changed."""
        super().updateData(obj, prop)

        if prop == "Shape" and obj.Shape and len(obj.Shape.Faces) > 0:
            # Get vertices from the shape
            vertices = [v.Point for v in obj.Shape.Vertexes]
            
            # Update coordinates
            self.coords.point.values = vertices
            
            # Create face indices (single quad)
            num_vertices = len(vertices)
            if num_vertices >= 4:
                # Face: 0, 1, 2, 3, -1
                self.face_set.coordIndex.values = [0, 1, 2, 3, -1]
                # Outline: 0, 1, 2, 3, 0, -1
                self.line_set.numVertices.values = [num_vertices + 1]
            
        elif prop == "Shape":
            # Clear if no shape
            self.coords.point.values = []
            self.face_set.coordIndex.values = []
            self.line_set.numVertices.values = []
