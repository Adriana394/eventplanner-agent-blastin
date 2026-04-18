# Demo Cases & Testcheckliste

Dieses Dokument definiert die Demo- und Regressionsszenarien fuer `eventplanner-agent`.
Vor internen Reviews, Live-Demos oder groesseren Modell-/Konfigurationsaenderungen durchlaufen.

---

## Anleitung

1. `uv run streamlit run src/dion_ui.py` starten
2. Jeden Case mit den angegebenen Inputs durchspielen
3. Ergebnis pruefen: UI-Ausgabe, strukturiertes Ergebnis (Expander), Markdown-Report
4. Case-Status setzen: `ready` | `needs review` | `blocked`
5. Konkrete Probleme notieren, keine vagen Eindruecke

### Status-Skala

| Status         | Bedeutung                                      |
|----------------|-------------------------------------------------|
| `ready`        | Stabil genug fuer eine Live-Demo                |
| `needs review` | Vielversprechend, muss aber nochmal geprueft werden |
| `blocked`      | Aktuell nicht vorzeigbar                        |

---

## Globale Checkliste (gilt fuer JEDEN Case)

Diese Punkte muessen bei jedem Durchlauf geprueft werden:

### Progress & UX
- [ ] Progress-Bar zeigt echte Schritte (nicht fake 10%/30%/60%/90%)
- [ ] Progress-Nachrichten erscheinen in der richtigen Sprache (EN oder DE je nach Sprachwahl)
- [ ] Progress-Schritte sind sinnvoll benannt (z.B. "Searching for events and places..." / "Events und Orte werden gesucht...")
- [ ] Kein UI-Freeze ohne Fortschrittsanzeige

### Strukturiertes Ergebnis
- [ ] Recommendation hat max. 5 Saetze
- [ ] Max. 5 Events im CoreResult
- [ ] Max. 3 Events in der UI-Ansicht (UIResult)
- [ ] Max. 5 Sightseeing-Stops pro Itinerary-Tag
- [ ] Keine generischen Platzhalter-Stops (z.B. "Dinner in a fine restaurant", "Visit historic places")
- [ ] Jeder Sightseeing-Stop im Itinerary hat ein passendes Gegenpart in `sightseeing_spots`
- [ ] Jeder Food-Stop im Itinerary hat ein passendes Gegenpart in `food_and_drink_spots`
- [ ] Keine zeitlich ueberlappenden Stops im selben Tag

### Links & Quellen
- [ ] Eventim-Links sind direkt vorhanden (keine extra Validierung noetig)
- [ ] Nicht-Eventim-Links (Sightseeing, Food) sind entweder verifiziert oder auf `null` gesetzt
- [ ] Bei entfernten Links erscheint eine Warning im Ergebnis
- [ ] Kein toter Link in der UI sichtbar (Button/Link fuehrt ins Leere)

### Report
- [ ] Markdown-Report wird korrekt gespeichert (Pfad in `outputs/reports/`)
- [ ] Report-Sprache stimmt mit der gewaehlten Sprache ueberein
- [ ] Report enthaelt keine erfundenen Fakten oder Preise
- [ ] Report-Expander ("Show structured report data") laesst sich oeffnen und zeigt valide Daten

### Fehlerverhalten
- [ ] Bei fehlenden Pflichtfeldern erscheint eine klare Fehlermeldung
- [ ] Kein Python-Traceback sichtbar fuer den User

---

## Case 1: Eleganter Wochenend-Staedtetrip (DE)

**Ziel:** Ausgewogene Planung mit Events, Food/Drinks und leichtem Sightseeing. Testet deutsche Sprachausgabe.

**Status:** `needs review`

### Inputs

| Feld                    | Wert                                     |
|-------------------------|------------------------------------------|
| Sprache                 | Deutsch                                  |
| Name                    | Adriana                                  |
| Stadt                   | Hannover                                 |
| Daten                   | Freitag bis Sonntag (3 Tage, naechstes WE) |
| Letzter Tag einbeziehen | Ja                                       |
| Planungsmodus           | Full Trip                                |
| Gruppengroesse          | 2                                        |
| Events                  | aktiviert                                |
| Sightseeing             | aktiviert                                |
| Food & Drinks           | aktiviert                                |
| Event-Vibe              | elegant, stilvoll, besonders             |
| Event-Kategorien        | Konzert, Show, Live-Performance          |
| Zeitpraeferenz          | Evening                                  |
| Nur kostenlose Events   | Nein                                     |
| Sightseeing-Interessen  | Architektur, Wahrzeichen, Stadtbild      |
| Sightseeing-Modus       | No preference                            |
| Nur kostenloses Sightsee.| Nein                                    |
| Budget                  | 150 - 300 EUR                            |
| Vermeiden               | Familienevents, Musicals                 |
| Freitext-Notizen        | (leer)                                   |

