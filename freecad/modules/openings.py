"""Detaillierte Türen, Fenster und Tierklappen für die Südwand."""

from __future__ import annotations

import FreeCAD as App
import Part


def _set_color(obj, color, transparency=0):
    view = getattr(obj, "ViewObject", None)
    if view is not None:
        view.ShapeColor = color
        try:
            view.Transparency = transparency
        except Exception:
            pass


def _feature(document, group, name, label, shape, *, material, color, transparency=0):
    obj = document.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Material", "Bauteil")
    obj.Material = material
    _set_color(obj, color, transparency)
    group.addObject(obj)
    return obj


def _box(document, group, name, label, x, y, z, dx, dy, dz, *, material, color,
         transparency=0):
    if min(dx, dy, dz) <= 0:
        raise ValueError(f"Ungültige Abmessung für {name}: {(dx, dy, dz)}")
    return _feature(
        document,
        group,
        name,
        label,
        Part.makeBox(dx, dy, dz, App.Vector(x, y, z)),
        material=material,
        color=color,
        transparency=transparency,
    )


def _cylinder(document, group, name, label, radius, length, base, direction, *,
              material, color):
    if radius <= 0 or length <= 0:
        raise ValueError(f"Ungültiger Zylinder für {name}.")
    return _feature(
        document,
        group,
        name,
        label,
        Part.makeCylinder(radius, length, base, direction),
        material=material,
        color=color,
    )


