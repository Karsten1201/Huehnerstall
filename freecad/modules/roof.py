"""Parametrisches Satteldach mit Tragwerk, Lattung, Blechdeckung und Entwässerung."""

from __future__ import annotations

import math

import FreeCAD as App
import Part


def _set_color(obj, color):
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color


def _feature(document, group, name, label, shape, material, color):
    obj = document.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Material", "Bauteil")
    obj.Material = material
    _set_color(obj, color)
    group.addObject(obj)
    return obj


def _beam_between(start, end, width, depth):
    """Erzeugt einen prismatischen Balken zwischen zwei 3D-Punkten."""
    direction = end.sub(start)
    length = direction.Length
    if length <= 0:
        raise ValueError("Balkenlänge muss größer als null sein.")
    shape = Part.makeBox(width, depth, length)
    rotation = App.Rotation(App.Vector(0, 0, 1), direction)
    shape.Placement = App.Placement(start, rotation)
    return shape


def _sloped_panel(y0, z0, y1, z1, thickness, x0, x_length):
    """Erzeugt eine geneigte Platte als entlang X extrudiertes YZ-Profil."""
    dy = y1 - y0
    dz = z1 - z0
    length = math.hypot(dy, dz)
    ny = -dz / length
    nz = dy / length
    points = [
        App.Vector(x0, y0, z0),
        App.Vector(x0, y1, z1),
        App.Vector(x0, y1 + ny * thickness, z1 + nz * thickness),
        App.Vector(x0, y0 + ny * thickness, z0 + nz * thickness),
        App.Vector(x0, y0, z0),
    ]
    return Part.Face(Part.makePolygon(points)).extrude(App.Vector(x_length, 0, 0))


