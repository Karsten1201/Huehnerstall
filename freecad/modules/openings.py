"""Türen, Fenster und Tierklappen für die Südwand."""

from __future__ import annotations

import FreeCAD as App
import Part


def _set_color(obj, color):
    """Setzt eine Farbe nur, wenn eine grafische Ansicht verfügbar ist."""
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color


def _box(document, group, name, label, x, y, z, dx, dy, dz, *, material, color):
    if min(dx, dy, dz) <= 0:
        raise ValueError(f"Ungültige Abmessung für {name}: {(dx, dy, dz)}")
    obj = document.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = Part.makeBox(dx, dy, dz, App.Vector(x, y, z))
    obj.addProperty("App::PropertyString", "Material", "Bauteil")
    obj.Material = material
    _set_color(obj, color)
    group.addObject(obj)
    return obj


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
    """Erzeugt funktionsfähige Bauteile in den Öffnungen der Südwand.

    Die Öffnungsmaße entsprechen den Rohbauöffnungen des Wandrahmens. Die
    sichtbaren Bauteile werden leicht vor die Fassadenebene gesetzt, damit sie
    im Gesamtmodell eindeutig erkennbar bleiben.
    """
    values = (
        wall_depth,
        door_width,
        door_height,
        window_width,
        window_height,
        flap_width,
        flap_height,
        frame_width,
        frame_depth,
        leaf_thickness,
        glass_thickness,
    )
    if min(values) <= 0 or clearance < 0:
        raise ValueError("Öffnungsbauteile benötigen positive Abmessungen.")

    group = document.addObject("App::Part", "SouthOpeningElements")
    group.Label = "Türen, Fenster und Tierklappe"

    exterior_y = wall_y - frame_depth
    wood = (0.66, 0.42, 0.20)
    leaf_color = (0.48, 0.26, 0.10)
    glass_color = (0.55, 0.78, 0.90)
    metal = (0.25, 0.25, 0.25)

    # Außentür: Zarge aus zwei Pfosten und oberem Querstück.
    door_z = wall_bottom
    for side, x in (("Left", door_x), ("Right", door_x + door_width - frame_width)):
        _box(
            document,
            group,
            f"DoorFrame_{side}",
            f"Türzarge {side}",
            x,
            exterior_y,
            door_z,
            frame_width,
            frame_depth,
            door_height,
            material="KVH / Rahmenholz",
            color=wood,
        )
    _box(
        document,
        group,
        "DoorFrame_Top",
        "Türzarge oben",
        door_x + frame_width,
        exterior_y,
        door_z + door_height - frame_width,
        door_width - 2.0 * frame_width,
        frame_depth,
        frame_width,
        material="KVH / Rahmenholz",
        color=wood,
    )
    leaf_x = door_x + frame_width + clearance
    leaf_z = door_z + clearance
    leaf_width = door_width - 2.0 * (frame_width + clearance)
    leaf_height = door_height - frame_width - 2.0 * clearance
    _box(
        document,
        group,
        "DoorLeaf",
        "Außentürblatt",
        leaf_x,
        exterior_y - leaf_thickness,
        leaf_z,
        leaf_width,
        leaf_thickness,
        leaf_height,
        material="Holztür",
        color=leaf_color,
    )
    for index, z in enumerate((door_z + 350.0, door_z + door_height - 450.0), start=1):
        _box(
            document,
            group,
            f"DoorHinge_{index}",
            f"Türband {index}",
            door_x + frame_width,
            exterior_y - leaf_thickness - 6.0,
            z,
            45.0,
            6.0,
            120.0,
            material="Stahl verzinkt",
            color=metal,
        )

    # Fenster: umlaufender Rahmen, mittiger Flügelsteg und Verglasung.
    window_z = wall_bottom + window_sill_height
    frame_parts = (
        ("Left", window_x, window_z, frame_width, window_height),
        ("Right", window_x + window_width - frame_width, window_z, frame_width, window_height),
        ("Bottom", window_x + frame_width, window_z, window_width - 2.0 * frame_width, frame_width),
        ("Top", window_x + frame_width, window_z + window_height - frame_width,
         window_width - 2.0 * frame_width, frame_width),
    )
    for name, x, z, dx, dz in frame_parts:
        _box(
            document,
            group,
            f"WindowFrame_{name}",
            f"Fensterrahmen {name}",
            x,
            exterior_y,
            z,
            dx,
            frame_depth,
            dz,
            material="Holzfensterrahmen",
            color=wood,
        )
    mullion_x = window_x + window_width / 2.0 - frame_width / 2.0
    _box(
        document,
        group,
        "WindowMullion",
        "Fenster-Mittelsteg",
        mullion_x,
        exterior_y - 2.0,
        window_z + frame_width,
        frame_width,
        frame_depth + 4.0,
        window_height - 2.0 * frame_width,
        material="Holzfensterrahmen",
        color=wood,
    )
    pane_z = window_z + frame_width + clearance
    pane_height = window_height - 2.0 * (frame_width + clearance)
    pane_total_width = window_width - 2.0 * frame_width - frame_width
    pane_width = pane_total_width / 2.0 - 1.5 * clearance
    for side, x in (
        ("Left", window_x + frame_width + clearance),
        ("Right", mullion_x + frame_width + clearance),
    ):
        _box(
            document,
            group,
            f"WindowGlass_{side}",
            f"Fensterscheibe {side}",
            x,
            exterior_y - glass_thickness,
            pane_z,
            pane_width,
            glass_thickness,
            pane_height,
            material="Isolierglas",
            color=glass_color,
        )

    # Tierklappe: Rahmen, Klappenblatt und kurze Außenrampe.
    flap_z = wall_bottom
    for side, x in (("Left", flap_x), ("Right", flap_x + flap_width - frame_width)):
        _box(
            document,
            group,
            f"FlapFrame_{side}",
            f"Tierklappenrahmen {side}",
            x,
            exterior_y,
            flap_z,
            frame_width,
            frame_depth,
            flap_height,
            material="Rahmenholz",
            color=wood,
        )
    _box(
        document,
        group,
        "FlapFrame_Top",
        "Tierklappenrahmen oben",
        flap_x + frame_width,
        exterior_y,
        flap_z + flap_height - frame_width,
        flap_width - 2.0 * frame_width,
        frame_depth,
        frame_width,
        material="Rahmenholz",
        color=wood,
    )
    _box(
        document,
        group,
        "AnimalFlapLeaf",
        "Tierklappenblatt",
        flap_x + frame_width + clearance,
        exterior_y - leaf_thickness,
        flap_z + clearance,
        flap_width - 2.0 * (frame_width + clearance),
        leaf_thickness,
        flap_height - frame_width - 2.0 * clearance,
        material="Siebdruckplatte",
        color=leaf_color,
    )
    ramp_length = 700.0
    ramp_width = flap_width - 2.0 * frame_width
    ramp = document.addObject("Part::Feature", "AnimalRamp")
    ramp.Label = "Außenrampe Tierklappe"
    ramp.Shape = Part.makeBox(ramp_width, ramp_length, 24.0)
    ramp.Placement.Base = App.Vector(flap_x + frame_width, exterior_y - ramp_length, 0.0)
    ramp.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), -5.0)
    ramp.addProperty("App::PropertyString", "Material", "Bauteil")
    ramp.Material = "Siebdruckplatte"
    _set_color(ramp, leaf_color)
    group.addObject(ramp)

    return group
