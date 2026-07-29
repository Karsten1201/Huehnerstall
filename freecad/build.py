#!/usr/bin/env python3
"""Erzeugt das parametrische FreeCAD-Modell des Hühner- und Gänsestalls."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import FreeCAD as App
except ModuleNotFoundError as exc:
    raise SystemExit(
        "FreeCAD-Pythonmodul nicht gefunden. Starte mit: FreeCADCmd freecad/build.py"
    ) from exc

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config.parameters import (  # noqa: E402
    BUILDING_LENGTH, BUILDING_WIDTH, OUTPUT_DIRECTORY, OUTPUT_FILENAME,
    PROJECT_NAME, RAFTER_DEPTH, ROOF_OVERHANG_EAVE, ROOF_OVERHANG_GABLE,
    ROOF_PITCH_DEG, SLAB_OVERHANG, SLAB_THICKNESS, STUD_DEPTH,
    STUD_SPACING, STUD_WIDTH, WALL_HEIGHT,
)
from modules.foundation import create_foundation  # noqa: E402
from modules.roof import create_gable_roof  # noqa: E402
from modules.wall_frame import create_wall_frame  # noqa: E402


def ensure_output_directory() -> Path:
    output = PROJECT_DIR / OUTPUT_DIRECTORY
    output.mkdir(parents=True, exist_ok=True)
    return output


def build() -> App.Document:
    old = App.getDocument(PROJECT_NAME)
    if old is not None:
        App.closeDocument(PROJECT_NAME)
    doc = App.newDocument(PROJECT_NAME)

    create_foundation(doc, length=BUILDING_LENGTH, width=BUILDING_WIDTH,
                      thickness=SLAB_THICKNESS, overhang=SLAB_OVERHANG)

    create_wall_frame(doc, name="SouthWall", origin=(0, 0, 0),
                      length=BUILDING_LENGTH, height=WALL_HEIGHT,
                      stud_width=STUD_WIDTH, stud_depth=STUD_DEPTH,
                      spacing=STUD_SPACING, direction="x")
    create_wall_frame(doc, name="NorthWall",
                      origin=(0, BUILDING_WIDTH - STUD_DEPTH, 0),
                      length=BUILDING_LENGTH, height=WALL_HEIGHT,
                      stud_width=STUD_WIDTH, stud_depth=STUD_DEPTH,
                      spacing=STUD_SPACING, direction="x")
    create_wall_frame(doc, name="WestWall", origin=(0, 0, 0),
                      length=BUILDING_WIDTH, height=WALL_HEIGHT,
                      stud_width=STUD_WIDTH, stud_depth=STUD_DEPTH,
                      spacing=STUD_SPACING, direction="y")
    create_wall_frame(doc, name="EastWall",
                      origin=(BUILDING_LENGTH - STUD_DEPTH, 0, 0),
                      length=BUILDING_WIDTH, height=WALL_HEIGHT,
                      stud_width=STUD_WIDTH, stud_depth=STUD_DEPTH,
                      spacing=STUD_SPACING, direction="y")

    create_gable_roof(doc, length=BUILDING_LENGTH, width=BUILDING_WIDTH,
                      wall_height=WALL_HEIGHT, pitch_deg=ROOF_PITCH_DEG,
                      eave_overhang=ROOF_OVERHANG_EAVE,
                      gable_overhang=ROOF_OVERHANG_GABLE,
                      rafter_depth=RAFTER_DEPTH)

    doc.recompute()
    target = ensure_output_directory() / OUTPUT_FILENAME
    doc.saveAs(os.fspath(target))
    print(f"FreeCAD-Modell gespeichert: {target}")
    return doc


if __name__ == "__main__":
    build()
