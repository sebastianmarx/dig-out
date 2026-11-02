# Projekt: „Dig Out“ – Browser-Umsetzung von *Dig Your Way Out*

> Arbeitstitel: **Dig Out**. Online-Multiplayer-Browsergame (mobile-first) basierend auf den Spielmechaniken des Brettspiels *Dig Your Way Out* (David Simide, Borderline Editions / Bannan Games, 2019) inkl. Team-Modus und einer eigenen Interpretation der Erweiterung *Dig In*.

---

## 0. Inhaltsverzeichnis

1. Ziele & Rahmenbedingungen
2. Rechercheergebnis: Das Brettspiel
3. Eigene Regel-Ergänzungen & Kartendesign
4. Gesamtarchitektur
5. Sicherheit
6. Kosten
7. Backend (Python) im Detail
8. Frontend im Detail (inkl. 8.6 Grafische Elemente / Blender-Assets)
9. Infrastruktur (Terraform) im Detail
10. Repository-Struktur
11. Teststrategie
12. CI/CD
13. Umsetzungsphasen & Meilensteine
14. Backlog (später)
15. Offene Fragen
16. Quellen

---

## 1. Ziele & Rahmenbedingungen

| Thema | Entscheidung |
|---|---|
| Spielmodus | Online-Multiplayer, jeder Spieler am eigenen Gerät, Echtzeit über WebSocket. Bots später (Engine wird von Anfang an bot-fähig gebaut). |
| Geräte | Mobile-first (Smartphone hochkant), funktioniert auch auf Tablet/Desktop. Installierbar als PWA. |
| Regelumfang | Basisspiel, Team-Modus, *Dig In* (eigene Interpretation). Erweiterungen sind **bei Spielerstellung einzeln an-/abwählbar**. |
| Karteninhalte | **Eigene Karten** (eigene Namen, Texte, Effekte, Grafiken). Keine Übernahme urheberrechtlich geschützter Texte/Artworks. |
| Zugangsschutz | 1) Gemeinsames **Plattform-Passwort** sperrt die gesamte Seite. 2) Danach individuelle **Cognito-Accounts** pro Spieler. |
| Infrastruktur | AWS, vollständig per Terraform, serverless. |
| Backend | Python 3.13 (AWS Lambda, arm64). |
| Frontend | React 19 + TypeScript + Vite (Begründung in Kap. 8). |
| Designprinzipien | So günstig wie möglich (Ziel: < 2 €/Monat im Leerlauf, quasi 0 € bei privater Nutzung), so sicher wie möglich. |

**Rechtlicher Hinweis:** Spielmechaniken sind nicht urheberrechtlich geschützt, Name, Logo, Artwork und Kartentexte schon. Daher: eigener Titel, eigene Grafiken und eigene Kartentexte. Die App bleibt zugangsgeschützt und privat.

---

## 2. Rechercheergebnis: Das Brettspiel

### 2.1 Eckdaten
- 2–6 Spieler, ca. 45 Min., ab 14 (laut Verlag 16+).
- Thema: Häftlinge wollen sich als Erste aus dem Gefängnis graben. Viel „Take that“: Erpressung, Kämpfe, versteckte Handkarten, Bluff.
- Mechaniken: Aktionspunkte (2 pro Zug), Area Movement per Würfel, Handmanagement, Set Collection, versteckte Information, Spielerfähigkeiten.

### 2.2 Material (Original)
| Komponente | Anzahl |
|---|---|
| Spielplan (doppelseitig: Normal / Team-Modus) | 1 |
| Häftlingstableaus (doppelseitig) | 6 |
| Suchkarten | 77 → 5 Behälter, 6 Spitzen (Pikes), 14 Kettenglieder (Links), 18 Accessoires, 6 seltene Gegenstände, 18 Aktionskarten, **10 Klingen** (gehören zum Suchstapel, so ergeben sich 77) |
| Waffenkarten | 30 → 10 Klingen (im Suchstapel), 20 Messer (offener Stapel auf dem Plan) |
| Werkzeugkarten | 33 → 11 Löffel, 11 Spitzhacken, 11 Schaufeln (offene Stapel) |
| Hintergrundkarten (Backgrounds) | 18 |
| Gangkarten | 24 → je 4 für 6 Gangs |
| Zigaretten-Marker | 55 (5× Wert 5, 50× Wert 1) |
| Prügel-Marker (Beatings) | 6 (Seite 1 / Seite 2) |
| Würfel (W6) | 1 |
| Michel/Michelle (Mini-Erweiterung) | 8 Karten, 2 Aufsteller |

### 2.3 Aufbau
1. Löffel, Messer, Spitzhacken, Schaufeln als offene Stapel auf den Plan. Abgeworfene Werkzeuge/Messer kommen oben auf ihren Stapel zurück.
2. Gangkarten je Gang gemischt auf den Plan, abgeworfene unten drunter.
3. Suchkarten gemischt, verdeckt. Ist der Stapel leer, wird der Ablagestapel neu gemischt.
4. Zigaretten und Prügel-Marker in den allgemeinen Vorrat.
5. Jeder Spieler wählt einen Häftling, seine Figur startet im **Zellentrakt**.
6. Jeder zieht verdeckt 1 Hintergrundkarte und 3 Suchkarten.

### 2.4 Ziel
Wer zuerst die nötigen **Tunnelpunkte** erreicht, gewinnt sofort.

| Spieler | Punkte |
|---|---|
| 2–3 | 12 |
| 4 | 10 |
| 5–6 | 8 |

### 2.5 Spielzug
- Startspieler: „die eindrucksvollste Narbe“ (digital: zufällig), dann im Uhrzeigersinn.
- Bis zu **2 Aktionen** pro Zug. **Basisaktionen** gehen überall, **Ortsaktionen** nur am passenden Ort.
- Kostenlos (keine Aktion): Hintergrundkarte aufdecken, Gang-Fähigkeit nutzen.
- **Handlimit 10** am Zugende.

### 2.6 Basisaktionen
- **Suchen** (1× pro Zug): ziehe so viele Suchkarten, wie der aktuelle Ort angibt (1–3). Zellentrakt = 1, Cafeteria = 2.
- **Bewegen:**
  - *Einfache Bewegung:* würfeln. Jedes Ergebnis nennt 2 Orte, man wählt einen. Steht man bereits auf einem davon, muss man zum anderen.
  - *Vorsichtige Bewegung:* 2 Aktionen, beliebiger Ort, kein Wurf.
- **Gang beitreten:** Accessoires (verschiedene Typen) abwerfen, oberste Gangkarte nehmen. Nur 1 Gang gleichzeitig, Wechsel wirft alte Gangkarte ab.
  - Crew: 2 verschiedene aus {Kappe, Bandana, Halskette}
  - Kartell: 2 verschiedene aus {Kappe, Uhr, Stiefel}
  - Biker: 2 verschiedene aus {Bandana, Ring, Stiefel}
  - Bratva: 2 verschiedene aus {Uhr, Halskette, Ring}
  - Triade / 6. Gang: 3 beliebige verschiedene
- **Aktionskarte spielen:** aufdecken, ausführen, abwerfen.
- **Erpressung** (1× pro Zug, Waffe auf der Hand, Ziel am selben Ort):
  - *Einschüchterung:* Werkzeug benennen (Löffel/Spitzhacke/Schaufel), Waffe offen zeigen. Hat das Ziel das Werkzeug und gibt nach, wird es übergeben.
  - *Kampf:* Weigert sich das Ziel oder hat es das Werkzeug nicht, spielen beide abwechselnd Waffen, der **Verteidiger beginnt**. Wer nicht mehr kann oder will, verliert und bekommt 1 Prügel.
  - *Belohnung:* Verliert der Verteidiger und hatte er das Werkzeug, bekommt der Sieger das Werkzeug. Sonst zieht der Sieger eine zufällige Handkarte des Verlierers.
  - Gespielte Waffen werden abgeworfen (Messer auf den Messerstapel, Klingen in die Suchablage).
- **Herstellen** (1× pro Zug, nicht im Zellentrakt oder in den Duschen, nicht mit Prügeln):
  - 2 Kettenglieder + 1 Spitze → 1 Spitzhacke
  - 2 Kettenglieder + 1 Behälter → 1 Schaufel
  - 2 Kettenglieder + 1 Klinge → 2 Messer
  - Leerer Zielstapel → nicht herstellbar.

### 2.7 Hintergrundkarten
- Verdeckt, 1× pro Spiel aufdeckbar, der Zeitpunkt steht auf der Karte. Aufdecken kostet keine Aktion.
- Ist man in der auf der Karte genannten Gang, gilt zusätzlich ein zweiter Effekt.

### 2.8 Prügel (Beatings)
- Maximal 2.
- 1 Prügel: kein Herstellen. 2 Prügel: kein Herstellen, kein Graben.

### 2.9 Ortsaktionen
| Ort | Aktion |
|---|---|
| Zellentrakt | **Graben:** 1 Werkzeug von der Hand offen vor sich legen → Punkte: Löffel 1, Spitzhacke 2, Schaufel 3. Nicht mit 2 Prügeln. |
| Cafeteria | **Löffel klauen:** 1 Löffel vom Stapel nehmen. |
| Krankenstation | **Heilen:** 1 Prügel entfernen. |
| Freizeitbereich | **Verkaufen:** beliebig viele Karten abwerfen → Zigaretten in Höhe ihres Werts. **Kaufen:** 2 Zig → 1 Messer, 5 Zig → 2 Messer, 6 Zig → 1 Spitzhacke, 8 Zig → 1 Schaufel. |
| Duschen | kein Herstellen. Startort von Michel(le). |

### 2.10 Team-Modus
- Gerade Spielerzahl (4 oder 6), Team A gegen Team B. Planrückseite mit **Zellentrakt A** und **Zellentrakt B** (zählen beide als Zellentrakt).
- Teampunkte zum Sieg: 4 Spieler → 16, 6 Spieler → 20.
- Einfache Bewegung: Bei 1, 2 oder 3 darf man in jeden der beiden Zellentrakte.
- Erpressung: Teamkollegen am selben Ort dürfen im Kampf an deiner Stelle eine Waffe spielen. Alle Helfer der Verliererseite bekommen 1 Prügel, der Sieger zieht von jedem Verlierer eine zufällige Karte.
- Herstellen nur im **gegnerischen** Zellentrakt, Graben nur im **eigenen**.
- Neue Basisaktion **Tausch:** Karten und Zigaretten beliebig mit Teamkollegen am selben Ort tauschen.
- Gang-Bonus: Statt zu würfeln darf man zum Ort eines Teamkollegen in derselben Gang ziehen.

### 2.11 Erweiterung *Dig In* (öffentlich bekannt)
- **Gefängnisdirektorin (NPC):** läuft über den Plan, schickt Häftlinge mit schlechtem Benehmen in **Einzelhaft**. In ihrem Büro kann man sie vorab mit Zigaretten bestechen und bekommt später Vorteile.
- **Neue Orte**, die einzelne Basisorte ersetzen können:
  - Bibliothek: sich „resozialisieren“ (neue Hintergrundkarte) oder Hände anderer ausspionieren.
  - Spielzellen: um Zigaretten zocken, Züge auf Klopapier „planen“.
  - Wäscherei: Gangbeitritt erleichtern, Bandagen (Herstellen/Heilen).
  - Werkstatt: Grabfähigkeit verbessern, Werkzeuge aufwerten.
  - Fitnessraum: auf Kämpfe vorbereiten oder Massenschlägerei mit allen Anwesenden.
  - Psychiatrie: Traumata, die Aktionen einschränken, bis sie geheilt sind.

