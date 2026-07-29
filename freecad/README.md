# Hühner- und Gänsestall – FreeCAD

Parametrischer FreeCAD-Generator für einen kombinierten Hühner- und Gänsestall.

## Abmessungen

- Grundfläche: 8,00 × 5,00 m
- Bodenplatte: 150 mm Stahlbeton
- Wandraster: 625 mm
- KVH: 60 × 120 mm, C24
- Satteldach: 25°
- Traufhöhe: 2,30 m

## Ausführen

Das Skript muss mit der Python-Umgebung von FreeCAD gestartet werden:

```bash
FreeCADCmd freecad/build.py
```

Alternativ in der FreeCAD-Python-Konsole:

```python
exec(open("freecad/build.py", encoding="utf-8").read())
```

Die erzeugte Datei wird standardmäßig unter `freecad/output/Huehner_Gaensestall.FCStd` gespeichert.
