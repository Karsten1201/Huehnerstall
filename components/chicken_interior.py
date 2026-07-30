"""FreeCAD-Bauteile für den Innenausbau des Hühnerstalls."""

from __future__ import annotations

import FreeCAD as App
import Part

from config import parameters as p


def _add_box(doc, name: str, length: float, width: float, height: float,
             x: float, y: float, z: float, label: str):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = Part.makeBox(length, width, height, App.Vector(x, y, z))
    return obj


def build_roosts(doc, origin_x: float = 3500, origin_y: float = 250,
                 origin_z: float = 0):
    """Erzeugt vier demontierbare Sitzstangen an der Nordseite."""
    group = doc.addObject("App::DocumentObjectGroup", "ChickenRoosts")
    group.Label = "Hühnerstall – Sitzstangen"

    for index in range(p.ROOST_COUNT):
        y = origin_y + index * p.ROOST_SPACING
        obj = _add_box(
            doc,
            f"Roost_{index + 1:02d}",
            p.ROOST_LENGTH,
            p.ROOST_WIDTH,
            p.ROOST_HEIGHT,
            origin_x + 150,
            y,
            origin_z + p.ROOST_BASE_HEIGHT,
            f"Sitzstange {index + 1}",
        )
        group.addObject(obj)

    return group


def build_droppings_board(doc, origin_x: float = 3500,
                          origin_y: float = 180, origin_z: float = 600):
    """Erzeugt das Kotbrett unterhalb der Sitzstangen."""
    return _add_box(
        doc,
        "DroppingsBoard",
        p.DROPPINGS_BOARD_LENGTH,
        p.DROPPINGS_BOARD_DEPTH,
        p.DROPPINGS_BOARD_THICKNESS,
        origin_x + 150,
        origin_y,
        origin_z,
        "Kotbrett 21 mm Siebdruckplatte",
    )


def build_nesting_boxes(doc, origin_x: float = 3500,
                        origin_y: float = 4450, origin_z: float = 400):
    """Erzeugt zwölf Legenester als vereinfachte Volumenkörper."""
    group = doc.addObject("App::DocumentObjectGroup", "NestingBoxes")
    group.Label = "Hühnerstall – Legenester"

    for row in range(p.NEST_ROWS):
        for column in range(p.NEST_COLUMNS):
            index = row * p.NEST_COLUMNS + column + 1
            x = origin_x + 250 + column * p.NEST_WIDTH
            z = origin_z + row * p.NEST_HEIGHT
            obj = _add_box(
                doc,
                f"Nest_{index:02d}",
                p.NEST_WIDTH,
                p.NEST_DEPTH,
                p.NEST_HEIGHT,
                x,
                origin_y,
                z,
                f"Legenest {index}",
            )
            group.addObject(obj)

    return group


def build_dust_bath(doc, origin_x: float = 3700,
                    origin_y: float = 3300, origin_z: float = 0):
    """Erzeugt die äußere Staubbadwanne als vereinfachten Körper."""
    return _add_box(
        doc,
        "DustBath",
        p.DUST_BATH_WIDTH,
        p.DUST_BATH_DEPTH,
        p.DUST_BATH_HEIGHT,
        origin_x,
        origin_y,
        origin_z,
        "Staubbad",
    )


def build_chicken_interior(doc):
    """Erzeugt den vollständigen parametrischen Hühnerstall-Innenausbau."""
    group = doc.addObject("App::DocumentObjectGroup", "ChickenInterior")
    group.Label = "Innenausbau Hühnerstall"

    roosts = build_roosts(doc)
    board = build_droppings_board(doc)
    nests = build_nesting_boxes(doc)
    dust_bath = build_dust_bath(doc)

    group.addObject(roosts)
    group.addObject(board)
    group.addObject(nests)
    group.addObject(dust_bath)
    return group
