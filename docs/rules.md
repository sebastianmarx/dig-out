# Dig Out – Spielregeln (Basisspiel)

Verbindliche Regeln der digitalen Version. Zahlenwerte und Kartentexte stehen in `game-data/*.yaml`; dieses Dokument beschreibt den Ablauf und alle Detailentscheidungen, die die Engine (`backend/src/digout/engine`) umsetzt. Abschnitte mit **Klarstellung** schließen Lücken der Brettspiel-Vorlage.

## 1. Ziel
Wer zuerst die **Tunnelpunkte** erreicht, gewinnt sofort (2–3 Spieler: 12, 4: 10, 5–6: 8). Punkte bringen eingegrabene Werkzeuge: Löffel 1, Spitzhacke 2, Schaufel 3, plus Boni durch Hintergründe.

## 2. Material & Aufbau
- Suchstapel (77): Materialien, Klingen, Accessoires, 6 seltene Gegenstände, 18 Aktionskarten (`cards.yaml`). Abwurf offen daneben; ist der Stapel leer, wird der Abwurf neu gemischt.
- Offene Stapel: 11 Löffel, 11 Spitzhacken, 11 Schaufeln, 20 Messer. Abgeworfene Werkzeuge/Messer kommen oben auf ihren Stapel zurück.
- 6 Gangs mit je 4 Karten. Abgegebene Gangkarten kommen unter ihren Stapel.
- 18 Hintergründe: Jeder Spieler erhält verdeckt einen.
- Jeder Spieler startet im Zellentrakt mit 3 Suchkarten, 0 Zigaretten, 0 Prügeln.
- Startspieler zufällig, dann reihum.

## 3. Spielzug
- Bis zu **2 Aktionen**. Der Zug endet erst durch „Zug beenden“ (oder Zeitablauf), auch bei 0 verbleibenden Aktionen – freie Aktionen bleiben möglich.
- **Freie Aktionen** (kosten nichts): Hintergrund aufdecken (Zeitpunkt `own_turn`), Zug beenden.
- **Handlimit** am Zugende: 10 (Hamsterer mit Crew: 12). Darüber muss der Spieler sofort abwerfen.
- Pro Zug je **höchstens einmal**: Suchen, Erpressen, Herstellen, Neu würfeln (Triade).

## 4. Basisaktionen (überall)
| Aktion | Kosten | Regel |
|---|---|---|
| Suchen | 1 | Ziehe so viele Karten wie der Suchwert des Ortes (Crew +1). |
| Einfache Bewegung | 1 | Würfeln, Augenzahl n bietet Ort n oder n+1 (`board.yaml`). Steht man auf einem davon, muss man zum anderen. Sonst Wahl. Triade: 1× pro Zug vor der Wahl neu würfeln. |
| Vorsichtige Bewegung | 2 | Beliebiger anderer Ort. |
| Gang beitreten | 1 | Accessoires abwerfen (verschieden, aus der erlaubten Auswahl), oberste Gangkarte nehmen. Alte Gangkarte geht unter ihren Stapel. Gefälschter Ausweis = beliebiges Accessoire. |
| Aktionskarte / Handy | 1 | Effekt ausführen, Karte abwerfen (Handy bleibt auf der Hand). |
| Erpressen | 1 | Siehe 6. |
| Herstellen | 1 | Siehe 7. |

## 5. Ortsaktionen
| Ort | Aktion | Regel |
|---|---|---|
| Zellentrakt | Graben | 1 Werkzeug von der Hand in den eigenen Tunnel (offen). Nicht mit 2 Prügeln. |
| Cafeteria | Löffel klauen | Obersten Löffel nehmen. |
| Krankenstation | Heilen | 1 Prügel entfernen. |
| Freizeitbereich | Verkaufen | Beliebig viele Karten abwerfen → Zigaretten = Summe ihrer Werte. |
| Freizeitbereich | Kaufen | 1 Messer (2), 2 Messer (5), Spitzhacke (6), Schaufel (8); Kartell −1 (min. 1). Nur wenn der Stapel genug hat. |
| Hof | Training | 1 Waffe von der Hand als **vorbereitete Waffe** ablegen (max. 1). Sie kann in einem späteren Kampf wie eine Handwaffe gespielt werden. |

