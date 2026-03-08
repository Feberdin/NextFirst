# NextFirst Codex-Spezifikation (MVP)

## 1) Ziel und Scope

NextFirst ist eine Home-Assistant-Integration mit lokal-first Architektur zur Planung, Umsetzung und Dokumentation neuer Erlebnisse.

MVP-Ziel:

- Listenmanagement für Erlebnisse (`open`, `skipped`, `experienced`, optional `archived`)
- Album-/Timeline-Grundansicht für erlebte Einträge
- Optionale KI-Vorschlagserstellung (provider-neutral, v1 mit OpenAI-Adapter)
- Robuste lokale Persistenz mit versionierbarem Schema

Nicht im MVP (nur vorbereitet):

- Multi-User-Rechtesystem
- Vollautomatische kontextbasierte Empfehlungen aus Wetter/Kalender/Presence
- Gamification/Challenges mit komplexen Regeln
- Separate mobile/web app

## 2) Annahmen

- Zielplattform: Home Assistant Core (Custom Integration)
- Integrations-Domain: `nextfirst`
- Namespace-Präfixe:
  - Entitäten: `sensor.nextfirst_*`, `button.nextfirst_*`
  - Services: `nextfirst.*`
  - Interne API-Kennung: `nextfirst`
- Persistenz über Home Assistant Storage (`Store`) mit JSON-Daten
- Medien binär außerhalb Kerndaten; Kerndaten speichern nur Referenzen
- Primäre Sprache v1: Deutsch, i18n-Struktur aber vorbereitet

## 3) Architektur

Warum diese Struktur:

- Trennung von Domäne, Infrastruktur und Integrationsschicht reduziert Kopplung.
- Kernlogik bleibt UI-unabhängig und kann später in App/Web wiederverwendet werden.

### 3.1 Module

1. Domain Layer
   - Erlebnismodell
   - Statusübergänge
   - Validierungen
   - Filter/Statistiken

2. Storage Layer
   - Laden/Speichern/Migration
   - Integritätsprüfung bei Medienreferenzen

3. Media Layer
   - Bildreferenzen verwalten (attach/remove/list)
   - Pfadvalidierung, defekte Referenzen tolerieren

4. AI Layer
   - Provider-Interface
   - SuggestionContext Builder
   - v1 Provider: OpenAI Adapter

5. HA Integration Layer
   - Config Flow
   - Options Flow
   - Services
   - Sensor/Button-Entitäten
   - Events (optional)

6. UI Layer (MVP minimal)
   - Dashboard-fähige Entitäten/Services
   - optional simple Karte/Panel später

## 4) Datenmodell

Warum so:

- Versionierbar, tolerant gegenüber zukünftigen Feldern, migrationsfähig.

### 4.1 Enums

- `status`: `open | skipped | experienced | archived`
- `origin`: `manual | ai`
- `courage_level`: `leicht | mittel | mutig | verrueckt`
- `indoor_outdoor`: `indoor | outdoor | mixed | unknown`

### 4.2 Erlebnisobjekt (logisches Schema)

```json
{
  "id": "uuid",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "origin": "manual",
  "title": "Nachwanderung im Wald",
  "description": "Optional",
  "category": "Natur",
  "tags": ["abend", "familie"],
  "courage_level": "mittel",
  "duration_minutes": 120,
  "cost_level": "low",
  "travel_minutes": 25,
  "age_group": "family",
  "weather_hint": "good_weather",
  "indoor_outdoor": "outdoor",
  "family_friendly": true,
  "notes": "Optional",
  "status": "open",
  "completed_at": null,
  "rating": null,
  "would_repeat": null,
  "location": null,
  "media": [
    {
      "media_id": "uuid",
      "experience_id": "uuid",
      "path": "/media/nextfirst/2026/03/photo1.jpg",
      "thumbnail_path": "/media/nextfirst/2026/03/thumb_photo1.jpg",
      "captured_at": "ISO-8601",
      "metadata": {
        "filename": "photo1.jpg"
      }
    }
  ],
  "history": [
    {
      "timestamp": "ISO-8601",
      "from": "open",
      "to": "experienced",
      "reason": "user_action"
    }
  ],
  "extra": {}
}
```

