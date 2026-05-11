# Dion UI — Testbericht
**Datum:** 2026-05-06  
**Tester:** Claude (automatisierter UI-Test via Browser)  
**Backend:** FastAPI auf `localhost:7860`  
**Version:** v0.4.2

---

## Testrunde 3 — Nach Production-Ready-Fixes (v0.4.3)

**Datum:** 2026-05-09  
**Getestete Cases:** Case 1–5 (DEMO_CASES.md)  
**Modell:** `google/gemini-2.5-flash` (Default)  
**Zweck:** Verifikation der von Claude Code umgesetzten Fixes aus `Production_ready.md` (B-01, B-02, Q-01–Q-04)

### Übersicht Testergebnisse

| Case | Beschreibung | Ergebnis | Laufzeit | Status |
|------|-------------|----------|----------|--------|
| Case 1 | Rock Weekend Düsseldorf (EN) | ⚠️ 2 Events ✅, Sightseeing/Food 0 ❌, Date-Labels-Bug ❌ | 63s | `needs review` |
| Case 2 | Nur Food & Drinks Köln (DE) | ⚠️ 2 Food-Spots ✅, DZT-Tool-Regression ❌ | 36s | `needs review` |
| Case 3 | Free-Budget Day Leipzig (EN) | ❌ Crashed — Gemini JSON+Function-Call-Konflikt | 37s | `blocked` |
| Case 4 | Minimale Eingabe Hamburg (DE) | ✅ 2 Sightseeing, 2 Food, Timing-Fix ✅ | 69s | `needs review` |
| Case 5 | Follow-Up Revision | ⚠️ 30s ✅ (war 272s), Sightseeing-Constraint nicht eingehalten ❌ | 30s | `needs review` |

---

### ✅ Behobene Bugs (seit Testrunde 2)

- **BUG-R2-02 BEHOBEN** — Follow-Up-Timeout gelöst durch `_slim_core_result_for_followup()`: 272s → 30s ✅
- **BUG-R2-03 BEHOBEN** — Recommendation-Einstieg bei 0 Ergebnissen korrekt: kein positiver Einstieg mehr ✅
- **BUG-R2-04 BEHOBEN** — Validator-False-Positive "bar" durch Word-Boundary-Regex behoben ✅
- **BUG-R2-05 BEHOBEN** — Mittagessen jetzt um 13:00 geplant (Case 4) ✅
- **INFO-R2-01 BEHOBEN** — Progress-Messages erscheinen auf Deutsch wenn DE gewählt ist ✅

---

### 🔴 BUG-R3-01 — DZT `get_pois_by_criteria` Tool nicht gefunden (Regression)

**Priorität:** Critical  
**Bereich:** Backend / MCP-Server  
**Betrifft:** Case 2 (Köln), Case 4 (Hamburg)

**Beschreibung:**  
Der DZT-MCP-Server gibt für `get_pois_by_criteria`-Aufrufe folgenden Fehler zurück:

> *`{'content': [{'type': 'text', 'text': 'tool "get_pois_by_criteria" not found'}]}`*

Der Agent fällt auf allgemeines Wissen zurück und erfindet Orte. In Case 4 erscheint zusätzlich `"DZT API unavailable"` im Ergebnis. Dieses Verhalten ist eine **Regression** — in Testrunde 2 funktionierte DZT für Hamburg und Köln.

**Wahrscheinliche Ursache:**  
Eine der Code-Änderungen aus den Production-Ready-Fixes hat die Tool-Registrierung oder den Tool-Namen im DZT-MCP-Server verändert.

**Verbesserungsvorschlag:**  
1. `mcp_servers/dzt_server.py` prüfen — wurde der Tool-Name oder die Signatur von `get_pois_by_criteria` geändert?
2. Tool-Name in `instructions.py` oder im Agent-Setup angleichen
3. MCP-Server neu starten und Tool-Listing verifizieren: `list_tools()` sollte `get_pois_by_criteria` enthalten

---

### 🟡 BUG-R3-02 — Gemini: JSON-Mode inkompatibel mit Function Calling (Regression)

**Priorität:** Low — Gemini ist nur temporäres Test-Modell, kein Production-Modell  
**Bereich:** Backend / Modell-Integration  
**Betrifft:** Case 3 (Leipzig) — vollständiger Absturz  
**Hinweis:** Nur relevant wenn Gemini weiterhin verwendet wird. Falls das Production-Modell kein Gemini ist, kann dieser Bug ignoriert werden — trotzdem dokumentiert damit der Fehler bekannt ist.

**Beschreibung:**  
Case 3 schlägt nach 37s komplett fehl mit:

> *"Function calling with a response mime type: 'application/json' is unsupported"*

`response_mime_type: 'application/json'` und Function Calling (Tool Use) sind bei Gemini mutually exclusive. Eine der Production-Ready-Änderungen hat offenbar `response_mime_type: 'application/json'` zum API-Call hinzugefügt, ohne zu beachten, dass der Agent MCP-Tools verwendet.