Zellentrakt und Duschen: kein Herstellen.

## 6. Erpressung & Kampf
1. Angreifer wählt ein Ziel am selben Ort, nennt ein Werkzeug (Löffel/Spitzhacke/Schaufel) und zeigt eine Waffe von der Hand. Ziele mit aktivem **Phantom** sind nicht wählbar.
2. Das Ziel antwortet:
   - **Nachgeben** (nur möglich, wenn es das Werkzeug hat): Werkzeug geht an den Angreifer, fertig. Die gezeigte Waffe bleibt beim Angreifer.
   - **Reaktion** Ablenkung (Karte) oder Bestecher (Hintergrund): Erpressung abgebrochen.
   - **Weigern** → Kampf.
3. **Kampf** (Klarstellung): Die gezeigte Waffe gilt als erste gespielte Waffe des Angreifers (abgeworfen). Danach muss der **Verteidiger** antworten, dann wieder der Angreifer usw. Wer am Zug ist, muss so viele Waffen spielen wie gefordert (normal 1) oder **aufgeben** und verliert.
   - Biker-Verteidiger: 1× pro Kampf **aussetzen** – der Gegner muss erneut 1 Waffe spielen.
   - Raufbold (Hintergrund): statt einer Waffe aufdecken; der Gegner muss danach 2 (Biker: 3) Waffen spielen.
   - Vorbereitete Waffe zählt wie eine Handwaffe.
4. **Verlierer** bekommt 1 Prügel (2, wenn der Sieger zuletzt den Zahnbürsten-Shiv gespielt hat). **Belohnung:** Verliert der Verteidiger und hat er das genannte Werkzeug, bekommt der Sieger dieses Werkzeug; sonst zieht der Sieger 1 zufällige Handkarte des Verlierers. Bratva-Sieger: +1 Zigarette je Prügel des Verlierers.
5. Gespielte Messer gehen auf den Messerstapel, Klingen/Shiv in den Suchabwurf.

## 7. Herstellen
Rezepte (`rules.yaml`): 2 Kettenglieder + Spitze → Spitzhacke; 2 Kettenglieder + Behälter → Schaufel; 2 Kettenglieder + Klinge → 2 Messer. Universalgriff = Spitze oder Behälter, Stahldraht = 2 Kettenglieder. Jede abgegebene Karte muss beitragen (keine überzähligen). Mechaniker: 1 (Biker 2) fehlende Zutaten ignorieren. Nicht im Zellentrakt/den Duschen, nicht mit Prügeln, nicht wenn der Zielstapel leer ist (bei 2 Messern: so viele wie vorhanden).

## 8. Prügel
Maximal 2. Mit 1: kein Herstellen. Mit 2: kein Herstellen, kein Graben. Prügel über dem Maximum verfallen.

## 9. Hintergründe
1× pro Spiel aufdeckbar, Zeitpunkt laut Karte (`backgrounds.yaml`), danach offen. Ist man in der genannten Gang, gilt der stärkere Wert. **Klarstellung zu Reaktionsfenstern:** Wer Prügel erhalten würde und noch einen verdeckten Hintergrund hat, bekommt immer ein Reaktionsfenster (auch ohne passende Karte), damit das Fenster nichts über die Karte verrät. Gleiches gilt für die Antwort auf eine Erpressung.

## 10. Spielende
Sobald ein Spieler die Zielpunkte erreicht (auch außerhalb seines Zuges, z. B. Meisterdieb), endet das Spiel sofort; er gewinnt.

## 11. Zeitlimits (Online)
Standard: **kein Zeitlimit**. Der Gastgeber kann im Warteraum 60/90/120 s pro Zug wählen (Reaktionen dann 25 s).
Läuft eine Entscheidung ab, greift die Standardwahl: Ortswahl → erster Ort; Erpressung → Weigern; Kampf → Aufgeben; Abwerfen → zuletzt gezogene Karten; Kartenwahl → erste Option; Reaktionsfenster → keine Reaktion; eigener Zug → Zug beenden.

## 12. Noch nicht umgesetzt
Team-Modus, *Dig In*, Michel & Michelle (Optionen werden bei Spielstart abgelehnt).