### 2.12 Lücken in der Recherche
Nicht öffentlich verfügbar (Kap. 3 schließt sie mit eigenem Design): genaue Texte von Aktions-, Selten-, Hintergrund- und Gangkarten, Zigarettenwerte pro Karte, der vollständige Plan (6. Ort, Suchwerte, Würfelzuordnung) sowie die Detailregeln von *Dig In*.

---

## 3. Eigene Regel-Ergänzungen & Kartendesign

Alle folgenden Werte sind **Entwurf v0** und liegen als Daten (YAML) im Repo (`game-data/`). Balancing erfolgt per Simulation (Kap. 7.9). Ändern geht ohne Code-Änderung.

### 3.1 Spielplan (Basis): 6 Orte im Ring
Würfelzuordnung: Augenzahl *n* → Ort *n* oder Ort *n+1* (6 → Ort 6 oder Ort 1). Das passt zum bekannten Beispiel „1 = Zellentrakt oder Cafeteria“.

| Nr. | Ort | Suchen | Ortsaktion | Herstellen erlaubt |
|---|---|---|---|---|
| 1 | Zellentrakt | 1 | Graben | nein |
| 2 | Cafeteria | 2 | Löffel klauen | ja |
| 3 | Duschen | 3 | – (bester Suchort, dafür kein Herstellen) | nein |
| 4 | Krankenstation | 1 | Heilen | ja |
| 5 | Freizeitbereich | 2 | Kaufen / Verkaufen | ja |
| 6 | Hof *(eigener Ort)* | 2 | **Training:** Lege 1 Waffe von der Hand offen als „vorbereitet“ ab. Sie zählt im nächsten Kampf als zusätzliche erste Waffe (max. 1). | ja |

**Team-Modus-Plan:** 7 Orte (Zellentrakt A und B statt Zellentrakt). Würfeltabelle:
1 → ZT-A / ZT-B / Cafeteria, 2 → ZT-A / ZT-B / Duschen, 3 → ZT-A / ZT-B / Krankenstation, 4 → Krankenstation / Freizeit, 5 → Freizeit / Hof, 6 → Hof / Cafeteria.

### 3.2 Suchstapel (77 Karten), Zigarettenwerte
| Typ | Anzahl | Zig.-Wert | Hinweis |
|---|---|---|---|
| Behälter | 5 | 1 | Schaufel-Zutat |
| Spitze | 6 | 1 | Spitzhacken-Zutat |
| Kettenglied | 14 | 1 | Basis-Zutat |
| Klinge | 10 | 2 | Waffe + Messer-Zutat |
| Accessoire (Kappe, Bandana, Halskette, Uhr, Stiefel, Ring) | 6 × 3 = 18 | 1 | Gangbeitritt |
| Seltener Gegenstand | 6 | 3–5 | siehe 3.3 |
| Aktionskarte | 18 | 1 | siehe 3.4 |

Werkzeuge verkaufen: Löffel 1, Spitzhacke 3, Schaufel 4. Messer: 1.

### 3.3 Seltene Gegenstände (eigene, 6 Stück)
| Name | Effekt | Wert |
|---|---|---|
| Goldzahn | nur Handelsware | 5 |
| Universalgriff | zählt beim Herstellen als Spitze **oder** Behälter | 3 |
| Stahldraht | zählt beim Herstellen als 2 Kettenglieder | 3 |
| Schmuggel-Handy | Aktion: Schau dir die Hand eines beliebigen Spielers an und tausche 1 deiner Karten gegen 1 seiner (Karte bleibt danach im Spiel) | 4 |
| Gefälschter Ausweis | zählt als beliebiges Accessoire | 3 |
| Zahnbürsten-Shiv | Waffe. Gewinnst du damit einen Kampf, bekommt der Verlierer 2 Prügel statt 1 | 3 |

### 3.4 Aktionskarten (eigene, 9 Typen × 2 = 18)
| Name | Timing | Effekt |
|---|---|---|
| Schichtwechsel | eigener Zug | +1 Aktion in diesem Zug |
| Schleichweg | eigener Zug | Bewege dich auf einen beliebigen Ort (statt 2 Aktionen: diese Aktion) |
| Paket von draußen | eigener Zug | Ziehe 3 Suchkarten (zählt nicht als Suchen) |
| Razzia | eigener Zug | Alle *anderen* Spieler an deinem Ort werfen je 1 Karte ihrer Wahl ab |
| Schmiergeld | eigener Zug | Nimm 1 Spitzhacke vom Stapel, wenn du 3 Zigaretten zahlst |
| Ablenkung | **Reaktion**: wenn du erpresst wirst | Die Erpressung wird abgebrochen, keine Aktion des Angreifers wird zurückerstattet |
| Erste Hilfe | jederzeit im eigenen Zug | Entferne 1 Prügel |
| Spitzel | eigener Zug | Sieh dir die Hand eines Spielers an und nimm 1 Karte (keine Waffe, kein Werkzeug) |
| Tunneleinbruch | eigener Zug | Ein Spieler deiner Wahl verliert sein zuletzt eingegrabenes **Löffel**-Werkzeug (−1 Punkt), falls vorhanden |

### 3.5 Gangs (eigene Fähigkeiten, je 4 Karten)
| Gang | Beitritt | Passive Fähigkeit (kostenlos) |
|---|---|---|
| Crew | 2 versch. aus {Kappe, Bandana, Halskette} | 1× pro Zug: Suchen zieht +1 Karte |
| Kartell | 2 versch. aus {Kappe, Uhr, Stiefel} | Kaufen kostet 1 Zigarette weniger (min. 1) |
| Biker | 2 versch. aus {Bandana, Ring, Stiefel} | Als Verteidiger: Du darfst 1× pro Kampf eine Runde aussetzen, ohne zu verlieren |
| Bratva | 2 versch. aus {Uhr, Halskette, Ring} | Gewinnst du eine Erpressung, erhältst du zusätzlich 1 Zigarette pro Prügel des Verlierers |
| Triade | 3 beliebige verschiedene | Einfache Bewegung: Du darfst neu würfeln (1× pro Zug) |
| Schatten | 3 beliebige verschiedene | Deine Handkartenanzahl ist für andere verborgen. Spitzel/Handy gegen dich zeigen nur 3 zufällige Karten |

### 3.6 Hintergrundkarten (eigene, 18 = 3 je Gang)
Format: **Name** – *Zeitpunkt* – Effekt / Bonus bei passender Gang.

| # | Name | Zeitpunkt | Effekt | Gang-Bonus |
|---|---|---|---|---|
| 1 | Ex-Bergarbeiter | beim Graben | +1 Punkt | Crew: +2 statt +1 |
| 2 | Taschendieb | eigener Zug | Ziehe 2 zufällige Karten von einem Spieler am selben Ort | Crew: von jedem am Ort 1 |
| 3 | Hamsterer | eigener Zug | Ziehe 4 Suchkarten | Crew: Handlimit dauerhaft 12 |
| 4 | Buchhalter | im Freizeitbereich | Erhalte 6 Zigaretten | Kartell: 10 |
| 5 | Schmuggler | eigener Zug | Nimm 1 Schaufel vom Stapel, wirf 3 Karten ab | Kartell: ohne Abwerfen |
| 6 | Bestecher | wenn du erpresst wirst | Brich ab, der Angreifer bekommt 1 Prügel | Kartell: zusätzlich ziehst du 1 Karte von ihm |
| 7 | Mechaniker | beim Herstellen | Ignoriere 1 Zutat | Biker: ignoriere 2 |
| 8 | Raufbold | zu Kampfbeginn | Zählt als 2 gespielte Waffen | Biker: 3 |
| 9 | Zäh wie Leder | wenn du Prügel bekommst | Ignoriere sie | Biker: zusätzlich 1 Prügel heilen |
| 10 | Vollstrecker | eigener Zug | Gib einem Spieler am selben Ort 1 Prügel | Bratva: 2 |
| 11 | Geldeintreiber | eigener Zug | Jeder Spieler gibt dir 1 Zigarette (falls vorhanden) | Bratva: 2 |
| 12 | Waffenhändler | eigener Zug | Nimm 3 Messer vom Stapel | Bratva: 5 |
| 13 | Akrobat | bei Bewegung | Ziehe auf einen beliebigen Ort (kostenlos) | Triade: zusätzlich +1 Aktion |
| 14 | Meisterdieb | im Zellentrakt | Nimm einem Spieler 1 offen eingegrabenes Löffel-Werkzeug weg und grabe es selbst ein | Triade: Spitzhacke statt Löffel |
| 15 | Glücksspieler | bei einem Würfelwurf | Lege das Ergebnis selbst fest | Triade: zusätzlich ziehst du 1 Karte |
| 16 | Informant | eigener Zug | Sieh dir alle Hände an | Schatten: nimm 1 Karte aus einer |
| 17 | Phantom | eigener Zug | Bis zu deinem nächsten Zug kannst du nicht erpresst werden | Schatten: zusätzlich +1 Aktion |
| 18 | Tunnelratte | beim Graben | Grabe 2 Werkzeuge mit einer Aktion | Schatten: 3 |

### 3.7 *Dig In*: eigene Detailregeln
**Gefängnisdirektorin (NPC)**
- Startet im Hof. Am Ende jeder **Runde** (nach dem letzten Spieler) bewegt sie sich per einfacher Bewegung (das System würfelt, der Startspieler wählt).
- **Fehlverhalten:** Wer in seinem Zug erpresst oder kämpft, bekommt einen **Verweis**-Marker (max. 1).
- Steht die Direktorin am Ende einer Bewegung oder am Zugende eines Spielers auf einem Ort mit Spielern mit Verweis → diese kommen in **Einzelhaft** (Sonderfeld). Dort verlieren sie den Verweis, haben im nächsten Zug nur 1 Aktion (nur Suchen mit Wert 1 oder Aktionskarte), danach geht es zurück in den Zellentrakt.
- **Büro der Direktorin** (Sonderort, nur per vorsichtiger Bewegung oder Karte erreichbar): **Bestechen:** 3 Zigaretten → 1 „Gefälligkeit“-Marker (max. 2). Einsatz: Einzelhaft verhindern **oder** Direktorin auf einen beliebigen Ort versetzen.

**Neue Orte** (jeder ersetzt einen der Orte 2–6, Zellentrakt ist fix). Bei der Spielerstellung wählbar, das System validiert, dass Kaufen/Verkaufen und Heilen weiterhin möglich bleiben (direkt oder per Ersatz).
| Ort | Suchen | Ortsaktion |
|---|---|---|
| Bibliothek | 1 | **Resozialisieren:** Lege unaufgedeckte Hintergrundkarte ab, ziehe 2, behalte 1. **oder** **Studieren:** Sieh die Hand eines Spielers an. |
| Spielzellen | 2 | **Zocken:** Setze X Zigaretten (max. 5), würfle: 1–2 verloren, 3–4 zurück, 5–6 doppelt. **oder** **Klopapier-Plan:** Lege fest, welches Würfelergebnis dein nächster Wurf hat (nächster Zug). |
| Wäscherei | 2 | **Bandagen:** Nimm 1 Bandage-Marker (heilt 1 Prügel als kostenlose Aktion **oder** ersetzt 1 Kettenglied). **Gang-Kontakte:** Nächster Gangbeitritt braucht 1 Accessoire weniger. Ersetzt Heilen. |
| Werkstatt | 2 | **Aufwerten:** Löffel + 2 Karten → Spitzhacke, Spitzhacke + 3 Karten → Schaufel. **Grabtechnik:** +1 dauerhafter Grabbonus beim nächsten Graben (Marker). |
| Fitnessraum | 1 | **Trainieren:** +1 Kampfmarker (zählt als Waffe, max. 2). **Massenschlägerei:** alle Anwesenden spielen gleichzeitig verdeckt 0–n Waffen; wer am meisten spielt, zieht von jedem 1 Karte; wer am wenigsten spielt, bekommt 1 Prügel. |
| Psychiatrie | 1 | **Trauma zufügen:** (benötigt Waffe) Ziel am Ort bekommt Trauma-Karte (z. B. „Paranoia: max. 1 Aktion“, „Zittern: kein Herstellen“, „Albträume: Handlimit 5“). Heilen entfernt zuerst Traumata. **Therapie:** Entferne eigenes Trauma + 1 Prügel. |