**Wahrscheinliche Ursache:**  
Wahrscheinlich aus dem Versuch entstanden, strukturierten JSON-Output zu erzwingen — aber das kollidiert mit Gemini's Function-Calling-Modus.

**Verbesserungsvorschlag:**  
1. In `event_client.py` (oder `dion_api.py`) prüfen, ob `response_mime_type` im API-Call-Body gesetzt wird
2. `response_mime_type` entfernen — strukturiertes JSON wird bereits durch den Agent-Output-Schema erzwungen, nicht durch den MIME-Type
3. Alternativ: bedingtes Setzen nur wenn kein Tool-Use aktiv ist

---

### 🟡 BUG-R3-03 — "Invalid Date" in Itinerary-Day-Headern (Frontend)

**Priorität:** Major  
**Bereich:** Frontend / Date-Rendering  
**Betrifft:** Case 1 (Düsseldorf)

**Beschreibung:**  
Im Itinerary-Bereich des UI erscheinen die Tages-Header als **"Invalid Date"** statt als lesbares Datum (z. B. "Friday, May 22"). Das deutet auf ein fehlgeschlagenes `new Date(day_label)` im JSX hin — wahrscheinlich weil `day_label` ein Format zurückgibt, das der Browser nicht parst.

**Verbesserungsvorschlag:**  
In `dion-output.jsx` die Date-Formatierung absichern:
```jsx
const formatDayLabel = (label) => {
  const d = new Date(label);
  if (isNaN(d)) return label;  // Fallback: raw string anzeigen
  return d.toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long' });
};
```

---

### 🟡 BUG-R3-04 — Event-Scheduling-Konflikt: Zwei Events gleichzeitig (Case 1)

**Priorität:** Major  
**Bereich:** Backend / Itinerary-Logik  
**Betrifft:** Case 1 (Düsseldorf)

**Beschreibung:**  
Der Agent plant zwei Events gleichzeitig auf denselben Timeslot:
- **Element of Crime** — Samstag 23. Mai, 20:00 Uhr
- **Broilers** — Samstag 23. Mai, 20:00 Uhr

Beide Events werden im Itinerary auf 20:00 am selben Tag platziert, was physisch unmöglich ist. Der Validator hat diesen Konflikt nicht erkannt.

**Verbesserungsvorschlag:**  
1. Im Validator prüfen, ob zwei Event-Stops am selben Tag dieselbe Start-Zeit haben → Warning ausgeben
2. In der Agent-Instruction: "Wenn zwei Events gleichzeitig stattfinden, wähle nur eines aus oder verteile sie auf verschiedene Tage"
3. Alternativ: Den Agent anweisen, bei Überschneidungen das relevantere Event (nach Vibe-Match) auszuwählen

---

### 🟡 BUG-R3-05 — Follow-Up: Sightseeing-Constraint nicht eingehalten (Case 5)

**Priorität:** Major  
**Bereich:** Backend / Follow-Up Agent  
**Betrifft:** Case 5 (Follow-Up Revision)

**Beschreibung:**  
Der Follow-Up-Request war: *"cut sightseeing down to max 2 stops."*  
Das Ergebnis enthält jedoch 3 Sightseeing-Stops. Die Instruction wurde teils ignoriert.

**Verbesserungsvorschlag:**  
1. In `_slim_core_result_for_followup()`: Follow-Up-Request explizit als Constraint-Liste mitgeben, damit der Agent die Änderungen priorisiert
2. Agent-Instruction für Follow-Ups: "Constraints im Follow-Up (max X, entferne Y) haben höchste Priorität — sie müssen exakt eingehalten werden"

---

### 🟢 BUG-R3-06 — Nicht-sequiturer Satz in Follow-Up-Recommendation (Case 5)

**Priorität:** Low  
**Bereich:** Backend / Agent-Output  
**Betrifft:** Case 5 (Follow-Up Revision)

**Beschreibung:**  
Die Follow-Up-Recommendation enthält einen inhaltlich nicht passenden Satz über Wetter oder eine unzusammenhängende Aussage, die nicht zum restlichen Plan passt. Wahrscheinlich ein Artefakt des komprimierten Context-Formats, bei dem der Agent einen nicht passenden Textteil aus dem Vorkontext übernimmt.

**Verbesserungsvorschlag:**  
In der Follow-Up-Instruction ergänzen: "Die Recommendation muss ausschließlich auf den aktualisierten Plan eingehen — keine Sätze aus dem vorherigen Plan kopieren, die nicht mehr zutreffen."

---

### Case-Detailergebnisse Testrunde 3