Hinweise:

- `extra` erlaubt unbekannte künftige Felder ohne sofortige Migration.
- Pflichtfelder: `id`, `title`, `status`, `created_at`, `origin`.

### 4.3 Root-Storage Schema

```json
{
  "schema_version": 1,
  "updated_at": "ISO-8601",
  "experiences": [],
  "categories": ["Natur", "Essen", "Ausflug", "Kreativ"],
  "stats_cache": {},
  "settings_snapshot": {}
}
```

## 5) Statuslogik

Erlaubte Übergänge:

- `open -> skipped`
- `open -> experienced`
- `skipped -> open`
- `experienced -> archived`
- `archived -> open` (optional Reaktivierung)

Nicht erlaubte Übergänge erzeugen User-Fehler mit klarer Meldung.

Beispiel:

- Input: `from=skipped`, `to=experienced` ohne Reaktivierung
- Output: Fehler `InvalidTransition`, Hinweis: erst `skipped -> open`, dann `open -> experienced`

## 6) Services (Home Assistant)

Empfohlene Service-Namen:

- `nextfirst.create_experience`
- `nextfirst.update_experience`
- `nextfirst.delete_experience`
- `nextfirst.mark_skipped`
- `nextfirst.reactivate_experience`
- `nextfirst.mark_experienced`
- `nextfirst.attach_media`
- `nextfirst.add_note`
- `nextfirst.generate_ai_suggestions`
- `nextfirst.get_statistics`

### 6.1 Service-Fehlerklassen

- User-Fehler (z. B. ungültige Eingaben):
  - Klar, freundlich, nächste Schritte
- System-Fehler (z. B. Storage/API):
  - Technischer Kontext + Prüfhilfe

Beispiel Fehlermeldung:

- `ExperienceNotFound: id=... nicht vorhanden. Prüfe die ID oder lade die Liste neu.`

## 7) Entitäten (MVP)

Sensoren:

- `sensor.nextfirst_open_count`
- `sensor.nextfirst_skipped_count`
- `sensor.nextfirst_experienced_count`
- `sensor.nextfirst_experienced_this_month`
- `sensor.nextfirst_last_ai_generation`

Buttons:

- `button.nextfirst_generate_suggestions`

Optional später:

- Select/Number/Text Helfer für schnelle Filter im Dashboard

## 8) Config Flow und Options Flow

### 8.1 Config Flow (Basis)

- Ein Instanz-Setup pro Home Assistant Installation
- Name/Title: `NextFirst`

### 8.2 Options Flow (MVP)

- `ai_enabled` (bool)
- `ai_provider` (enum, v1: `openai`)
- `ai_model` (str)
- `ai_suggestion_count` (int)
- `ai_temperature` (float)
- `ai_max_tokens` (int)
- `max_travel_minutes` (int)
- `preferred_categories` (list)
- `preferred_courage_levels` (list)
- `preferred_days` (list)
- `preferred_time_windows` (list)
- `budget_preference` (enum)
- `family_friendly_only` (bool)
- `indoor_outdoor_preference` (enum)
- `good_weather_only` (bool)
- `custom_interests` (text)
- `exclusions` (text)

Datenschutztext Pflicht:

- Welche Daten an externe KI gehen
- Dass Bilder standardmäßig lokal bleiben
- Wie KI komplett deaktiviert werden kann

## 9) KI-Architektur (provider-neutral)

Interface:

```text
SuggestionProvider.generate(context: SuggestionContext) -> list[SuggestionDraft]
```

`SuggestionContext` enthält:

- Nutzerpräferenzen
- optionale HA-Kontextdaten (später)
- Limits (Anzahl, Kosten, Fahrzeit, Mut-Level)
- Sprache/Locale

Adapter v1:

- `OpenAISuggestionProvider`
- Prompt-Template in Optionen überschreibbar
- Antwortparser robust gegen unvollständige/fehlerhafte KI-Ausgaben

Fallback-Verhalten:

- KI-Fehler darf Kernfunktion nicht blockieren
- Fehler loggen, freundliche Meldung im Service-Result

## 10) Logging und Debugbarkeit

