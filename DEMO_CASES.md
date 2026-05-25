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
- [ ] Da alle Cases Events-only sind: `sightseeing_spots` und `food_and_drink_spots` sind leer
- [ ] Kein Sightseeing- oder Food-Stop im Itinerary
- [ ] Keine zeitlich ueberlappenden Stops im selben Tag

### Links & Quellen
- [ ] Eventim-Links sind direkt vorhanden (keine extra Validierung noetig)
- [ ] Bei entfernten Links erscheint eine Warning im Ergebnis
- [ ] Kein toter Link in der UI sichtbar

### Report
- [ ] Markdown-Report wird korrekt gespeichert (Pfad in `outputs/reports/`)
- [ ] Report-Sprache stimmt mit der gewaehlten Sprache ueberein
- [ ] Report-Expander laesst sich oeffnen und zeigt valide Daten

### Fehlerverhalten
- [ ] Kein Python-Traceback sichtbar fuer den User

---

## Case 1: Techno Weekend Berlin (EN)

**Ziel:** Events-only Pipeline (Sightseeing + Food deaktiviert). Vibe-Relevanz und Budget-Einhaltung ueber ein Wochenende mit zwei Naechten testen.

**Status:** `needs review`

### Inputs

| Feld                     | Wert                                      |
|--------------------------|-------------------------------------------|
| Sprache                  | English                                   |
| Name                     | Mia                                       |
| Stadt                    | Berlin                                    |
| Daten                    | 2026-06-26 bis 2026-06-28                 |
| Letzter Tag einbeziehen  | Nein                                      |
| Planungsmodus            | Full Trip                                 |
| Gruppengroesse           | 3                                         |
| Events                   | aktiviert                                 |
| Sightseeing              | deaktiviert                               |
| Food & Drinks            | deaktiviert                               |
| Event-Vibe               | techno, house, underground                |
| Event-Kategorien         | Club, Electronic, Rave                    |
| Zeitpraeferenz           | Night                                     |
| Nur kostenlose Events    | Nein                                      |
| Budget                   | 80 – 200 EUR                              |
| Vermeiden                | Pop, Schlager, Mainstream-EDM             |
| Freitext-Notizen         | (leer)                                    |

### Erwartetes Ergebnis
- Nur Eventim-Events im Ergebnis, keine Sightseeing- und keine Food-Spots
- Events passen zum Techno/House/Underground-Vibe (kein Pop, kein Schlager, kein Mainstream-EDM)
- Ticketpreise liegen im Budgetband 80–200 EUR
- Nacht-orientierte Auswahl (time_pref = Night)
- Itinerary deckt Freitag und Samstag ab, Sonntag faellt weg (include_last_day = false)
- Alle Texte und der Report auf Englisch

### Case-spezifische Checkliste
- [ ] `sightseeing_spots` und `food_and_drink_spots` sind leer
- [ ] Kein Sightseeing- oder Food-Stop im Itinerary
- [ ] Jedes Event passt zum Techno/Underground-Vibe
- [ ] Kein Event ist Pop, Schlager oder Mainstream-EDM
- [ ] Ticketpreise liegen im Budget (oder Warning bei Ueberschreitung statt stiller Aufnahme)
- [ ] Events sind abend-/nachtorientiert
- [ ] Sonntag taucht nicht im Itinerary auf
- [ ] Personalisierung: Mia wird erwaehnt

---

## Case 2: Jazz Wochenende München (DE)

**Ziel:** Events-only Pipeline auf Deutsch. Sprachausgabe und Genre-Relevanz (Jazz) ueber ein Wochenende mit zwei Naechten testen.

**Status:** `needs review`

### Inputs

| Feld                     | Wert                                      |
|--------------------------|-------------------------------------------|
| Sprache                  | Deutsch                                   |
| Name                     | Lena                                      |
| Stadt                    | München                                   |
| Daten                    | 2026-07-03 bis 2026-07-05                 |
| Letzter Tag einbeziehen  | Ja                                        |
| Planungsmodus            | Full Trip                                 |
| Gruppengroesse           | 2                                         |
| Events                   | aktiviert                                 |
| Sightseeing              | deaktiviert                               |
| Food & Drinks            | deaktiviert                               |
| Event-Vibe               | jazz, soul, swing                         |
| Event-Kategorien         | Jazz, Live Music, Konzert                 |
| Zeitpraeferenz           | Evening                                   |
| Nur kostenlose Events    | Nein                                      |
| Budget                   | 50 – 150 EUR                              |
| Vermeiden                | Techno, Electronic, Pop                   |
| Freitext-Notizen         | Lieber kleine Clubs als grosse Hallen.    |

### Erwartetes Ergebnis
- Nur Eventim-Events im Ergebnis, keine Sightseeing- und keine Food-Spots
- Events passen zum Jazz/Soul/Swing-Genre (kein Techno, kein Electronic, kein Pop)
- Auswahl bevorzugt kleinere Clubs statt grosser Hallen (Freitext-Notiz)
- Itinerary deckt Freitag, Samstag und Sonntag ab (include_last_day = true)
- Alle Texte und der Report auf Deutsch

### Case-spezifische Checkliste
- [ ] `sightseeing_spots` und `food_and_drink_spots` sind leer
- [ ] Kein Sightseeing- oder Food-Stop im Itinerary
- [ ] Jedes Event passt zum Jazz-Genre, kein Techno/Electronic/Pop
- [ ] Empfehlung beschreibt den Jazz-Vibe, nicht generischen Stadtbesuch
- [ ] Freitext-Wunsch (kleine Clubs) ist in Auswahl oder Report sichtbar
- [ ] Sonntag ist im Itinerary enthalten
- [ ] Alle Texte, Empfehlung und Report sind auf Deutsch
- [ ] Progress-Nachrichten erscheinen auf Deutsch
- [ ] Personalisierung: Lena wird erwaehnt