### 3.8 Spielerstellung: Optionen
- Spielerzahl 2–6; Team-Modus (nur 4 oder 6) an/aus.
- *Dig In:* Direktorin an/aus, Orte einzeln an/aus mit Slot-Zuweisung.
- Michel & Michelle (Backlog).
- Siegpunkte (Standard laut Tabelle, überschreibbar). Zug-Timer (Standard 90 s, Reaktions-Timer 20 s).

---

## 4. Gesamtarchitektur

```
                         ┌──────────────────────────────────────────┐
 Browser / PWA  ───────► │ CloudFront (HTTPS, Shield Std, Headers)   │
 (React SPA)             │  ├─ CF Function: Plattform-Gate (Cookie)  │
                         │  ├─ /*        → S3 (privat, OAC)          │
                         │  ├─ /api/*    → API Gateway HTTP API      │
                         │  └─ /ws       → API Gateway WebSocket API │
                         └──────────────────────────────────────────┘
                                   │                     │
                     HTTP API (JWT-Authorizer)    WebSocket API ($connect/$disconnect/$default)
                                   │                     │
                         ┌─────────┴─────────────────────┴─────────┐
                         │      Python-Lambdas (arm64, 3.13)        │
                         │  gate · lobby · ws-ticket · ws-connect   │
                         │  ws-disconnect · game-action · timeout   │
                         │  cognito-pre-signup                      │
                         └─────────┬──────────────┬────────────────┘
                                   │              │
                           DynamoDB (On-Demand)  EventBridge Scheduler (Timeouts)
                                   │
                           Cognito User Pool (Lite)  ·  SSM Parameter Store  ·  CloudWatch
```

**Kernprinzipien**
- **Server-autoritativ:** Die gesamte Spiellogik läuft im Backend. Der Client sendet nur Absichten („Aktion X“), der Server validiert und berechnet. Würfel und Mischen passieren nur serverseitig.
- **Versteckte Information:** Jeder Client bekommt nur eine gefilterte **Spieler-Sicht** (eigene Hand, fremde Handgrößen, offene Auslagen). Der Stapelinhalt verlässt den Server nie.
- **Reine Engine:** Die Spiellogik ist ein reines Python-Paket ohne AWS-Abhängigkeiten. Das macht sie testbar, simulierbar und bot-fähig.
- **Zustandslose Lambdas, Zustand in DynamoDB** mit optimistischem Locking (Versionsnummer, Conditional Writes).
- **Nur eine Origin** (CloudFront) für Seite, API und WebSocket. Dadurch gibt es kein CORS, das Gate-Cookie gilt überall und die CSP wird einfach.

---

## 5. Sicherheit

### 5.1 Ebene 1: Plattform-Passwort (Gate)
- **CloudFront Function** (viewer-request, `cloudfront-js-2.0`) auf allen Behaviors außer `/gate*` und `/api/gate`:
  - Prüft das Cookie `__Host-gate=<exp>.<nonce>.<hmac>` mit HMAC-SHA256. Den Schlüssel liest sie aus dem **CloudFront KeyValueStore**, das Ablaufdatum wird geprüft.
  - Ungültig → 302 auf `/gate` (statische, minimale Seite ohne App-Code). Für `/api` und `/ws` → 401.
- **`POST /api/gate`** (Lambda):
  - Vergleicht das Passwort mit einem **Argon2id-Hash** aus dem SSM Parameter Store (SecureString). Konstantzeit-Vergleich über `argon2.verify`.
  - **Brute-Force-Schutz:** Zähler pro IP-Hash in DynamoDB (TTL 15 min), max. 5 Versuche/15 min, danach exponentielles Backoff. Zusätzlich Stage-Throttling der API.
  - Erfolg → `Set-Cookie: __Host-gate=…; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000` (30 Tage).
- **Rotation:** Neuer Passwort-Hash → `aws ssm put-parameter`. Neuer HMAC-Key → alle Gate-Cookies werden ungültig. Ein Skript `scripts/rotate-gate.sh` erledigt beides.
- Optional (kostet ca. 6–8 $/Monat): AWS WAF mit Rate-Based-Rule. Wegen der Kosten standardmäßig **aus**, als Terraform-Flag vorbereitet.

### 5.2 Ebene 2: Cognito-Accounts
- Cognito User Pool, **Lite-Tier** (Free Tier 10.000 MAU), Region eu-central-1.
- **Self-Sign-up nur mit Plattform-Passwort:** Ein **Pre-Sign-up-Lambda-Trigger** verlangt `validationData.platformPassword` und prüft es gegen denselben Argon2id-Hash. So kann niemand die öffentliche Cognito-API direkt nutzen, um am Gate vorbei Accounts anzulegen.
- E-Mail-Verifizierung (Cognito-Standard-Mailversand reicht für kleine Gruppen, Limit 50/Tag, sonst SES).
- Passwortrichtlinie: min. 12 Zeichen. Optional **TOTP-MFA** (kostenlos).
- Login per SRP über `aws-amplify/auth` (v6, modular). Access-Token-Lebensdauer 15 min, Refresh-Token 30 Tage, **Token-Revocation** aktiv.
- Benutzername = Anzeigename (eindeutig, Regex-validiert, 3–20 Zeichen).

### 5.3 API- & WebSocket-Sicherheit
- **HTTP API:** nativer **JWT-Authorizer** (Cognito, kostenlos) auf allen Routen außer `/api/gate`.
- **WebSocket-Auth über Ticket** (kein JWT in URLs/Logs):
  1. Client: `POST /api/ws-ticket` (JWT) → Server erzeugt ein zufälliges 256-Bit-Ticket und speichert es in DynamoDB (TTL 30 s, einmalig nutzbar, an `sub` gebunden).
  2. Client verbindet `wss://<domain>/ws?ticket=…`. `$connect`-Lambda löst das Ticket per `DeleteItem` mit `ReturnValues=ALL_OLD` atomar ein.
  - Zusätzlich prüft die CF-Function das Gate-Cookie (Browser schicken Cookies beim WS-Handshake mit).
- **Origin-Schutz:** CloudFront setzt einen geheimen Header `X-Origin-Verify`, den alle Lambdas prüfen. Direkte Aufrufe der `execute-api`-URL werden abgelehnt.
- **Eingabevalidierung:** Alle Nachrichten sind Pydantic-v2-Modelle (`extra="forbid"`, Längen- und Wertebereiche). Max. Nachrichtengröße 8 KB.
- **Rate-Limits:** API-Gateway-Stage-/Route-Throttling (z. B. 10 req/s, Burst 20) plus Aktions-Rate pro Verbindung in der Engine.
- **Autorisierung pro Aktion:** Der Server prüft, ob der Aufrufer Spieler dieses Spiels ist und gerade handeln darf (am Zug oder ausstehende Entscheidung).

### 5.4 Web-Sicherheit (Frontend)
- CloudFront **Response Headers Policy**:
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' https://cognito-idp.eu-central-1.amazonaws.com; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'`
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy` restriktiv, `Cross-Origin-Opener-Policy: same-origin`.
- Kein `dangerouslySetInnerHTML`, kein Inline-Script. Spielernamen werden immer escaped (React-Standard).
- Mindestens TLS 1.2 (Viewer-Policy `TLSv1.2_2021`).
- Token-Speicherung: Amplify speichert standardmäßig in localStorage. Die strikte CSP minimiert das XSS-Risiko. Alternative später: Refresh-Token als HttpOnly-Cookie über ein eigenes Token-Endpoint-Lambda.

### 5.5 AWS-Account & Infrastruktur
- Root-Account mit MFA, keine Root-Keys. Zugriff über **IAM Identity Center**.
- CI deployt per **GitHub OIDC**, keine statischen Keys.
- **Least Privilege:** eigene IAM-Rolle pro Lambda, nur benötigte DynamoDB-Aktionen und -Ressourcen.
- S3: Block Public Access, Zugriff nur über CloudFront OAC, SSE-S3, Bucket-Policy erzwingt TLS.
- DynamoDB: Verschlüsselung (AWS-owned Key, kostenlos), TTL für temporäre Daten, optional PITR.
- Secrets nur im SSM Parameter Store (SecureString, Standard-Tier kostenlos), nicht in Code oder Terraform-Variablen. Terraform referenziert nur Parameternamen. Der Gate-HMAC-Key wird von Terraform erzeugt und landet im State, daher ist der State-Bucket privat, verschlüsselt und versioniert.
- CloudTrail (1 Management-Trail kostenlos), **AWS Budgets** (Alarm bei 5 $), CloudWatch-Alarme (Lambda-Errors, Throttles) → SNS → E-Mail.
- Log-Retention 14 Tage. Keine Tokens, Passwörter oder Handkarten in Logs (Powertools Logger mit Redaction).
- Sicherheits-Tooling in CI: `bandit`, `pip-audit`, `ruff`, `npm audit`, `trivy`/`checkov` für Terraform, Dependabot, Secret-Scanning.

---

## 6. Kosten

Annahme: private Gruppe, ca. 10 Spieler, ~20 Partien/Monat à 45 min.

| Dienst | Nutzung | Kosten/Monat |
|---|---|---|
| CloudFront | < 1 GB, < 1 Mio. Requests (Always-Free 1 TB / 10 Mio.) | 0 € |
| CloudFront Functions / KVS | < 2 Mio. Aufrufe frei | 0 € |
| S3 | < 50 MB | ~0,01 € |
| Lambda (arm64) | << 1 Mio. Aufrufe (Always-Free) | 0 € |
| API GW WebSocket | ~50k Nachrichten + Verbindungsminuten | ~0,05 € |
| API GW HTTP | ~10k Requests | ~0,01 € |
| DynamoDB On-Demand | < 25 GB, wenige Requests | ~0 € |
| Cognito Lite | < 10k MAU | 0 € |
| EventBridge Scheduler | < 14 Mio. frei | 0 € |
| SSM Parameter Store (Standard) | – | 0 € |
| CloudWatch Logs | < 5 GB | 0 € |
| Route 53 (nur mit eigener Domain) | 1 Hosted Zone | 0,50 € + Domain |
| **Summe** | | **≈ 0,10 € (ohne Domain) / ≈ 0,60 € + Domain** |

Bewusst vermieden: NAT Gateway, VPC-Lambdas, RDS, ElastiCache, Fargate, WAF (optional), KMS-CMKs (1 $/Key), Secrets Manager (0,40 $/Secret), Cognito Plus/Essentials-Features.

---

## 7. Backend (Python) im Detail

### 7.1 Tooling
- Python 3.13, **uv** (Dependency-Management, Lockfile), **ruff** (Lint und Format), **mypy --strict**, **pytest** + **hypothesis**.
- Libraries: `pydantic` v2, `aws-lambda-powertools` (Logger, Tracer optional, Event-Handler, Idempotency), `boto3` (in Runtime enthalten, gepinnt), `argon2-cffi`.
- Build: Lambda-Zips für `manylinux2014_aarch64` (pydantic-core und argon2 sind native). Ein gemeinsamer **Lambda Layer** für Dependencies, Code-Zips pro Funktion klein.

