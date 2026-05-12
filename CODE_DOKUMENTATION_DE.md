# Code-Dokumentation — eventplanner-agent

Dieses Dokument erklärt die Architektur, die Dateien und die zentralen Konzepte von `eventplanner-agent`
für Team-Mitglieder, die neu im Projekt sind. Es beantwortet: *Was tut welche Datei, warum existiert sie,
und wie greifen die Teile ineinander?*

---

## Was ist dieses Projekt?

**Dion** ist ein KI-gestützter City-Trip- und Event-Planer, entwickelt für BlastIn.

Ein Nutzer füllt ein Planungsformular aus (Stadt, Daten, Vibe, Budget usw.) und Dion liefert:
- eine kuratierte Liste von **Events** (Quelle: Eventim)
- **Sightseeing-Spots** sowie **Food- & Drink-Empfehlungen** (Quelle: DZT)
- ein **Tag-für-Tag-Itinerary**, das alles sinnvoll zusammenführt
- einen **Markdown-Report**, den der Nutzer speichern oder herunterladen kann

Das System basiert auf drei KI-Agenten, einer Validierungsschleife und einem Satz strukturierter
Datenverträge (Schemas), die exakt steuern, was jeder Agent zurückgeben darf.

---

## Schlüsselkonzept: Was sind Schemas?

`src/schemas.py` ist der **gemeinsame Datenvertrag** für das gesamte Projekt.

Man kann sich das wie ein Formular mit strengen Regeln vorstellen: jedes Feld hat einen Namen, einen Typ
und teilweise eine Constraint. Wenn ein Agent versucht, Daten zurückzugeben, die nicht ins Schema passen,
bricht der Lauf mit einem klaren Fehler ab, statt stillschweigend Müll zu erzeugen.

### Input-Schemas (was die UI an den Agent schickt)

| Schema | Was es darstellt |
|--------|------------------|
| `UserRequest` | Das Top-Level-Objekt, das die UI baut und an Dion übergibt. Enthält alles Folgende. |
| `UserProfile` | Optionaler Nutzername für die Personalisierung. |
| `TripRequest` | Stadt, Daten, Planungsmodus, Gruppengröße, Budget, Scope-Flags (events/sightseeing/food). |
| `EventPreferences` | Vibe, Kategorien, Zeitpräferenz, Free-Only-Flag. |
| `SightseeingPreferences` | Interessen, Indoor/Outdoor-Präferenz, Free-Only-Flag. |
| `ItineraryPreferences` | Must-Avoid-Liste. |
| `DeliveryOption` | Sprachauswahl, optionaler E-Mail-Versand. |
| `Budget` | Min/Max-Budget in EUR. Validiert: Min muss ≤ Max sein. |
| `PlanningMode` | Entweder `full_trip` (mehrtägig) oder `event_day_trip` (Fokus auf einen Tag/ein Event). |
| `TimePreferences` | `daytime` (10–17 Uhr), `evening` (17–22 Uhr), `night` (ab 22 Uhr) oder `no preferences`. |
| `Language` | `English` oder `Deutsch`. Steuert die Ausgabesprache aller Agenten. |

### Output-Schemas (was die Agenten zurückgeben)

| Schema | Was es darstellt |
|--------|------------------|
| `CoreResult` | Das vollständige Planungsergebnis von `Dion_Planner`. Enthält Events, Sightseeing-Spots, Food-/Drink-Spots, Itinerary, Recommendation, Warnings und Personal Feedback. |
| `EventItem` | Ein einzelnes Event mit Start-/Endzeit, Gebiet/Adresse, Preisinfos, `source_url`, optionaler `ticket_url` und Backend-`event_id`. |
| `SightseeingSpot` | Eine Sightseeing-Location (Name, Adresse, Eintrittspreis, Öffnungszeiten, Begründung der Auswahl). |
| `FoodDrinkSpot` | Ein Restaurant, eine Bar oder ein Café (Name, Typ, Preis-Hinweis, Begründung der Passung). |
| `ItineraryDay` | Ein Tag im Plan mit geordneter Liste von `ItineraryStop`-Objekten. Max. 5 Sightseeing-Stops pro Tag. |
| `ItineraryStop` | Ein einzelner Stop im Itinerary: Titel, Zeit, Typ (`sightseeing`, `event`, `food`, `other`), Notizen, `linked_item_name` und optional `source_url`. |
| `Recommendation` | Max. 5 Sätze, die erklären, warum der Plan zum Wunsch des Nutzers passt. |
| `UIResult` | Eine abgespeckte Version des `CoreResult` für die UI. Max. 3 Events sichtbar, gekürzte Stop-Informationen. |
| `ValidationResult` | Output von `Dion_Validator`: ob der Plan überarbeitet werden muss und eine Liste konkreter Probleme. |
| `ValidationIssue` | Ein einzelner Validierungsbefund mit Code, Nachricht und Severity (`info`, `warning`, `error`). |
| `MarkdownReport` | Der vollständige Trip-Report: Titel, Recommendation, geordnete Sektionen, Quellen, Zeitstempel. |
| `ReporterResult` | Wrapper um `MarkdownReport`, geliefert vom `Dion_Reporter`, mit optionalem `saved_report_path`. |

