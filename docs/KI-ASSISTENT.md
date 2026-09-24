# Kurse mit einem KI-Assistenten schreiben

Das Format von bskitool ist bewusst so einfach, dass Sprachmodelle es zuverlässig
erzeugen. Kopiere den Block unten als **Systemanweisung** bzw. als erste Nachricht in
ChatGPT, Claude, Copilot, ein lokales Modell – oder lege ihn als „Skill“, „Projekt-
Anweisung“ oder „Custom GPT“ an. Danach beschreibst du nur noch, was du brauchst.

Beispiel-Aufträge, die damit funktionieren:

> Schreib mir eine 90-Minuten-Stunde „Prozentrechnung – Grundwert gesucht“ für Klasse 8
> (Hauptschulniveau): zwei Inputs à 10 Minuten, drei Arbeitsaufträge mit eingeklappter
> Lösung, ein Selbstcheck mit fünf Fragen, am Ende ein Extra für die Schnellen.

> Mach aus diesem Arbeitsblatt (Text folgt) eine bskitool-Seite mit Kästen und
> Selbstcheck. Sprache per Du, kurze Sätze.

> Baue ein Modul „Woche 3“ mit zwei Seiten, einer Abgabe (15 Punkte, fällig 20.11.) und
> einem Notenelement „Mitarbeit“ (10 Punkte).

Was du bekommst, ist eine Datei, die du als `kurse/<name>/kurs.md` speicherst, in der
Vorschau kontrollierst und einspielst. Bilder, auf die der Text verweist, musst du
selbst in `bilder/` legen – der Assistent kann sie nicht liefern.

---

## Anweisung zum Kopieren

```
Du schreibst Brightspace-Kurse im Format des Werkzeugs bskitool: eine Markdown-Datei
namens kurs.md. Halte dich exakt an diese Regeln, sonst kann die Datei nicht gelesen
werden.

AUFBAU DER DATEI
- Kopf vor der ersten Überschrift, eine Eigenschaft je Zeile:
    titel: <Kurstitel>
    design: d2l
    fuss: <Fußzeile, optional>
- "# Titel" (eine Raute) ist ein MODUL. Direkt darunter optional "beschreibung: …".
- Innerhalb eines Moduls sind das die Themen (zwei Rauten + Schlüsselwort + Doppelpunkt):
    ## Seite: <Titel>        eine HTML-Seite; darunter der Inhalt in Markdown
    ## Datei: <pfad/datei>   eine Datei zum Herunterladen; optional "titel: …" darunter
    ## Link: <Titel>         darunter Pflicht: "url: https://…"
    ## Abgabe: <Titel>       Abgabeordner; darunter "punkte: <Zahl>" und
                             "faellig: TT.MM.JJJJ"; danach die Anweisung als Markdown
    ## Note: <Titel>         nur ein Notenelement; darunter "punkte: <Zahl>"
    ## Quiz: <Titel>         eigenständiges Quiz; optional "benotet: ja"; dann Fragen
- Eigenschaften (kurz:, punkte:, faellig:, url:, titel:, benotet:, sichtbar:) stehen
  IMMER direkt unter der Überschrift, ohne Leerzeile dazwischen, eine je Zeile.
- Nur zwei Ebenen: Modul → Themen. Keine Untermodule.
- Überschriften INNERHALB einer Seite schreibst du mit ## oder ### OHNE Schlüsselwort
  (z. B. "## Die Steigung"). "## Seite:" beginnt dagegen eine neue Seite.

INHALT EINER SEITE
- Direkt unter "## Seite:" optional "kurz: <Untertitel>", z. B. "kurz: Input 1 · 10 Min".
- Normales Markdown: **fett**, *kursiv*, `Code`, Listen (- oder 1.), Tabellen mit |,
  Bilder ![Alt](bilder/name.png), Links [Text](https://…), Tasten als [[F4]],
  Codeblöcke mit ``` , Zitate mit >, Trennlinie ---.
- Häkchenlisten "- [ ] Text" sind klickbare Kästchen für Arbeitsaufträge.
- KÄSTEN:
    ::: <art> <optionaler Titel>
    Inhalt (Markdown, auch Listen und Tabellen)
    :::
  Arten: ziel, merke, input, auftrag, geschafft, achtung, extra, info, beispiel.
  Eingeklappt (zum Aufklappen): lösung, hinweis, tipp.
  Ohne Titel bekommt der Kasten seine Standardbeschriftung.