def _ridge_cap(x0, length, ridge_y, ridge_z, half_width, height):
    points = [
        App.Vector(x0, ridge_y - half_width, ridge_z),
        App.Vector(x0, ridge_y, ridge_z + height),
        App.Vector(x0, ridge_y + half_width, ridge_z),
        App.Vector(x0, ridge_y + half_width - 35.0, ridge_z - 20.0),
        App.Vector(x0, ridge_y, ridge_z + height - 35.0),
        App.Vector(x0, ridge_y - half_width + 35.0, ridge_z - 20.0),
        App.Vector(x0, ridge_y - half_width, ridge_z),
    ]
    return Part.Face(Part.makePolygon(points)).extrude(App.Vector(length, 0, 0))


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
    """Erzeugt einen vollständigen symmetrischen Satteldachaufbau."""
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
    if pitch_deg >= 60:
        raise ValueError("Die Dachneigung muss kleiner als 60 Grad sein.")
    if eave_overhang < 0 or gable_overhang < 0:
        raise ValueError("Dachüberstände dürfen nicht negativ sein.")

    group = document.addObject("App::Part", "Roof")
    group.Label = "Satteldach komplett"

    timber = (0.76, 0.56, 0.32)
    batten_color = (0.68, 0.47, 0.26)
    membrane_color = (0.35, 0.38, 0.42)
    metal_color = (0.22, 0.24, 0.27)
    gutter_color = (0.32, 0.34, 0.36)

    pitch = math.radians(pitch_deg)
    half_span = width / 2.0
    ridge_y = half_span
    ridge_z = wall_height + half_span * math.tan(pitch)
    eave_drop = eave_overhang * math.tan(pitch)
    south_eave = App.Vector(0, -eave_overhang, wall_height - eave_drop)
    north_eave = App.Vector(0, width + eave_overhang, wall_height - eave_drop)
    south_ridge = App.Vector(0, ridge_y, ridge_z)
    north_ridge = App.Vector(0, ridge_y, ridge_z)
    roof_length = length + 2.0 * gable_overhang
    x0 = -gable_overhang

    # Firstpfette
    ridge = _feature(
        document,
        group,
        "RidgeBeam",
        "Firstpfette",
        Part.makeBox(roof_length, ridge_width, ridge_depth,
                     App.Vector(x0, ridge_y - ridge_width / 2.0, ridge_z - ridge_depth)),
        "KVH C24",
        timber,
    )
    ridge.addProperty("App::PropertyLength", "RidgeHeight", "Dach")
    ridge.RidgeHeight = ridge_z

    # Sparren und Konterlatten
    count = max(2, math.ceil((roof_length - rafter_width) / rafter_spacing) + 1)
    offsets = sorted({min(i * rafter_spacing, roof_length - rafter_width) for i in range(count)})
    counter_width = 40.0
    counter_depth = 60.0

    for index, offset in enumerate(offsets):
        x = x0 + offset
        for side, eave, ridge_point in (
            ("South", south_eave, south_ridge),
            ("North", north_eave, north_ridge),
        ):
            start = App.Vector(x, eave.y, eave.z)
            end = App.Vector(x, ridge_point.y, ridge_point.z)
            rafter = _feature(
                document,
                group,
                f"Rafter_{side}_{index:02d}",
                f"Sparren {side} {index + 1}",
                _beam_between(start, end, rafter_width, rafter_depth),
                "KVH C24",
                timber,
            )
            rafter.addProperty("App::PropertyLength", "Spacing", "Dach")
            rafter.Spacing = rafter_spacing

            direction = end.sub(start)
            unit = direction.normalize()
            counter_start = start.add(App.Vector(0, 0, rafter_depth))
            counter_end = end.add(App.Vector(0, 0, rafter_depth))
            _feature(
                document,
                group,
                f"CounterBatten_{side}_{index:02d}",
                f"Konterlatte {side} {index + 1}",
                _beam_between(counter_start, counter_end, counter_width, counter_depth),
                "Konterlatte 40x60",
                batten_color,
            )

    # Unterspannbahn als durchgehende Dachflächen
    underlay_offset = rafter_depth + counter_depth
    south_underlay = _sloped_panel(
        south_eave.y,
        south_eave.z + underlay_offset,
        ridge_y,
        ridge_z + underlay_offset,
        2.0,
        x0,
        roof_length,
    )
    north_underlay = _sloped_panel(
        ridge_y,
        ridge_z + underlay_offset,
        north_eave.y,
        north_eave.z + underlay_offset,
        2.0,
        x0,
        roof_length,
    )
    _feature(document, group, "UnderlaySouth", "Unterspannbahn Süd", south_underlay,
             "Unterspannbahn", membrane_color)
    _feature(document, group, "UnderlayNorth", "Unterspannbahn Nord", north_underlay,
             "Unterspannbahn", membrane_color)

    # Dachlatten quer zur Dachneigung
    batten_width = 50.0
    batten_height = 30.0
    batten_spacing = 350.0
    slope_run = half_span + eave_overhang
    slope_length = slope_run / math.cos(pitch)
    batten_count = max(2, math.floor(slope_length / batten_spacing) + 1)

    for side, y_start, sign in (
        ("South", -eave_overhang, 1.0),
        ("North", width + eave_overhang, -1.0),
    ):
        for index in range(batten_count + 1):
            distance = min(index * batten_spacing, slope_length)
            horizontal = distance * math.cos(pitch)
            vertical = distance * math.sin(pitch)
            y = y_start + sign * horizontal
            z = wall_height - eave_drop + vertical + underlay_offset
            shape = Part.makeBox(roof_length, batten_width, batten_height,
                                 App.Vector(x0, y - batten_width / 2.0, z))
            _feature(
                document,
                group,
                f"RoofBatten_{side}_{index:02d}",
                f"Dachlatte {side} {index + 1}",
                shape,
                "Dachlatte 30x50",
                batten_color,
            )

    # Trapezbleche als einzelne Bahnen von Traufe bis First
    sheet_effective_width = 1000.0
    sheet_count = math.ceil(roof_length / sheet_effective_width)
    cover_offset = underlay_offset + batten_height
    for index in range(sheet_count):
        sheet_x = x0 + index * sheet_effective_width
        sheet_width = min(sheet_effective_width, x0 + roof_length - sheet_x)
        south_sheet = _sloped_panel(
            south_eave.y,
            south_eave.z + cover_offset,
            ridge_y,
            ridge_z + cover_offset,
            cover_thickness,
            sheet_x,
            sheet_width,
        )
        north_sheet = _sloped_panel(
            ridge_y,
            ridge_z + cover_offset,
            north_eave.y,
            north_eave.z + cover_offset,
            cover_thickness,
            sheet_x,
            sheet_width,
        )
        _feature(document, group, f"RoofSheetSouth_{index:02d}",
                 f"Trapezblech Süd {index + 1}", south_sheet,
                 "Trapezblech", metal_color)
        _feature(document, group, f"RoofSheetNorth_{index:02d}",
                 f"Trapezblech Nord {index + 1}", north_sheet,
                 "Trapezblech", metal_color)

    # First- und Traufabschlüsse
    ridge_cap = _ridge_cap(
        x0,
        roof_length,
        ridge_y,
        ridge_z + cover_offset + cover_thickness,
        220.0,
        110.0,
    )
    _feature(document, group, "RidgeCap", "Firstblech", ridge_cap,
             "Stahlblech beschichtet", metal_color)

    for side, y in (("South", south_eave.y), ("North", north_eave.y)):
        z = south_eave.z + cover_offset - 20.0
        drip = Part.makeBox(roof_length, 80.0, 40.0,
                            App.Vector(x0, y - 40.0, z))
        _feature(document, group, f"EaveFlashing{side}", f"Traufblech {side}",
                 drip, "Stahlblech beschichtet", metal_color)

    # Dachrinnen und zwei Fallrohre
    gutter_radius = 75.0
    for side, y in (("South", south_eave.y - 85.0), ("North", north_eave.y + 85.0)):
        gutter = Part.makeCylinder(
            gutter_radius,
            roof_length,
            App.Vector(x0, y, south_eave.z + cover_offset - 65.0),
            App.Vector(1, 0, 0),
            180.0,
        )
        _feature(document, group, f"Gutter{side}", f"Dachrinne {side}", gutter,
                 "Stahl verzinkt", gutter_color)

    pipe_radius = 45.0
    for side, x, y in (
        ("SouthWest", x0 + 120.0, south_eave.y - 85.0),
        ("NorthEast", x0 + roof_length - 120.0, north_eave.y + 85.0),
    ):
        pipe = Part.makeCylinder(
            pipe_radius,
            wall_height,
            App.Vector(x, y, 0.0),
            App.Vector(0, 0, 1),
        )
        _feature(document, group, f"Downpipe{side}", f"Fallrohr {side}", pipe,
                 "Stahl verzinkt", gutter_color)

    return group