### 7.2 Paketstruktur
```
backend/
  src/digout/
    engine/          # reine Spiellogik, keine I/O
      models.py      # GameState, Player, Card, Pending, Options (Pydantic)
      cards.py       # Laden & Validieren von game-data/*.yaml
      board.py       # Orte, Würfelmapping, Varianten (Basis/Team/DigIn)
      actions.py     # Action-Typen (discriminated union)
      rules/         # je Regelbereich ein Modul: move, search, craft, extort, dig, gang, market, warden, places_digin, team
      effects/       # Karteneffekte (Registry: effect_id → Funktion)
      engine.py      # apply(), legal_actions(), view_for(), start_game()
      rng.py         # deterministischer RNG (seed + counter, secrets-basiert initialisiert)
      events.py      # Domain-Events (für Animationen/Log im Client)
    api/             # Lambda-Handler (dünn)
      gate.py, lobby.py, ws_ticket.py, ws_connect.py, ws_disconnect.py, ws_default.py, timeout.py, pre_signup.py
    infra/           # Adapter: dynamo.py (Repository), broadcast.py (ApiGatewayManagementApi), scheduler.py
    sim/             # Simulation & Bots: random_bot.py, heuristic_bot.py, run_sim.py
  tests/
```

### 7.3 Engine-API (Kern)
```python
def start_game(options: GameOptions, players: list[PlayerInfo], seed: int) -> GameState
def legal_actions(state: GameState, player_id: str) -> list[Action]
def apply(state: GameState, player_id: str, action: Action) -> tuple[GameState, list[Event]]  # raises IllegalAction
def view_for(state: GameState, player_id: str | None) -> PlayerView  # None = Zuschauer
def on_timeout(state: GameState, pending_id: str) -> tuple[GameState, list[Event]]
```
- **Unveränderlicher Zustand:** `apply` gibt einen neuen State zurück, der alte bleibt für Rollback/Replay erhalten.
- **Determinismus:** Bei gleichem Seed und gleicher Aktionsfolge entsteht der gleiche Zustand. Das ermöglicht Replays, Debugging und reproduzierbare Bugreports.
- **`legal_actions`** ist die Grundlage für die UI (nur erlaubte Buttons werden aktiv), Bots und Fuzz-Tests.

### 7.4 Zustandsmodell (Auszug)
```
GameState
  id, version, options, phase (LOBBY|RUNNING|FINISHED), round, turn_player, actions_left
  turn_flags {searched, extorted, crafted, ...}
  players[]: id, name, seat, team?, place, hand[], tools_dug[], gang?, background{card, revealed},
             beatings, cigarettes, markers{verweis, gefaelligkeit, bandage, trauma[], kampf, ...}
  piles: spoons, knives, pickaxes, shovels (Zähler), gang_piles{gang: [cards]}
  search_deck[], search_discard[], background_deck[]
  npc: warden{place}?, michel?
  pending: Pending | None  # ausstehende Entscheidung (s. 7.5)
  rng_state, log_seq, winner?
```

### 7.5 Interaktive Abläufe: „Pending Decisions“
Viele Regeln brauchen Antworten anderer Spieler außerhalb ihres Zuges (Erpressung, Kampf-Wechsel, Reaktionskarten, Massenschlägerei). Dafür gibt es einen **Entscheidungsstapel**:
- `Pending{ id, kind, actor(s), options, deadline, context }`, z. B. `EXTORT_RESPONSE` (nachgeben/weigern), `COMBAT_PLAY` (Waffe spielen/aufgeben), `REACTION_WINDOW`, `CHOOSE_PLACE` (nach Würfelwurf), `DISCARD_TO_LIMIT`, `BRAWL_BID` (verdeckt, gleichzeitig).
- **Informationsleck vermeiden:** Reaktionsfenster (z. B. „Ablenkung“, „Bestecher“) werden **immer** geöffnet, auch wenn der Spieler keine passende Karte hat. Sonst würde die Existenz des Fensters verraten, was auf der Hand ist. Clients können „Auto-Passen, wenn nichts spielbar“ einstellen. Der Server antwortet dann nach einer kurzen, zufälligen Verzögerung (1–3 s), damit die Antwortzeit nichts verrät.
- **Timeouts:** Jede Pending- und Zug-Phase hat eine Deadline. Beim Setzen wird ein **EventBridge-Scheduler**-One-Shot (`at(...)`) mit `{gameId, pendingId, version}` angelegt. Feuert er und die Version passt noch, wird die Standardaktion ausgeführt (passen, weigern, Zug beenden, zufällig abwerfen). Veraltete Timer laufen ins Leere (Idempotenz über `pendingId`).

### 7.6 DynamoDB (Single-Table, On-Demand)
| PK | SK | Inhalt | TTL |
|---|---|---|---|
| `GAME#<id>` | `STATE` | kompletter GameState (JSON, gzip falls > 100 KB), `version` | 30 Tage nach Ende |
| `GAME#<id>` | `EVT#<seq>` | Aktion + Events (Replay/Audit) | 30 Tage |
| `GAME#<id>` | `SEAT#<userId>` | Spieler-Zuordnung, aktuelle connectionId(s) | 30 Tage |
| `CONN#<connId>` | `META` | userId, gameId | 3 h |
| `USER#<sub>` | `PROFILE` / `GAMES` | Name, Statistiken, laufende Spiele | – |
| `TICKET#<t>` | `META` | sub | 30 s |
| `RL#<hash>` | `GATE` | Fehlversuche | 15 min |
| `CODE#<6-stellig>` | `META` | gameId (Beitrittscode) | 24 h |
- GSI1 (`gsi1pk = LOBBY#OPEN`, `gsi1sk = createdAt`) zeigt offene Lobbys.
- **Schreiben:** `TransactWriteItems` mit Condition `version = :expected` (STATE) und Put für das EVT. Bei Konflikt → Retry (neu laden, neu validieren).

### 7.7 Schnittstellen
**HTTP (`/api`, JWT):**
| Methode | Pfad | Zweck |
|---|---|---|
| POST | `/api/gate` | Plattform-Passwort → Gate-Cookie (ohne JWT) |
| GET | `/api/me` | Profil, laufende Spiele |
| POST | `/api/games` | Spiel anlegen (Optionen) → `{gameId, code}` |
| GET | `/api/games?open=1` | offene Lobbys |
| POST | `/api/games/{id}/join` / `join-by-code` | beitreten |
| POST | `/api/games/{id}/leave` | verlassen (nur in der Lobby) |
| POST | `/api/ws-ticket` | WebSocket-Ticket |

**WebSocket (`/ws`), JSON-Nachrichten:**
- Client → Server: `{"t":"sub","gameId":…}`, `{"t":"act","gameId":…,"v":<version>,"a":{"type":"MOVE_ROLL"}}`, `{"t":"lobby","op":"ready|start|seat|options"}`, `{"t":"emote","id":3}`, `{"t":"ping"}`.
- Server → Client: `{"t":"state","v":…,"view":{…}}` (komplette gefilterte Sicht, typ. < 8 KB, einfacher und robuster als Diffs), `{"t":"events","items":[…]}` (für Animationen), `{"t":"error","code":"ILLEGAL_ACTION"}`, `{"t":"pong"}`.
- Broadcast: nach jedem `apply` für jede Verbindung im Spiel ein eigenes `view_for(player)` per `PostToConnection`. Bei `GoneException` wird die Verbindung aufgeräumt.
- **Reconnect:** Nach Neuladen oder Netzwechsel holt sich der Client ein neues Ticket, verbindet neu, sendet `sub` und bekommt den kompletten Zustand.
- Emotes statt freiem Chat (kein Moderationsbedarf, keine XSS-Fläche).

### 7.8 Lobby & Spielablauf
1. Host erstellt ein Spiel (Optionen aus 3.8), bekommt Link und 6-stelligen Code.
2. Spieler treten bei und wählen Sitz, Häftlingsfigur und (im Team-Modus) Team. „Bereit“-Status.
3. Host startet → `start_game` (Seed aus `secrets.randbits(64)`) → alle bekommen ihren State.
4. Disconnect: Der Spieler bleibt im Spiel, Timeouts greifen. Nach 3 verpassten Zügen kann der Host ihn „ersetzen“ (später durch einen Bot) oder das Spiel abbrechen.
5. Spielende → Statistik in `USER#…`, Replay bleibt 30 Tage abrufbar.

### 7.9 Simulation & Balancing (Bot-Grundlage)
- `sim/random_bot.py`: wählt zufällig aus `legal_actions`. Damit laufen Fuzz-Tests (10.000 Partien ohne Crash oder Invarianten-Bruch).
- `sim/heuristic_bot.py`: einfache Prioritäten (graben > Werkzeug beschaffen > heilen > suchen). Grundlage für spätere Bots.
- `run_sim.py`: Massensimulation pro Variante → Statistiken (durchschnittliche Partiedauer in Runden, Siegquote nach Sitzplatz, Nutzungs- und Siegkorrelation pro Karte/Gang/Background). Das ist das Werkzeug, um das eigene Kartendesign zu balancieren.

---

## 8. Frontend im Detail

### 8.1 Framework-Wahl: React 19 + TypeScript + Vite
- **Verbreitung:** größtes Ökosystem, beste Library-Auswahl für Animation, Gesten und Auth. Leicht, Mitwirkende zu finden.
- **Passend zum Use Case:** Das Spiel ist eine stark interaktive Single-Page-App mit Live-Zustand. SSR/SEO ist irrelevant (passwortgeschützt), daher reicht ein **statischer Vite-Build**. Er liegt auf S3/CloudFront und kostet praktisch nichts. Next.js/SSR würde nur Serverkosten und Komplexität bringen.
- Alternative wäre SvelteKit (statisch, kleinere Bundles). React gewinnt wegen Verbreitung und Ökosystem.

### 8.2 Libraries
| Zweck | Library |
|---|---|
| Build/Dev | Vite, TypeScript (strict) |
| Styling | Tailwind CSS v4 (keine Runtime-Styles → CSP-freundlich) |
| UI-Primitives | Radix UI / shadcn/ui (zugänglich: Dialoge, Sheets, Tooltips) |
| Client-State | Zustand (Spielzustand aus WebSocket) |
| Server-State (REST) | TanStack Query |
| Routing | React Router |
| Animation | Motion (ehem. Framer Motion): Kartenflug, Würfel, Figurenbewegung |
| Gesten | @use-gesture/react (Wischen der Hand, Bottom-Sheet) |
| Auth | aws-amplify v6 (nur `auth`-Modul) |
| Schemas | Zod (validiert eingehende Server-Nachrichten), TS-Typen generiert aus Pydantic (`pydantic` → JSON Schema → `json-schema-to-typescript`) |
| i18n | i18next (Deutsch zuerst, Englisch vorbereitet) |
| PWA | vite-plugin-pwa (Offline-Shell, Installierbarkeit, **kein** Caching von API-Daten) |
| Tests | Vitest, Testing Library, Playwright |

### 8.3 Screens
1. **Gate** (statisch, eigenes Mini-HTML): Passwortfeld.
2. **Login / Registrieren / Passwort vergessen / MFA**.
3. **Lobby-Übersicht:** eigene laufende Spiele, offene Lobbys, „Spiel erstellen“, „Mit Code beitreten“.
4. **Spiel erstellen:** Spielerzahl, Team-Modus, *Dig In*-Toggles (Direktorin, Orte mit Slot-Auswahl inkl. Live-Validierung), Timer, Siegpunkte.
5. **Warteraum:** Sitze, Figuren, Teams, Bereit-Status, Einladungslink teilen (Web Share API).
6. **Spielbildschirm** (Kern, s. 8.4).
7. **Spielende/Replay:** Gewinner, Statistik, Schritt-für-Schritt-Replay aus dem Event-Log.
8. **Regeln/Kartenlexikon:** durchsuchbar, aus `game-data` generiert.