---

## Case 3: Kleinststadt Goslar (EN)

**Ziel:** No-Results-Verhalten testen. Eine sehr kleine Stadt liefert vermutlich keine oder kaum Eventim-Events — Dion muss ehrlich und ohne Crash reagieren.

**Status:** `needs review`

### Inputs

| Feld                     | Wert                                      |
|--------------------------|-------------------------------------------|
| Sprache                  | English                                   |
| Name                     | Tom                                       |
| Stadt                    | Goslar                                    |
| Daten                    | 2026-07-11 (ein Tag)                      |
| Letzter Tag einbeziehen  | Ja                                        |
| Planungsmodus            | Event or Day Trip                         |
| Gruppengroesse           | 2                                         |
| Events                   | aktiviert                                 |
| Sightseeing              | deaktiviert                               |
| Food & Drinks            | deaktiviert                               |
| Event-Vibe               | indie, live music                         |
| Event-Kategorien         | Concert, Live Music                       |
| Zeitpraeferenz           | Evening                                   |
| Nur kostenlose Events    | Nein                                      |
| Budget                   | 30 – 120 EUR                              |
| Vermeiden                | (leer)                                    |
| Freitext-Notizen         | (leer)                                    |

### Erwartetes Ergebnis
- Dion findet keine oder nur sehr wenige passende Eventim-Events
- Klare, ehrliche Rueckmeldung statt erfundener Events
- Kein Python-Traceback und kein UI-Freeze
- Sinnvoller Hinweis (z.B. groesserer Radius oder nahegelegene groessere Stadt) statt stiller Auffuellung
- Alle Texte und der Report auf Englisch

### Case-spezifische Checkliste
- [ ] Keine erfundenen oder halluzinierten Events in der Ausgabe
- [ ] Bei leerem Ergebnis: klare Meldung/Warning, kein stilles Auffuellen mit irrelevanten Events
- [ ] Kein Sightseeing- oder Food-Spot wird als Ersatz untergeschoben
- [ ] Kein Python-Traceback fuer den User sichtbar
- [ ] Recommendation erklaert die fehlenden Ergebnisse statt generischem Text
- [ ] Plan/Report werden trotzdem ohne Absturz erzeugt
- [ ] Texte und Report auf Englisch

---

## Case 4: Follow-Up Datum & Vibe (basiert auf Case 1)

**Ziel:** Beweisen, dass das Follow-Up-Panel geaenderte Formularwerte (Datum + Vibe) als Revision uebernimmt — nicht als kompletten Neuaufbau — und dabei Events-only bleibt.

**Status:** `needs review`

### Voraussetzung
Einen erfolgreichen Durchlauf von **Case 1** (Techno Weekend Berlin) als Basis.

### Schritt 1: Case 1 ausfuehren
Case 1 vollstaendig durchlaufen und Ergebnis pruefen.

### Schritt 2: Follow-Up ueber das Panel senden
Im Follow-Up-Panel die Formularwerte aendern und re-submitten:
- **Datum** von `2026-06-26 bis 2026-06-28` auf `2026-07-17 bis 2026-07-19`
- **Event-Vibe** von `techno, house, underground` auf `disco, funk, house classics`

Dazu im Textfeld den Kontext notieren:

> "Moved the trip to the weekend of July 17–19 and switched the vibe from techno to disco & funk — please update the events accordingly."

Anschliessend **"Update plan"** klicken (nicht "Start fresh").

### Erwartetes Ergebnis
- Lauf wird als Follow-Up-Iteration (#2) behandelt, nicht als frischer Plan
- Events passen zum neuen Datumsfenster (17.–19. Juli)
- Events passen zum neuen Vibe (disco/funk/house classics statt techno)
- Weiterhin Events-only: keine Sightseeing- oder Food-Spots
- Budget (80–200 EUR) und Sprache (English) bleiben erhalten
- Report wird korrekt aktualisiert

### Case-spezifische Checkliste
- [ ] Progress-Bar zeigt "Revising the current plan…" (Follow-Up, kein Neuaufbau)
- [ ] Neue Iteration erscheint als versionierte Karte im Follow-up-Tab
- [ ] Events liegen im neuen Datumsfenster (17.–19. Juli)
- [ ] Events spiegeln den neuen Vibe (disco/funk) statt techno wider
- [ ] `sightseeing_spots` und `food_and_drink_spots` bleiben leer
- [ ] Budget und Sprache bleiben unveraendert
- [ ] Report spiegelt das aktualisierte Datum und den neuen Vibe wider

---

## Erfolgskriterien

Das Projekt gilt als **demo-ready**, wenn:

1. **Alle 4 Cases** den Status `ready` haben
2. **Kein Case** hat den Status `blocked`
3. **Globale Checkliste** wird in jedem Case vollstaendig bestanden
4. **Kein sichtbarer Python-Traceback** in irgendeinem Case

### Qualitaets-Schwellen

| Bereich              | Minimum fuer "ready"                                |
|----------------------|------------------------------------------------------|
| Event-Relevanz       | Kein offensichtlich unpassendes Event                |
| Constraint-Einhaltung| Events-only, Budget, Vibe und Vermeiden-Liste strikt |
| Link-Qualitaet       | Keine toten Links in der UI sichtbar                 |
| Report-Qualitaet     | Lesbar, faktisch korrekt, richtige Sprache           |
| Progress-UX          | Echte Schritte sichtbar, richtige Sprache            |
| Follow-Up            | Selektive Aenderung, kein kompletter Neuaufbau       |
| Fehlerbehandlung     | Klare Meldungen, kein Crash                          |
