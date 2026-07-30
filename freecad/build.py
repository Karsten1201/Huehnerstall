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
        "FreeCAD-Pythonmodul nicht gefunden. Starte über FreeCADCmd oder das AppImage."
    ) from exc

PROJECT_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else (Path.cwd() / "freecad").resolve()
)
if not (PROJECT_DIR / "config" / "parameters.py").is_file():
    raise SystemExit(
        f"FreeCAD-Projektverzeichnis nicht gefunden: {PROJECT_DIR}\n"
        "Starte den Befehl im Stammverzeichnis des geklonten Repositories."
    )
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config.parameters import (  # noqa: E402
    ANIMAL_FLAP_HEIGHT,
    ANIMAL_FLAP_WIDTH,
    ANIMAL_FLAP_X,
    BUILDING_LENGTH,
    BUILDING_WIDTH,
    DOOR_HEIGHT,
    DOOR_WIDTH,
    DOOR_X,
    OUTPUT_DIRECTORY,
    OUTPUT_FILENAME,
    PARTITION_X,
    PROJECT_NAME,
    RAFTER_DEPTH,
    RAFTER_SPACING,
    RAFTER_WIDTH,
    RIDGE_BEAM_DEPTH,
    RIDGE_BEAM_WIDTH,
    ROOF_COVER_THICKNESS,
    ROOF_OVERHANG_EAVE,
    ROOF_OVERHANG_GABLE,
    ROOF_PITCH_DEG,
    SLAB_OVERHANG,
    SLAB_THICKNESS,
    STUD_DEPTH,
    STUD_SPACING,
    STUD_WIDTH,
    WALL_HEIGHT,
    WINDOW_HEIGHT,
    WINDOW_SILL_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_X,
)
from modules.foundation import create_foundation  # noqa: E402
from modules.roof import create_gable_roof  # noqa: E402
from modules.wall_frame import Opening, create_wall_frame  # noqa: E402


def ensure_output_directory() -> Path:
    output = PROJECT_DIR / OUTPUT_DIRECTORY
    output.mkdir(parents=True, exist_ok=True)
    return output


def build() -> App.Document:
    if PROJECT_NAME in App.listDocuments():
        App.closeDocument(PROJECT_NAME)
    doc = App.newDocument(PROJECT_NAME)

    create_foundation(
        doc,
        length=BUILDING_LENGTH,
        width=BUILDING_WIDTH,
        thickness=SLAB_THICKNESS,
        overhang=SLAB_OVERHANG,
    )

    south_openings = (
        Opening(
            name="Tierklappe",
            offset=ANIMAL_FLAP_X,
            width=ANIMAL_FLAP_WIDTH,
            height=ANIMAL_FLAP_HEIGHT,
            sill_height=0.0,
        ),
        Opening(
            name="Tuer",
            offset=DOOR_X,
            width=DOOR_WIDTH,
            height=DOOR_HEIGHT,
            sill_height=0.0,
        ),
        Opening(
            name="Fenster",
            offset=WINDOW_X,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            sill_height=WINDOW_SILL_HEIGHT,
        ),
    )

    create_wall_frame(
        doc,
        name="SouthWall",
        origin=(0, 0, 0),
        length=BUILDING_LENGTH,
        height=WALL_HEIGHT,
        stud_width=STUD_WIDTH,
        stud_depth=STUD_DEPTH,
        spacing=STUD_SPACING,
        direction="x",
        openings=south_openings,
    )
    create_wall_frame(
        doc,
        name="NorthWall",
        origin=(0, BUILDING_WIDTH - STUD_DEPTH, 0),
        length=BUILDING_LENGTH,
        height=WALL_HEIGHT,
        stud_width=STUD_WIDTH,
        stud_depth=STUD_DEPTH,
        spacing=STUD_SPACING,
        direction="x",
    )
    create_wall_frame(
        doc,
        name="WestWall",
        origin=(0, 0, 0),
        length=BUILDING_WIDTH,
        height=WALL_HEIGHT,
        stud_width=STUD_WIDTH,
        stud_depth=STUD_DEPTH,
        spacing=STUD_SPACING,
        direction="y",
    )
    create_wall_frame(
        doc,
        name="EastWall",
        origin=(BUILDING_LENGTH - STUD_DEPTH, 0, 0),
        length=BUILDING_WIDTH,
        height=WALL_HEIGHT,
        stud_width=STUD_WIDTH,
        stud_depth=STUD_DEPTH,
        spacing=STUD_SPACING,
        direction="y",
    )
    create_wall_frame(
        doc,
        name="PartitionWall",
        origin=(PARTITION_X, STUD_DEPTH, 0),
        length=BUILDING_WIDTH - 2.0 * STUD_DEPTH,
        height=WALL_HEIGHT,
        stud_width=STUD_WIDTH,
        stud_depth=STUD_DEPTH,
        spacing=STUD_SPACING,
        direction="y",
    )

    create_gable_roof(
        doc,
        length=BUILDING_LENGTH,
        width=BUILDING_WIDTH,
        wall_height=WALL_HEIGHT,
        pitch_deg=ROOF_PITCH_DEG,
        eave_overhang=ROOF_OVERHANG_EAVE,
        gable_overhang=ROOF_OVERHANG_GABLE,
        rafter_width=RAFTER_WIDTH,
        rafter_depth=RAFTER_DEPTH,
        rafter_spacing=RAFTER_SPACING,
        ridge_width=RIDGE_BEAM_WIDTH,
        ridge_depth=RIDGE_BEAM_DEPTH,
        cover_thickness=ROOF_COVER_THICKNESS,
    )

    doc.recompute()
    target = ensure_output_directory() / OUTPUT_FILENAME
    doc.saveAs(os.fspath(target))
    print(f"FreeCAD-Modell gespeichert: {target}")
    return doc


if __name__ == "__main__":
    build()