**Case 1 — Düsseldorf (Highlights):**
- ✅ MCP-Fallback funktioniert — 2 Events gefunden (Element of Crime, Broilers) trotz ursprünglich 0 Ergebnissen
- ✅ Laufzeit 63s (verbessert gegenüber 139s in R2)
- ❌ DZT liefert 0 Sightseeing + 0 Food (separates DZT-Problem, BUG-R3-01)
- ❌ "Invalid Date" in allen Itinerary-Day-Headern (BUG-R3-03)
- ❌ Zwei Events gleichzeitig 20:00 Uhr am selben Tag (BUG-R3-04)

**Case 2 — Köln (Highlights):**
- ✅ 2 Food-Spots gefunden
- ✅ Progress-Messages auf Deutsch ✅
- ❌ DZT `get_pois_by_criteria` not found — Regression (BUG-R3-01)
- ✅ Laufzeit 36s

**Case 3 — Leipzig (vollständiger Absturz):**
- ❌ Crash nach 37s: *"Function calling with response_mime_type 'application/json' is unsupported"*
- Kein Ergebnis geliefert — Case komplett blockiert (BUG-R3-02)

**Case 4 — Hamburg (Highlights):**
- ✅ 2 Sightseeing + 2 Food trotz DZT-Problemen
- ✅ Lunch korrekt um 13:00 (BUG-R2-05 behoben)
- ✅ Progress-Messages auf Deutsch
- ✅ Keine Personalisierung ohne Namen
- ❌ DZT API unavailable (BUG-R3-01)
- ✅ Laufzeit 69s (verbessert von 114s)

**Case 5 — Follow-Up (Highlights):**
- ✅ Completed in 30s (war 272s Timeout → BUG-R2-02 behoben)
- ✅ Selektive Revision — unbeteiligte Stops bleiben erhalten
- ✅ Brunch-Stop konkret (Name + Adresse)
- ❌ 3 Sightseeing-Spots statt max. 2 (BUG-R3-05)
- ❌ Nicht-sequiturer Satz in Recommendation (BUG-R3-06)

---

## Testrunde 2 — Neue Demo Cases (v0.4.2)

**Datum:** 2026-05-06  
**Getestete Cases:** Case 1–5 (neue DEMO_CASES.md)  
**Modell:** `google/gemini-2.5-flash` (Default)  
**Neue Modelle in Dropdown:** `z-ai/glm-4.7`, `moonshotai/kimi-k2.6`

### Übersicht Testergebnisse

| Case | Beschreibung | Ergebnis | Laufzeit | Status |
|------|-------------|----------|----------|--------|
| Case 1 | Rock Weekend Düsseldorf (EN) | ❌ 0 Events, 0 Sightseeing, 0 Food | 139s | `blocked` |
| Case 2 | Nur Food & Drinks Köln (DE) | ✅ 2 Food-Spots, sauber | 30s | `ready` |
| Case 3 | Free-Budget Day Leipzig (EN) | ❌ 0 Events, 0 Sightseeing | 127s | `needs review` |
| Case 4 | Minimale Eingabe Hamburg (DE) | ✅ 5 Sightseeing, 2 Food | 114s | `ready` |
| Case 5 | Follow-Up Revision | ❌ Fehler nach 272s | 272s | `blocked` |

---

### ✅ Behobene Bugs (seit letzter Testrunde)

- **BUG-C1-04 BEHOBEN** — Report-Sektionen haben jetzt Inhalt (`body_markdown` gefüllt)
- **BUG-C1-03 BEHOBEN** — Kein "überarbeiteten"-Sprachgebrauch beim ersten Run mehr

---

### 🔴 BUG-R2-01 — MCP-Tools finden keine Daten für mehrere Städte

**Priorität:** Critical  
**Bereich:** Backend / MCP-Tool-Abdeckung  
**Betrifft:** Case 1 (Düsseldorf), Case 3 (Leipzig)

**Beschreibung:**  
Bei Düsseldorf und Leipzig liefern alle MCP-Tools 0 Ergebnisse — weder Events, noch Sightseeing, noch Food. Bei Hamburg (Case 4) funktioniert das Sightseeing. Bei Köln (Case 2) funktioniert Food. Das deutet auf eine lückenhafte Datenabdeckung oder Query-Probleme bei bestimmten Kombinationen (Datum + Vibe + Stadt) hin.

**Konkrete Fehlermeldungen (Case 1):**
- `"Could not retrieve any sightseeing spots for the requested criteria"`
- `"Could not retrieve any food and drink spots for the requested criteria"`

**Verbesserungsvorschlag:**
1. Fallback-Suche ohne Vibe-Filter, wenn erster Query 0 Ergebnisse liefert
2. Bei 0 Events: breiter suchen (anderen Zeitraum, andere Kategorien)
3. Logging einbauen, welcher MCP-Tool-Call scheitert, um Ursache einzugrenzen

---

### 🔴 BUG-R2-02 — Follow-Up schlägt nach ~270s mit "invalid tool call" fehl

**Priorität:** Critical  
**Bereich:** Backend / Follow-Up Agent  
**Betrifft:** Case 5

