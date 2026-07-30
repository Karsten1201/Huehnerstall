"""Geschlossene Gebäudehülle für das Stallmodell."""

from __future__ import annotations

import math

import FreeCAD as App
import Part


def _feature(doc, group, name, label, shape, color):
    obj = doc.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape
    group.addObject(obj)
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
    return obj


def _cut_openings(panel, openings, y, depth):
    result = panel
    for x, width, z, height in openings:
        cutter = Part.makeBox(width, depth + 4.0, height, App.Vector(x, y - 2.0, z))
        result = result.cut(cutter)
    return result


def _gable_shape(x, thickness, width, wall_height, ridge_height):
    points = [
        App.Vector(x, 0.0, 0.0),
        App.Vector(x, width, 0.0),
        App.Vector(x, width, wall_height),
        App.Vector(x, width / 2.0, ridge_height),
        App.Vector(x, 0.0, wall_height),
        App.Vector(x, 0.0, 0.0),
    ]
    wire = Part.makePolygon(points)
    face = Part.Face(wire)
    return face.extrude(App.Vector(thickness, 0.0, 0.0))


def create_building_envelope(
    doc,
    *,
    length,
    width,
    wall_height,
    pitch_deg,
    stud_depth,
    cladding_thickness,
    floor_thickness,
    door_x,
    door_width,
    door_height,
    window_x,
    window_width,
    window_height,
    window_sill_height,
    flap_x,
    flap_width,
    flap_height,
):
    """Erzeugt Boden, geschlossene Fassaden und Giebelverkleidungen."""
    group = doc.addObject("App::DocumentObjectGroup", "BuildingEnvelope")
    group.Label = "Gebäudehülle"

    timber = (0.72, 0.50, 0.28)
    inner = (0.84, 0.78, 0.65)

    floor = Part.makeBox(
        length - 2.0 * stud_depth,
        width - 2.0 * stud_depth,
        floor_thickness,
        App.Vector(stud_depth, stud_depth, 0.0),
    )
    _feature(doc, group, "FinishedFloor", "Fertiger Stallboden", floor, inner)

    south_y = -cladding_thickness
    south = Part.makeBox(length, cladding_thickness, wall_height, App.Vector(0.0, south_y, 0.0))
    south = _cut_openings(
        south,
        (
            (flap_x, flap_width, 0.0, flap_height),
            (door_x, door_width, 0.0, door_height),
            (window_x, window_width, window_sill_height, window_height),
        ),
        south_y,
        cladding_thickness,
    )
    _feature(doc, group, "SouthCladding", "Südfassade", south, timber)

    north = Part.makeBox(
        length,
        cladding_thickness,
        wall_height,
        App.Vector(0.0, width, 0.0),
    )
    _feature(doc, group, "NorthCladding", "Nordfassade", north, timber)

    ridge_height = wall_height + (width / 2.0) * math.tan(math.radians(pitch_deg))
    west = _gable_shape(-cladding_thickness, cladding_thickness, width, wall_height, ridge_height)
    east = _gable_shape(length, cladding_thickness, width, wall_height, ridge_height)
    _feature(doc, group, "WestGableCladding", "Westgiebel", west, timber)
    _feature(doc, group, "EastGableCladding", "Ostgiebel", east, timber)

    return group