### 8.4 Spielbildschirm, mobile-first (Hochformat)
```
┌──────────────────────────────┐
│ Gegnerleiste (scrollbar)      │ Avatar · Punkte · Handgröße · Prügel · Gang · Ort
├──────────────────────────────┤
│                              │
│   Spielplan (SVG, 6–7 Orte   │ Orte antippen = Info / Ziel wählen
│   im Ring, Figuren, NPCs)    │ Würfelanimation in der Mitte
│                              │
├──────────────────────────────┤
│ Statuszeile: „Dein Zug · 2   │ Timer-Ring
│ Aktionen“ / „Warte auf Max“  │
├──────────────────────────────┤
│ Aktionsleiste: kontextuelle  │ nur legal_actions aktiv, ≥ 48 px Touch-Ziele
│ Buttons (Suchen, Bewegen …)  │
├──────────────────────────────┤
│ Eigene Hand (Bottom-Sheet,   │ hochwischen = vergrößern, Karten antippen
│ Fächer, Zig., Tableau)       │ zum Auswählen (kein Drag nötig)
└──────────────────────────────┘
```
- **Entscheidungen** (Erpressung beantworten, Kampf, Reaktion) erscheinen als Modal mit Countdown und Haptik (`navigator.vibrate`, wo verfügbar).
- Querformat und Desktop: Spielplan links, Hand/Log rechts.
- **Barrierefreiheit:** Farben nicht als einziger Informationsträger, Screenreader-Labels, `prefers-reduced-motion` reduziert Animationen.
- **Performance:** SVG statt Canvas (wenige Objekte, gut skalierbar, zugänglich), Code-Splitting pro Route, Ziel < 200 KB JS gzip initial.
- **Screen Wake Lock** während des Spiels (optional, Einstellung).
- **Grafik:** eigene Assets, größtenteils in Blender gerendert, einheitlicher Stil (Details und vollständige Asset-Liste in 8.6). Bis die Assets fertig sind: SVG-Platzhalter (Icon + Farbe pro Kartentyp).

### 8.5 Client-Architektur
- `useGameSocket`: Verbindungsmanagement (Ticket holen, verbinden, Heartbeat alle 5 min, da API GW nach 10 min Idle trennt, exponentielles Reconnect, `sub`).
- Store hält `view` und `version`. Aktionen werden nicht optimistisch angewendet, denn Zufall und versteckte Information erfordern das Server-Ergebnis. Stattdessen zeigt die UI einen „Pending“-Zustand mit Spinner auf dem Button.
- Event-Queue spielt Server-Events sequenziell als Animationen ab, bevor der neue View angezeigt wird.

### 8.6 Grafische Elemente (Asset-Spezifikation)

#### 8.6.1 Grundsatzentscheidung: Blender rendert, der Browser zeigt 2D
- Blender liefert **vorgerenderte 2D-Bilder** (WebP mit Transparenz). Im Browser läuft **kein Echtzeit-3D** (kein three.js/WebGL).
  - Begründung: kleine Downloads, wenig Akkuverbrauch auf Handys, einfache CSP, ein einheitlicher Look auch auf schwachen Geräten.
- Die App setzt Plan, Karten und UI dynamisch per **SVG/HTML** aus den Einzelbildern zusammen. Das ist nötig, weil *Dig In* Orte austauscht und der Team-Modus 7 statt 6 Orte hat.
- **Texte stehen nie im Bild.** Kartennamen, Effekttexte, Zahlen und Ortsnamen rendert die App (i18n, Balancing-Änderungen ohne Neu-Rendern).
- **Wofür Blender sinnvoll ist (✅):**
  - Orte, Figuren, Gegenstände, Werkzeuge, Marker in großer Darstellung, Logo, Hintergründe, Kartenillustrationen.
  - Grund: Diese Dinge sollen plastisch wirken, und eine gemeinsame Licht- und Material-Basis hält sie konsistent.
- **Wofür Blender nicht sinnvoll ist (❌), sondern Vektor (SVG, z. B. Inkscape/Figma):**
  - Kartenrahmen, UI-Icons, kleine Piktogramme (≤ 32 px), Verbindungswege auf dem Plan, Fortschrittsbalken, Teamfarben-Ringe, Kartenrückseiten-Muster.
  - Grund: Diese Elemente müssen gestochen scharf skalieren, umfärbbar sein (CSS-Variablen) und winzig bleiben.

#### 8.6.2 Art Direction (Style Guide)
| Aspekt | Vorgabe |
|---|---|
| Stil | Moderner, **düsterer Soft-3D-Look** (abgenommen, Referenz: `art/renders/place.cellblock.soft.png`): abgerundete Kanten, keine Konturlinien, weiche Schatten, Nachtstimmung. Heruntergekommen: prozeduraler Schmutz und Laufspuren an Wänden und Böden, Risse, Strichlisten, Gang-Graffiti. Karikaturhaft statt realistisch, nicht brutal (keine Blutdarstellung, Prügel = Pflaster/Veilchen). |
| Kamera Orte | **Orthografisch, isometrisch** (Rotation X 54,736°, Z 45°), für alle Orte identisch. Ein Kamera-Preset in der Asset-Library. |
| Kamera Objekte | Orthografisch, Dreiviertel-Draufsicht (X = 50°, d. h. 40° über dem Boden, Z = 30°). Längliche Objekte liegen diagonal im Bild (z. B. Löffel: Kelle oben rechts), Objekt füllt ca. 80 % des Bildes. |
| Kamera Figuren | Orthografisch, frontal-leicht-seitlich (X = 82°, Z = 20°), Ganzkörper, Füße auf gemeinsamer Bodenlinie. Figuren schauen in Richtung -Y. Auf dem Spielplan werden sie zur Isometrie-Kamera gedreht (+35°). |
| Licht | Gemeinsames **Nacht-Licht-Rig:** kaltes Mondlicht als Key von vorne oben links (`#b9c8ff`, Stärke 2,6, Winkel 6°), kühles Rim-Licht von hinten (`#8fb0ff`, 1,6), dunkelblauer Himmel als Ambient (`#3a4a6e`, 0,3). **Warme Punktlichter** an jeder Lampe im Raum (`#ffb560`, 45 W) erzeugen Lichtinseln im Kalt-Warm-Kontrast. Lesbarkeit geht vor Stimmung: Spielrelevante Flächen (Gang, Figurenpositionen) müssen hell genug bleiben. |
| Shading | Principled BSDF: Roughness 0,65 (Standard), 0,3 (Porzellan, Papier, Kunststoff), Metall 0,55/0,38. Alle Objekte haben einen **Bevel-Modifier** (3 Segmente, *Harden Normals*) + Smooth Shading. Wände und Böden: **prozeduraler Schmutz** (Noise-Flecken + vertikal gestreckte Noise-Laufspuren, multipliziert mit Braun `#6e5f48`), Stärke pro Material einstellbar. Der verworfene Toon-Stil liegt nur noch als Referenzbild in `art/renders/archive_*`. |
| Farbpalette | Gedeckt und schmuddelig mit wenigen satten Akzenten: Wand Schmutzbeige `#b3ab9b`, Sockel dunkles Petrol `#285552`, Fliesen `#8a8f97`/`#4f545d` (Schachbrett, starker Kontrast), Gitter fast Schwarz `#16181e`, Erde `#6e4529`. Akzente: Häftlings-Orange `#d4581f`, Graffiti-Rot `#c0262d`, Lampenlicht `#ffcf8a`. Akzentfarben je Kartentyp (s. 8.6.5). Die Palette ist als Blender-Material-Library **und** als CSS-Tokens definiert. |
| Hintergrund | Transparent (*Film → Transparent*), weiche Kontaktschatten mit im Bild. |
| Renderer | **Cycles** (CPU, 160 Samples + Denoiser, ca. 15 s pro 1024²-Bild). View-Transform **AgX**, Look *Medium High Contrast*. |
| Lizenzen | Nur eigene Modelle oder **CC0**-Quellen (Poly Haven, ambientCG, Kenney). Quellen in `art/LICENSES.md` dokumentiert. |

#### 8.6.3 Spielplan & Orte
Jeder Ort ist ein **eigenständiges isometrisches Diorama-Tile**: ein Raumausschnitt auf einer quadratischen Bodenplatte, angeschnittene Wände („Puppenhaus“-Schnitt), in der Mitte frei für 1–6 Figuren. Die App ordnet die Tiles im Ring an und zeichnet die Wege per SVG.

| ID | Ort | Bildinhalt (Briefing) | Phase |
|---|---|---|---|
| `place.cellblock` | Zellentrakt | Zwei Zellen mit Gittertür, Etagenbett, Waschbecken, Poster an der Wand, Loch im Boden hinter Bett (Tunneleingang) | 2/5 |
| `place.cellblock_a` / `_b` | Zellentrakt A/B | Variante des Zellentrakts, farbige Bodenmarkierung (Team-Farbe als separates SVG-Overlay, Tile neutral) | 6 |
| `place.cafeteria` | Cafeteria | Lange Tische, Tabletts, Essensausgabe mit Besteckbehälter (Löffel!), Kochtopf | 5 |
| `place.showers` | Duschen | Gekachelter Raum, Duschköpfe, Dampf, Seife am Boden, Abfluss | 5 |
| `place.infirmary` | Krankenstation | Liege, Medikamentenschrank, Infusionsständer, Paravent | 5 |
| `place.recreation` | Freizeitbereich | Tischtennisplatte, Fernseher, Kartentisch mit Zigarettenstapeln, Sofa | 5 |
| `place.yard` | Hof | Asphalt, Basketballkorb, Hantelbank, Zaun mit Stacheldraht, Wachturm-Ecke | 5 |
| `place.library` | Bibliothek | Regale, Leselampe, Bücherwagen, Schachbrett | 7 |
| `place.gambling` | Spielzellen | Zelle mit Würfeln, Karten, Klopapierrolle mit Notizen, Kerze | 7 |
| `place.laundry` | Wäscherei | Waschmaschinen, Wäschekörbe, Leinen mit Häftlingskleidung, Bandagenrolle | 7 |
| `place.workshop` | Werkstatt | Werkbank, Schraubstock, Werkzeugwand (mit Lücken), Schleifmaschine | 7 |
| `place.gym` | Fitnessraum | Boxsack, Hanteln, Matten, Spiegel | 7 |
| `place.psych` | Psychiatrie | Gepolsterter Raum, Zwangsjacke am Haken, Stuhl, Lampe | 7 |
| `place.office` | Büro der Direktorin | Schreibtisch, Aktenschrank, Ventilator, Bestechungs-Umschlag, Fenster mit Jalousie | 7 |
| `place.solitary` | Einzelhaft | Kleine dunkle Zelle, Lichtschacht, Stahltür mit Klappe | 7 |

- **Ausgabe:** 1024 × 1024 px (zusätzlich 512er Version), transparenter Rand, Bodenplatte nimmt einheitlich die untere ⅔ ein.
- **Plan-Hintergrund** `board.bg`: kachelbare Textur (Erde/Beton mit Rissen), 1024 × 1024, nahtlos, kein Alpha. Optional sieht man im Querschnitt Tunnel unter dem Boden.
- **Platzhalter-Slots** für Figuren: Im Tile gibt es keine Markierungen, die Positionen definiert `board.yaml` (relative Koordinaten pro Ort).

#### 8.6.4 Figuren
| ID | Inhalt | Varianten | Ausgabe |
|---|---|---|---|
| `char.01` … `char.06` | 6 spielbare Häftlinge mit klar unterscheidbarer Silhouette und Farbe (z. B. der Riese, die Alte, der Nerd, die Tätowierte, der Dandy, der Junge). Einheitliches Grundrig. | **Standee** (Ganzkörper, auf dem Plan), **Portrait** (Büste, Avatar), **Pose „Graben“**, **Pose „Kampf“**, **Pose „verprügelt“** (Pflaster, Veilchen), **Pose „Sieg“** | Standee 256 × 384 (@1x, zusätzlich @2x/@3x), Portrait 256 × 256 (rund maskiert per CSS), Posen 512 × 512 |
| `npc.warden` | Gefängnisdirektorin: Uniform, Mütze, Klemmbrett, Pfeife | Standee, Portrait, Pose „Erwischt!“ (zeigt mit Finger) | wie oben |
| `npc.michel` / `npc.michelle` | Schläger-NPCs (Backlog) | Standee, Portrait | wie oben |

