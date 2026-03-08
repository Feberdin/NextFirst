# NextFirst

NextFirst ist eine Home-Assistant-Integration für neue Erlebnisse: planen, umsetzen, dokumentieren und als Album wieder ansehen.

## Zweck

- Neue Aktivitäten als Einträge verwalten (`offen`, `übersprungen`, `erlebt`, `archiviert`)
- Erlebnisse nach Abschluss mit Bildern/Notizen ergänzen
- Optionale KI-Vorschläge erzeugen (lokal nutzbar auch ohne KI)

## Features der v0.1.0 (erste Version)

- Config Flow + Options Flow
- CRUD und Statuswechsel via Home-Assistant-Services
- Sensoren für Überblicksstatistiken
- Button zum KI-Vorschläge-Generieren
- JSON-Storage mit Schema-Version und migrationsfähiger Struktur
- Defensives Fehlerhandling mit klaren Meldungen
- Provider-neutrale KI-Schicht (v1 Provider: OpenAI)
- Album-Grundansicht über Sensor-Attribute + Service-Response

## Projektstruktur

```text
NextFirst/
├─ custom_components/nextfirst/
│  ├─ __init__.py
│  ├─ manifest.json
│  ├─ config_flow.py
│  ├─ const.py
│  ├─ domain.py
│  ├─ errors.py
│  ├─ manager.py
│  ├─ services.py
│  ├─ services.yaml
│  ├─ sensor.py
│  ├─ button.py
│  ├─ storage.py
│  ├─ strings.json
│  ├─ translations/
│  │  ├─ de.json
│  │  └─ en.json
│  └─ ai/
│     ├─ service.py
│     └─ providers/
│        ├─ base.py
│        └─ openai.py
├─ docs/codex_spec.md
├─ tests/test_domain.py
├─ CONTRIBUTING.md
├─ .gitignore
└─ pyproject.toml
```

## Quickstart

### A) Integration in Home Assistant laden

#### Über HACS (empfohlen)

1. HACS -> `Integrationen` -> `Custom repositories`.
2. Repository hinzufügen: `https://github.com/Feberdin/NextFirst` als `Integration`.
3. `NextFirst` installieren und Home Assistant neu starten.

#### Manuell

1. Repository in dein HA-`config` Verzeichnis kopieren.
2. Ordner `custom_components/nextfirst` nach `config/custom_components/nextfirst` legen.
3. Home Assistant neu starten.
4. Unter `Einstellungen -> Geräte & Dienste -> Integration hinzufügen` nach `NextFirst` suchen.

### B) Lokale Tests ausführen (3 Zeilen)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip pytest
pytest
```

## Konfiguration

Optionen (Auszug) im Options Flow:

- `ai_enabled`
- `ai_provider` (v1: `openai`)
- `ai_model`
- `ai_api_key`
- `ai_suggestion_count`
- `ai_temperature`
- `ai_max_tokens`
- `max_travel_minutes`
- `preferred_categories` (CSV)
- `preferred_courage_levels` (CSV)
- `family_friendly_only`
- `good_weather_only`
- `custom_interests`
- `exclusions`

## Services (Auszug)

- `nextfirst.create_experience`
- `nextfirst.update_experience`
- `nextfirst.delete_experience`
- `nextfirst.mark_skipped`
- `nextfirst.reactivate_experience`
- `nextfirst.mark_experienced`
- `nextfirst.attach_media`
- `nextfirst.add_note`
- `nextfirst.generate_ai_suggestions`
- `nextfirst.get_statistics` (Response)
- `nextfirst.get_album` (Response)

## Troubleshooting

- Integration startet nicht:
  - Prüfe `manifest.json`, `config_flow.py` und HA-Logs auf Importfehler.
- Einträge fehlen nach Neustart:
  - Prüfe `.storage`/Store-Datei auf gültiges JSON und `schema_version`.
- KI-Vorschläge schlagen fehl:
  - Prüfe API-Key, Modellname, Internetzugang und Fehlermeldung in HA-Logs.
- Album zeigt keine Bilder:
  - Prüfe `attach_media` Pfade und ob die referenzierten Dateien existieren.

## Logging und Debug

- Logger-Namespace: `custom_components.nextfirst`
- Empfohlene Level:
  - `INFO` im Regelbetrieb
  - `DEBUG` für Fehlersuche
- Sensible Daten (API-Key) niemals unmaskiert loggen.

## Security-Hinweise

- KI bleibt optional; ohne KI ist NextFirst vollständig nutzbar.
- Bilder bleiben standardmäßig lokal (nur Referenzen im Datensatz).
- API-Schlüssel nur in HA-Optionen/Speichermechanismen pflegen.

## Lizenz

MIT (siehe `LICENSE`)
