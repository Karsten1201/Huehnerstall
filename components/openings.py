"""Parametrische Türen, Fenster und Tierklappen für das Stallgebäude.

Koordinatensystem:
- X: West -> Ost, Gebäudelänge 8.000 mm
- Y: Süd -> Nord, Gebäudetiefe 5.000 mm
- Z: Höhe

Die Bauteile werden zunächst als sichtbare Baugruppen erzeugt. Die in
``OPENING_SPECS`` hinterlegten Maße können später von den Wandmodulen
für echte Boolesche Ausschnitte wiederverwendet werden.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import FreeCAD as App
import Part

from config import parameters as p

WallSide = Literal["south", "north", "west", "east"]


@dataclass(frozen=True)
class OpeningSpec:
    name: str
    label: str
    kind: str
    wall: WallSide
    position: float
    sill: float
    width: float
    height: float
    frame_width: float = 60.0
    frame_depth: float = 80.0


OPENING_SPECS = (
    OpeningSpec("GooseDoor", "Außentür Gänsestall 900 x 2000", "door", "south", 900, 0, 900, 2000),
    OpeningSpec("ChickenDoor", "Außentür Hühnerstall 1000 x 2100", "door", "south", 5150, 0, 1000, 2100),
    OpeningSpec("GooseWindow", "Fenster Gänsestall 1000 x 600", "window", "north", 1150, 1200, 1000, 600),
    OpeningSpec("ChickenWindowWest", "Fenster Hühnerstall West 800 x 600", "window", "north", 4100, 1200, 800, 600),
    OpeningSpec("ChickenWindowEast", "Fenster Hühnerstall Ost 800 x 600", "window", "north", 6250, 1200, 800, 600),
    OpeningSpec("QuarantineWindow", "Fenster Quarantäne 600 x 400", "window", "east", 3350, 1450, 600, 400),
    OpeningSpec("GooseHatch", "Gänseklappe 500 x 600", "hatch", "south", 2550, 150, 500, 600, 40, 50),
    OpeningSpec("ChickenHatch", "Hühnerklappe 300 x 400", "hatch", "south", 6950, 150, 300, 400, 35, 45),
)


def _feature(doc, name: str, label: str, shape):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    return obj


def _local_box(spec: OpeningSpec, u: float, v: float, width: float, height: float, depth: float):
    """Erzeugt einen Rahmenkörper in lokaler Wandebene und setzt ihn global."""
    if spec.wall in ("south", "north"):
        x = spec.position + u
        y = -depth / 2 if spec.wall == "south" else p.BUILDING_DEPTH - depth / 2
        z = spec.sill + v
        return Part.makeBox(width, depth, height, App.Vector(x, y, z))

    y = spec.position + u
    x = -depth / 2 if spec.wall == "west" else p.BUILDING_LENGTH - depth / 2
    z = spec.sill + v
    return Part.makeBox(depth, width, height, App.Vector(x, y, z))


def _build_frame(doc, spec: OpeningSpec, group):
    fw = spec.frame_width
    d = spec.frame_depth

    members = (
        ("Left", 0, 0, fw, spec.height),
        ("Right", spec.width - fw, 0, fw, spec.height),
        ("Bottom", fw, 0, spec.width - 2 * fw, fw),
        ("Top", fw, spec.height - fw, spec.width - 2 * fw, fw),
    )
    for suffix, u, v, width, height in members:
        obj = _feature(
            doc,
            f"{spec.name}Frame{suffix}",
            f"{spec.label} – Rahmen {suffix}",
            _local_box(spec, u, v, width, height, d),
        )
        group.addObject(obj)


def _build_panel(doc, spec: OpeningSpec, group):
    clearance = 12.0
    u = spec.frame_width + clearance
    v = spec.frame_width + clearance
    width = spec.width - 2 * (spec.frame_width + clearance)
    height = spec.height - 2 * (spec.frame_width + clearance)
    depth = 24.0 if spec.kind == "window" else 40.0

    panel = _feature(
        doc,
        f"{spec.name}Panel",
        f"{spec.label} – {'Verglasung' if spec.kind == 'window' else 'Türblatt'}",
        _local_box(spec, u, v, width, height, depth),
    )
    group.addObject(panel)

    if spec.kind == "window":
        panel.addProperty("App::PropertyString", "Glazing", "Ausführung")
        panel.Glazing = "Isolierglas; innen raubtiersicheres Drahtgitter"
    elif spec.kind == "hatch":
        panel.addProperty("App::PropertyString", "Drive", "Ausführung")
        panel.Drive = "Vertikalschieber; vorbereitet für automatischen Antrieb"
    else:
        panel.addProperty("App::PropertyString", "OpeningDirection", "Ausführung")
        panel.OpeningDirection = "Nach außen öffnend"


def build_opening(doc, spec: OpeningSpec):
    group = doc.addObject("App::DocumentObjectGroup", f"{spec.name}Assembly")
    group.Label = spec.label
    _build_frame(doc, spec, group)
    _build_panel(doc, spec, group)
    return group


def build_openings(doc):
    """Erzeugt alle Türen, Fenster und Tierklappen."""
    root = doc.addObject("App::DocumentObjectGroup", "Openings")
    root.Label = "Türen, Fenster und Tierklappen"

    doors = doc.addObject("App::DocumentObjectGroup", "ExteriorDoors")
    doors.Label = "Außentüren"
    windows = doc.addObject("App::DocumentObjectGroup", "Windows")
    windows.Label = "Fenster"
    hatches = doc.addObject("App::DocumentObjectGroup", "AnimalHatches")
    hatches.Label = "Tierklappen"

    root.addObject(doors)
    root.addObject(windows)
    root.addObject(hatches)

    for spec in OPENING_SPECS:
        assembly = build_opening(doc, spec)
        if spec.kind == "door":
            doors.addObject(assembly)
        elif spec.kind == "window":
            windows.addObject(assembly)
        else:
            hatches.addObject(assembly)

    return root


def opening_cutters():
    """Liefert Ausschnittkörper für zukünftige Wandmodule.

    Die Körper sind rundum 5 mm größer als das lichte Öffnungsmaß, damit
    Boolesche Schnitte zuverlässig durch die komplette Wandstärke laufen.
    """
    cutters = {}
    extra = 5.0
    depth = p.WALL_THICKNESS + 20.0
    for spec in OPENING_SPECS:
        expanded = OpeningSpec(
            spec.name,
            spec.label,
            spec.kind,
            spec.wall,
            spec.position - extra,
            max(0.0, spec.sill - extra),
            spec.width + 2 * extra,
            spec.height + 2 * extra,
            spec.frame_width,
            depth,
        )
        cutters[spec.name] = _local_box(expanded, 0, 0, expanded.width, expanded.height, depth)
    return cutters