- **Basis: realistische Körper** aus Blender Studios **Human Base Meshes** (CC0, `art/vendor/human-base-meshes/`, v1.4.1). Die Spielzeugfiguren aus Grundkörpern wurden verworfen (wirkten „wie Lego“). Pro Figur in `art/scripts/characters.py`:
  - Mesh laden, Multires-Detail (Stufe 2) anwenden, Proportionen per Skalierung (z. B. „Der Riese“ 1,14× breiter).
  - **Regionen über die Face Sets des Meshes** (Kopf, Gesicht, Rumpf, Ober-/Unterarme, Hände, Beine, Füße) → Materialien Haut / Overall / Schuhe.
  - **Overall & Schuhe:** Regionen stark glätten (Muskeln/Zehen verschwinden) und entlang der Normalen aufpolstern. Beides läuft zur Stoffkante hin aus, damit Säume an der Haut anliegen. Stoffstruktur per Bump (Falten + Gewebe), hochgekrempelte Ärmel als Ringe, Häftlingsnummer per Raycast auf die Brust geklebt.
  - **Haut:** Principled mit leichtem Subsurface. Narbe, Tattoo sowie Schattierung unter Bart/Brauen als Punkt-Attribute (Masken), die der Shader liest.
  - **Haare** (Bart, Brauen, später Kopfhaar/Stoppeln): echte Haarkurven per Geometry Nodes aus denselben Masken (Dichte, Länge, Kämmrichtung einstellbar), gerendert mit Principled Hair BSDF. Wichtig: Der Haarträger muss ein `Curves`-Objekt sein, sonst rendert Cycles nichts.
  - **Augen:** mitgelieferte Augapfel-Meshes, Iris/Pupille per Shader.
- **Skelett:** Ein Armature mit 25 Knochen wird aus den Nahtstellen der Face Sets abgeleitet:
  - Becken, Wirbelsäule, Brust, Hals, Kopf.
  - Je Seite Oberarm, Unterarm, Hand und ein Finger-Knochen. Die Finger hängen gemeinsam an diesem Knochen, der Daumen bleibt an der Hand.
  - Je Seite Oberschenkel, Unterschenkel und Fuß.

  Die Hautgewichte berechnet das Skript selbst, mit weichen Übergängen an allen Gelenken. Augen und Brille hängen am Kopf-Knochen, die Häftlingsnummer an der Brust, die Ärmelaufschläge am Arm. Die Haare folgen automatisch.
- **Posen** (`characters.py`, `apply_pose(char, name)`), aufgebaut aus den Werkzeugen `rotate_bone()` (Achse X/Y/Z oder Eigendrehung), `move_bone()`, `crouch()` (Knie beugen, Füße bleiben am Boden) und `curl_fingers()` (Faust):
  - `relaxed`: Standee, natürliche Standhaltung
  - `dig`: tief gehockt, Löffel (`props.build_spoon`) in der linken Faust
  - `fight`: Deckung mit Fäusten
  - `beaten`: gekrümmt, Hand am Bauch, Veilchen (Hautmaske `bruise`), Pflaster
  - `victory`: Fäuste im V
- **Steckbriefe:** Jeder Häftling ist ein `CharacterSpec` in `characters.py`. Gesichtsmasken (Bart, Brauen, Haaransatz, Narbe) sind relativ zur Augenhöhe definiert und funktionieren damit für männliche und weibliche Basis-Meshes.

| ID | Name | Basis | Merkmale |
|---|---|---|---|
| `char.01` | Der Riese | männlich, 1,14× breit | Glatze, getrimmter Vollbart, grimmige Brauen, Narbe, Tattoo linker Unterarm, Ärmel hochgekrempelt |
| `char.02` | Die Alte | weiblich | kurze graue Locken, Brille, helle Haut, lange Ärmel |
| `char.03` | Der Nerd | männlich, schmal | kurzes braunes Haar, Brille, lange Ärmel |
| `char.04` | Die Tätowierte | weiblich | schwarzer Buzzcut, Tattoos an Hals und beiden Unterarmen, Träne unter dem Auge |
| `char.05` | Der Dandy | männlich | zurückgegeltes schwarzes Haar, Schnurrbart, hochgezogene Brauen, lange Ärmel |
| `char.06` | Der Junge | männlich, schmaler/kleiner | dunkle Haut, kurze schwarze Locken, Bartstoppeln |

- **Größe auf dem Spielplan:** Im Größentest (`art/renders/place.cellblock.preview.png`) ist eine Figur ~1,6 Einheiten hoch bei 2,4 Einheiten Wandhöhe. Auf dem Handy wird ein Ort-Tile ~300 px groß angezeigt, die Figur also nur ~60 px. Die App zeigt Standees daher ca. 1,3× größer als maßstabsgetreu an.
- Die Spielerfarbe wird nicht ins Bild gerendert, sondern per SVG-Ring um Standee und Portrait gelegt (Farbe bleibt frei zuweisbar, gut für Farbenblindheit).

#### 8.6.5 Karten
**Aufbau einer Karte (SVG/HTML, kein Blender):** Rahmen in Typ-Farbe, Kopfzeile (Name), **Illustrationsfeld (Blender-Bild)**, Textfeld (Effekt), Fußzeile (Zigarettenwert-Icon + Zahl, Typ-Icon). Format 5:7, Mindestbreite auf dem Handy 72 px (Fächer) bzw. 280 px (Detailansicht).

| Kartenart | Typ-Farbe | Illustrationen (je 1 Blender-Render, 512 × 512, transparent) | Anzahl Motive |
|---|---|---|---|
| Material | Grau | Behälter (Blechdose), Spitze (angespitzter Metallstab), Kettenglied (Kettenstück) | 3 |
| Waffe | Rot | Klinge (Rasierklinge mit Tape-Griff), Messer (selbstgemachtes Messer) | 2 |
| Accessoire | Lila | Kappe, Bandana, Halskette, Uhr, Stiefel, Ring | 6 |
| Seltener Gegenstand | Gold | Goldzahn, Universalgriff, Stahldraht, Schmuggel-Handy, Gefälschter Ausweis, Zahnbürsten-Shiv | 6 |
| Werkzeug | Braun | Löffel, Spitzhacke, Schaufel (improvisiert, mit Klebeband/Holzresten) | 3 |
| Aktionskarte | Blau | 9 Szenen-Motive: Schichtwechsel (Stempeluhr), Schleichweg (Lüftungsschacht), Paket von draußen (aufgerissenes Paket), Razzia (Taschenlampe + Wärterhand), Schmiergeld (Umschlag mit Zigaretten), Ablenkung (umgeworfenes Tablett), Erste Hilfe (Verbandskasten), Spitzel (Auge durch Türschlitz), Tunneleinbruch (einstürzender Gang) | 9 |
| Gang | je Gang eigene Farbe | 6 **Gang-Embleme** als 3D-Wappen/Patch (Crew, Kartell, Biker, Bratva, Triade, Schatten). Zusätzlich ein vereinfachtes SVG-Emblem für kleine Größen. | 6 |
| Hintergrund | Schwarz/Sepia | 18 kleine Szenen mit einer Häftlingsfigur in typischer Pose/Situation (z. B. „Ex-Bergarbeiter“ mit Grubenlampe). Wiederverwendung der Figuren-Rigs. | 18 |
| Trauma (*Dig In*) | Grünlich | Paranoia, Zittern, Albträume (+ evtl. weitere) als symbolische Objekte/Szenen | 3–4 |
| Rückseiten | – | Suchkarten, Hintergrund, Gang, Trauma: SVG-Muster + Logo (Logo aus Blender) | 4 |

**Summe Kartenillustrationen: ca. 57 Motive** (Karten gleichen Typs teilen sich ein Motiv, z. B. alle 14 Kettenglieder).

#### 8.6.6 Werkzeuge, Marker & Spielmaterial
| ID | Element | Blender | SVG-Piktogramm (24 px) |
|---|---|---|---|
| `token.cig1` / `token.cig5` | Einzelne Zigarette / Packung | ✅ 256 px | ✅ |
| `token.beating1` / `2` | Prügel (Pflaster / Pflaster + Veilchen) | ✅ | ✅ |
| `token.warning` | Verweis (rote Karte/Strafzettel) | ✅ | ✅ |
| `token.favor` | Gefälligkeit (Umschlag mit Siegel) | ✅ | ✅ |
| `token.bandage` | Bandage | ✅ | ✅ |
| `token.combat` | Kampfmarker (Boxhandschuh) | ✅ | ✅ |
| `token.digbonus` | Grabbonus (Grubenlampe) | ✅ | ✅ |
| `token.trauma` | Trauma (Gewitterwolke) | ✅ | ✅ |
| `pile.*` | Stapel-Ansicht für Löffel/Messer/Spitzhacke/Schaufel (3–4 übereinander liegende Objekte) | ✅ 256 px | – |
| `tunnel.stage0`…`stage5` | **Tunnel-Fortschritt** pro Spieler: Querschnitt durch Erdreich, Tunnel wird stufenweise länger, Stufe 5 = Licht am Ende | ✅ 512 × 256 | – (Balken zusätzlich SVG) |
| `dice.face1`…`6` | Würfelseiten (abgenutzter Knochenwürfel / Holzwürfel) | ✅ 256 px Texturen | ✅ |

**Würfel:** Die Animation läuft im Browser als **CSS-3D-Würfel** (6 Flächen = Blender-gerenderte Seitentexturen). Jedes Ergebnis ist flüssig animierbar, kein Video und keine großen Sprite-Sheets.

#### 8.6.7 Branding, UI & Screens
| ID | Element | Blender | Ausgabe |
|---|---|---|---|
| `brand.logo` | Schriftzug „Dig Out“ als 3D-Lettering, aus Erde/Beton gebrochen, Schaufel steckt im „O“ | ✅ (Cycles) | 1600 × 600 transparent + SVG-Vereinfachung |
| `brand.appicon` | App-Icon: Schaufel + Gitterstäbe, starke Silhouette | ✅ | 512, 192 (`any` + `maskable` mit Safe Zone 80 %), 180 (Apple Touch); Favicon als SVG (❌ Blender) |
| `screen.gate` | Hintergrund Passwortseite: Gefängnismauer bei Nacht, Suchscheinwerfer | ✅ | 1080 × 1920 (Hochformat) + 1920 × 1080, stark komprimiert (≤ 150 KB) |
| `screen.lobby` | Hintergrund Lobby: Blick in den Zellenblock | ✅ | wie oben |
| `screen.victory` | Siegerbild: Figur kriecht aus dem Tunnel ins Freie (pro Charakter mit Figuren-Rig) | ✅ | 6 × 1080 × 1080 |
| `screen.defeat` | Verlierer hinter Gittern | ✅ | 1 × 1080 × 1080 |
| `anim.loading` | Lade-Animation: Schaufel gräbt (Loop, 24 Frames) | ✅ | Animated WebP oder Sprite-Sheet, ≤ 100 KB |
| `emote.*` | 8 Emotes (lachen, wütend, Daumen hoch, schwitzen, Faust, Tränen, Pfeifen, schockiert) als Figuren-Köpfe | optional ✅, sonst SVG | 128 × 128 |
| `ui.icons` | Aktions-Icons (Suchen, Bewegen, Gang, Erpressen, Herstellen, Graben, Heilen, Kaufen …), Navigation | ❌ SVG (z. B. Lucide-Basis + eigene) | SVG-Sprite |