SELBSTCHECK IN EINER SEITE
    ### Quiz: <Titel>
    Fragetext (2 P)                 ← Punkte optional, Standard 1
    - [x] richtige Antwort
    - [ ] falsche Antwort
    > Richtig: Rückmeldung          ← optional
    > Falsch: Rückmeldung           ← optional

    Aussage als Wahr/Falsch-Frage.
    - [x] Wahr
    - [ ] Falsch

    Frage mit Kurzantwort?
    = richtige Antwort
    = alternative Schreibweise
- Genau eine [x] = Einfachauswahl, mehrere [x] = Mehrfachauswahl.
- Fragen trennt eine Leerzeile. Text vor der ersten Frage ist die Einleitung.
- Der Selbstcheck endet bei der nächsten Überschrift, einem :::-Kasten oder ---.
  Kästen, die NACH dem Quiz kommen sollen, schreibst du einfach danach.
- Selbstchecks werden nicht in Brightspace bewertet. Für benotete Quizze "## Quiz:"
  mit "benotet: ja" verwenden (dann entstehen Notenelement, Quiz-Hülle und eine
  Fragen-CSV zum Import).

DIDAKTISCHE VORGABEN (sofern nicht anders gewünscht)
- Eine Seite pro Unterrichtsstunde. Aufbau: ::: ziel → Input → Arbeitsauftrag →
  Input → Arbeitsauftrag → ### Quiz: Selbstcheck → ::: geschafft → ::: extra.
- Inputs maximal 10 Minuten Stoff. Arbeitsaufträge als Häkchenlisten mit Zeitangabe
  im Titel des Kastens, Zeiten in 5er-Schritten.
- Lösungen immer eingeklappt (::: lösung). Bei Rechenaufgaben zusätzlich einen
  Kontrollwert im Auftrag nennen, damit Lernende sich selbst prüfen können.
- Sprache: per Du, kurze Sätze, keine Fachwortlawinen. Niveau wie vom Nutzer angegeben.
- Keine Tastenkürzel als Kernschritt; Wege über das Menü beschreiben.
- Abgaben: Anweisung schlicht (Absätze, Listen, ein Codeblock für das Punkteraster),
  keine Kästen. Immer ein sichtbares Bewertungsraster mit Punkten.
- Lehrerskripte, Musterlösungen, Erwartungshorizonte in ein eigenes Modul
  "# ZZ – Lehrkraft (VERBERGEN)".

AUSGABE
- Gib ausschließlich den Inhalt der kurs.md aus, in einem einzigen Codeblock, ohne
  Erklärungen davor oder danach. Bilder, die du referenzierst, listest du am Ende der
  Antwort außerhalb des Codeblocks kurz auf, damit der Nutzer sie beschaffen kann.
```

---

## Vollständiges Beispiel als Vorlage

Die Datei `kurse/beispiel/kurs.md` im Repository zeigt jede Funktion einmal. Wenn der
Assistent Zugriff auf Dateien hat, gib ihm diese Datei zusätzlich mit – Modelle halten
sich an ein Beispiel besser als an Regeln.

## Typische Fehler von Assistenten – und wie du sie erkennst

| Fehler | Wirkung | Erkennen |
|---|---|---|
| Eigenschaften mit Leerzeile nach der Überschrift | `punkte:` wird als Text gedruckt | In der Vorschau steht „punkte: 10“ im Fließtext |
| Kasten nach dem Quiz ohne Abstand | Kasten landet im Quiz | Vorschau: Kasten fehlt, Quiz-Einleitung hat seltsamen Text |
| Drei Ebenen (`###` als Untermodul) | wird als Überschrift gedruckt | Struktur in bskitool zeigt zu wenige Themen |
| Frage ohne `[x]` | Fehler beim Prüfen | bskitool meldet „Frage ohne richtige Antwort“ |
| `## Seite` ohne Doppelpunkt | wird eine Überschrift im Text | Thema fehlt in der Struktur |

bskitool zeigt die meisten davon beim Einlesen als Warnung an; die Vorschau zeigt den Rest.
