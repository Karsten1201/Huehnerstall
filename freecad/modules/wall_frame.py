"""KVH-Wandrahmen für FreeCAD."""

from __future__ import annotations

import math
import FreeCAD as App
import Part


def _beam(document, name, label, x, y, z, dx, dy, dz):
    obj = document.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = Part.makeBox(dx, dy, dz, App.Vector(x, y, z))
    obj.addProperty("App::PropertyString", "Material", "Bauteil")
    obj.Material = "KVH C24"
    obj.ViewObject.ShapeColor = (0.76, 0.56, 0.32)
    return obj


def create_wall_frame(document, *, name, origin, length, height,
                      stud_width, stud_depth, spacing, direction="x"):
    """Erzeugt Schwelle, Rähm und Ständer einer geraden Holzrahmenwand."""
    if min(length, height, stud_width, stud_depth, spacing) <= 0:
        raise ValueError("Wandparameter müssen größer als null sein.")
    group = document.addObject("App::Part", name)
    group.Label = name
    ox, oy, oz = origin
    horizontal = direction.lower() == "x"
    if direction.lower() not in {"x", "y"}:
        raise ValueError("direction muss 'x' oder 'y' sein.")

    if horizontal:
        group.addObject(_beam(document, f"{name}_Bottom", "Schwelle", ox, oy, oz,
                              length, stud_depth, stud_width))
        group.addObject(_beam(document, f"{name}_Top", "Rähm", ox, oy,
                              oz + height - stud_width, length, stud_depth, stud_width))
    else:
        group.addObject(_beam(document, f"{name}_Bottom", "Schwelle", ox, oy, oz,
                              stud_depth, length, stud_width))
        group.addObject(_beam(document, f"{name}_Top", "Rähm", ox, oy,
                              oz + height - stud_width, stud_depth, length, stud_width))

    count = max(2, math.ceil((length - stud_width) / spacing) + 1)
    clear_height = height - 2.0 * stud_width
    for index in range(count):
        offset = min(index * spacing, length - stud_width)
        if horizontal:
            beam = _beam(document, f"{name}_Stud_{index:02d}", f"Ständer {index + 1}",
                         ox + offset, oy, oz + stud_width,
                         stud_width, stud_depth, clear_height)
        else:
            beam = _beam(document, f"{name}_Stud_{index:02d}", f"Ständer {index + 1}",
                         ox, oy + offset, oz + stud_width,
                         stud_depth, stud_width, clear_height)
        group.addObject(beam)
    return group
