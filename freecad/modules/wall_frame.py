"""KVH-Wandrahmen für FreeCAD mit Tür-, Fenster- und Klappenöffnungen."""

from __future__ import annotations

import math
from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Opening:
    """Rechteckige Öffnung, gemessen ab Wandanfang und Oberkante Schwelle."""

    name: str
    offset: float
    width: float
    height: float
    sill_height: float = 0.0

    @property
    def end(self) -> float:
        return self.offset + self.width


def _beam(document, name, label, x, y, z, dx, dy, dz):
    if min(dx, dy, dz) <= 0:
        raise ValueError(f"Ungültige Balkenabmessung für {name}: {(dx, dy, dz)}")
    obj = document.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = Part.makeBox(dx, dy, dz, App.Vector(x, y, z))
    obj.addProperty("App::PropertyString", "Material", "Bauteil")
    obj.Material = "KVH C24"
    obj.ViewObject.ShapeColor = (0.76, 0.56, 0.32)
    return obj


def _add_longitudinal_beam(document, group, *, name, label, origin, direction,
                           offset, z, length, stud_width, stud_depth):
    ox, oy, oz = origin
    if direction == "x":
        beam = _beam(document, name, label, ox + offset, oy, oz + z,
                     length, stud_depth, stud_width)
    else:
        beam = _beam(document, name, label, ox, oy + offset, oz + z,
                     stud_depth, length, stud_width)
    group.addObject(beam)
    return beam


def _add_stud(document, group, *, name, label, origin, direction, offset,
              bottom, height, stud_width, stud_depth):
    ox, oy, oz = origin
    if direction == "x":
        beam = _beam(document, name, label, ox + offset, oy, oz + bottom,
                     stud_width, stud_depth, height)
    else:
        beam = _beam(document, name, label, ox, oy + offset, oz + bottom,
                     stud_depth, stud_width, height)
    group.addObject(beam)
    return beam


def _validate_openings(openings, *, length, height, stud_width):
    ordered = sorted(openings, key=lambda opening: opening.offset)
    previous_end = 0.0
    for opening in ordered:
        if min(opening.offset, opening.width, opening.height, opening.sill_height) < 0:
            raise ValueError(f"Negative Öffnungsangabe: {opening.name}")
        if opening.width <= 0 or opening.height <= 0:
            raise ValueError(f"Öffnung muss positive Abmessungen haben: {opening.name}")
        if opening.offset < stud_width or opening.end > length - stud_width:
            raise ValueError(f"Öffnung {opening.name} liegt außerhalb des Wandfeldes.")
        if opening.sill_height + opening.height > height - 2.0 * stud_width:
            raise ValueError(f"Öffnung {opening.name} ist höher als das verfügbare Wandfeld.")
        if opening.offset < previous_end:
            raise ValueError(f"Öffnungen überlappen bei {opening.name}.")
        previous_end = opening.end
    return ordered


def create_wall_frame(document, *, name, origin, length, height,
                      stud_width, stud_depth, spacing, direction="x",
                      openings=()):
    """Erzeugt einen Holzrahmen mit automatisch gerahmten Öffnungen."""
    if min(length, height, stud_width, stud_depth, spacing) <= 0:
        raise ValueError("Wandparameter müssen größer als null sein.")
    direction = direction.lower()
    if direction not in {"x", "y"}:
        raise ValueError("direction muss 'x' oder 'y' sein.")

    normalized = [item if isinstance(item, Opening) else Opening(**item) for item in openings]
    normalized = _validate_openings(normalized, length=length, height=height,
                                    stud_width=stud_width)

    group = document.addObject("App::Part", name)
    group.Label = name

    _add_longitudinal_beam(document, group, name=f"{name}_Bottom", label="Schwelle",
                           origin=origin, direction=direction, offset=0.0, z=0.0,
                           length=length, stud_width=stud_width, stud_depth=stud_depth)
    _add_longitudinal_beam(document, group, name=f"{name}_Top", label="Rähm",
                           origin=origin, direction=direction, offset=0.0,
                           z=height - stud_width, length=length,
                           stud_width=stud_width, stud_depth=stud_depth)

    clear_bottom = stud_width
    clear_top = height - stud_width
    count = max(2, math.ceil((length - stud_width) / spacing) + 1)
    regular_offsets = {min(index * spacing, length - stud_width) for index in range(count)}

    for opening in normalized:
        regular_offsets = {
            offset for offset in regular_offsets
            if offset + stud_width <= opening.offset or offset >= opening.end
        }

    for index, offset in enumerate(sorted(regular_offsets)):
        _add_stud(document, group, name=f"{name}_Stud_{index:02d}",
                  label=f"Ständer {index + 1}", origin=origin, direction=direction,
                  offset=offset, bottom=clear_bottom,
                  height=clear_top - clear_bottom,
                  stud_width=stud_width, stud_depth=stud_depth)

    for index, opening in enumerate(normalized):
        left = opening.offset - stud_width
        right = opening.end
        header_z = clear_bottom + opening.sill_height + opening.height

        for side, offset in (("L", left), ("R", right)):
            _add_stud(document, group,
                      name=f"{name}_{opening.name}_King_{side}",
                      label=f"{opening.name} Königsständer {side}",
                      origin=origin, direction=direction, offset=offset,
                      bottom=clear_bottom, height=clear_top - clear_bottom,
                      stud_width=stud_width, stud_depth=stud_depth)

            jack_height = opening.sill_height + opening.height
            _add_stud(document, group,
                      name=f"{name}_{opening.name}_Jack_{side}",
                      label=f"{opening.name} Wechselständer {side}",
                      origin=origin, direction=direction,
                      offset=offset + (stud_width if side == "L" else -stud_width),
                      bottom=clear_bottom, height=jack_height,
                      stud_width=stud_width, stud_depth=stud_depth)

        _add_longitudinal_beam(document, group,
                               name=f"{name}_{opening.name}_Header",
                               label=f"{opening.name} Sturz", origin=origin,
                               direction=direction, offset=opening.offset,
                               z=header_z, length=opening.width,
                               stud_width=stud_width, stud_depth=stud_depth)

        if opening.sill_height > 0:
            _add_longitudinal_beam(document, group,
                                   name=f"{name}_{opening.name}_Sill",
                                   label=f"{opening.name} Brüstung", origin=origin,
                                   direction=direction, offset=opening.offset,
                                   z=clear_bottom + opening.sill_height - stud_width,
                                   length=opening.width, stud_width=stud_width,
                                   stud_depth=stud_depth)

            cripple_height = opening.sill_height - stud_width
            if cripple_height > 0:
                cripple_count = max(1, math.floor(opening.width / spacing))
                for cripple_index in range(1, cripple_count + 1):
                    local = opening.offset + min(cripple_index * spacing,
                                                 opening.width - stud_width)
                    _add_stud(document, group,
                              name=f"{name}_{opening.name}_Cripple_{cripple_index:02d}",
                              label=f"{opening.name} Brüstungsständer {cripple_index}",
                              origin=origin, direction=direction, offset=local,
                              bottom=clear_bottom, height=cripple_height,
                              stud_width=stud_width, stud_depth=stud_depth)

    return group
