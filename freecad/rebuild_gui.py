#!/usr/bin/env python3
"""Erzeugt das Stallmodell in der FreeCAD-GUI und speichert eine sichtbare 3D-Startansicht."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui


def _find_project_dir() -> Path:
    """Findet den Ordner ``freecad`` auch bei Ausführung aus der Python-Konsole.

    In der eingebauten FreeCAD-Python-Konsole ist ``__file__`` bei einem mit
    ``exec(compile(...))`` gestarteten Skript nicht zuverlässig gesetzt. Daher
    werden zusätzlich das Arbeitsverzeichnis, dessen Eltern und typische
    Repository-Pfade unterhalb des Benutzerverzeichnisses geprüft.
    """
    candidates: list[Path] = []

    if "__file__" in globals():
        try:
            candidates.append(Path(__file__).expanduser().resolve().parent)
        except (OSError, RuntimeError):
            pass

    cwd = Path.cwd().expanduser().resolve()
    candidates.extend((cwd, cwd / "freecad"))
    for parent in cwd.parents:
        candidates.extend((parent, parent / "freecad"))

    home = Path.home()
    candidates.extend(
        (
            home / "Dokumente" / "Hühnerstall" / "Huehnerstall" / "freecad",
            home / "Dokumente" / "Huehnerstall" / "freecad",
            home / "Dokumente" / "huehnerstall-freecad" / "freecad",
            home / "Dokumente" / "huehnerstall-freecad",
        )
    )

    env_dir = os.environ.get("HUEHNERSTALL_FREECAD_DIR")
    if env_dir:
        candidates.insert(0, Path(env_dir).expanduser())

    checked: set[Path] = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except (OSError, RuntimeError):
            continue
        if candidate in checked:
            continue
        checked.add(candidate)
        if (candidate / "build.py").is_file() and (
            candidate / "config" / "parameters.py"
        ).is_file():
            return candidate

    checked_text = "\n".join(f"  - {path}" for path in sorted(checked, key=str))
    raise RuntimeError(
        "FreeCAD-Projektverzeichnis nicht gefunden. Geprüfte Pfade:\n"
        f"{checked_text}\n"
        "Optional HUEHNERSTALL_FREECAD_DIR auf den vollständigen freecad-Ordner setzen."
    )


PROJECT_DIR = _find_project_dir()
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
    print(f"Verwendetes FreeCAD-Projektverzeichnis: {PROJECT_DIR}")
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
