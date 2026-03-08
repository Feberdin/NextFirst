# Changelog

## 0.3.3 - 2026-03-08

- Hotfix: OptionsFlow Konstruktor für diese HA-Version korrigiert (`NextFirstOptionsFlow(config_entry)`)
- Hotfix: Sensor-Description kompatibel gemacht (`entity_registry_enabled_default` ergänzt)
- Hotfix: Panel-Registrierung und Cleanup für sync/async Frontend-API abgesichert

## 0.3.2 - 2026-03-08

- Hotfix: Sensor-Importfehler behoben (Dataclass-Feldreihenfolge in `sensor.py` korrigiert)
- Hotfix: Panel-Frontend-Registrierung kompatibel gemacht (ohne `hass.components` Zugriff)

## 0.3.1 - 2026-03-08

- Hotfix: Config-Flow 500 behoben (OptionsFlow Initialisierung angepasst)
- Hotfix: Sensor-Setup kompatibel gemacht (device_class Feld ergänzt)

## 0.3.0 - 2026-03-08

- Social Posting mit echten Providern ergänzt: `webhook`, `mastodon`, `bluesky`
- Monats-Scheduler ergänzt (monatlicher Rückblick nach konfigurierbarem Tag/Stunde)
- Share-Historie persistent im Storage inkl. API/Service-Zugriff
- UI erweitert um Social-Tab mit Share-Aktionen, Monatsvorschau und Historie
- Debug-Schalter in Optionen ergänzt (`debug_enabled`), kein YAML-Edit nötig

## 0.2.1 - 2026-03-08

- Grundlagen für Social-Integration ergänzt (provider-neutrale Schnittstellen + neue Services)
- Monatszusammenfassung als lokale Vorschau-Logik implementiert (`preview_monthly_summary`)
- Optionen für Social-Posting, Datenschutzmodus für Kinderbilder und Bild-Preprocessing ergänzt
- Roadmap-Platzhalter für Social-Provider und Bild-Transform-Provider mit klaren Fehlermeldungen

## 0.2.0 - 2026-03-08

- Eigenes Sidebar-Panel `NextFirst` unter `/nextfirst` implementiert
- Neue Panel-Ansichten: `Offen`, `Übersprungen`, `Erlebt`, `Album`
- Neue HTTP-API-Endpunkte unter `/api/nextfirst/*` für UI-Interaktionen
- UI-Aktionen: Erstellen, Bearbeiten, Überspringen, Als erlebt markieren, Reaktivieren, Archivieren, Löschen, Notiz/Bild hinzufügen
- KI-Vorschläge direkt aus dem Panel auslösbar
- Integration-Manifest auf `0.2.0` erhöht

## 0.1.2 - 2026-03-08

- Config-Flow stabilisiert (lazy service import, kompatiblere Service-Typisierung)
- API-Key kann bereits im initialen Setup erfasst werden
- Options-Flow-Normalisierung robuster umgesetzt

## 0.1.1 - 2026-03-08

- HACS-Kompatibilität verbessert: `hacs.json` ergänzt
- Manifest um `homeassistant` Mindestversion ergänzt
- Erstes getaggtes Release für HACS vorbereitet

## 0.1.0 - 2026-03-08

- Erste lauffähige Version der NextFirst Home-Assistant-Integration
- Config Flow + Options Flow
- Services für CRUD, Statuswechsel, Medien, Notizen, KI-Generierung
- Statistik- und Album-Sensoren
- Button für KI-Vorschlagsgenerierung
- Versionierbares JSON-Storage und Domain-Tests
