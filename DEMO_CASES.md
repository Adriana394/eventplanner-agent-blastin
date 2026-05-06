# Demo Cases & Testcheckliste

Dieses Dokument definiert die Demo- und Regressionsszenarien fuer `eventplanner-agent`.
Vor internen Reviews, Live-Demos oder groesseren Modell-/Konfigurationsaenderungen durchlaufen.

---

## Anleitung

1. Server starten: `uv run python ui/dion_api.py`
2. Demo Case ueber das Dropdown im UI laden
3. Plan absenden und Ergebnis pruefen: UI-Ausgabe, strukturiertes Ergebnis, Markdown-Report
4. Case-Status setzen: `ready` | `needs review` | `blocked`
5. Konkrete Probleme notieren, keine vagen Eindruecke

### Status-Skala

| Status         | Bedeutung                                           |
|----------------|------------------------------------------------------|
| `ready`        | Stabil genug fuer eine Live-Demo                     |
| `needs review` | Vielversprechend, muss aber nochmal geprueft werden  |
| `blocked`      | Aktuell nicht vorzeigbar                             |

---

## Globale Checkliste (gilt fuer JEDEN Case)

### Progress & UX
- [ ] Progress-Bar zeigt echte Schritte (nicht fake 10%/30%/60%/90%)
- [ ] Progress-Nachrichten erscheinen in der richtigen Sprache (EN oder DE je nach Sprachwahl)
- [ ] Kein UI-Freeze ohne Fortschrittsanzeige

### Strukturiertes Ergebnis
- [ ] Recommendation hat max. 5 Saetze
- [ ] Max. 3 Events in der UI-Ansicht (UIResult)
- [ ] Keine generischen Platzhalter-Stops (z.B. "Dinner in a fine restaurant", "Visit historic places")
- [ ] Jeder Sightseeing-Stop im Itinerary hat ein passendes Gegenpart in `sightseeing_spots`
- [ ] Jeder Food-Stop im Itinerary hat ein passendes Gegenpart in `food_and_drink_spots`
- [ ] Keine zeitlich ueberlappenden Stops im selben Tag

### Links & Quellen
- [ ] Eventim-Links sind direkt vorhanden (keine extra Validierung noetig)
- [ ] Nicht-Eventim-Links (Sightseeing, Food) sind entweder verifiziert oder auf `null` gesetzt
- [ ] Bei entfernten Links erscheint eine Warning im Ergebnis
- [ ] Kein toter Link in der UI sichtbar

### Report
- [ ] Markdown-Report wird korrekt gespeichert (Pfad in `outputs/reports/`)
- [ ] Report-Sprache stimmt mit der gewaehlten Sprache ueberein
- [ ] Report-Expander laesst sich oeffnen und zeigt valide Daten

### Fehlerverhalten
- [ ] Kein Python-Traceback sichtbar fuer den User

---

## Case 1: Rock Weekend Düsseldorf (EN)

**Ziel:** Vollstaendige Pipeline mit allen drei Scopes, 2 Naechte, englische Ausgabe, Vibe-Relevanz testen.

**Status:** `needs review`

### Inputs

| Feld                     | Wert                                      |
|--------------------------|-------------------------------------------|
| Sprache                  | English                                   |
| Name                     | Chris                                     |
| Stadt                    | Düsseldorf                                |
| Daten                    | 2026-05-22 bis 2026-05-24                 |
| Letzter Tag einbeziehen  | Nein                                      |
| Planungsmodus            | Full Trip                                 |
| Gruppengroesse           | 2                                         |
| Events                   | aktiviert                                 |
| Sightseeing              | aktiviert                                 |
| Food & Drinks            | aktiviert                                 |
| Event-Vibe               | rock, indie, alternative                  |
| Event-Kategorien         | Concert, Live Music                       |
| Zeitpraeferenz           | Evening                                   |
| Nur kostenlose Events    | Nein                                      |
| Sightseeing-Interessen   | Altstadt, Rheinufer, street art           |
| Sightseeing-Modus        | Mixed                                     |
| Nur kostenloses Sightsee.| Nein                                      |
| Budget                   | 120 – 350 EUR                             |
| Vermeiden                | Techno, Pop, Familienevents               |
| Freitext-Notizen         | (leer)                                    |

