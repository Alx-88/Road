# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides functions to create Datum Plane objects."""

import FreeCAD
from ..objects.datum_plane import DatumPlane
from ..viewproviders.view_datum_plane import ViewProviderDatumPlane


def create():
    """Factory method for Datum Plane object."""
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "DatumPlane")
    DatumPlane(obj)
    ViewProviderDatumPlane(obj.ViewObject)
    return obj
