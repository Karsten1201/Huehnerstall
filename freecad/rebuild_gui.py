#!/usr/bin/env python3
"""Erzeugt das Stallmodell innerhalb der FreeCAD-GUI und speichert eine sichtbare 3D-Startansicht."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui

PROJECT_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else (Path.cwd() / "freecad").resolve()
)
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from build import build  # noqa: E402
from config.parameters import OUTPUT_DIRECTORY, OUTPUT_FILENAME  # noqa: E402


def _show_complete_model(doc: App.Document) -> None:
    """Macht alle echten Bauteile sichtbar und speichert eine Gesamtansicht."""
    Gui.activeDocument().activeView().setAnimationEnabled(False)

    for obj in doc.Objects:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue

        # Origin-Hilfsobjekte und Koordinatensysteme bleiben ausgeblendet.
        if obj.Name.startswith("Origin") or obj.TypeId.startswith("App::Origin"):
            view.Visibility = False
            continue

        try:
            view.Visibility = True
        except Exception:
            pass

    doc.recompute()
    view = Gui.activeDocument().activeView()
    view.viewAxonometric()
    view.fitAll()


def main() -> None:
    doc = build()
    Gui.activeDocument().activeView().setCameraType("Perspective")
    _show_complete_model(doc)

    target = PROJECT_DIR / OUTPUT_DIRECTORY / OUTPUT_FILENAME
    doc.recompute()
    doc.saveAs(os.fspath(target))
    Gui.activeDocument().activeView().fitAll()
    print(f"Sichtbares FreeCAD-Gesamtmodell gespeichert: {target}")


if __name__ == "__main__":
    main()