### Erwartetes Ergebnis
- Events passen zum Rock/Indie-Vibe (kein Techno, kein Pop, kein Familienprogramm)
- Sightseeing fokussiert auf Altstadt und Rheinufer
- Samstag (mittlerer Tag) hat eine sinnvolle Tagesstruktur
- Kein letzter Tag (Sonntag) im Itinerary
- Alle Texte und der Report auf Englisch

### Case-spezifische Checkliste
- [ ] Kein einziges Event ist Techno, Pop oder ein Familienformat
- [ ] Recommendation beschreibt Rock/Indie-Vibe, nicht generischen Stadtbesuch
- [ ] Samstag enthaelt Tages- und Abendstruktur
- [ ] Sonntag taucht nicht im Itinerary auf (include_last_day = false)
- [ ] Personalisierung: Chris wird erwaehnt

---

## Case 2: Nur Food & Drinks Köln (DE)

**Ziel:** Testen, dass das Deaktivieren von Events und Sightseeing vollstaendig funktioniert. Nur Food-Scope aktiv.

**Status:** `needs review`

### Inputs

| Feld                     | Wert                                                           |
|--------------------------|----------------------------------------------------------------|
| Sprache                  | Deutsch                                                        |
| Name                     | Jonas                                                          |
| Stadt                    | Köln                                                           |
| Daten                    | 2026-05-30 (ein Tag)                                           |
| Letzter Tag einbeziehen  | Ja                                                             |
| Planungsmodus            | Event or Day Trip                                              |
| Gruppengroesse           | 3                                                              |
| Events                   | deaktiviert                                                    |
| Sightseeing              | deaktiviert                                                    |
| Food & Drinks            | aktiviert                                                      |
| Zeitpraeferenz           | Evening                                                        |
| Budget                   | 60 – 180 EUR                                                   |
| Vermeiden                | Fast Food, Kettenrestaurants                                   |
| Freitext-Notizen         | Cocktails zuerst, danach schick essen. Einer ist Vegetarier.   |

### Erwartetes Ergebnis
- Keine Events und keine Sightseeing-Spots im Ergebnis
- Kein Event- oder Sightseeing-Stop im Itinerary
- Food-Empfehlungen sind konkret, nicht generisch
- Vegetarische Option wird beruecksichtigt
- Alle Texte und der Report auf Deutsch

### Case-spezifische Checkliste
- [ ] `events` Liste im CoreResult ist leer
- [ ] `sightseeing_spots` Liste im CoreResult ist leer
- [ ] Kein Event-Stop oder Sightseeing-Stop im Itinerary
- [ ] Kein Fast Food, keine Kettenrestaurants in den Empfehlungen
- [ ] Vegetarischer Kontext sichtbar (Report oder Empfehlung)
- [ ] Food-Spots sind konkret (Name, Adresse, kein Platzhalter)
- [ ] Progress-Nachrichten erscheinen auf Deutsch

---

## Case 3: Free-Budget Day Leipzig (EN)

**Ziel:** Strikte Constraint-Behandlung testen: free_only Events + free_only Sightseeing + kein Food-Scope.

**Status:** `needs review`

### Inputs

| Feld                     | Wert                                       |
|--------------------------|--------------------------------------------|
| Sprache                  | English                                    |
| Name                     | (leer)                                     |
| Stadt                    | Leipzig                                    |
| Daten                    | 2026-06-06 (ein Tag)                       |
| Letzter Tag einbeziehen  | Ja                                         |
| Planungsmodus            | Event or Day Trip                          |
| Gruppengroesse           | 2                                          |
| Events                   | aktiviert                                  |
| Sightseeing              | aktiviert                                  |
| Food & Drinks            | deaktiviert                                |
| Event-Vibe               | indie, alternative, experimental           |
| Event-Kategorien         | Free Concert, Open Air                     |
| Zeitpraeferenz           | Daytime                                    |
| Nur kostenlose Events    | Ja                                         |
| Sightseeing-Interessen   | street art, parks, Karl-Marx-Platz         |
| Sightseeing-Modus        | Outdoor                                    |
| Nur kostenloses Sightsee.| Ja                                         |
| Budget                   | 0 – 20 EUR                                 |
| Vermeiden                | paid clubs, expensive venues, nightlife    |

### Erwartetes Ergebnis
- Alle Events und Sightseeing-Spots sind kostenlos
- Keine Food/Drink-Empfehlungen und keine Food-Stops im Itinerary
- Falls zu wenig kostenlose Optionen: klare Warnung statt stiller Auffuellung
- Kein Nightlife (Vermeiden-Liste respektiert)
- Alle Texte und Report auf Englisch