**Beschreibung:**  
Der Follow-Up-Aufruf scheitert nach 272 Sekunden mit:
> *"The selected model generated an invalid tool call. Please try a different model."*

Der Agent bleibt sehr lange im Schritt "Writing the report" (von 72s bis 272s), bevor der Fehler auftritt. Wahrscheinliche Ursache: Im zweiten Iteration-Context sind bereits alle Tool-Antworten des ersten Runs enthalten — was den Context massiv vergrößert und dazu führt, dass das Modell einen fehlerhaften Tool-Call generiert.

**Verbesserungsvorschlag:**
1. Context-Kompression zwischen Iterationen (Summary des vorherigen Plans statt kompletter History)
2. Gezieltes Error-Handling für "invalid tool call" — eigene Fehlermeldung statt rohem Fehler
3. Follow-Up sollte nur die Delta-Änderungen an das Modell schicken, nicht den kompletten Konversationsverlauf

---

### 🟡 BUG-R2-03 — Recommendation-Widerspruch bei 0 Ergebnissen (Case 3)

**Priorität:** Major  
**Bereich:** Backend / Agent-Instruction

**Beschreibung:**  
Die Recommendation beginnt mit:
> *"I found some events and sightseeing options in Leipzig for your trip on June 6th, 2026."*

Unmittelbar danach:
> *"Unfortunately, there were no free events found..."*

Der erste Satz behauptet, etwas gefunden zu haben — der zweite widerspricht dem direkt.

**Verbesserungsvorschlag:**  
Agent-Instruction anpassen: Wenn 0 Ergebnisse vorliegen, darf der erste Satz nicht suggerieren, dass etwas gefunden wurde. Alternativer Einstieg: *"I searched for events and sightseeing options in Leipzig, but unfortunately..."*

---

### 🟡 BUG-R2-04 — Validator-False-Positive: "bar" in Recommendation ohne Bar-Spot

**Priorität:** Low  
**Bereich:** Backend / Validator

**Beschreibung:**  
In Case 4 (Hamburg) erscheint die Warnung:
> *"Validation issue remains: The recommendation emphasizes bar or drink options, but no bar venue appears in food_and_drink_spots."*

Die Recommendation erwähnt jedoch keine Bars — es handelt sich um einen False Positive im Validator. Dieser prüft anscheinend auf bestimmte Keywords zu aggressiv.

**Verbesserungsvorschlag:**  
Validator-Logik verfeinern: Nur warnen, wenn spezifische Bar-Keywords explizit in der Recommendation vorkommen.

---

### 🟡 BUG-R2-05 — Mittagessen-Stop um 15:00 Uhr (Case 4)

**Priorität:** Low  
**Bereich:** Backend / Itinerary-Logik

**Beschreibung:**  
Im Hamburg-Itinerary (Case 4) wird das Mittagessen ("Mittagessen im KARMA KITCHEN") auf 15:00 Uhr geplant. Das entspricht eher einem späten Nachmittag als Mittagessen.

**Verbesserungsvorschlag:**  
Itinerary-Logik überprüfen: Mittagessen-Stops sollten zwischen 12:00 und 14:00 geplant werden. Alternativ die Bezeichnung anpassen ("Spätes Mittagessen" oder "Nachmittagssnack").

---

### ℹ️ INFO-R2-01 — Progress-Messages weiterhin auf Englisch bei DE-Output

**Priorität:** Info  
**Bereich:** Frontend / Lokalisierung

**Beschreibung:**  
Auch in Testrunde 2 erscheinen die Progress-Steps ("Searching for events and places…", "Building the plan…") auf Englisch, obwohl Deutsch als Ausgabesprache gewählt ist. Bereits in Testrunde 1 dokumentiert (INFO-C1-01) — noch nicht behoben.

---

### Case-Detailergebnisse Testrunde 2

**Case 2 — Köln (Highlights):**
- ✅ Seiberts Classic Bar & Liquid Kitchen + Ox & Klee (Michelin) gefunden
- ✅ Vegetarischer Kontext im Itinerary berücksichtigt
- ✅ 0 Warnings — sauberster Run aller Tests
- ✅ Scope korrekt: `scope: food` in Header angezeigt

**Case 4 — Hamburg (Highlights):**
- ✅ Ohne Budgetangabe kein Crash
- ✅ 5 Sightseeing-Spots, 2 Food-Spots, vollständiges Itinerary
- ✅ Kein "Hi, " ohne Namen
- ✅ Graceful degradation bei 0 Events mit klarer Warnung auf Deutsch

---

## Testrunde 1 — Erste Tests (v0.4.x)

**Datum:** 2026-05-06  
**Getestete Fälle:** Case 1 (JGA Hamburg, DE), Case 2 (Underground Leipzig, EN)  
**Modelle getestet:** `deepseek/deepseek-v3.2`, `anthropic/claude-haiku-4-5`, `google/gemini-2.5-flash`