---

## Die drei Agenten

Das System nutzt drei spezialisierte KI-Agenten. Jeder hat eine fest umrissene Rolle und kann nicht das tun,
was die anderen tun.

### 1. Dion_Planner
**Was er tut:** Plant den Trip. Sucht Events (über Eventim), Sightseeing- und Food-Spots (über DZT),
kann Playwright zur URL-Suche/-Verifizierung nutzen und liefert ein `CoreResult`.

**Verfügbare Tools:** Eventim MCP, DZT MCP, Playwright, Filesystem MCP

**System-Instructions:** `SYSTEM_INSTRUCTIONS_PLANNER` in `src/instructions.py`

**Wichtigste Regeln aus den Instructions:**
- Niemals Events, Venues, Preise oder Öffnungszeiten erfinden
- Event-Relevanz ist Pflicht — keine unpassenden Inhalte
- Zeitpräferenzen sind konkreten Zeitbereichen zugeordnet (daytime 10–17 Uhr, evening 17–22 Uhr, night ab 22 Uhr)
- Kein Venue darf bei Food/Drink-Stops über mehrere Tage hinweg wiederverwendet werden
- Bei mehrtägigen Trips müssen mindestens 2 separate DZT-Calls für Sightseeing erfolgen
- Scope-Flags (`events_enabled`, `sightseeing_enabled`, `food_drink_enabled`) sind Hard Constraints
- **Retry-Regeln:** Liefert Eventim 0 Events mit Filtern, wird zuerst ohne Filter, dann mit erweitertem Datumsbereich erneut gesucht; liefert DZT 0 Treffer, wird mit breiten generischen Begriffen erneut versucht, bevor aufgegeben wird
- **Playwright-Fallback:** Liefert DZT nach 2 Retries weiterhin 0 Treffer, sucht der Planner über Playwright im Web nach Sightseeing-Spots oder Restaurants in der Stadt

### 2. Dion_Validator
**Was er tut:** Prüft das `CoreResult` gegen die ursprüngliche `UserRequest` und liefert ein
`ValidationResult` mit allen konkret gefundenen Problemen.

**Verfügbare Tools:** Keine (rein lesende Analyse)

**System-Instructions:** `SYSTEM_INSTRUCTIONS_VALIDATOR` in `src/instructions.py`

**Wichtigste Regeln aus den Instructions:**
- Es werden nur Issues gemeldet, die tatsächlich in den Daten begründet sind
- Überlappende Itinerary-Stops sind High-Severity
- Der Validator-Prompt akzeptiert bezahlte Sightseeing-Spots, die als "optional" gekennzeichnet sind, wenn Free-Only nicht voll erfüllbar ist
- Das finale `needs_revision` stammt nicht allein vom Validator; Python merged deterministische Issues mit den Agent-Findings und leitet die Endentscheidung aus dieser kombinierten Liste ab

**Wichtiger Runtime-Hinweis:** `src/event_client.py` flaggt aktuell weiterhin bezahlte Sightseeing-Spots
in der deterministischen Validierung, wenn `sightseeing.free_only = true` — das tatsächliche Laufzeit-Verhalten
ist also strenger als der reine Validator-Prompt.

### 3. Dion_Reporter
**Was er tut:** Nimmt das validierte `CoreResult` und liefert ein `ReporterResult` mit einem
`MarkdownReport`. Sucht keine neuen Informationen.

**Verfügbare Tools:** Keine (nur Ausgabe)

