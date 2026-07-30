"""Parametrisches Satteldach mit Sparren, Firstbalken und Dachflächen."""

from __future__ import annotations

import math

import FreeCAD as App
import Part


def _set_color(obj, color):
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


def _beam_between(start, end, width, depth):
    """Erzeugt einen prismatischen Balken mit seiner Längsachse zwischen zwei Punkten."""
    direction = end.sub(start)
    length = direction.Length
    if length <= 0:
        raise ValueError("Balkenanfang und Balkenende dürfen nicht identisch sein.")

    shape = Part.makeBox(width, depth, length)
    rotation = App.Rotation(App.Vector(0, 0, 1), direction)
    shape.Placement = App.Placement(start, rotation)
    return shape


def _roof_panel_shape(*, roof_length, start_y, start_z, end_y, end_z,
                      thickness, x_start):
    """Erzeugt eine massive Dachplatte als entlang X extrudiertes YZ-Profil."""
    dy = end_y - start_y
    dz = end_z - start_z
    slope = math.hypot(dy, dz)
    if slope <= 0:
        raise ValueError("Ungültige Dachplattengeometrie.")

    # Normalenvektor in der YZ-Ebene. Die Plattenstärke liegt oberhalb der Sparren.
    ny = -dz / slope * thickness
    nz = dy / slope * thickness

    points = [
        App.Vector(x_start, start_y, start_z),
        App.Vector(x_start, end_y, end_z),
        App.Vector(x_start, end_y + ny, end_z + nz),
        App.Vector(x_start, start_y + ny, start_z + nz),
        App.Vector(x_start, start_y, start_z),
    ]
    face = Part.Face(Part.makePolygon(points))
    return face.extrude(App.Vector(roof_length, 0.0, 0.0))


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
    """Erzeugt ein symmetrisches Satteldach mit geometrisch korrekter Ausrichtung."""
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
    pitch = math.radians(pitch_deg)
    ridge_height = wall_height + half_span * math.tan(pitch)
    roof_length = length + 2.0 * gable_overhang
    x_start = -gable_overhang

    south_eave = App.Vector(0.0, -eave_overhang,
                            wall_height - eave_overhang * math.tan(pitch))
    north_eave = App.Vector(0.0, width + eave_overhang,
                            wall_height - eave_overhang * math.tan(pitch))
    ridge_south = App.Vector(0.0, half_span - ridge_width / 2.0, ridge_height)
    ridge_north = App.Vector(0.0, half_span + ridge_width / 2.0, ridge_height)

    count = max(2, math.ceil((roof_length - rafter_width) / rafter_spacing) + 1)
    offsets = sorted({
        min(index * rafter_spacing, roof_length - rafter_width)
        for index in range(count)
    })

    for index, offset in enumerate(offsets):
        x = x_start + offset
        for side, start, end in (
            ("South", south_eave, ridge_south),
            ("North", north_eave, ridge_north),
        ):
            start_point = App.Vector(x, start.y, start.z)
            end_point = App.Vector(x, end.y, end.z)
            rafter = _feature(
                document,
                f"Rafter_{side}_{index:02d}",
                f"Sparren {side} {index + 1}",
                _beam_between(start_point, end_point, rafter_width, rafter_depth),
                "KVH C24",
                (0.76, 0.56, 0.32),
            )
            rafter.addProperty("App::PropertyLength", "Spacing", "Dach")
            rafter.addProperty("App::PropertyAngle", "Pitch", "Dach")
            rafter.Spacing = rafter_spacing
            rafter.Pitch = pitch_deg
            group.addObject(rafter)

    ridge = _feature(
        document,
        "RidgeBeam",
        "Firstbalken",
        Part.makeBox(roof_length, ridge_width, ridge_depth,
                     App.Vector(x_start, half_span - ridge_width / 2.0,
                                ridge_height - ridge_depth)),
        "KVH C24",
        (0.76, 0.56, 0.32),
    )
    ridge.addProperty("App::PropertyLength", "RidgeHeight", "Dach")
    ridge.RidgeHeight = ridge_height
    group.addObject(ridge)

    south_cover = _feature(
        document,
        "RoofCover_South",
        "Dachdeckung Süd",
        _roof_panel_shape(
            roof_length=roof_length,
            start_y=south_eave.y,
            start_z=south_eave.z + rafter_depth,
            end_y=half_span,
            end_z=ridge_height + rafter_depth,
            thickness=cover_thickness,
            x_start=x_start,
        ),
        "Dachdeckung",
        (0.28, 0.30, 0.32),
    )
    south_cover.addProperty("App::PropertyAngle", "Pitch", "Dach")
    south_cover.Pitch = pitch_deg
    group.addObject(south_cover)

    north_cover = _feature(
        document,
        "RoofCover_North",
        "Dachdeckung Nord",
        _roof_panel_shape(
            roof_length=roof_length,
            start_y=north_eave.y,
            start_z=north_eave.z + rafter_depth,
            end_y=half_span,
            end_z=ridge_height + rafter_depth,
            thickness=cover_thickness,
            x_start=x_start,
        ),
        "Dachdeckung",
        (0.28, 0.30, 0.32),
    )
    north_cover.addProperty("App::PropertyAngle", "Pitch", "Dach")
    north_cover.Pitch = pitch_deg
    group.addObject(north_cover)

    return group