### Erwartetes Ergebnis
- Stimmiges Wochenend-Framing mit abendlichem Fokus
- Keine Musicals, Familienevents oder thematisch unpassende Inhalte
- Mittlerer Tag (Samstag) hat eine sinnvolle Tagesstruktur, nicht nur Abendprogramm
- Itinerary endet sauber am Sonntag
- Personalisierung: Adriana wird namentlich angesprochen

### Case-spezifische Checkliste
- [ ] Events passen zum gehobenen Ton (kein Comedy-Open-Mic, kein Kinderprogramm)
- [ ] Recommendation uebertreibt nicht (z.B. keine falschen "kostenlos"-Claims)
- [ ] Food/Drink-Empfehlungen passen zum Abend-Stil (kein Fast Food)
- [ ] Samstag enthaelt Tagesstruktur (Fruehstueck/Cafe, Sightseeing, dann Abend)
- [ ] Alle Texte in der UI und im Report sind auf Deutsch
- [ ] Progress-Nachrichten erscheinen auf Deutsch

---

## Case 2: Berlin Nightlife (EN)

**Ziel:** Relevanz der Nightlife-Auswahl und Event-Qualitaet unter Stress testen. Englische Ausgabe.

**Status:** `needs review`

### Inputs

| Feld                    | Wert                                     |
|-------------------------|------------------------------------------|
| Sprache                 | English                                  |
| Name                    | (leer)                                   |
| Stadt                   | Berlin                                   |
| Daten                   | Freitag bis Sonntag (2 Naechte)          |
| Letzter Tag einbeziehen | Ja                                       |
| Planungsmodus           | Full Trip                                |
| Gruppengroesse          | 2                                        |
| Events                  | aktiviert                                |
| Sightseeing             | aktiviert                                |
| Food & Drinks           | aktiviert                                |
| Event-Vibe              | techno, underground, late-night          |
| Event-Kategorien        | Club, Concert                            |
| Zeitpraeferenz          | Night                                    |
| Nur kostenlose Events   | Nein                                     |
| Sightseeing-Interessen  | viewpoints, neighborhoods                |
| Sightseeing-Modus       | Outdoor                                  |
| Nur kostenloses Sightsee.| Ja                                      |
| Budget                  | 100 - 250 EUR                            |
| Vermeiden               | musicals, theatre, family events         |
| Freitext-Notizen        | (leer)                                   |

### Erwartetes Ergebnis
- Event-Auswahl ist Nightlife-relevant (Clubs, Techno, elektronische Musik)
- Kein Tages-Filler (Musicals, Theater, Shows) als Event-Ersatz
- Sightseeing bleibt strikt kostenlos
- Keine namentliche Ansprache (Name leer)

### Case-spezifische Checkliste
- [ ] Kein einziges Event ist ein Musical, Theater oder Familienprogramm
- [ ] Sightseeing enthaelt keine Eintraege mit Eintrittspreis
- [ ] Recommendation beschreibt tatsaechlich Nightlife, nicht generischen Stadtbesuch
- [ ] Bar-Empfehlungen sind konkret (Name, Adresse), nicht generisch
- [ ] Alle Texte und der Report sind auf Englisch
- [ ] Progress-Nachrichten erscheinen auf Englisch
- [ ] Kein "Hi [Name]" oder aehnliche leere Personalisierung

---

## Case 3: Food-Fokus ohne Events (DE)

**Ziel:** Trip ohne Events, staerker auf Stadt und Kulinarik. Testet das Abschalten von Scopes und `include_last_day = false`.

**Status:** `needs review`

### Inputs

| Feld                    | Wert                                     |
|-------------------------|------------------------------------------|
| Sprache                 | Deutsch                                  |
| Name                    | Max                                      |
| Stadt                   | Hamburg                                  |
| Daten                   | Samstag bis Montag                       |
| Letzter Tag einbeziehen | Nein                                     |
| Planungsmodus           | Full Trip                                |
| Gruppengroesse          | 2                                        |
| Events                  | deaktiviert                              |
| Sightseeing             | aktiviert                                |
| Food & Drinks           | aktiviert                                |
| Sightseeing-Interessen  | Hafen, Wasserkante, Aussichtspunkte      |
| Sightseeing-Modus       | Outdoor                                  |
| Nur kostenloses Sightsee.| Nein                                    |
| Budget                  | 120 - 260 EUR                            |
| Vermeiden               | Museen                                   |
| Freitext-Notizen        | (leer)                                   |

