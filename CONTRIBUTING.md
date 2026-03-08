# Contributing to NextFirst

## Ziel

Änderungen sollen nachvollziehbar, testbar und für Nicht-Programmierer wartbar bleiben.

## Entwicklungsprinzipien

- Korrektheit vor Geschwindigkeit
- Kleine Änderungen statt Big-Bang
- Defensive Programmierung und klare Fehlermeldungen
- Tests für Kernlogik sind Pflicht

## Lokaler Ablauf

1. Branch erstellen (`feature/...` oder `fix/...`)
2. Änderungen in kleinen Commits umsetzen
3. Tests lokal ausführen
4. Dokumentation bei Verhaltensänderung aktualisieren
5. Pull Request mit kurzer Risiko- und Testbeschreibung

## Test-Anforderungen

Mindestens pro relevanter Änderung:

- 1 Happy-Path
- 1 Edge-Case
- 1 Negativtest

## Code-Style

- Lesbare Namen, kleine Funktionen
- Kommentare erklären Absicht
- Keine still verschluckten Exceptions
- Sensitive Daten nie unmaskiert loggen

## Pull-Request-Checkliste

- [ ] Verhalten klar beschrieben
- [ ] Tests ergänzt/angepasst
- [ ] Fehlermeldungen verständlich
- [ ] README/Spezifikation aktualisiert (falls nötig)
