# Huehnerstall

Parametrische FreeCAD-Planung für einen kombinierten Hühner- und Gänsestall.

## Projektstand

- Gesamtgebäude: 8,00 × 5,00 m
- Gänsestall: 3,50 × 5,00 m
- Hühnerstall: 4,50 × 5,00 m
- Quarantänebereich: 2,00 × 2,00 m
- Satteldach
- parametrischer Innenausbau des Hühnerstalls

## Struktur

```text
build.py
components/
  chicken_interior.py
config/
  parameters.py
docs/
  12_innenausbau_huehnerstall.md
```

## Ausführung

Das Skript muss mit der Python-Umgebung von FreeCAD ausgeführt werden, nicht mit einem gewöhnlichen System-Python ohne FreeCAD-Modul.

Beispiel:

```bash
FreeCADCmd build.py
```

Unter Linux kann der genaue Programmname je nach Installation auch `freecadcmd` oder ein vollständiger Pfad zur FreeCAD-Installation sein.

Die erzeugte Datei wird unter `output/Huehnerstall_Gaensestall.FCStd` gespeichert.