Log-Konzept:

- `DEBUG`: Validierungsdetails, Service-Eingänge (maskiert)
- `INFO`: wichtige Aktionen (Erlebnis erstellt, Status gewechselt)
- `WARNING`: inkonsistente Medienreferenz, recoverable issue
- `ERROR`: Storage-/API-Fehler

Maskierung:

- API-Key, personenbezogene Freitexte, exakte Standorte nur reduziert loggen

Reproduzierbarkeit:

- Versionsinfo (`integration_version`, `schema_version`) in Debug-Kontext
- Request-/Action-ID pro Service-Aufruf empfohlen

## 11) Defensive Programmierung

Pflicht vor externem Zugriff:

- Input validieren
- Pfade prüfen
- API-Timeouts setzen
- Fehler typisieren

Keine stillen Exceptions:

- Immer loggen + kontrollierte Rückgabe oder sauberer Abbruch

Medienrobustheit:

- Fehlende Datei darf Eintrag nicht unlesbar machen
- Betroffene Referenz markieren und überspringen

## 12) Tests

Mindestsatz für MVP:

1. Unit-Tests Kernlogik
   - Statusübergänge erlaubt/verboten
   - Pflichtfeldvalidierung
   - Filter-/Statistikfunktionen

2. Happy-Path Tests
   - Eintrag anlegen -> als erlebt markieren -> Bild anhängen

3. Edge-Cases
   - Leere Listen
   - Unbekannte Zusatzfelder in `extra`
   - Defekte Medienreferenz

4. Negativtests
   - Ungültiger Statuswechsel
   - KI-Antwort ohne verwertbares Format

5. Migrationstests
   - `schema_version` alt -> neu

## 13) UX-Grundsätze (MVP)

- Sofort verständliche Begriffe: `Offen`, `Übersprungen`, `Erlebt`, `Album`
- Hauptaktionen direkt verfügbar je Status
- Abschlussmoment positiv: nach `als erlebt markieren` direkt `Bild/Notiz hinzufügen`
- Hilfe kontextnah im UI-Text
- Sichere Defaults (KI aus, lokale Nutzung möglich)

## 14) Roadmap nach MVP

1. Kontextvorschläge aus Wetter/Kalender/Presence
2. Wiedervorlage-Mechanismen und smarte Erinnerungen
3. Statistik-/Challenge-Module
4. Eigene Custom Card / Panel mit starker Album-UX
5. Entkoppelte Web-/Mobile-Clients auf Basis gleicher Kernlogik

## 15) Umsetzungsreihenfolge (empfohlen)

1. Domain + Storage + Tests
2. Services + Entitäten + Status-/Statistikpfade
3. Medienreferenzen und Album-Grundansicht
4. Options Flow + AI Interface + OpenAI Adapter
5. Fehlertexte, Logging-Härtung, Dokumentation

## 16) Erweiterungsvorbereitung: Social & Monatsalbum

Bereits vorbereitet:

- Neue Optionen für Social Sharing, Monatszusammenfassung und Bild-Preprocessing
- Services:
  - `nextfirst.preview_monthly_summary`
  - `nextfirst.share_experience`
  - `nextfirst.share_monthly_summary`
- Module:
  - `social/` (provider-neutrale Posting-Schnittstellen)
  - `media_processing/` (privacy-sichere Bild-Transform-Pipeline)
  - `monthly_summary.py` (lokale Recap-Generierung)
  - `scheduler.py` (monatlicher Trigger nach konfigurierbarem Intervall)

Datenschutz-Guardrails:

- Social Sharing bleibt standardmäßig deaktiviert (Opt-in).
- Bild-Preprocessing bleibt standardmäßig deaktiviert (Opt-in).
- Kinderbild-Schutzmodus konfigurierbar (`none`, `blur_kids`, `ai_stylize`).
- Provider-Adapter müssen vor Aktivierung klare Datenschutzhinweise anzeigen.

Aktueller Implementierungsstand:

- Social Provider live: `webhook`, `mastodon`, `bluesky`
- Debug-Schalter (`debug_enabled`) über Options Flow
- Share-Historie persistent gespeichert und abrufbar
