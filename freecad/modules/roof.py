"""Parametrisches Satteldach."""

from __future__ import annotations

import math
import FreeCAD as App
import Part


def create_gable_roof(document, *, length, width, wall_height, pitch_deg,
                       eave_overhang, gable_overhang, rafter_depth):
    """Erzeugt zwei vereinfachte Dachflächen als Volumenkörper."""
    if min(length, width, wall_height, pitch_deg, rafter_depth) <= 0:
        raise ValueError("Dachparameter müssen größer als null sein.")
    group = document.addObject("App::Part", "Roof")
    group.Label = "Satteldach"

    run = width / 2.0 + eave_overhang
    slope = run / math.cos(math.radians(pitch_deg))
    roof_length = length + 2.0 * gable_overhang
    rise = run * math.tan(math.radians(pitch_deg))

    for side, angle, y in (("South", pitch_deg, -eave_overhang),
                           ("North", -pitch_deg, width / 2.0)):
        panel = document.addObject("Part::Feature", f"Roof_{side}")
        panel.Label = f"Dachfläche {side}"
        panel.Shape = Part.makeBox(roof_length, slope, rafter_depth)
        panel.Placement.Base = App.Vector(-gable_overhang, y, wall_height)
        panel.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), angle)
        panel.addProperty("App::PropertyAngle", "Pitch", "Dach")
        panel.addProperty("App::PropertyLength", "RidgeHeight", "Dach")
        panel.Pitch = pitch_deg
        panel.RidgeHeight = wall_height + rise
        panel.ViewObject.ShapeColor = (0.28, 0.30, 0.32)
        group.addObject(panel)
    return group
