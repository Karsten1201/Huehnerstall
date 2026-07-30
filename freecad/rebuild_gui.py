#!/usr/bin/env python3
"""Erzeugt das Stallmodell in der FreeCAD-GUI und speichert eine sichtbare 3D-Startansicht."""

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
if not (PROJECT_DIR / "build.py").is_file():
    raise RuntimeError(
        f"FreeCAD-Projektverzeichnis nicht gefunden: {PROJECT_DIR}\n"
        "Starte das Makro aus dem Repository oder setze den vollständigen Pfad."
    )
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from build import build  # noqa: E402
from config.parameters import OUTPUT_DIRECTORY, OUTPUT_FILENAME  # noqa: E402


def _gui_document(doc: App.Document):
    """Aktiviert genau das soeben erzeugte Dokument und liefert sein GUI-Dokument."""
    Gui.activateDocument(doc.Name)
    Gui.updateGui()
    gui_doc = Gui.getDocument(doc.Name)
    if gui_doc is None:
        raise RuntimeError(f"Kein GUI-Dokument für {doc.Name} verfügbar.")
    return gui_doc


def _show_complete_model(doc: App.Document) -> tuple[int, int]:
    """Macht alle Bauteile sichtbar und gibt (sichtbare Shapes, leere Shapes) zurück."""
    gui_doc = _gui_document(doc)
    active_view = gui_doc.activeView()
    active_view.setAnimationEnabled(False)

    visible_shapes = 0
    empty_shapes = 0

    # Zuerst Baugruppen sichtbar schalten, danach die eigentlichen Shape-Objekte.
    for obj in doc.Objects:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        if obj.Name.startswith("Origin") or obj.TypeId.startswith("App::Origin"):
            view.Visibility = False
            continue
        if obj.TypeId in {"App::Part", "App::DocumentObjectGroup"}:
            view.Visibility = True

    for obj in doc.Objects:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        if obj.Name.startswith("Origin") or obj.TypeId.startswith("App::Origin"):
            continue

        shape = getattr(obj, "Shape", None)
        if shape is None:
            continue
        try:
            is_null = shape.isNull()
        except Exception:
            is_null = True

        if is_null:
            empty_shapes += 1
            view.Visibility = False
        else:
            visible_shapes += 1
            view.Visibility = True
            try:
                view.DisplayMode = "Flat Lines"
            except Exception:
                pass

    doc.recompute()
    Gui.updateGui()

    active_view.setCameraType("Perspective")
    active_view.viewAxonometric()
    active_view.fitAll(0.85)
    active_view.redraw()
    Gui.updateGui()
    return visible_shapes, empty_shapes


def main() -> None:
    doc = build()
    visible_shapes, empty_shapes = _show_complete_model(doc)

    if visible_shapes == 0:
        raise RuntimeError(
            "Das Dokument enthält keine darstellbaren Shapes. "
            "Der Modellaufbau wurde deshalb nicht gespeichert."
        )

    target = PROJECT_DIR / OUTPUT_DIRECTORY / OUTPUT_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    doc.recompute()
    Gui.updateGui()
    doc.saveAs(os.fspath(target))

    # Nach dem Speichern nochmals aktivieren und einpassen, damit auch die aktuelle
    # Sitzung sofort das Modell zeigt.
    gui_doc = _gui_document(doc)
    gui_doc.activeView().viewAxonometric()
    gui_doc.activeView().fitAll(0.85)
    gui_doc.activeView().redraw()
    Gui.updateGui()

    print(
        f"Sichtbares FreeCAD-Gesamtmodell gespeichert: {target}\n"
        f"Darstellbare Shape-Objekte: {visible_shapes}; leere Shape-Objekte: {empty_shapes}"
    )


if __name__ == "__main__":
    main()
