"""Zusätzliche Türen, Fenster und Tierklappen am vollständigen Stallmodell.

Das Modul bearbeitet die bereits von ``modules.envelope`` erzeugten Fassaden
und erzeugt echte Ausschnitte sowie gut sichtbare Öffnungselemente.
"""

from __future__ import annotations

from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class OpeningSpec:
    name: str
    label: str
    facade: str
    x: float
    width: float
    height: float
    sill: float
    kind: str


def _color(obj, value, transparency=0):
    view = getattr(obj, "ViewObject", None)
    if view is not None:
        view.ShapeColor = value
        try:
            view.Transparency = transparency
        except Exception:
            pass


def _feature(doc, group, name, label, shape, color, transparency=0):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    group.addObject(obj)
    _color(obj, color, transparency)
    return obj


def _cut_facade(doc, facade_name, specs, *, y, depth):
    facade = doc.getObject(facade_name)
    if facade is None or getattr(facade, "Shape", None) is None:
        raise RuntimeError(f"Fassadenobjekt {facade_name!r} wurde nicht gefunden.")

    result = facade.Shape
    for spec in specs:
        cutter = Part.makeBox(
            spec.width,
            depth + 8.0,
            spec.height,
            App.Vector(spec.x, y - 4.0, spec.sill),
        )
        result = result.cut(cutter)
    facade.Shape = result


def _frame(doc, group, spec, *, y, outward):
    frame = 45.0
    trim_depth = 35.0
    wood = (0.76, 0.55, 0.31)
    dark = (0.36, 0.20, 0.10)
    glass = (0.52, 0.76, 0.90)
    metal = (0.32, 0.34, 0.36)

    fy = y + outward * trim_depth
    dy = trim_depth

    parts = (
        ("Left", spec.x, spec.sill, frame, spec.height),
        ("Right", spec.x + spec.width - frame, spec.sill, frame, spec.height),
        ("Top", spec.x + frame, spec.sill + spec.height - frame,
         spec.width - 2.0 * frame, frame),
    )
    if spec.kind == "window":
        parts += (("Bottom", spec.x + frame, spec.sill,
                   spec.width - 2.0 * frame, frame),)

    for suffix, x, z, dx, dz in parts:
        shape = Part.makeBox(dx, dy, dz, App.Vector(x, min(fy, fy + outward * dy), z))
        _feature(doc, group, f"{spec.name}Frame{suffix}",
                 f"{spec.label} – Rahmen {suffix}", shape, wood)

    clear_x = spec.x + frame + 5.0
    clear_z = spec.sill + (frame + 5.0 if spec.kind == "window" else 5.0)
    clear_w = spec.width - 2.0 * (frame + 5.0)
    clear_h = spec.height - frame - 10.0
    if spec.kind == "window":
        clear_h = spec.height - 2.0 * (frame + 5.0)
        leaf_depth = 8.0
        leaf_y = y + outward * (trim_depth + leaf_depth)
        shape = Part.makeBox(
            clear_w, leaf_depth, clear_h,
            App.Vector(clear_x, min(leaf_y, leaf_y + outward * leaf_depth), clear_z),
        )
        _feature(doc, group, f"{spec.name}Glass", f"{spec.label} – Verglasung",
                 shape, glass, transparency=65)
    else:
        leaf_depth = 35.0
        leaf_y = y + outward * (trim_depth + leaf_depth)
        shape = Part.makeBox(
            clear_w, leaf_depth, clear_h,
            App.Vector(clear_x, min(leaf_y, leaf_y + outward * leaf_depth), clear_z),
        )
        _feature(doc, group, f"{spec.name}Leaf", f"{spec.label} – Blatt",
                 shape, dark if spec.kind == "door" else metal)


def create_supplementary_openings(doc, *, building_width, cladding_thickness):
    """Schneidet und bestückt alle bislang fehlenden Fassadenöffnungen."""
    if doc.getObject("SupplementaryOpenings") is not None:
        return doc.getObject("SupplementaryOpenings")

    group = doc.addObject("App::DocumentObjectGroup", "SupplementaryOpenings")
    group.Label = "Ergänzte Fenster, Türen und Tierklappen"

    south_specs = (
        OpeningSpec("GooseDoor", "Außentür Gänsestall", "south", 350.0, 900.0, 2000.0, 0.0, "door"),
        OpeningSpec("GooseWindow", "Fenster Gänsestall", "south", 2300.0, 1000.0, 600.0, 1200.0, "window"),
        OpeningSpec("ChickenFlap", "Hühnerklappe", "south", 7450.0, 300.0, 400.0, 120.0, "flap"),
    )
    north_specs = (
        OpeningSpec("QuarantineWindow", "Fenster Quarantänebereich", "north", 3850.0, 600.0, 400.0, 1350.0, "window"),
        OpeningSpec("ChickenNorthWindow", "Fenster Hühnerstall Nord", "north", 6100.0, 800.0, 600.0, 1200.0, "window"),
    )

    south_y = -cladding_thickness
    north_y = building_width
    _cut_facade(doc, "SouthCladding", south_specs, y=south_y, depth=cladding_thickness)
    _cut_facade(doc, "NorthCladding", north_specs, y=north_y, depth=cladding_thickness)

    for spec in south_specs:
        _frame(doc, group, spec, y=south_y, outward=-1.0)
    for spec in north_specs:
        _frame(doc, group, spec, y=north_y, outward=1.0)

    doc.recompute()
    return group


def install_envelope_hook():
    """Hängt die Zusatzöffnungen transparent an create_building_envelope an."""
    from modules import envelope

    original = envelope.create_building_envelope
    if getattr(original, "_supplementary_openings_hook", False):
        return

    def wrapped(doc, **kwargs):
        group = original(doc, **kwargs)
        create_supplementary_openings(
            doc,
            building_width=kwargs["width"],
            cladding_thickness=kwargs["cladding_thickness"],
        )
        return group

    wrapped._supplementary_openings_hook = True
    envelope.create_building_envelope = wrapped


install_envelope_hook()