---

## Allgemeine UI-Befunde (alle Cases)

### 🔴 BUG-UI-01 — Horizontaler Overflow bei Viewports < 1440px

**Priorität:** Critical  
**Bereich:** Frontend / Layout

**Beschreibung:**  
Die Seite ist für 1440px Breite ausgelegt (`<meta name="viewport" content="width=1440">`), überläuft aber auf kleineren Bildschirmen horizontal. Der "Build plan with Dion"-Button ist auf normalen Laptops (1280–1366px) nicht sichtbar und kann nicht angeklickt werden.

**Beobachtung:**  
- Bei 1294px Viewport ist der Button rechts abgeschnitten
- Der dritte Scope-Toggle ("Food & Drinks") ist ebenfalls abgeschnitten
- Die Topbar-Tabs gehen rechts aus dem Bild

**Verbesserungsvorschlag:**  
```css
/* In der Haupt-CSS: responsive max-width statt fixem width */
.main-content {
  max-width: 1440px;
  width: 100%;
  overflow-x: hidden;
}
```
Alternativ: `<meta name="viewport" content="width=device-width, initial-scale=1">` setzen und Layout auf `min-width: 1100px` anpassen.

---

### 🟡 BUG-UI-02 — Babel-Warnung in der Konsole

**Priorität:** Low  
**Bereich:** Frontend / Build

**Beschreibung:**  
Die JSX-Dateien werden im Browser durch Babel Standalone kompiliert. Das verursacht eine Konsolenwarnung und ist für Production ungeeignet (langsamere Ladezeit, kein Caching).

**Verbesserungsvorschlag:**  
JSX-Dateien vor dem Deployment vorcompilieren (z. B. mit Vite oder esbuild). Die resultierenden `.js`-Dateien statt `.jsx` einbinden.

---

## Case 2 — Underground-Wochenende Leipzig (EN)

**Eingabe:** Leipzig, Vibe: techno/minimal/dark/underground, Sightseeing free only: Yes  
**Erwartetes Ergebnis:** Erfolgreicher Plan mit Underground-Events  
**Tatsächliches Ergebnis:** ❌ Alle drei Modelle schlagen fehl

---

### 🔴 BUG-C2-01 — Standardmodell schlägt fehl (Context-Overflow)

**Priorität:** Critical  
**Bereich:** Backend / Modellkonfiguration

**Beschreibung:**  
`deepseek/deepseek-v3.2` (das Standardmodell) schlägt bei einer normalen Planungsanfrage fehl. OpenRouter gibt einen 400-Fehler zurück:

> *"This endpoint's maximum context length is 163840 tokens. However, you requested about 295,656 tokens (288,186 text + 7,470 tool input)."*

Das Modell hat ein Kontextfenster von 163k Tokens, die Agent-Prompts + MCP-Tool-Antworten benötigen jedoch ca. 295k Tokens.

**Verbesserungsvorschlag:**  
1. `deepseek/deepseek-v3.2` aus der Modellliste entfernen oder als "nicht empfohlen" markieren
2. Ein Modell mit größerem Kontextfenster als Standard setzen (z. B. `google/gemini-2.5-flash` mit 1M Tokens)
3. Im Backend `_handle_error` einen gezielten Check für Context-Length-Fehler ergänzen:

```python
if 'maximum context length' in msg.lower() or 'context_length_exceeded' in msg.lower():
    raise HTTPException(
        status_code=422,
        detail='Das gewählte Modell hat ein zu kleines Kontextfenster für diesen Request. '
               'Bitte wähle ein anderes Modell (z. B. Gemini 2.5 Flash).'
    )
```

---

### 🔴 BUG-C2-02 — claude-haiku-4-5 schlägt fehl (Tool-Schema zu groß)

**Priorität:** Critical  
**Bereich:** Backend / Modellkonfiguration

**Beschreibung:**  
`anthropic/claude-haiku-4-5` via OpenRouter (Amazon Bedrock) gibt folgenden Fehler zurück:

> *"The compiled grammar is too large, which would cause performance issues. Simplify your tool schemas or reduce the number of strict tools."*

Die MCP-Tool-Schemas sind für Amazon Bedrock zu komplex.

**Verbesserungsvorschlag:**  
1. `anthropic/claude-haiku-4-5` aus der Modellliste entfernen bis Kompatibilität geprüft ist
2. Alternativ: Tool-Schemas für Bedrock-kompatible Modelle vereinfachen
3. Im Backend prüfen, ob das Modell "Bedrock-backed" ist, und ggf. warnen

---

---

## Case 1 — JGA-Wochenende Hamburg (DE)

**Eingabe:** Hamburg, Name: Sara, Gruppe: 6, Budget: 80–250 €, Vibe: RnB/Party/Girly, Sprache: Deutsch  
**Modell:** `google/gemini-2.5-flash`  
**Tatsächliches Ergebnis:** ✅ Plan erfolgreich erstellt (70 Sekunden)

