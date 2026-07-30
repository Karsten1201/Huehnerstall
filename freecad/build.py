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
    DOOR_LEAF_THICKNESS,
    DOOR_WIDTH,
    DOOR_X,
    NEST_BOX_DEPTH,
    NEST_BOX_HEIGHT,
    NEST_BOX_WIDTH,
    NEST_COUNT,
    NEST_FLOOR_HEIGHT,
    NEST_WALL_THICKNESS,
    OPENING_CLEARANCE,
    OPENING_FRAME_DEPTH,
    OPENING_FRAME_WIDTH,
    OUTPUT_DIRECTORY,
    OUTPUT_FILENAME,
    PARTITION_X,
    PERCH_COUNT,
    PERCH_DIAMETER,
    PERCH_FIRST_HEIGHT,
    PERCH_LENGTH,
    PERCH_SPACING,
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
    WINDOW_GLASS_THICKNESS,
    WINDOW_HEIGHT,
    WINDOW_SILL_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_X,
)
from modules.foundation import create_foundation  # noqa: E402
from modules.interior import create_interior  # noqa: E402
from modules.openings import create_south_opening_elements  # noqa: E402
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

    create_south_opening_elements(
        doc,
        wall_y=0.0,
        wall_bottom=STUD_WIDTH,
        wall_depth=STUD_DEPTH,
        door_x=DOOR_X,
        door_width=DOOR_WIDTH,
        door_height=DOOR_HEIGHT,
        window_x=WINDOW_X,
        window_width=WINDOW_WIDTH,
        window_height=WINDOW_HEIGHT,
        window_sill_height=WINDOW_SILL_HEIGHT,
        flap_x=ANIMAL_FLAP_X,
        flap_width=ANIMAL_FLAP_WIDTH,
        flap_height=ANIMAL_FLAP_HEIGHT,
        frame_width=OPENING_FRAME_WIDTH,
        frame_depth=OPENING_FRAME_DEPTH,
        leaf_thickness=DOOR_LEAF_THICKNESS,
        glass_thickness=WINDOW_GLASS_THICKNESS,
        clearance=OPENING_CLEARANCE,
    )

    create_interior(
        doc,
        partition_x=PARTITION_X,
        building_length=BUILDING_LENGTH,
        stud_depth=STUD_DEPTH,
        perch_count=PERCH_COUNT,
        perch_length=PERCH_LENGTH,
        perch_diameter=PERCH_DIAMETER,
        perch_spacing=PERCH_SPACING,
        perch_height=PERCH_FIRST_HEIGHT,
        nest_count=NEST_COUNT,
        nest_width=NEST_BOX_WIDTH,
        nest_depth=NEST_BOX_DEPTH,
        nest_height=NEST_BOX_HEIGHT,
        nest_wall=NEST_WALL_THICKNESS,
        nest_floor_height=NEST_FLOOR_HEIGHT,
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