#### 8.6.8 Technische Vorgaben & Pipeline
- **Formate:** WebP (Qualität ~82, Alpha), AVIF optional für große Hintergründe. Responsive über `srcset` mit @1x/@2x/@3x. Farbraum sRGB. Durch AgX weichen die gerenderten Farben leicht von den Hex-Werten ab, daher werden die CSS-Tokens aus den **fertigen Renders** gepickt, nicht aus der Blender-Palette.
- **Benennung:** `<kategorie>/<id>@<n>x.webp`, z. B. `cards/item.chain@2x.webp`. Die **IDs entsprechen den IDs in `game-data/*.yaml`**, sodass das Frontend Assets automatisch zuordnet. Fehlendes Asset → Platzhalter.
- **Größenbudget:** Initial geladen (Gate, Login, Lobby) ≤ 400 KB Bilder. Das Spiel lädt die Plan- und Kartenbilder beim Betreten (≤ 2,5 MB gesamt), die PWA cached sie danach. Gesamtbudget aller Assets ≤ 8 MB.
- **Ordnerstruktur:**
  ```
  art/
    blender/
      places/*.blend          # generiert, zum Nachbearbeiten/Ansehen (nicht die Quelle!)
      characters/*.blend
      props/*.blend
    scripts/
      digout_art.py          # gemeinsame Bibliothek: Palette, Materialien inkl. Schmutz, Grundkörper,
                             #   Kamera-Presets (place/object/character), Licht-Rigs (place/studio), Render
      characters.py          # Figuren-Builder (char.01 „Der Riese“ …)
      build_cellblock.py     # je Asset(-Gruppe) ein Build-Skript; Quelle der Wahrheit ist der Code
      build_character.py     # Standee + Portrait
      build_spoon.py
      build_place.py         # Orte außer Zellentrakt (places.py + diorama.py)
      build_items.py         # Karten-Illustrationen, Marker, Würfel, Tunnelstufen, Logo, App-Icon (items.py)
      render_all.sh          # alles rendern + postprocess
      postprocess.mjs        # WebP @1x/@2x/@3x via sharp, PNG-App-Icons, Größenbudget-Check
    manifest.yaml            # Regeln pro Asset-Gruppe (Muster → Zielordner, Anzeigebreite @1x)
    renders/                 # Roh-PNGs (archive_* = verworfene Stilproben)
    vendor/human-base-meshes/  # Blender Studio Human Base Meshes v1.4.1 (CC0), Git LFS
    LICENSES.md
  frontend/public/assets/    # Ausgabe (nur fertige WebP/SVG)
  ```
- **Automatisierung:**
  1. `blender --factory-startup -b --python art/scripts/build_<asset>.py` baut die Szene komplett aus Code und rendert headless (Cycles, CPU: ca. 10–30 s pro Bild). `art/scripts/render_all.sh` rendert alles (ca. 40 min).
  2. `cd art && npm run postprocess` erzeugt nach `manifest.yaml` WebPs in @1x/@2x/@3x (nie hochskaliert) und PNG-App-Icons (512/192/180) in `frontend/public/assets/` und prüft das Größenbudget.
  3. Ein CI-Check (ohne Blender) prüft, ob alle IDs aus `game-data` ein Asset haben oder bewusst auf Platzhalter stehen, und ob das Größenbudget eingehalten wird.
- **Versionierung:** `.blend`-Dateien und Texturen über **Git LFS**, gerenderte WebPs normal im Repo (klein).
- **Erstellung lassen (z. B. durch einen KI-Agenten per Blender-MCP oder einen Grafiker):** Jede Tabellenzeile in 8.6.3–8.6.7 ist als Briefing formuliert (ID, Inhalt, Kamera, Größe). Empfohlene Reihenfolge:
  1. **Style-Probe:** ✅ erledigt (Zellentrakt, char.01, Löffel, gemeinsame Bibliothek `digout_art.py`).
  2. Danach in Batches nach Phase: Basisspiel-Assets (Phase 5) → Team (Phase 6) → *Dig In* (Phase 7).
  3. Jedes Batch: Render → Screenshot im echten UI auf Handy-Größe prüfen (Lesbarkeit bei 72 px Kartenbreite!) → Korrekturen.

#### 8.6.9 Mengenübersicht
| Kategorie | Anzahl Blender-Motive | davon Basisspiel |
|---|---|---|
| Orte (inkl. Team & *Dig In*) | 16 + Plan-Textur | 7 |
| Figuren (6 Häftlinge + Direktorin) × Varianten | 7 × ~6 = ~42 Renders aus 1 Rig | 36 |
| Kartenillustrationen | ~57 | ~53 |
| Marker, Stapel, Tunnelstufen, Würfel | ~30 | ~22 |
| Branding & Screens | ~14 | ~14 |
| **Summe** | **~160 Renders** (aus ca. 40 Modellen) | **~132** |
| SVG (nicht Blender) | Kartenrahmen (9 Typen), 4 Rückseiten, ~30 UI-Icons, ~15 Piktogramme, Favicon | |

---

## 9. Infrastruktur (Terraform) im Detail

### 9.1 Grundsätze
- Terraform ≥ 1.10, AWS Provider 6.x, gepinnt.
- **Remote State:** S3-Bucket mit **nativem S3-Locking** (`use_lockfile = true`, keine DynamoDB-Lock-Tabelle nötig), versioniert, verschlüsselt, Public Access blockiert. Wird einmalig per `infra/bootstrap` angelegt.
- Region **eu-central-1**. ACM-Zertifikat (nur mit eigener Domain) in **us-east-1** (CloudFront-Pflicht), per Provider-Alias.
- Umgebungen: `dev` und `prod` als getrennte State-Keys (gleiche Module, eigene `tfvars`). Ideal: getrennte AWS-Accounts per AWS Organizations.
- Standard-Tags: `project=digout`, `env`, `managed-by=terraform`.

### 9.2 Module
| Modul | Ressourcen |
|---|---|
| `static_site` | S3-Bucket (privat), CloudFront-Distribution (OAC, 3 Behaviors), Response Headers Policy, Cache Policies (SPA: `index.html` no-cache, Assets immutable), Custom Error → `index.html` |
| `gate` | CloudFront Function + KeyValueStore (HMAC-Key via `random_password`), Gate-Lambda, SSM-Parameter (nur Name, Wert manuell/Script, `ignore_changes`) |
| `auth` | Cognito User Pool (Lite), App Client (kein Secret, SRP), Pre-Sign-up-Trigger, Passwort-Policy, MFA optional |
| `data` | DynamoDB-Tabelle (On-Demand, TTL, GSI1, optional PITR) |
| `api_http` | HTTP API, JWT-Authorizer, Routen → Lambdas, Throttling, Access-Logs (ohne Query-Strings/Header) |
| `api_ws` | WebSocket API, Routen `$connect`/`$disconnect`/`$default`, Stage-Throttling |
| `lambda_fn` | generisches Modul: Funktion (python3.13, arm64), Rolle mit Inline-Least-Privilege-Policy, Log-Group (14 Tage), Layer-Anbindung |
| `scheduler` | Scheduler-Gruppe, IAM-Rolle zum Aufruf des Timeout-Lambdas |
| `observability` | SNS-Topic + E-Mail-Subscription, CloudWatch-Alarme, AWS Budget |
| `dns` (optional) | Route 53 Zone/Records, ACM-Zertifikat |
| `ci_oidc` | GitHub-OIDC-Provider + Deploy-Rolle (auf Repo/Branch eingeschränkt) |

### 9.3 Deployment-Ablauf
1. `terraform apply` (Infra + Lambda-Zips aus dem CI-Build-Artefakt).
2. Frontend-Build → `aws s3 sync` (Assets mit `Cache-Control: immutable`, danach `index.html`) → CloudFront-Invalidation nur für `/index.html` (die ersten 1.000 Invalidierungspfade pro Monat sind frei).
3. Smoke-Test (Playwright gegen `dev`).

---

## 10. Repository-Struktur
```
dig-out/
  project.md
  README.md
  game-data/                 # Single Source of Truth für Regeln-Daten
    board.yaml               # Orte, Suchwerte, Würfelmapping je Variante
    cards/search.yaml, backgrounds.yaml, gangs.yaml, actions.yaml, rare.yaml, trauma.yaml
    variants/base.yaml, team.yaml, digin.yaml
    schema/                  # JSON-Schemas zur Validierung der YAMLs
  backend/                   # siehe 7.2
  frontend/
    src/{app,routes,features/{gate,auth,lobby,game,replay,rules},components,lib,i18n}
    public/
  infra/
    bootstrap/               # State-Bucket, OIDC
    modules/…
    envs/dev, envs/prod
  art/                       # Blender-Dateien (Git LFS), manifest.yaml, Render-/Postprocess-Skripte (siehe 8.6.8)
  scripts/                   # rotate-gate.sh, build-lambdas.sh, gen-types.sh, seed-dev.sh
  docs/                      # rules.md (vollständige Spielregeln der eigenen Version), adr/ (Architekturentscheidungen)
  .github/workflows/
```
**Lokale Entwicklung ohne AWS:** `backend/devserver.py` (Starlette + WebSockets) nutzt dieselben Handler mit In-Memory-Repository und Fake-Auth. `npm run dev` proxyt `/api` und `/ws` dorthin. So kann man 6 Browser-Tabs als 6 Spieler öffnen.

---

## 11. Teststrategie
| Ebene | Werkzeug | Inhalt |
|---|---|---|
| Engine-Unit | pytest | jede Regel aus Kap. 2/3 als Testfall (z. B. „Herstellen im Zellentrakt verboten“, „Verteidiger beginnt Kampf“) |
| Engine-Property | hypothesis | **Invarianten:** Kartenerhaltung (Summe aller Karten konstant), Zigaretten ≥ 0, Prügel ∈ {0,1,2}, `legal_actions` nie leer solange Spiel läuft, `apply(legal)` wirft nie, `view_for` leakt keine fremden Handkarten/Stapelinhalte |
| Fuzz/Simulation | `sim/` | 10.000 Zufallspartien pro Variante in CI (nightly) |
| Daten | JSON-Schema | YAML-Kartendaten valide, alle `effect_id`s implementiert |
| Handler | pytest + moto | Lambdas gegen gemockte DynamoDB/API GW |
| Frontend-Unit | Vitest + Testing Library | Komponenten, Store, Protokoll-Parsing |
| E2E | Playwright | Gate → Registrierung → Lobby → 3 Spieler (3 Browser-Kontexte) spielen eine gescriptete Partie, inkl. **Mobile-Viewports** (iPhone, Pixel) |
| Security | bandit, pip-audit, npm audit, checkov/trivy, ZAP-Baseline gegen dev | in CI |
| Last (leicht) | Locust/k6 | 10 parallele Spiele, Konflikt-/Retry-Verhalten |

Coverage-Ziel Engine ≥ 95 %, Rest ≥ 80 %.

---

## 12. CI/CD (GitHub Actions)
- **PR:** Lint, Typecheck, Unit- und Property-Tests (Backend und Frontend), YAML-Schema-Check, `terraform fmt/validate/plan` (dev), Security-Scans. Der Plan wird als PR-Kommentar gepostet.
- **main:** Build (Lambda-Zips arm64, Frontend) → Deploy `dev` → E2E-Smoke.
- **Release-Tag:** Deploy `prod` mit manueller Freigabe (GitHub Environments).
- **Nightly:** Simulation (Fuzz und Balancing-Report als Artefakt), Dependency-Audit.
- Auth zu AWS ausschließlich per OIDC-Rolle, keine Secrets im Repo.

---

## 13. Umsetzungsphasen & Meilensteine

