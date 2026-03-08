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

### Bereits gestartet (Roadmap-Phase Social/Album)

- Konfigurationsgrundlagen für Social Sharing, Monatsrückblick und Bild-Preprocessing sind integriert
- Neue Services: `nextfirst.preview_monthly_summary`, `nextfirst.share_experience`, `nextfirst.share_monthly_summary`
- Social Provider integriert: `webhook`, `mastodon`, `bluesky`
- Debug-Schalter in Optionen (`debug_enabled`) ergänzt

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

### v0.3.0 (2026-03-08)

- Social Provider integriert: `webhook`, `mastodon`, `bluesky`
- Social-Tab im Panel ergänzt (Erlebnis teilen, Monatsrückblick teilen, Historie)
- Monats-Scheduler für automatische Zusammenfassung mit optionalem Auto-Share
- Debug-Schalter in den Optionen ergänzt (`debug_enabled`)
- Kinderbild-Schutzregel vor Social-Posting ergänzt (Guardrail mit optionaler Preprocessing-Pipeline)

### v0.2.1 (2026-03-08)

- Social/Album-Roadmap Phase 1 gestartet: neue Optionen, Services und Modul-Schnittstellen
- Monatszusammenfassung als lokale Vorschau-Logik ergänzt (`nextfirst.preview_monthly_summary`)
- Neue Service-Grundlagen für spätere Social-Provider-Integration
- Datenschutz-Optionen für Kinderbild-Schutz und optionales Bild-Preprocessing ergänzt


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