### Erwartetes Ergebnis
- Kein einziges Event im Ergebnis oder Itinerary
- Montag (letzter Tag) taucht nicht im Itinerary auf
- Plan wirkt trotzdem komplett und nuetzlich ohne Event-Anker
- Natuerliche Mahlzeiten-Struktur (Fruehstueck, Mittagessen, Abendessen)

### Case-spezifische Checkliste
- [ ] `events` Liste im CoreResult ist leer
- [ ] Kein Event-Stop im Itinerary
- [ ] Itinerary enthaelt keinen Montag
- [ ] Food/Drink-Spots sind konkret und keine Platzhalter
- [ ] Keine Museen im Sightseeing (Vermeiden-Liste respektiert)
- [ ] Report erklaert die stadtfokussierte Richtung klar

---

## Case 4: Strenger Budget-Tag (EN)

**Ziel:** Strikte Constraint-Behandlung testen: free_only Events + free_only Sightseeing + kein Food.

**Status:** `needs review`

### Inputs

| Feld                    | Wert                                     |
|-------------------------|------------------------------------------|
| Sprache                 | English                                  |
| Name                    | (leer)                                   |
| Stadt                   | Leipzig                                  |
| Daten                   | Ein einzelner Tag                        |
| Letzter Tag einbeziehen | Ja                                       |
| Planungsmodus           | Event or Day Trip                        |
| Gruppengroesse          | 3                                        |
| Events                  | aktiviert                                |
| Sightseeing             | aktiviert                                |
| Food & Drinks           | deaktiviert                              |
| Event-Vibe              | casual, cultural                         |
| Event-Kategorien        | free concert, local event                |
| Zeitpraeferenz          | Daytime                                  |
| Nur kostenlose Events   | Ja                                       |
| Sightseeing-Interessen  | historic center                          |
| Sightseeing-Modus       | No preference                            |
| Nur kostenloses Sightsee.| Ja                                      |
| Budget                  | 0 - 60 EUR                               |
| Vermeiden               | nightlife                                |
| Freitext-Notizen        | (leer)                                   |

### Erwartetes Ergebnis
- Alle Events und Sightseeing-Spots sind kostenlos
- Kein Food/Drink-Bereich oder Food-Stops im Itinerary
- Ergebnis bleibt nuetzlich trotz enger Filter
- Falls zu wenig kostenlose Optionen: klare Warnung statt stille Auffuellung

### Case-spezifische Checkliste
- [ ] Kein Event hat einen Ticketpreis > 0
- [ ] Kein Sightseeing-Spot hat eine Eintrittgebuehr
- [ ] `food_and_drink_spots` Liste ist leer
- [ ] Kein Food-Stop im Itinerary
- [ ] Recommendation-Sprache bleibt konsistent mit Low-Budget
- [ ] Falls wenig gefunden: Warning statt stiller Constraint-Verletzung
- [ ] Keine Nightlife-Empfehlungen (Vermeiden-Liste)

---

## Case 5: Nur Events, kein Sightseeing/Food (DE)

**Ziel:** Testet den reinen Event-Modus. Nur Events aktiv, alles andere deaktiviert.

**Status:** `needs review`

### Inputs

| Feld                    | Wert                                     |
|-------------------------|------------------------------------------|
| Sprache                 | Deutsch                                  |
| Name                    | Lena                                     |
| Stadt                   | Muenchen                                 |
| Daten                   | Samstag (ein Tag)                        |
| Letzter Tag einbeziehen | Ja                                       |
| Planungsmodus           | Event or Day Trip                        |
| Gruppengroesse          | 4                                        |
| Events                  | aktiviert                                |
| Sightseeing             | deaktiviert                              |
| Food & Drinks           | deaktiviert                              |
| Event-Vibe              | Hip-Hop, RnB, Urban                     |
| Event-Kategorien        | Konzert, Club                            |
| Zeitpraeferenz          | Night                                    |
| Nur kostenlose Events   | Nein                                     |
| Budget                  | 80 - 200 EUR                             |
| Vermeiden               | Schlager, Volksmusik                     |
| Freitext-Notizen        | (leer)                                   |

