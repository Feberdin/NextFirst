# Changelog

## 0.3.6 - 2026-03-08

- Fix: KI-Generierung liefert jetzt stabil die angeforderte Anzahl (z. B. 2 oder 5)
- Fix: Bilderupload nutzt jetzt sicheren HA-API-Flow via `callApi` (kein separater 401-Fetch mehr)
- UI: Share-Buttons als direkte Klick-Buttons (Instagram, X, Facebook, WhatsApp, Telegram)
- UI: Share-Text wird angezeigt und beim Teilen in Zwischenablage kopiert
- Defaults: KI-Felder sinnvoll vorbefüllt (Kategorien, Mut-Level, Interessen)
- Defaults: Standard-Hashtag auf `NextFirstHA` gesetzt

## 0.3.5 - 2026-03-08

- Hotfix: NextFirst Setup-Crash behoben (`sensor.py` Dataclass-Feldreihenfolge via `kw_only=True`)
- Hotfix: Bilderupload-Auth im Panel korrigiert (HA `fetchWithAuth` statt manuellem Bearer-Header)
- Hotfix: `/media/*` Bildpfade im Album lösen keine unauthenticated Requests mehr aus
- UX: Eigener Tab `Protokoll` in der UI ergänzt

## 0.3.4 - 2026-03-08

- Hotfix: Sensoren wieder voll kompatibel mit aktueller HA-Version (`entity_registry_visible_default`)
- Hotfix: Panel sendet HTTP-Methoden korrekt in Großbuchstaben (`PATCH`-Fehler behoben)
- Fix: KI-Antwortparser akzeptiert jetzt reale OpenAI-Formate (`activities`, Einzelobjekt, JSON-Block)
- Neu: Bild-Upload direkt im Panel (Dateiauswahl) statt manuellem Dateipfad
- Änderung: Social-Flow auf manuelles Teilen über direkte Share-Links umgestellt (ohne Webhook/Mastodon/Bluesky-Zwang)
- Änderung: Automatisches Monats-Autoposting entfernt
- Neu: NextFirst-eigenes Protokoll mit API (`/api/nextfirst/protocol`) für Debug/Support
- UX: Optionen klarer benannt (kommaseparierte Felder, Interessen/Ausschlüsse, Fahrzeit-Startpunkt)

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