def create_south_opening_elements(
    document,
    *,
    wall_y,
    wall_bottom,
    wall_depth,
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
    frame_width,
    frame_depth,
    leaf_thickness,
    glass_thickness,
    clearance,
):
    """Erzeugt detaillierte Außentür, zweiflügeliges Fenster und Tierklappe.

    Höhen der Öffnungen beziehen sich auf Oberkante Bodenplatte. ``wall_bottom``
    bleibt aus Kompatibilitätsgründen Bestandteil der Schnittstelle.
    """
    del wall_bottom

    values = (
        wall_depth, door_width, door_height, window_width, window_height,
        flap_width, flap_height, frame_width, frame_depth, leaf_thickness,
        glass_thickness,
    )
    if min(values) <= 0 or clearance < 0:
        raise ValueError("Öffnungsbauteile benötigen positive Abmessungen.")

    group = document.addObject("App::Part", "SouthOpeningElements")
    group.Label = "Türen, Fenster und Tierklappe – detailliert"

    exterior_y = wall_y - frame_depth
    wood = (0.66, 0.42, 0.20)
    leaf_color = (0.48, 0.26, 0.10)
    trim_color = (0.79, 0.63, 0.39)
    glass_color = (0.55, 0.78, 0.90)
    metal = (0.25, 0.25, 0.25)
    sill_color = (0.55, 0.57, 0.60)

    # ------------------------------------------------------------------ Tür
    door_z = 0.0
    jamb_depth = max(frame_depth, wall_depth * 0.75)
    for side, x in (("Left", door_x), ("Right", door_x + door_width - frame_width)):
        _box(document, group, f"DoorFrame_{side}", f"Türzarge {side}", x,
             wall_y - jamb_depth, door_z, frame_width, jamb_depth, door_height,
             material="KVH / Rahmenholz", color=wood)
    _box(document, group, "DoorFrame_Top", "Türzarge oben",
         door_x + frame_width, wall_y - jamb_depth, door_z + door_height - frame_width,
         door_width - 2.0 * frame_width, jamb_depth, frame_width,
         material="KVH / Rahmenholz", color=wood)

    # umlaufender äußerer Blendrahmen
    trim = max(35.0, frame_width * 0.55)
    trim_depth = 22.0
    for side, x in (("Left", door_x - trim), ("Right", door_x + door_width)):
        _box(document, group, f"DoorTrim_{side}", f"Türbekleidung {side}", x,
             exterior_y - trim_depth, door_z, trim, trim_depth, door_height + trim,
             material="Fassadenbrett", color=trim_color)
    _box(document, group, "DoorTrim_Top", "Türbekleidung oben",
         door_x, exterior_y - trim_depth, door_z + door_height,
         door_width, trim_depth, trim,
         material="Fassadenbrett", color=trim_color)

    leaf_x = door_x + frame_width + clearance
    leaf_z = door_z + clearance
    leaf_width = door_width - 2.0 * (frame_width + clearance)
    leaf_height = door_height - frame_width - 2.0 * clearance
    _box(document, group, "DoorLeaf", "Außentürblatt", leaf_x,
         exterior_y - leaf_thickness, leaf_z, leaf_width, leaf_thickness,
         leaf_height, material="Holztür", color=leaf_color)

    # Z-förmige Aufdopplung auf dem Türblatt
    brace_depth = 22.0
    brace_width = 85.0
    face_y = exterior_y - leaf_thickness - brace_depth
    for suffix, z in (("Bottom", leaf_z + 130.0), ("Top", leaf_z + leaf_height - 215.0)):
        _box(document, group, f"DoorBrace_{suffix}", f"Türquerleiste {suffix}",
             leaf_x + 55.0, face_y, z, leaf_width - 110.0, brace_depth, brace_width,
             material="Rahmenholz", color=trim_color)

    diagonal_length = max(100.0, leaf_height - 430.0)
    diagonal = Part.makeBox(brace_width, brace_depth, diagonal_length)
    diagonal.Placement = App.Placement(
        App.Vector(leaf_x + 95.0, face_y, leaf_z + 210.0),
        App.Rotation(App.Vector(0, 1, 0), -math_degrees_atan((leaf_width - 190.0) / diagonal_length)),
    )
    _feature(document, group, "DoorBrace_Diagonal", "Türdiagonalstrebe", diagonal,
             material="Rahmenholz", color=trim_color)

    for index, z in enumerate((330.0, door_height - 520.0), start=1):
        _box(document, group, f"DoorHinge_{index}", f"Türband {index}",
             door_x + frame_width - 15.0, face_y - 5.0, z,
             135.0, 8.0, 55.0, material="Stahl verzinkt", color=metal)
        _cylinder(document, group, f"DoorHingePin_{index}", f"Türbandbolzen {index}",
                  10.0, 90.0,
                  App.Vector(door_x + frame_width - 18.0, face_y - 8.0, z - 18.0),
                  App.Vector(0, 0, 1), material="Stahl verzinkt", color=metal)

    handle_z = min(1050.0, door_height * 0.52)
    handle_x = leaf_x + leaf_width - 125.0
    _box(document, group, "DoorHandlePlate", "Türdrückerschild",
         handle_x - 30.0, face_y - 5.0, handle_z - 95.0,
         60.0, 8.0, 190.0, material="Stahl", color=metal)
    _cylinder(document, group, "DoorHandle", "Türdrücker", 12.0, 105.0,
              App.Vector(handle_x, face_y - 10.0, handle_z), App.Vector(-1, 0, 0),
              material="Stahl", color=metal)
    _box(document, group, "DoorThreshold", "Türschwelle", door_x,
         wall_y - wall_depth, 0.0, door_width, wall_depth + frame_depth, 28.0,
         material="Aluminium", color=sill_color)

    # -------------------------------------------------------------- Fenster
    window_z = window_sill_height
    frame_parts = (
        ("Left", window_x, window_z, frame_width, window_height),
        ("Right", window_x + window_width - frame_width, window_z, frame_width, window_height),
        ("Bottom", window_x + frame_width, window_z,
         window_width - 2.0 * frame_width, frame_width),
        ("Top", window_x + frame_width, window_z + window_height - frame_width,
         window_width - 2.0 * frame_width, frame_width),
    )
    for name, x, z, dx, dz in frame_parts:
        _box(document, group, f"WindowFrame_{name}", f"Fenster-Blendrahmen {name}",
             x, exterior_y, z, dx, frame_depth, dz,
             material="Holzfensterrahmen", color=wood)

    mullion_x = window_x + window_width / 2.0 - frame_width / 2.0
    _box(document, group, "WindowMullion", "Fenster-Mittelpfosten", mullion_x,
         exterior_y - 2.0, window_z + frame_width, frame_width, frame_depth + 4.0,
         window_height - 2.0 * frame_width,
         material="Holzfensterrahmen", color=wood)

    # zwei eingelassene Flügelrahmen
    sash_width = max(28.0, frame_width * 0.55)
    sash_depth = max(22.0, frame_depth * 0.45)
    clear_left = window_x + frame_width
    clear_right = window_x + window_width - frame_width
    half_gap = 4.0
    openings = (
        ("Left", clear_left + clearance, mullion_x - half_gap),
        ("Right", mullion_x + frame_width + half_gap, clear_right - clearance),
    )
    pane_z = window_z + frame_width + sash_width
    pane_height = window_height - 2.0 * (frame_width + sash_width)
    sash_y = exterior_y - sash_depth - 3.0
    for side, x1, x2 in openings:
        clear_w = x2 - x1
        for name, x, z, dx, dz in (
            ("Left", x1, window_z + frame_width, sash_width, window_height - 2.0 * frame_width),
            ("Right", x2 - sash_width, window_z + frame_width, sash_width, window_height - 2.0 * frame_width),
            ("Bottom", x1 + sash_width, window_z + frame_width,
             clear_w - 2.0 * sash_width, sash_width),
            ("Top", x1 + sash_width, window_z + window_height - frame_width - sash_width,
             clear_w - 2.0 * sash_width, sash_width),
        ):
            _box(document, group, f"WindowSash_{side}_{name}",
                 f"Fensterflügel {side} {name}", x, sash_y, z, dx, sash_depth, dz,
                 material="Holzfensterflügel", color=trim_color)
        pane_width = clear_w - 2.0 * sash_width
        _box(document, group, f"WindowGlass_{side}", f"Isolierglasscheibe {side}",
             x1 + sash_width, sash_y - glass_thickness + 2.0, pane_z,
             pane_width, glass_thickness, pane_height,
             material="Isolierglas", color=glass_color, transparency=65)

    sill_projection = 90.0
    _box(document, group, "WindowSill", "Außenfensterbank",
         window_x - 25.0, exterior_y - sill_projection,
         window_z - 32.0, window_width + 50.0, sill_projection + frame_depth, 32.0,
         material="Aluminium beschichtet", color=sill_color)

    # ----------------------------------------------------------- Tierklappe
    flap_z = 0.0
    for side, x in (("Left", flap_x), ("Right", flap_x + flap_width - frame_width)):
        _box(document, group, f"FlapFrame_{side}", f"Tierklappenrahmen {side}", x,
             exterior_y, flap_z, frame_width, frame_depth, flap_height,
             material="Rahmenholz", color=wood)
    _box(document, group, "FlapFrame_Top", "Tierklappenrahmen oben",
         flap_x + frame_width, exterior_y, flap_z + flap_height - frame_width,
         flap_width - 2.0 * frame_width, frame_depth, frame_width,
         material="Rahmenholz", color=wood)

    flap_leaf_x = flap_x + frame_width + clearance
    flap_leaf_width = flap_width - 2.0 * (frame_width + clearance)
    flap_leaf_height = flap_height - frame_width - 2.0 * clearance
    _box(document, group, "AnimalFlapLeaf", "Tierklappenblatt", flap_leaf_x,
         exterior_y - leaf_thickness, flap_z + clearance, flap_leaf_width,
         leaf_thickness, flap_leaf_height,
         material="Siebdruckplatte", color=leaf_color)

    hinge_z = flap_z + flap_height - frame_width - 35.0
    for index, x in enumerate((flap_leaf_x + 55.0,
                               flap_leaf_x + flap_leaf_width - 95.0), start=1):
        _box(document, group, f"FlapHinge_{index}", f"Tierklappenscharnier {index}",
             x, exterior_y - leaf_thickness - 7.0, hinge_z,
             40.0, 7.0, 70.0, material="Edelstahl", color=metal)

    ramp_length = 700.0
    ramp_width = flap_width - 2.0 * frame_width
    ramp_thickness = 24.0
    ramp_angle = -8.0
    ramp = Part.makeBox(ramp_width, ramp_length, ramp_thickness)
    ramp.Placement = App.Placement(
        App.Vector(flap_x + frame_width, exterior_y - ramp_length, -ramp_thickness),
        App.Rotation(App.Vector(1, 0, 0), ramp_angle),
    )
    _feature(document, group, "AnimalRamp", "Außenrampe Tierklappe", ramp,
             material="Siebdruckplatte", color=leaf_color)

    for index in range(1, 6):
        y = exterior_y - ramp_length + index * ramp_length / 6.0
        cleat = Part.makeBox(ramp_width, 28.0, 24.0,
                            App.Vector(flap_x + frame_width, y, -4.0))
        cleat.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), ramp_angle)
        _feature(document, group, f"RampCleat_{index}", f"Rampensprosse {index}",
                 cleat, material="Hartholz", color=trim_color)

    return group


def math_degrees_atan(value):
    """Kleine lokale Hilfsfunktion ohne zusätzliche Modulabhängigkeiten."""
    import math
    return math.degrees(math.atan(value))