### Erwartetes Ergebnis
- Nur Events im Ergebnis, keine Sightseeing- oder Food-Eintraege
- Events passen zum Hip-Hop/RnB-Vibe
- Plan funktioniert auch ohne Tagesstruktur

### Case-spezifische Checkliste
- [ ] `sightseeing_spots` Liste ist leer
- [ ] `food_and_drink_spots` Liste ist leer
- [ ] Keine Sightseeing- oder Food-Stops im Itinerary
- [ ] Events sind thematisch relevant (kein Schlager, keine Volksmusik)
- [ ] Itinerary hat nur einen Tag
- [ ] Personalisierung: Lena wird angesprochen

---

## Case 6: Follow-Up Revision

**Ziel:** Beweisen, dass Follow-Up-Planung selektiv aendert statt alles neu zu bauen.

**Status:** `needs review`

### Voraussetzung
Ein erfolgreicher Durchlauf von **Case 1** oder **Case 2** als Basis.

### Schritt 1: Basis-Plan erstellen
Einen der oben genannten Cases durchspielen und das Ergebnis pruefen.

### Schritt 2: Follow-Up senden
Im Follow-Up-Bereich eingeben:

> "Mach den Samstag eleganter, reduziere Sightseeing auf maximal 2 Stops, und ergaenze eine staerkere Bar-Empfehlung fuer den Abend."

### Schritt 3: Alternatives Follow-Up (nur Form-Aenderung)
Statt Freitext: im Formular die Gruppengroesse von 2 auf 4 aendern und ohne Freitext absenden.

### Erwartetes Ergebnis
- Nur betroffene Teile aendern sich
- Unveraenderte gute Auswahl bleibt stabil
- Report wird korrekt aktualisiert
- Bei Form-Aenderung: automatischer Hinweis auf die Aenderung

### Case-spezifische Checkliste
- [ ] Follow-Up bewahrt unbeteiligte Tage/Stops
- [ ] Angefordertes Sightseeing-Limit wird respektiert
- [ ] Neue Bar-Empfehlung ist konkret (Name, Adresse)
- [ ] Validator flaggt keine neuen Inkonsistenzen
- [ ] Report spiegelt die aktualisierte Struktur wider
- [ ] Progress-Bar zeigt "Revising the current plan..." / "Plan wird ueberarbeitet..."
- [ ] Bei reiner Form-Aenderung: kein Fehler, Plan wird korrekt aktualisiert

---

## Case 7: Reset und Neustart

**Ziel:** Testen, dass der Reset-Button die Session korrekt zuruecksetzt.

**Status:** `needs review`

### Voraussetzung
Ein abgeschlossener Plan aus einem beliebigen Case.

### Ablauf
1. Bestehenden Plan im Ergebnis-Bereich pruefen
2. "Reset Dion and create a new plan" / "Dion zuruecksetzen und neuen Plan erstellen" klicken
3. Neue Inputs eingeben (z.B. komplett andere Stadt und Vibe)
4. Neuen Plan absenden

### Case-spezifische Checkliste
- [ ] Nach Reset: Ergebnis-Bereich zeigt den leeren Zustand ("No plan generated yet")
- [ ] Formular ist zurueckgesetzt / bereit fuer neue Eingabe
- [ ] Neuer Plan enthaelt keine Reste des alten Plans
- [ ] Session-State (`last_core_result`, `last_request`) ist sauber

---

## Case 8: Nicht unterstuetzte Stadt

**Ziel:** Testen wie der Agent reagiert, wenn die Stadt nicht in der Eventim-Datenbank ist.

**Status:** `needs review`

### Inputs

| Feld                    | Wert                                     |
|-------------------------|------------------------------------------|
| Sprache                 | English                                  |
| Stadt                   | Salzburg                                 |
| Daten                   | Naechstes Wochenende                     |
| Planungsmodus           | Full Trip                                |
| Events                  | aktiviert                                |
| Sightseeing             | aktiviert                                |
| Food & Drinks           | aktiviert                                |
| Event-Vibe              | classical, cultural                      |
| Budget                  | 100 - 300 EUR                            |

### Erwartetes Ergebnis
- Agent erkennt, dass Salzburg nicht in Eventim verfuegbar ist
- Klaerer Hinweis oder Warnung im Ergebnis
- Sightseeing und Food funktionieren trotzdem (DZT-basiert)
- Kein Crash oder leere Seite

### Case-spezifische Checkliste
- [ ] Warning ueber fehlende Event-Abdeckung erscheint
- [ ] Kein Python-Error oder leere Ergebnis-Seite
- [ ] Sightseeing/Food-Empfehlungen werden trotzdem geliefert
- [ ] Report handhabt den fehlenden Event-Bereich sauber