**Was gut funktioniert hat:**
- ✅ Deutsche Sprachausgabe durchgehend korrekt
- ✅ Sara wird namentlich angesprochen
- ✅ Constraints respektiert (kein Techno, Metal, Familienevents)
- ✅ Eventim-Links vorhanden und valide
- ✅ Report wird gespeichert (`.md`-Datei, 1.5 KB)
- ✅ Strukturierter Request/Result-Accordion funktioniert

---

### 🟡 BUG-C1-01 — Itinerary-Datum stimmt nicht mit Event-Datum überein

**Priorität:** Major  
**Bereich:** Backend / Agent-Logik

**Beschreibung:**  
Beide Events haben `start_datetime: 2026-05-23T20:00:00+02:00` (Samstag). Im Itinerary wird der Pub Crawl jedoch auf **Freitag 22. Mai** platziert, die Bordparty auf Samstag 23. Mai. Die Recommendation sagt explizit "Am Freitagabend starten wir mit dem Hamburg Pub Crawl" — obwohl das Event am Samstag stattfindet.

**Strukturiertes Ergebnis (Ausschnitt):**
```json
"events": [
  { "name": "Pubcrawl Hamburg - Ladies Night Party", "start_datetime": "2026-05-23T20:00:00+02:00" },
  { "name": "Original Hamburger Bordparty",          "start_datetime": "2026-05-23T20:00:00+02:00" }
],
"itinerary": [
  { "day_label": "2026-05-22", "stops": [{ "title": "Pubcrawl Hamburg..." }] },
  { "day_label": "2026-05-23", "stops": [{ "title": "Original Hamburger Bordparty" }] }
]
```

**Verbesserungsvorschlag:**  
Im Validator prüfen, ob `day_label` des Itinerary-Stops mit dem Datum aus `start_datetime` des verlinkten Events übereinstimmt. Bei Abweichung entweder korrigieren oder eine Warning ausgeben.

---

### 🟡 BUG-C1-02 — Food & Drinks: 0 Spots trotz aktiviertem Scope

**Priorität:** Major  
**Bereich:** Backend / Agent-Logik

**Beschreibung:**  
`food_drink_enabled: true` war gesetzt, dennoch wurden 0 Food/Drink-Spots gefunden. Der Agent selbst gibt 2 Warnings aus:
- *"The recommendation mentions bars/drinks, but no specific bar or drink spot could be found for food_and_drink_spots."*
- *"Validation issue remains: The recommendation emphasizes bar or drink options, but no bar venue appears in food_and_drink_spots."*

Die Recommendation spricht explizit von "Cocktails trinken", nennt aber kein konkretes Lokal.

**Verbesserungsvorschlag:**  
1. Wenn Food & Drinks aktiviert, aber 0 Spots gefunden wurden: Fallback-Suche starten (z. B. allgemeine Bars/Cocktailbars in der Stadt)
2. In der Recommendation keine Food/Drink-Versprechungen machen, wenn keine Spots verfügbar sind (Agent-Instruction anpassen)
3. Im UI: bei 0 Spots trotz aktiviertem Scope eine auffälligere Warnung zeigen (aktuell zeigt der Result-Header nur "0" ohne Kontext)

---

### 🟡 BUG-C1-03 — Recommendation-Text impliziert fälschlicherweise eine Revision

**Priorität:** Low  
**Bereich:** Backend / Agent-Instruction

**Beschreibung:**  
Die erste Sentence der Recommendation lautet:
> *"Hallo Sara, für euren Junggesellinnenabschied in Hamburg habe ich einen **überarbeiteten und noch besseren Plan** zusammengestellt!"*

"Überarbeiteten" impliziert, dass es sich um eine Follow-Up-Revision handelt — es ist aber ein komplett neuer erster Plan.

**Verbesserungsvorschlag:**  
In den Agent-Instructions klarstellen, dass der erste Plan-Run keine Revisions-Sprache verwenden soll. Die Follow-Up-Instructions und die First-Run-Instructions sollten verschiedene Formulierungsvorgaben haben.

---

### 🟡 BUG-C1-04 — Report-Sektionen leer im strukturierten Report-Accordion

**Priorität:** Low  
**Bereich:** Frontend / Report-Rendering

**Beschreibung:**  
Das "Show structured report data"-Accordion zeigt für alle Sektionen `body_markdown: ""`:
```json
"sections": [
  { "heading": "Events",              "body_markdown": "" },
  { "heading": "Sightseeing",         "body_markdown": "" },
  { "heading": "Food & Drinks",       "body_markdown": "" },
  { "heading": "Day-by-day itinerary","body_markdown": "" }
]
```

Der eigentliche Report ist in der `.md`-Datei vollständig vorhanden — er wird aber nicht in das Frontend-Datenobjekt übertragen.

