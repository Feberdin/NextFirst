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
- Social Sharing als direkte Share-Links (z. B. Instagram/X/Facebook/WhatsApp/Telegram)
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
  - Notiz bearbeiten, Bild-Upload
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

### v0.3.14 (2026-03-08)

- Anti-Halluzinations-Hotfix: KI-Vorschläge werden nur übernommen, wenn die Angebots-URL echt wirkt und erreichbar ist
- Such-/Maps-Links als Angebots-URL werden blockiert (`google`, `bing`, `duckduckgo`, Maps)
- Keine künstlichen Google-Such-Fallback-Links mehr für fehlende Angebots-URLs
- Prompt verschärft: keine erfundenen Angebote/Workshops, bei Unsicherheit lieber nichts zurückgeben
- Standard-Kreativität (`temperature`) auf `0.4` reduziert, um faktische Stabilität zu erhöhen

### v0.3.13 (2026-03-08)

- Native Sharing Abstraktion im Panel ergänzt (strukturierter Payload: `title`, `body`, optional `url`, optional `image_ref`)
- Plattform-Reihenfolge: iOS Bridge (`window.webkit.messageHandlers.nextfirstShare`) -> Android Bridge (`window.NextFirstAndroidShare.share`) -> Web Share API -> bestehender Share-Dialog
- Graceful Fallback ergänzt, wenn Ziel-Apps einzelne Felder ignorieren (Text bleibt immer erhalten)
- Referenz-Implementierungen für native Layer ergänzt:
  - iOS: `UIActivityViewController`
  - Android: `Intent.ACTION_SEND` mit MIME-Typen und Content-URI-/FileProvider-Hinweisen

### v0.3.12 (2026-03-08)

- Startpunkt für Fahrzeit auf Wohnort-/Startadresse umgestellt (kein `zone.home`-Standard mehr)
- KI-Generierung validiert Startadresse und zeigt klare Fehlermeldung bei fehlender Adresse
- KI-Prompt erweitert: volle Adresse + Angebots-URL werden explizit verlangt
- KI-Parser erweitert (`offer_url`, `website_url`, `booking_url`, `url`) und Angebots-Link wird gespeichert
- Adress-Normalisierung verbessert (Nominatim + Fallback-Abfragen), nur konkrete Adressen werden akzeptiert
- UI ergänzt: direkter `Angebot`-Button zusätzlich zu `Maps`
- Default `max_tokens` auf `900` erhöht

### v0.3.11 (2026-03-08)

- UI: Ladebalken mit Laufzeitanzeige während der KI-Generierung ergänzt
- UI: Im Debug-Modus wird vor dem Senden eine Prompt-Vorschau angezeigt (mit explizitem "jetzt senden")
- Produktentscheidung umgesetzt: pro Klick genau 1 KI-Vorschlag (Auswahl im Panel entfernt)
- API: neuer Endpoint für Prompt-Vorschau (`/api/nextfirst/ai/prompt_preview`)
- KI-Parser verbessert: akzeptiert zusätzliche Location-Felder (`location_address`, `ort`) und bevorzugt normalisierte Adressen

### v0.3.10 (2026-03-08)

- KI-Generierung-Hotfix: Vorschläge werden nicht mehr komplett verworfen, wenn Geocoding/Routing-Dienste temporär nicht antworten
- Max-Fahrzeit bleibt aktiv: Wenn `travel_minutes` vom Modell vorhanden ist und zu groß ist, wird weiterhin gefiltert
- Neues Debug-Logging für KI-Filterpfad (`dropped_missing_location`, `dropped_distance`, `fallback_without_verified_route`)

### v0.3.9 (2026-03-08)

- KI-Standard auf 2 Vorschläge vereinheitlicht (UI + Backend-Fallback)
- Fahrzeitprüfung verbessert: `travel_origin` (z. B. `zone.home`) wird auf Koordinaten aufgelöst
- KI-Vorschläge ohne konkrete Location werden verworfen
- Vorschläge außerhalb der maximalen Fahrzeit werden per Geocoding/Routing herausgefiltert
- Kalenderaktion erweitert: `.ics`-Download plus separater Google-Kalender-Link
- Budget-Pill im Dashboard robust gemacht (kein leeres `EUR` mehr)

### v0.3.4 (2026-03-08)

- Sensor-Fix für aktuelle HA-EntityDescription
- Datei-Upload für Bilder im Panel
- KI-Parser robuster für reale OpenAI-Antworten
- Social-Sharing vereinfacht auf direkte Share-Links
- NextFirst-eigenes Protokoll ergänzt

### v0.3.3 (2026-03-08)

- Hotfix für verbleibende Setup-Fehler aus dem HA-Log (OptionsFlow, Sensor-Description, Panel sync/async)

### v0.3.2 (2026-03-08)

- Hotfix: ImportError in `sensor.py` behoben
- Hotfix: Panel-Registrierung für deine HA-Version stabilisiert

### v0.3.1 (2026-03-08)

- Hotfix für `Der Konfigurationsfluss konnte nicht geladen werden` (500 Fehler)
- Sensor-Setup-Fix für aktuelle Home-Assistant-Version

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