---

## Case 9: Maximale Freitext-Nutzung

**Ziel:** Testen, dass der Freitext (user_notes) korrekt verarbeitet wird und die Zeichengrenze eingehalten wird.

**Status:** `needs review`

### Inputs

| Feld                    | Wert                                     |
|-------------------------|------------------------------------------|
| Sprache                 | Deutsch                                  |
| Name                    | Tom                                      |
| Stadt                   | Koeln                                    |
| Daten                   | Samstag bis Sonntag                      |
| Letzter Tag einbeziehen | Ja                                       |
| Planungsmodus           | Full Trip                                |
| Events                  | aktiviert                                |
| Sightseeing             | aktiviert                                |
| Food & Drinks           | aktiviert                                |
| Event-Vibe              | (leer)                                   |
| Zeitpraeferenz          | No preference                            |
| Budget                  | (leer, kein Budget)                      |
| Freitext-Notizen        | "Wir feiern den Geburtstag meiner Freundin. Sie liebt Cocktailbars und gutes Essen. Bitte etwas Besonderes fuer den Samstagabend einplanen. Am Sonntag moechten wir entspannt fruehstuecken." |

### Erwartetes Ergebnis
- Freitext beeinflusst die Planung sichtbar
- Samstagabend hat etwas Besonderes (gehobenes Restaurant oder spezielle Bar)
- Sonntagmorgen enthaelt Fruehstuecks-Empfehlung
- Geburtstags-Kontext wird in Recommendation erwaehnt

### Case-spezifische Checkliste
- [ ] Freitext-Wuensche spiegeln sich im Plan wider
- [ ] Samstagabend hat eine herausragende Empfehlung
- [ ] Sonntag beginnt mit Fruehstueck/Brunch
- [ ] Personalisierung: Tom und Geburtstag werden erwaehnt
- [ ] Freitext-Limit (220 Zeichen) wird in der UI respektiert

---

## Case 10: Minimale Eingabe

**Ziel:** Testen, dass die Validierung greift und sinnvolle Defaults gesetzt werden.

**Status:** `needs review`

### Ablauf
1. Formular oeffnen
2. Nur Stadt und Datum ausfuellen, alles andere auf Default lassen
3. Absenden

### Inputs

| Feld                    | Wert                                     |
|-------------------------|------------------------------------------|
| Sprache                 | English                                  |
| Name                    | (leer)                                   |
| Stadt                   | Frankfurt                                |
| Daten                   | Morgen (1 Tag)                           |
| Alles andere            | Defaults                                 |

### Erwartetes Ergebnis
- Plan wird erfolgreich erstellt trotz minimaler Eingabe
- Defaults greifen sinnvoll (Full Trip, alle Scopes aktiv, no preferences)
- Ergebnis ist brauchbar, wenn auch generisch

### Case-spezifische Checkliste
- [ ] Kein Fehler bei Absenden
- [ ] Events, Sightseeing und Food werden alle geliefert
- [ ] Recommendation ist nicht leer
- [ ] Itinerary hat einen sinnvollen Tag
- [ ] Keine leere Personalisierung (kein "Hi, " ohne Name)

---

## Erfolgskriterien fuer das Projekt

Das Projekt gilt als **demo-ready**, wenn:

1. **Mindestens 7 von 10 Cases** den Status `ready` haben
2. **Case 1, 2, 3 und 6** muessen alle `ready` sein (Kern-Features)
3. **Kein Case** hat den Status `blocked`
4. **Globale Checkliste** wird in jedem getesteten Case vollstaendig bestanden
5. **Kein sichtbarer Python-Traceback** in irgendeinem Case

### Qualitaets-Schwellen

| Bereich                | Minimum fuer "ready"                               |
|------------------------|-----------------------------------------------------|
| Event-Relevanz         | Kein offensichtlich unpassendes Event                |
| Constraint-Einhaltung  | free_only, disabled scopes, Vermeiden-Liste strikt   |
| Link-Qualitaet         | Keine toten Links in der UI sichtbar                 |
| Report-Qualitaet       | Lesbar, faktisch korrekt, richtige Sprache           |
| Progress-UX            | Echte Schritte sichtbar, richtige Sprache            |
| Follow-Up              | Selektive Aenderung, kein kompletter Neuaufbau       |
| Fehlerbehandlung       | Klare Meldungen, kein Crash                          |