**System-Instructions:** `SYSTEM_INSTRUCTIONS_REPORTER` in `src/instructions.py`

**Wichtigste Regeln aus den Instructions:**
- Keine neuen Fakten — nur das, was in den übergebenen Daten steht
- Report-Sprache muss zur Sprachauswahl des Nutzers passen
- Tag-für-Tag-Sektionen sollen wie eine zusammenhängende Geschichte gelesen werden, nicht wie ein Daten-Dump
- Das System speichert den Report automatisch auf der Festplatte

---

## End-to-End-Flow

```
Nutzer füllt Formular im Browser aus (ui/Dion UI.html — React, kein Build-Step)
      │
      ▼
POST /api/plan  →  ui/dion_api.py  (FastAPI, synchroner Endpoint, intern asyncio.run)
      │
      ▼  baut UserRequest aus dem Request-Body
run_full_planner_flow(user_request, planner_model=selected_model) (src/event_client.py)
      │
      ├─ 1. MCP-Server starten (Playwright, Filesystem, Eventim, DZT)
      │
      ├─ 2. Dion_Planner läuft → liefert CoreResult
      │
      ├─ 3. Post-Processing-Pipeline (Python, deterministisch):
      │      • autoritative Eventim-Event-Daten synchronisieren
      │      • generische Platzhalter-Stops entfernen
      │      • doppelte Food-Venues über Tage hinweg entfernen
      │      • Event-/Sightseeing-/Food-URLs normalisieren
      │      • Place-URLs parallel auf Erreichbarkeit prüfen
      │      • verifizierte URLs zurück in die Itinerary-Stops synchronisieren
      │
      ├─ 4. Deterministische Validierung (Python):
      │      • Scope-Flags respektiert?
      │      • Free-Only-Constraints erfüllt?
      │      • Itinerary-Stops verweisen auf reale Items?
      │      • Daten passen zum Request?
      │      • Fehlerhafte Place-URLs werden geflaggt
      │
      ├─ 5. Dion_Validator läuft mit den deterministischen Findings als Input
      │      • finales ValidationResult merged Python-Checks + Agent-Findings
      │
      ├─ 6. Wenn needs_revision = true:
      │      └─ Dion_Planner bekommt einen Repair-Prompt → überarbeitetes CoreResult
      │         └─ Post-Processing-Pipeline läuft erneut
      │
      ├─ 7. CoreResult → UIResult (für die Anzeige)
      │
      ├─ 8. Dion_Reporter läuft → liefert ReporterResult
      │
      └─ 9. Python ergänzt bei Bedarf finale Link-Hinweise und speichert den Report unter outputs/reports/
```

**Follow-up-Flow** (`run_followup_planner_flow`) ist analog, komprimiert aber das bestehende `CoreResult`
vorher zu einem schlanken Dict (nur Namen, Daten und Itinerary-Struktur — keine Beschreibungen), bevor
es als Kontext mitgegeben wird. So bleibt der Follow-up-Input klein genug, um einen Context-Overflow zu
vermeiden. Der Reporter bekommt weiterhin das vollständige `CoreResult`.

---

## Dateireferenz

### `src/`

| Datei | Aufgabe |
|-------|---------|
| `event_client.py` | Kern-Orchestrierung. Startet Agenten, verwaltet MCP-Server, Post-Processing, Validierungsschleife, Report-Persistenz. Die wichtigste Datei im Projekt. Definiert außerdem `AVAILABLE_MODELS` und `DEFAULT_MODEL` für den UI-Model-Selector. |
| `schemas.py` | Alle Pydantic-Datenverträge (Inputs + Outputs). Die gemeinsame Sprache zwischen UI, Agenten und Code. |
| `instructions.py` | System-Prompts für alle drei Agenten. Ein Großteil des Produktverhaltens lebt hier, nicht im Python-Code. |
| `reporting.py` | Helfer zum Aufbau des Markdown-Reports aus strukturierten Daten und zum Speichern auf der Platte. |

### `ui/`