### Phase 0: Fundament
- [x] Repo-Struktur, Backend-Tooling (uv, ruff, mypy strict, pytest, hypothesis), Git + LFS-Attribute
- [ ] Frontend-Tooling (Vite, ESLint, Prettier), pre-commit-Hooks
- [ ] AWS-Account absichern (Root-MFA, Identity Center, Budget-Alarm)
- [ ] `infra/bootstrap`: State-Bucket, GitHub-OIDC-Rolle
- [ ] ADRs: Framework, Single-Table, Ticket-Auth, Gate-Mechanik
- **Ergebnis:** leere Pipeline läuft grün.

### Phase 1: Regelwerk & Daten
- [x] `docs/rules.md`: verbindliche Regeln des Basisspiels inkl. aller Klarstellungen (Team/Dig In folgen)
- [x] `game-data/*.yaml`; Schema = Pydantic-Modelle in `digout.engine.data` (strikt, Querverweise geprüft)
- [x] Karten-Effektkatalog: jede Karte/jeder Hintergrund hat `effect` + `timing`
- **Ergebnis:** Regeln und Daten freigegeben (Review durch dich).

### Phase 2: Spiel-Engine Basisspiel (rein Python)
- [x] Modelle, deterministischer RNG (splitmix64), Board, Setup
- [x] Alle Aktionen des Basisspiels inkl. Erpressung/Kampf, Herstellen, Graben, Markt, Training
- [x] Pending-Stapel + Schritt-Queue, Reaktionsfenster, Handlimit, Siegbedingung, Standardaktionen bei Zeitablauf
- [x] Alle Karteneffekte (9 Aktionskarten, seltene Gegenstände, 18 Hintergründe, 6 Gang-Fähigkeiten)
- [x] `view_for` + Leak-Property-Test, `legal_actions` (per Probelauf garantiert legal)
- [x] Random- und Heuristik-Bot, Simulation (30 Partien/4 Spieler: alle beendet, Median 28 Runden)
- [ ] Balancing: bessere Bots, größere Simulationen, Spieldauer Richtung 15–20 Runden
- **Ergebnis:** CLI-Partie mit Bots komplett spielbar, Property-Tests grün.

### Phase 3: Lokaler Multiplayer-Prototyp
- [x] Service-Schicht `digout.service` (Lobby, Spiel, Zeitlimits, Repository-Interface; transportunabhängig für die Lambdas)
- [x] Devserver (Starlette/Uvicorn, In-Memory, Dev-Login per Header/Query), WS-Protokoll inkl. Versions-Check (`STALE`)
- [x] Frontend-Grundgerüst: React 19, Vite 8, Tailwind 4, Zustand, React Router; Socket mit Auto-Reconnect
- [x] UI: Login (Dev), Lobby, Warteraum mit Figurenwahl, Spielplan mit gerenderten Orten, Spielerleiste, Hand mit Kartenauswahl, Aktionsleiste, Entscheidungsdialoge, Verlauf, Sieg-Overlay
- [x] Ende-zu-Ende geprüft: 2 WS-Clients spielen 400 Aktionen über den Vite-Proxy, kein Hand-Leak; Screenshot-Check (Headless Chrome)
- [x] Feedback-Runde 1 umgesetzt:
  - zusammenhängender Spielplan (`art/scripts/build_board.py`: alle 6 Räume auf einem Erdblock, Ring-Anordnung in Würfelreihenfolge, `board.layout.json` mit Raum-Umrissen, Figuren-Stellplätzen und Maßstab)
  - Würfelzahlen an jedem Raum, erreichbare Räume leuchten nach dem Würfeln; gezieltes Gehen klar als „2 Aktionen = ganzer Zug“ gekennzeichnet
  - Raum-Infos (Suchwert, Herstellen, Spezialaktion) als Schild auf dem Plan + Raum-Fenster mit allen Aktionen, gesperrte Aktionen mit Begründung (`frontend/src/lib/rooms.ts`)
  - Gang-Embleme (gerendert) + Gang-Übersicht mit Stärke, Beitrittsbedingung, freien Plätzen, Mitgliedern
  - Ganzkörper-Figuren (Standees) stehen in den Räumen statt Porträt-Kreisen
- [ ] TS-Typen aus Pydantic generieren (aktuell handgeschrieben in `frontend/src/lib/types.ts`)
- [ ] Animationen (Würfel, Kartenflug, Figuren), Sounds
- **Ergebnis:** 2–6 Tabs spielen lokal eine Partie.

### Phase 4: AWS-Infrastruktur & Backend-Deployment
- [x] Terraform (`infra/`): DynamoDB, Cognito (Lite, Pre-Sign-up-Trigger), 6 Lambdas mit eigener Least-Privilege-Rolle, HTTP-API (JWT) + WebSocket-API, EventBridge Scheduler, CloudFront (OAC, Gate-Function + KeyValueStore, Security-Header/CSP), S3, SSM, Alarme + Budget; `terraform validate` grün
- [x] Lambdas (`digout.aws.handlers`): HTTP, WS connect/disconnect/default, Timeout, Pre-Sign-up; DynamoDB-Repository mit optimistischem Locking; WS-Tickets; Gate mit scrypt + Rate-Limit
- [x] Frontend: Laufzeit-Config (`config.json`), Cognito-Login/Registrierung (ohne SDK), WS über Ticket, statische Passwortseite `/gate/`
- [x] Deploy-Skript `scripts/deploy.py` (State-Bucket-Bootstrap, Lambda-Build arm64, Terraform, Passwort, Frontend-Upload, Invalidation) + Anleitung `docs/deploy.md`
- [x] Tests gegen moto (DynamoDB/SSM): Locking, Gate, Rate-Limit, Tickets, kompletter Spielablauf über die Handler
- [ ] Erstes echtes Deployment + Smoke-Test (durch dich, siehe `docs/deploy.md`)
- **Abweichungen vom ursprünglichen Plan (bewusst):** WebSocket direkt zum API Gateway statt über CloudFront (Ticket-Auth macht das Gate-Cookie dort unnötig, kein Pfad-Mapping-Problem); scrypt (Standardbibliothek) statt Argon2 (keine nativen Pakete); Cognito ohne E-Mail mit Auto-Bestätigung nach Plattform-Passwort, Passwort-Reset durch Admin; Login per `USER_PASSWORD_AUTH` ohne Amplify; eine Umgebung pro `--env` statt getrennter Konten.

### Phase 5: Mobile UX & Polish
- [ ] Mobile-Layout final, Gesten, Animationen (Würfel, Karten, Figuren), Haptik, Sounds (optional)
- [ ] PWA, Reconnect-Robustheit (Netzwechsel, Tab im Hintergrund), Wake Lock
- [x] Blender-Pipeline Grundlage (8.6.8): Bibliothek `digout_art.py`, Build-Skripte
- [x] Blender-Pipeline Rest: Manifest, `render_all.sh`, Postprocessing (WebP, Größen, Budget)
- [x] Style-Probe (Zellentrakt, char.01, Löffel)
- [x] Figuren: 6 Häftlinge × (Standee, Portrait, 4 Posen) – `art/scripts/build_character.py`
- [x] Orte Basisspiel: Zellentrakt, Cafeteria, Duschen, Krankenstation, Freizeitbereich, Hof – `build_cellblock.py`, `build_place.py`
- [x] Karten-Illustrationen (Material, Waffen, Accessoires, seltene Gegenstände, Werkzeuge, 9 Aktions-Motive), Marker, Würfel, Tunnelstufen, Logo, App-Icon – `build_items.py`
- [ ] Noch offen: Gang-Embleme, 18 Hintergrund-Szenen, Kartenrückseiten/-rahmen (SVG), Screens (Gate, Lobby, Sieg/Niederlage), Lade-Animation, Emotes, Overall-Falten
- [ ] SVG: Kartenrahmen, UI-Icons, Piktogramme. Kartenlexikon, Tutorial-Overlay für den ersten Zug
- [ ] Replay-Ansicht, Statistiken
- [ ] Playwright-E2E mobil, Barrierefreiheits-Check (axe)
- **Ergebnis:** Basisspiel „Release Candidate“.

### Phase 6: Team-Modus
- [ ] Team-Plan (7 Orte), Teampunkte, Kampfhilfe, Tausch-Aktion, Craft-/Dig-Ortsregeln, Gang-Bewegung
- [ ] Lobby: Teamzuweisung, Validierung 4/6 Spieler
- [ ] Tests + Simulation
- **Ergebnis:** Team-Modus wählbar.

### Phase 7: *Dig In*
- [ ] Direktorin (Bewegung, Verweis, Einzelhaft), Büro & Bestechung
- [ ] 6 neue Orte, Slot-System + Validierung bei Spielerstellung
- [ ] Trauma-Karten, Bandagen, Kampfmarker, Massenschlägerei (simultan-verdeckt)
- [ ] Balancing-Simulation aller Kombinationen
- **Ergebnis:** alle Module frei kombinierbar.

### Phase 8: Härtung & Go-Live `prod`
- [ ] Security-Review (Threat Model nach STRIDE, ZAP-Scan, IAM-Review mit IAM Access Analyzer)
- [ ] Lasttest, Kostenkontrolle (Cost Explorer nach 1 Woche)
- [ ] `prod` deployen, Plattform-Passwort setzen, Freunde einladen
- [ ] Feedback-Runde → Balancing v1

---

## 14. Backlog (später)
- **Bots:** Heuristik-Bot (Phase 2) → besserer Bot (MCTS mit Determinisierung der versteckten Information). Bots füllen freie Plätze oder ersetzen Disconnects.
- **Michel & Michelle** (Regeln bekannt, Kap. 2): NPC-Schläger mit eigenem Kartenstapel, besonders für 2 Spieler. Lässt sich leicht als weiteres Toggle ergänzen.
- Asynchrones Spielen (lange Timer + Web-Push-Benachrichtigung „Du bist dran“).
- Zuschauermodus.
- Eigene Domain + SES für E-Mails.
- Account-Löschung (Self-Service, DSGVO).
- Kartendaten-Editor (Admin-UI) für Balancing.

---

## 15. Offene Fragen
1. **Eigene Domain?** Ohne Domain läuft alles unter `xyz.cloudfront.net` (kostenlos, HTTPS inklusive). Mit Domain: Route 53 + ACM.
2. **Spieltitel und Grafikstil:** Arbeitstitel „Dig Out“ ok? Wer erstellt die Blender-Assets (KI-Agent per Blender-MCP, du selbst, Grafiker)?
3. **Sprache:** nur Deutsch, oder Deutsch + Englisch von Anfang an?
4. **Zug-Timer:** 90 s Zug / 20 s Reaktion als Standard ok? Soll es zusätzlich einen „entspannten“ Modus ohne Timer geben?
5. **Kartendesign v0 (Kap. 3):** Richtung ok, oder lieber andere Schwerpunkte (z. B. weniger „Take that“)?
6. **Getrennte AWS-Accounts** für dev/prod (empfohlen) oder ein Account mit zwei Umgebungen?

---

## 16. Quellen
- RulesPal – Dig Your Way Out Rulebook: https://rulespal.com/dig-your-way-out/rulebook
- Brettspielgilde – Rezension: https://www.brettspielgilde.com/blog/dig-your-way-out
- board-game-rules.com – Dig In Expansion: https://board-game-rules.com/boardgames/dig-your-way-out/dig-your-way-out-dig-in-expansion/
- board-game-rules.com – Basisspiel: https://board-game-rules.com/boardgames/dig-your-way-out/
- Dice Tower – Spielseite: https://dicetower.com/board-game/266504
- Board Game Bliss – Produktseite: https://www.boardgamebliss.com/products/dig-your-way-out
- Kickstarter (Borderline): https://www.kickstarter.com/projects/borderline/dig-your-way-out
- BoardGameGeek: https://boardgamegeek.com/boardgame/266504