**Verbesserungsvorschlag:**  
In `_serialize_result()` (in `dion_api.py`) den Markdown-Report-Inhalt in die `sections` einbauen, oder alternativ den Report-Text direkt als String zurückgeben und im Frontend rendern.

---

### 🟢 INFO-C1-01 — Laufzeit 70 Sekunden (Gemini 2.5 Flash)

**Priorität:** Info  
**Bereich:** Performance

**Beschreibung:**  
Der Plan wurde in 70 Sekunden erstellt. Das ist für ein agentic System akzeptabel, für eine produktive Demo aber an der Grenze. Progress-Steps wurden korrekt durchlaufen ("Searching for events and places… → Plan and report created successfully").

**Verbesserungsvorschlag:**  
Ladezeit-Erwartung in der UI kommunizieren (z. B. *"Dion braucht typischerweise 1–2 Minuten"*). Den Progress-Text auf Deutsch ausgeben wenn Deutsch gewählt ist (aktuell: englische Step-Messages auch bei DE-Output).

---

## Zusammenfassung & Priorisierung (alle Testrunden)

| ID | Beschreibung | Priorität | Status |
|----|-------------|-----------|--------|
| BUG-R3-01 | DZT `get_pois_by_criteria` not found (Regression R3) | 🔴 Critical | Offen |
| BUG-R3-02 | Gemini JSON-Mode + Function Calling Konflikt (Regression R3) | 🟢 Low | Offen — nur relevant wenn Gemini Production-Modell bleibt |
| BUG-R2-01 | MCP-Tools 0 Ergebnisse (Düsseldorf, Leipzig) | 🔴 Critical | ⚠️ Teilweise — Events-Fallback ✅, DZT noch offen |
| BUG-UI-01 | Horizontaler Overflow < 1440px | 🔴 Critical | ℹ️ Nicht relevant (Test-UI intern) |
| BUG-C2-02 | Haiku Tool-Schema zu groß | 🔴 Critical | Offen |
| BUG-R3-03 | "Invalid Date" in Itinerary-Day-Headern | 🟡 Major | Offen |
| BUG-R3-04 | Event-Scheduling-Konflikt: 2 Events gleichzeitig | 🟡 Major | Offen |
| BUG-R3-05 | Follow-Up: Sightseeing-Constraint nicht eingehalten | 🟡 Major | Offen |
| BUG-C1-01 | Itinerary-Datum != Event-Datum | 🟡 Major | Offen |
| BUG-C1-02 | Food & Drinks 0 Spots trotz aktiviert | 🟡 Major | ⚠️ Teilweise — Köln/Hamburg ✅, Düsseldorf noch offen |
| BUG-R3-06 | Nicht-sequiturer Satz in Follow-Up-Recommendation | 🟢 Low | Offen |
| BUG-UI-02 | Babel-Warnung in Konsole | 🟢 Low | ℹ️ Nicht relevant (Test-UI intern) |
| BUG-C2-01 | Standardmodell Context-Overflow (deepseek) | 🔴 Critical | ✅ Behoben (Modell entfernt) |
| BUG-R2-02 | Follow-Up "invalid tool call" nach 272s | 🔴 Critical | ✅ Behoben (30s in R3) |
| BUG-R2-03 | Recommendation-Widerspruch bei 0 Ergebnissen | 🟡 Major | ✅ Behoben |
| BUG-R2-04 | Validator-False-Positive "bar" | 🟢 Low | ✅ Behoben |
| BUG-R2-05 | Mittagessen-Stop um 15:00 Uhr | 🟢 Low | ✅ Behoben (jetzt 13:00) |
| BUG-C1-03 | "Überarbeiteten" bei First-Run | 🟢 Low | ✅ Behoben |
| BUG-C1-04 | Report-Sektionen leer im Accordion | 🟢 Low | ✅ Behoben |
| INFO-R2-01 | Progress-Messages nicht auf Deutsch | ℹ️ Info | ✅ Behoben |

### Empfohlene Sofortmaßnahmen (vor nächster Demo)

1. **DZT-Server-Regression reparieren** — Tool-Name `get_pois_by_criteria` ist nach den R3-Fixes nicht mehr gefunden (BUG-R3-01)
2. **Invalid-Date-Labels im Frontend fixen** — `day_label`-Format wird im Browser nicht korrekt geparst (BUG-R3-03)
3. **Event-Scheduling-Konflikt prüfen** — Validator sollte zwei Events am selben Timeslot erkennen (BUG-R3-04)
4. **Gemini JSON-Mode** (BUG-R3-02) — nur fixen wenn Gemini Production-Modell bleibt, sonst ignorieren

---

## Token-Verbrauch & Kostenberechnung

### Gemessene Werte (aus Fehlerresponse deepseek, Case 2)

| Typ | Tokens |
|-----|--------|
| Text-Input (Prompt + MCP-Antworten) | ~288.000 |
| Tool-Input | ~7.500 |
| **Gesamt Input** | **~295.500** |
| Output | nicht gemessen (Run fehlgeschlagen) |