### Case-spezifische Checkliste
- [ ] Kein Event hat einen Ticketpreis > 0
- [ ] Kein Sightseeing-Spot hat eine Eintrittgebuehr
- [ ] `food_and_drink_spots` Liste ist leer
- [ ] Kein Food-Stop im Itinerary
- [ ] Keine Nachtclub- oder Nightlife-Empfehlungen
- [ ] Falls wenig gefunden: Warning statt stiller Constraint-Verletzung
- [ ] Keine Personalisierung ohne Namen (kein "Hi, ")

---

## Case 4: Minimale Eingabe Hamburg (DE)

**Ziel:** Testen, dass sinnvolle Defaults greifen und kein Crash bei Minimal-Input entsteht.

**Status:** `needs review`

### Inputs

| Feld                     | Wert                    |
|--------------------------|-------------------------|
| Sprache                  | Deutsch                 |
| Name                     | (leer)                  |
| Stadt                    | Hamburg                 |
| Daten                    | 2026-06-13 (ein Tag)    |
| Alles andere             | Defaults                |

### Erwartetes Ergebnis
- Plan wird erfolgreich erstellt trotz minimaler Eingabe
- Events, Sightseeing und Food werden alle geliefert
- Kein leere Personalisierung (kein "Hi, " ohne Namen)
- Itinerary hat einen sinnvollen Tag
- Alle Texte und Report auf Deutsch

### Case-spezifische Checkliste
- [ ] Kein Fehler beim Absenden
- [ ] Events, Sightseeing und Food sind alle vorhanden
- [ ] Recommendation ist nicht leer oder generisch
- [ ] Kein "Hi, " ohne Namensangabe
- [ ] Itinerary hat mindestens 2 Stops
- [ ] Progress-Nachrichten erscheinen auf Deutsch

---

## Case 5: Follow-Up Revision (basiert auf Case 1)

**Ziel:** Beweisen, dass Follow-Up selektiv aendert statt alles neu aufzubauen.

**Status:** `needs review`

### Voraussetzung
Einen erfolgreichen Durchlauf von **Case 1** (Rock Weekend Düsseldorf) als Basis.

### Schritt 1: Case 1 ausfuehren
Case 1 vollstaendig durchlaufen und Ergebnis pruefen.

### Schritt 2: Follow-Up senden

> "Add a Sunday brunch spot, replace the Saturday dinner with something more upscale, and cut sightseeing down to max 2 stops."

### Erwartetes Ergebnis
- Samstag-Dinner wird durch eine hochwertigere Option ersetzt
- Sonntag-Brunch-Stop kommt neu hinzu
- Sightseeing auf max. 2 Spots reduziert
- Unveraenderte Events und Tagesstruktur bleiben stabil
- Report wird korrekt aktualisiert

### Case-spezifische Checkliste
- [ ] Follow-Up bewahrt unbeteiligte Tage und Stops
- [ ] Neues Brunch-Stop ist konkret (Name, kein Platzhalter)
- [ ] Sightseeing enthaelt nach Revision max. 2 Spots
- [ ] Validator flaggt keine neuen Inkonsistenzen
- [ ] Report spiegelt die aktualisierte Struktur wider
- [ ] Progress-Bar zeigt "Revising the current plan…"

---

## Erfolgskriterien

Das Projekt gilt als **demo-ready**, wenn:

1. **Alle 5 Cases** den Status `ready` haben
2. **Kein Case** hat den Status `blocked`
3. **Globale Checkliste** wird in jedem Case vollstaendig bestanden
4. **Kein sichtbarer Python-Traceback** in irgendeinem Case

### Qualitaets-Schwellen

| Bereich              | Minimum fuer "ready"                                |
|----------------------|------------------------------------------------------|
| Event-Relevanz       | Kein offensichtlich unpassendes Event                |
| Constraint-Einhaltung| free_only, disabled scopes, Vermeiden-Liste strikt   |
| Link-Qualitaet       | Keine toten Links in der UI sichtbar                 |
| Report-Qualitaet     | Lesbar, faktisch korrekt, richtige Sprache           |
| Progress-UX          | Echte Schritte sichtbar, richtige Sprache            |
| Follow-Up            | Selektive Aenderung, kein kompletter Neuaufbau       |
| Fehlerbehandlung     | Klare Meldungen, kein Crash                          |
