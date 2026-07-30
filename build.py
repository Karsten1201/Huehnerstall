#!/usr/bin/env python3
"""Einstiegspunkt für den parametrischen FreeCAD-Aufbau."""

from __future__ import annotations

import os

import FreeCAD as App

from components.chicken_interior import build_chicken_interior
from components.openings import build_openings
from config.parameters import PROJECT_NAME


def ensure_output_directory(path: str) -> str:
    """Erzeugt das Ausgabeverzeichnis und gibt dessen absoluten Pfad zurück."""
    absolute_path = os.path.abspath(path)
    os.makedirs(absolute_path, exist_ok=True)
    return absolute_path


def build(output_directory: str = "output") -> str:
    """Erzeugt das FreeCAD-Dokument und speichert es als FCStd-Datei."""
    output_directory = ensure_output_directory(output_directory)

    existing = App.getDocument(PROJECT_NAME)
    if existing is not None:
        App.closeDocument(PROJECT_NAME)

    doc = App.newDocument(PROJECT_NAME)

    build_chicken_interior(doc)
    build_openings(doc)

    doc.recompute()

    output_path = os.path.join(output_directory, f"{PROJECT_NAME}.FCStd")
    doc.saveAs(output_path)
    return output_path


if __name__ == "__main__":
    result = build()
    print(f"FreeCAD-Datei erzeugt: {result}")