Das ist ein **sehr hoher Input-Wert** — der Agent lädt offenbar große MCP-Antworten vollständig in den Kontext. Output dürfte im Vergleich klein sein (typisch ~2.000–5.000 Tokens für den strukturierten Plan).

### Empfehlung: Token-Anzeige im UI einbauen

Um Modelle kosteneffizient vergleichen zu können, sollte das Backend die Token-Nutzung aus der OpenRouter-Antwort zurückgeben und die UI sie anzeigen.

**Schritt 1 — Backend (`dion_api.py`):** Usage aus dem Agent-Result extrahieren und zurückgeben:

```python
# In _serialize_result() am Ende ergänzen:
usage = result.get('usage')  # falls das agents SDK usage zurückgibt
return {
    ...bisherige Felder...,
    'token_usage': {
        'input_tokens': usage.input_tokens if usage else None,
        'output_tokens': usage.output_tokens if usage else None,
    }
}
```

Falls das agents SDK keine Usage direkt liefert, kann sie über einen OpenRouter-Middleware-Hook erfasst werden (OpenRouter gibt `usage` im Response-Body zurück).

**Schritt 2 — Frontend (`dion-output.jsx` oder Result-Block):** Im Result-Header anzeigen:

```jsx
{plan.token_usage?.input_tokens && (
  <div className="token-info">
    <span>Input: {(plan.token_usage.input_tokens / 1000).toFixed(1)}k Tokens</span>
    <span>Output: {(plan.token_usage.output_tokens / 1000).toFixed(1)}k Tokens</span>
  </div>
)}
```

### Modellkosten-Vergleich (OpenRouter, Stand Mai 2026 — vor Auswahl prüfen)

| Modell | Input ($/1M) | Output ($/1M) | Kontext | Status |
|--------|-------------|---------------|---------|--------|
| deepseek/deepseek-v3.2 | ~$0.14 | ~$0.28 | 163k | ❌ Zu kleines Kontextfenster |
| anthropic/claude-haiku-4-5 | ~$0.80 | ~$4.00 | 200k | ❌ Bedrock-Schema-Fehler |
| google/gemini-2.5-flash | ~$0.15 | ~$0.60 | 1M | ✅ Funktioniert |

Bei ~295k Input-Tokens und ~3k Output-Tokens pro Run kostet ein Gemini-2.5-Flash-Run ca. **$0.046** (~4,6 Cent). Das ist sehr günstig.

---

## Neue Modellauswahl — basierend auf τ²-Bench Leaderboard

**Hintergrund:** τ²-Bench (Tau-2 Bench) von Sierra Research testet genau die Fähigkeiten, die Dion benötigt: ein Agent koordiniert mit einem User über Tools in einer gemeinsamen Umgebung. Das macht diesen Benchmark besonders aussagekräftig für agentic Event-Planer wie Dion.

**Quelle:** https://artificialanalysis.ai/evaluations/tau2-bench

### Aktualisierte Modellliste in `event_client.py`

```python
AVAILABLE_MODELS = [
    'google/gemini-2.5-flash',    # ✅ Bewährt, funktioniert, 1M Kontext
    'z-ai/glm-4.7',               # 🥇 #1 auf τ²-Bench (98.8%)
    'moonshotai/kimi-k2.6',       # 🆕 ~96% auf τ²-Bench, großes Kontextfenster
    'anthropic/claude-haiku-4-5', # ⚠️  Bedrock-Schema-Problem noch offen
]
DEFAULT_MODEL = AVAILABLE_MODELS[0]  # google/gemini-2.5-flash
```

`deepseek/deepseek-v3.2` wurde entfernt (Kontextfenster zu klein für Dion).

### τ²-Bench Scores der aktuellen Modellliste

| Modell | τ²-Bench Score | Kontext | Status |
|--------|---------------|---------|--------|
| `google/gemini-2.5-flash` | 83.3% | 1M | ✅ Default, bewährt |
| `z-ai/glm-4.7` | **98.8%** (Platz 1) | groß | ✅ Noch zu testen |
| `moonshotai/kimi-k2.6` | ~96.2% (Platz 11) | groß | ✅ Noch zu testen |
| `anthropic/claude-haiku-4-5` | ~59.9% | 200k | ⚠️ Bedrock-Schema-Fehler |

### Weitere interessante Modelle für spätere Tests

- **`qwen/qwen3-235b-a22b`** — Qwen3-Familie, ~97% auf τ²-Bench, Alibaba, sehr stark bei Tool-Use
- **`deepseek/deepseek-v4-flash`** — ~95.6% auf τ²-Bench, günstiger DeepSeek-Nachfolger mit deutlich größerem Kontext als v3.2

---

*Bericht erstellt von Claude — automatisierter Browsertest via Claude in Chrome*