| Datei | Aufgabe |
|-------|---------|
| `dion_api.py` | FastAPI-Server. Stellt `POST /api/plan` und `POST /api/followup` bereit, serialisiert `UIResult` in das vom Frontend erwartete JSON-Format und liefert die statischen HTML-/JSX-Dateien aus. Start mit `uv run python ui/dion_api.py`. |
| `Dion UI.html` | React-Frontend-Einstieg. Lädt React und Babel vom CDN und importiert die JSX-Module. Kein Build-Step nötig — über den FastAPI-Server unter `http://localhost:7860` aufrufen. |
| `dion-app.jsx` | Wurzel-Komponente `App`. Hält den gesamten State (Form, Scope, Plan, History), baut den API-Request-Body aus den Formwerten, ruft `/api/plan` und `/api/followup` auf und rendert die vier-Tab-Hülle. |
| `dion-data.jsx` | Konstanten: `AVAILABLE_MODELS`, Dropdown-Optionen und `DEMO_PLAN` (Berlin-Demo-Daten für den „Fill with demo data"-Button). |
| `dion-icons.jsx` | Leichte SVG-Icon-Komponenten, die in der gesamten UI verwendet werden. |
| `dion-mark.jsx` | Animiertes Dion-Maskottchen (`DionMark`) und Begrüßungs-Sprechblase (`DionBubble`), gerendert als fixes Floating-Widget unten rechts im Viewport. Die Bubble läuft durch eine deutsche und eine englische Nachricht und verschwindet danach. |
| `dion-output.jsx` | Output-Spalten-Komponenten: `StatusBar`, `EventList`, `SpotList`, `Itinerary`, `FollowUpPanel`, `ReportFile` und Accordion-JSON-Viewer. |
| `dion-tabs.jsx` | Die drei Nicht-Planner-Tab-Views: `VenueTab` (flaches, filterbares Inventar), `BriefTab` (JSON-Inspector), `IterationTab` (versionierte Plan-Historie). |

### `mcp_servers/`

| Datei | Aufgabe |
|-------|---------|
| `mcp_servers.py` | MCP-Server-Konfiguration und -Lifecycle. Definiert, welche Server verfügbar sind, gibt Konfiguration weiter (z. B. Reports-Verzeichnis), übernimmt Start/Stopp. |
| `event_server.py` | Eigener Eventim-MCP-Server. Löst Städte auf, holt Events für einen Datumsbereich, normalisiert UTC↔Europe/Berlin und cached Antworten. |
| `dzt_server.py` | DZT-MCP-Server. Kapselt DZT-Tool-Calls für POI-Suche, lokale Events, Trails und Entity-Details. |

### Root-Dateien

| Datei | Aufgabe |
|-------|---------|
| `README.md` | Projektüberblick und Setup-Anleitung. Hier anfangen. |
| `DEMO_CASES.md` | Alle Test-/Demo-Szenarien mit Inputs, erwarteten Ergebnissen und Checklisten. |
| `EVENT_API_ENDPOINTS.md` | Referenznotizen zu den Eventim-Backend-Endpoints und erwarteten Request-/Response-Formaten. |
| `pyproject.toml` | Projekt-Metadaten und Dependencies (verwaltet mit `uv`). |
| `.env` | Lokale Environment-Variablen (Modell-Keys, API-Endpoints). Nicht committed. |
| `outputs/reports/` | Hier werden die generierten Markdown-Reports zur Laufzeit gespeichert. |

---

## MCP-Tools — Was der Planner nutzen kann

MCP (Model Context Protocol) ist die Schnittstelle, über die die KI-Agenten externe Tools aufrufen.
Die Runtime startet vier MCP-Server. Der Planner ist mit allen vier verbunden, wobei der Filesystem-Server
hauptsächlich vom Python-Code für die kontrollierte Report-Speicherung genutzt wird.

**Eventim** (über `event_server.py`)
- `get_supported_cities_with_active_events` — löst einen Stadtnamen zu einem Backend-City-Key auf
- `get_events_for_city` — holt Events für eine Stadt und einen Datumsbereich
- `get_similar_events` — optional: findet verwandte Events
- `get_popular_events` — optional: liefert beliebte Events (kann zufällig sein)

**DZT** (über `dzt_server.py`)
- `get_pois_by_criteria` — strukturierte POI-Suche für Sightseeing, Restaurants, Bars, Cafés und ähnliche Place-Typen
- `get_events_by_criteria` — strukturierte Suche für lokale Events (Festivals, Märkte, Stadt-Events), die nicht über Eventim laufen
- `get_trails_by_criteria` — strukturierte Trail-Suche
- `get_entity_details` — holt vollständige Details zu einer bestimmten DZT-Entität

**Playwright** (über externen MCP-Server)
- Web-Browsing und Content-Extraktion
- Wird genutzt, um korrekte URLs für Nicht-Eventim-Places zu finden und zu verifizieren
- Kann bei Bedarf auch Inhalte von Event- oder Venue-Seiten extrahieren

**Filesystem** (über externen MCP-Server)
- Auf `REPORTS_DIR` beschränkt
- Wird von der Anwendung genutzt, um den finalen Markdown-Report in das erlaubte Reports-Verzeichnis zu schreiben

---

## Post-Processing-Pipeline

Nachdem der Planner ein `CoreResult` zurückgegeben hat, läuft eine deterministische Python-Pipeline,
bevor irgendetwas die UI oder den Validator erreicht. Diese Pipeline läuft für Initial- und Follow-up-Runs
identisch.

```python
_sync_core_result_events_with_authoritative_data()   # mit Eventim-Backend anreichern
_fix_event_stop_dates()                              # Event-Stops, die auf dem falschen Tag liegen, verschieben
_sanitize_itinerary_placeholders()                   # generische Filler-Stops entfernen
_deduplicate_food_stops_in_itinerary()               # wiederholte Food-Venues entfernen
_insert_default_food_structure()                     # fehlende Mahlzeit-Slots auffüllen
_sanitize_event_source_urls()                        # Event-Links normalisieren
_sanitize_sightseeing_source_urls()                  # Sightseeing-Links normalisieren
_sanitize_food_and_drink_source_urls()               # Food-/Drink-Links normalisieren
_verify_place_source_urls()                          # alle Place-Links per HTTP prüfen (parallel)
_sync_itinerary_stop_source_urls()                   # verifizierte URLs in die Stops zurückpropagieren
```

Wichtige Verhaltensweisen:
- **Places werden niemals wegen Link-Problemen entfernt.** Kann ein Link nicht verifiziert werden, bleibt der Place erhalten und der Link wird auf `null` gesetzt. Eine Warning wird hinzugefügt.
- **Doppelte Food-Venues werden entfernt.** Verwendet der Agent dasselbe Restaurant an mehreren Tagen oder zweimal am selben Tag, werden die Duplikate gestrippt und eine Warning angezeigt.
- **Link-Verifizierung läuft parallel** (`asyncio.gather`) — die Prüfung von 10+ Links dauert ungefähr genauso lange wie die Prüfung eines einzigen.

---

## Progress-Reporting

Die FastAPI-Endpoints (`/api/plan`, `/api/followup`) sind synchron — sie blockieren, bis der Agent fertig
ist, und liefern dann das vollständige Ergebnis als JSON. Es gibt kein serverseitiges Streaming.

Das React-Frontend simuliert während des Wartens Fortschritt: ein `setInterval`-Timer durchläuft das
`PROGRESS_STEPS_I18N`-Objekt in `dion-app.jsx` alle 18 Sekunden. Die Sprache (`en` oder `de`) wird zu
Beginn jedes Runs aus `form.language` abgeleitet. Sobald die API-Antwort eintrifft, wird der Timer
gestoppt und das echte Ergebnis sofort gerendert. Liefert die API einen Fehler, zeigt die Statusleiste
einen roten Punkt mit der Fehlermeldung.

Die Step-Labels passen sich an die gewählte Sprache an:

| Step | English | Deutsch |
|------|---------|---------|
| 1 | Starting MCP servers… | MCP-Server werden gestartet… |
| 2 | Searching for events and places… | Events und Orte werden gesucht… |
| 3 | Building the plan… | Plan wird erstellt… |
| 4 | Validating and refining the plan… | Plan wird geprüft und verfeinert… |
| 5 | Writing the report… | Bericht wird geschrieben… |
| 6 | Plan and report created successfully. | Plan und Bericht erfolgreich erstellt. |

---

## UI-Model-Selector

Die obere Leiste der React-UI bietet ein Dropdown, mit dem der Nutzer auswählt, welches KI-Modell
`Dion_Planner` für den aktuellen Request nutzen soll. Die Auswahlmöglichkeiten und der Default werden
als Konstanten in `src/event_client.py` definiert:

```python
AVAILABLE_MODELS = [
    'google/gemini-2.5-flash',   # default — großer Context, zuverlässig
    'z-ai/glm-4.7',              # Top-Score im τ²-Bench
    'moonshotai/kimi-k2.6',      # starke Ergebnisse in Agentic-Benchmarks
]
DEFAULT_MODEL = AVAILABLE_MODELS[0]
```

**Wie es durch den Code fließt:**

1. `ui/dion-data.jsx` importiert `AVAILABLE_MODELS` und `DEFAULT_MODEL` als statische Konstanten (Backend-Spiegelung)
2. Der ausgewählte Wert wird als `model` im JSON-Body an `POST /api/plan` oder `POST /api/followup` mitgeschickt
3. `ui/dion_api.py` liest `body.model` und reicht es als `planner_model=body.model` an `run_full_planner_flow` und `run_followup_planner_flow` weiter
4. Beide Flow-Funktionen akzeptieren einen optionalen `planner_model`-Parameter — wenn gesetzt, überschreibt er den Wert aus `.env`

`reporter_model` und `validator_model` sind nicht betroffen und nutzen weiterhin die Konfiguration aus `.env`.

Um Modelle hinzuzufügen oder zu entfernen: `AVAILABLE_MODELS` in `src/event_client.py` aktualisieren **und**
die Änderung in `ui/dion-data.jsx` spiegeln — die beiden Listen werden aktuell manuell synchron gehalten.

---

## Konfiguration

Die Runtime liest folgende Werte aus Environment-Variablen, die typischerweise aus `.env` geladen werden.

| Variable | Zweck |
|----------|-------|
| `MODEL_PROVIDER` | `openai` oder `openrouter` |
| `OPENAI_API_KEY` | OpenAI-Key |
| `OPENROUTER_API_KEY` | OpenRouter-Key |
| `OPENROUTER_BASE_URL` | OpenRouter-API-Base-URL (Default: `https://openrouter.ai/api/v1`) |
| `OPENROUTER_APP_NAME` | Optionaler OpenRouter-App-Title-Header |
| `OPENROUTER_SITE_URL` | Optionaler OpenRouter-Referer-Header |
| `OPENAI_PLANNER_MODEL` | Modellname für Dion_Planner (OpenAI) |
| `OPENAI_REPORTER_MODEL` | Modellname für Dion_Reporter (OpenAI) |
| `OPENAI_VALIDATOR_MODEL` | Modellname für Dion_Validator (OpenAI) |
| `OPENROUTER_PLANNER_MODEL` | Default-Modellname für Dion_Planner (OpenRouter) — wird pro Request überschrieben, wenn der Nutzer in der UI ein Modell auswählt |
| `OPENROUTER_REPORTER_MODEL` | Modellname für Dion_Reporter (OpenRouter) |
| `OPENROUTER_VALIDATOR_MODEL` | Modellname für Dion_Validator (OpenRouter) |
| `PLANNER_MODEL` | Provider-unabhängiger Fallback für das Planner-Modell |
| `REPORTER_MODEL` | Provider-unabhängiger Fallback für das Reporter-Modell |
| `VALIDATOR_MODEL` | Provider-unabhängiger Fallback für das Validator-Modell |
| `CITY_URL` | Eventim-City-Lookup-Endpoint |
| `EVENT_URL` | Eventim-Event-Fetch-Endpoint |
| `DZT_URL` | DZT-RPC-Endpoint |
| `DZT_API_KEY` | API-Key für DZT |
| `REPORTS_DIR` | Pfad für gespeicherte Reports (Default: `outputs/reports/`) |

---

## Empfohlene Lesereihenfolge

Für jemanden, der neu im Projekt ist:

1. `README.md` — Setup- und Run-Anleitung
2. `DEMO_CASES.md` — verstehen, was das System liefern soll
3. `src/schemas.py` — die Datenverträge lernen, bevor man Logik anfasst
4. `src/instructions.py` — verstehen, wie das Agent-Verhalten gesteuert wird
5. `src/event_client.py` — den Laufzeit-Flow von Anfang bis Ende verfolgen
6. `ui/dion_api.py` — sehen, wie die API-Schicht den `UserRequest` baut, die Flows aufruft und Ergebnisse serialisiert
7. `ui/dion-app.jsx` — sehen, wie das Frontend Requests sendet und die Response rendert
8. `mcp_servers/mcp_servers.py` + `event_server.py` + `dzt_server.py` — die Tool-Schicht verstehen
