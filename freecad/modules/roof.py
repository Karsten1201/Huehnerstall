"""Parametrisches Satteldach mit Sparren, Firstbalken und Dachflächen."""

from __future__ import annotations

import math

import FreeCAD as App
import Part


def _set_color(obj, color):
    """Setzt eine Farbe nur, wenn FreeCAD mit GUI/ViewProvider läuft."""
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color


def _feature(document, name, label, shape, material, color):
    obj = document.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Material", "Bauteil")
    obj.Material = material
    _set_color(obj, color)
    return obj


def create_gable_roof(
    document,
    *,
    length,
    width,
    wall_height,
    pitch_deg,
    eave_overhang,
    gable_overhang,
    rafter_width,
    rafter_depth,
    rafter_spacing,
    ridge_width,
    ridge_depth,
    cover_thickness,
):
    """Erzeugt ein symmetrisches Satteldach als konstruktive Baugruppe.

    Die Sparren laufen in Y-Richtung von der Traufe zum First. Das Raster wird
    entlang der Gebäudelänge in X-Richtung verteilt. Zusätzlich werden ein
    durchgehender Firstbalken und zwei vereinfachte Dachdeckungsflächen erzeugt.
    """
    values = (
        length,
        width,
        wall_height,
        pitch_deg,
        rafter_width,
        rafter_depth,
        rafter_spacing,
        ridge_width,
        ridge_depth,
        cover_thickness,
    )
    if min(values) <= 0:
        raise ValueError("Dachparameter müssen größer als null sein.")
    if pitch_deg >= 90:
        raise ValueError("Die Dachneigung muss kleiner als 90 Grad sein.")
    if eave_overhang < 0 or gable_overhang < 0:
        raise ValueError("Dachüberstände dürfen nicht negativ sein.")

    group = document.addObject("App::Part", "Roof")
    group.Label = "Satteldach"

    half_span = width / 2.0
    run = half_span + eave_overhang
    slope_length = run / math.cos(math.radians(pitch_deg))
    ridge_height = wall_height + half_span * math.tan(math.radians(pitch_deg))
    roof_length = length + 2.0 * gable_overhang

    count = max(2, math.ceil((roof_length - rafter_width) / rafter_spacing) + 1)
    offsets = [
        min(index * rafter_spacing, roof_length - rafter_width)
        for index in range(count)
    ]
    offsets = sorted(set(offsets))

    for index, offset in enumerate(offsets):
        x = -gable_overhang + offset
        for side, y, angle in (
            ("South", -eave_overhang, pitch_deg),
            ("North", width + eave_overhang, 180.0 - pitch_deg),
        ):
            shape = Part.makeBox(rafter_width, slope_length, rafter_depth)
            rafter = _feature(
                document,
                f"Rafter_{side}_{index:02d}",
                f"Sparren {side} {index + 1}",
                shape,
                "KVH C24",
                (0.76, 0.56, 0.32),
            )
            rafter.Placement.Base = App.Vector(x, y, wall_height)
            rafter.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), angle)
            rafter.addProperty("App::PropertyLength", "Spacing", "Dach")
            rafter.addProperty("App::PropertyAngle", "Pitch", "Dach")
            rafter.Spacing = rafter_spacing
            rafter.Pitch = pitch_deg
            group.addObject(rafter)

    ridge = _feature(
        document,
        "RidgeBeam",
        "Firstbalken",
        Part.makeBox(roof_length, ridge_width, ridge_depth),
        "KVH C24",
        (0.76, 0.56, 0.32),
    )
    ridge.Placement.Base = App.Vector(
        -gable_overhang,
        half_span - ridge_width / 2.0,
        ridge_height - ridge_depth,
    )
    ridge.addProperty("App::PropertyLength", "RidgeHeight", "Dach")
    ridge.RidgeHeight = ridge_height
    group.addObject(ridge)

    for side, y, angle in (
        ("South", -eave_overhang, pitch_deg),
        ("North", width + eave_overhang, 180.0 - pitch_deg),
    ):
        panel = _feature(
            document,
            f"RoofCover_{side}",
            f"Dachdeckung {side}",
            Part.makeBox(roof_length, slope_length, cover_thickness),
            "Dachdeckung",
            (0.28, 0.30, 0.32),
        )
        panel.Placement.Base = App.Vector(
            -gable_overhang,
            y,
            wall_height + rafter_depth,
        )
        panel.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), angle)
        panel.addProperty("App::PropertyAngle", "Pitch", "Dach")
        panel.addProperty("App::PropertyLength", "RidgeHeight", "Dach")
        panel.Pitch = pitch_deg
        panel.RidgeHeight = ridge_height
        group.addObject(panel)

    return group
