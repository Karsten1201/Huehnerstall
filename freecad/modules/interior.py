"""Parametrische Inneneinrichtung für den Hühner- und Gänsestall."""

from __future__ import annotations

import FreeCAD as App
import Part


def _feature(document, group, name, label, shape, material, color=None):
    obj = document.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Material", "Bauteil")
    obj.Material = material
    if color is not None and obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
    group.addObject(obj)
    return obj


def create_perches(
    document,
    *,
    origin,
    count,
    length,
    diameter,
    spacing,
    first_height,
):
    """Erzeugt parallel angeordnete runde Sitzstangen mit Wandkonsolen."""
    if min(count, length, diameter, spacing, first_height) <= 0:
        raise ValueError("Sitzstangenparameter müssen größer als null sein.")

    group = document.addObject("App::Part", "Perches")
    group.Label = "Sitzstangenanlage"
    ox, oy, oz = origin

    for index in range(int(count)):
        y = oy + index * spacing
        z = oz + first_height + index * spacing * 0.35
        pole = Part.makeCylinder(
            diameter / 2.0,
            length,
            App.Vector(ox, y, z),
            App.Vector(1, 0, 0),
        )
        _feature(
            document,
            group,
            f"Perch_{index + 1:02d}",
            f"Sitzstange {index + 1}",
            pole,
            "Rundholz",
            (0.68, 0.46, 0.25),
        )

        for side, x in (("L", ox), ("R", ox + length - 40.0)):
            bracket = Part.makeBox(40.0, 80.0, z - oz, App.Vector(x, y - 40.0, oz))
            _feature(
                document,
                group,
                f"PerchBracket_{index + 1:02d}_{side}",
                f"Sitzstangenstütze {index + 1} {side}",
                bracket,
                "KVH C24",
                (0.76, 0.56, 0.32),
            )

    return group


def create_nest_boxes(
    document,
    *,
    origin,
    count,
    box_width,
    box_depth,
    box_height,
    wall_thickness,
    floor_height,
):
    """Erzeugt eine Reihe offener Legenester mit Trennwänden und Pultdach."""
    if min(count, box_width, box_depth, box_height, wall_thickness) <= 0:
        raise ValueError("Nestkastenparameter müssen größer als null sein.")
    if floor_height < 0:
        raise ValueError("Nestkasten-Bodenhöhe darf nicht negativ sein.")

    group = document.addObject("App::Part", "NestBoxes")
    group.Label = "Legenester"
    ox, oy, oz = origin
    total_width = count * box_width
    z = oz + floor_height

    floor = Part.makeBox(total_width, box_depth, wall_thickness, App.Vector(ox, oy, z))
    _feature(document, group, "NestFloor", "Nestkastenboden", floor, "Siebdruckplatte")

    back = Part.makeBox(
        total_width,
        wall_thickness,
        box_height,
        App.Vector(ox, oy + box_depth - wall_thickness, z),
    )
    _feature(document, group, "NestBack", "Nestkastenrückwand", back, "Siebdruckplatte")

    for index in range(count + 1):
        x = ox + index * box_width
        side = Part.makeBox(
            wall_thickness,
            box_depth,
            box_height,
            App.Vector(x, oy, z),
        )
        _feature(
            document,
            group,
            f"NestDivider_{index:02d}",
            f"Nestkastentrennwand {index + 1}",
            side,
            "Siebdruckplatte",
        )

    roof = Part.makeBox(
        total_width + 2.0 * wall_thickness,
        box_depth + 40.0,
        wall_thickness,
        App.Vector(ox - wall_thickness, oy - 20.0, z + box_height),
    )
    roof.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), -8.0)
    _feature(document, group, "NestRoof", "Nestkastendach", roof, "Siebdruckplatte")

    lip = Part.makeBox(
        total_width,
        wall_thickness,
        120.0,
        App.Vector(ox, oy, z),
    )
    _feature(document, group, "NestLip", "Nestkasten-Vorderkante", lip, "Siebdruckplatte")
    return group


def create_interior(document, *, partition_x, building_length, stud_depth,
                    perch_count, perch_length, perch_diameter, perch_spacing,
                    perch_height, nest_count, nest_width, nest_depth,
                    nest_height, nest_wall, nest_floor_height):
    """Erzeugt die Grundausstattung im Hühnerstallbereich östlich der Trennwand."""
    usable_start = partition_x + stud_depth + 250.0
    usable_length = building_length - usable_start - stud_depth - 250.0
    actual_perch_length = min(perch_length, usable_length)
    if actual_perch_length <= 0:
        raise ValueError("Für die Inneneinrichtung steht keine nutzbare Länge bereit.")

    group = document.addObject("App::Part", "Interior")
    group.Label = "Inneneinrichtung"

    perches = create_perches(
        document,
        origin=(usable_start, 3100.0, 0.0),
        count=perch_count,
        length=actual_perch_length,
        diameter=perch_diameter,
        spacing=perch_spacing,
        first_height=perch_height,
    )
    nests = create_nest_boxes(
        document,
        origin=(usable_start, 250.0, 0.0),
        count=nest_count,
        box_width=nest_width,
        box_depth=nest_depth,
        box_height=nest_height,
        wall_thickness=nest_wall,
        floor_height=nest_floor_height,
    )
    group.addObject(perches)
    group.addObject(nests)
    return group
