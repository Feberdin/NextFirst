# NextFirst

NextFirst ist eine Home-Assistant-Integration, die Menschen dabei unterstützt, bewusst neue Erfahrungen zu planen, umzusetzen und als Erinnerungsalbum festzuhalten.

Die Integration verbindet:

- Erlebnislisten (`Offen`, `Übersprungen`, `Erlebt`, `Archiviert`)
- optionale KI-Vorschläge für neue Aktivitäten
- ein visuelles Album mit Bildern, Notizen und Metadaten

> Hinweis: Bilder/Screenshots werden später ergänzt.

## Installation über HACS

1. HACS öffnen -> `Integrationen` -> `Custom repositories`.
2. Repository hinzufügen: `https://github.com/Feberdin/NextFirst` als Typ `Integration`.
3. `NextFirst` installieren.
4. Home Assistant neu starten.
5. Integration hinzufügen unter `Einstellungen -> Geräte & Dienste -> Integration hinzufügen`.

## Features

- Eigener Sidebar-Panel-Eintrag `NextFirst`
- Vier Hauptansichten im Panel:
  - `Offen`
  - `Übersprungen`
  - `Erlebt`
  - `Album`
- Direkte Aktionen in der UI:
  - Erstellen, Bearbeiten, Löschen
  - Als übersprungen markieren, reaktivieren
  - Als erlebt markieren, archivieren
  - Notiz bearbeiten, Bildpfad hinzufügen
- Home-Assistant-Services für Automationen (`nextfirst.*`)
- Sensoren für Statistiken (`sensor.nextfirst_*`)
- Optionaler KI-Modus (provider-neutral vorbereitet, v1 OpenAI)
- Lokal-first JSON-Storage mit versionsfähigem Schema

## Community-Dokumente

- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [License](LICENSE)

## Antichronologischer Changelog

### v0.2.0 (2026-03-08)

- Sidebar-Panel `NextFirst` in Home Assistant ergänzt
- Neue Views: `Offen`, `Übersprungen`, `Erlebt`, `Album`
- HTTP-API für Panel-Interaktionen unter `/api/nextfirst/*`
- UI-Aktionen für Statuswechsel, CRUD, Notizen und Medien ergänzt

### v0.1.2 (2026-03-08)

- Config-Flow stabilisiert
- API-Key bereits im initialen Setup erfassbar
- Options-Flow-Normalisierung robuster umgesetzt

### v0.1.1 (2026-03-08)

- HACS-Kompatibilität verbessert (`hacs.json` ergänzt)
- Manifest um `homeassistant` Mindestversion ergänzt
- Getaggtes Release für HACS veröffentlicht

### v0.1.0 (2026-03-08)

- Erste lauffähige MVP-Version der Integration
- Config Flow + Options Flow
- Services, Sensoren und Basis-Datenhaltung implementiert
