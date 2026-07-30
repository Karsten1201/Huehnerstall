"""Fundament- und Bodenplattengeometrie."""

from __future__ import annotations

import FreeCAD as App
import Part


def create_foundation(
    document: App.Document,
    *,
    length: float,
    width: float,
    thickness: float,
    overhang: float = 0.0,
) -> App.DocumentObject:
    """Erzeugt eine rechteckige Stahlbetonbodenplatte.

    Der Gebäudenullpunkt liegt auf der Oberkante der Bodenplatte an der
    südwestlichen Gebäudeecke. Die Platte ragt optional umlaufend über die
    Außenkante der Holzkonstruktion hinaus.
    """
    if min(length, width, thickness) <= 0:
        raise ValueError("Länge, Breite und Dicke müssen größer als null sein.")
    if overhang < 0:
        raise ValueError("Der Plattenüberstand darf nicht negativ sein.")

    slab = document.addObject("Part::Feature", "FoundationSlab")
    slab.Label = "Stahlbeton-Bodenplatte"
    slab.addProperty("App::PropertyLength", "BuildingLength", "Abmessungen")
    slab.addProperty("App::PropertyLength", "BuildingWidth", "Abmessungen")
    slab.addProperty("App::PropertyLength", "Thickness", "Abmessungen")
    slab.addProperty("App::PropertyLength", "Overhang", "Abmessungen")
    slab.addProperty("App::PropertyString", "Material", "Bauphysik")

    slab.BuildingLength = length
    slab.BuildingWidth = width
    slab.Thickness = thickness
    slab.Overhang = overhang
    slab.Material = "Stahlbeton"

    slab.Shape = Part.makeBox(
        length + 2.0 * overhang,
        width + 2.0 * overhang,
        thickness,
        App.Vector(-overhang, -overhang, -thickness),
    )
    if slab.ViewObject is not None:
        slab.ViewObject.ShapeColor = (0.72, 0.72, 0.72)
    return slab
