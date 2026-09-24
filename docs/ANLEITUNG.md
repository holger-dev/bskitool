# bskitool – Anleitung für Lehrkräfte

Diese Anleitung führt dich von der Installation bis zum freigegebenen Kurs. Du brauchst
keine Programmierkenntnisse. Wenn du weißt, wie man eine Textdatei schreibt und einen
Ordner anlegt, reicht das.

**Inhalt**

1. [Was bskitool macht – in 60 Sekunden](#1-was-bskitool-macht--in-60-sekunden)
2. [Installation](#2-installation)
3. [Die Oberfläche kennenlernen (ohne Brightspace)](#3-die-oberfläche-kennenlernen-ohne-brightspace)
4. [Deinen ersten Kurs schreiben](#4-deinen-ersten-kurs-schreiben)
5. [Zugang zu Brightspace einrichten](#5-zugang-zu-brightspace-einrichten)
6. [Einspielen: Trockenlauf, echt, rückgängig](#6-einspielen-trockenlauf-echt-rückgängig)
7. [Nach dem Einspielen: freigeben](#7-nach-dem-einspielen-freigeben)
8. [Einen Kurs weiterentwickeln](#8-einen-kurs-weiterentwickeln)
9. [Aufräumen: Module und Co. löschen](#9-aufräumen-module-und-co-löschen)
10. [Mit einem KI-Assistenten arbeiten](#10-mit-einem-ki-assistenten-arbeiten)
11. [Gute Kurse schreiben – was sich bewährt hat](#11-gute-kurse-schreiben--was-sich-bewährt-hat)
12. [Wenn etwas nicht klappt](#12-wenn-etwas-nicht-klappt)

---

## 1. Was bskitool macht – in 60 Sekunden

Du schreibst deinen Kurs in **eine Textdatei** namens `kurs.md`. Darin steht mit ein paar
festen Regeln, welche Module es gibt, welche Seiten darin liegen, was auf den Seiten
steht, wo ein Selbstcheck hingehört, welche Abgaben es gibt und wie viele Punkte sie
bringen. Bilder und Dateien legst du daneben.

bskitool liest diese Datei, baut daraus fertige HTML-Seiten im Design der Brightspace-
Vorlage und legt über die Brightspace-Schnittstelle (API) alles in deinem Kurs an:
Module, Seiten, Dateien, Links, Abgabeordner, Notenelemente. Alles **verborgen** – du
gibst dann frei, was die Klasse sehen soll.

Vorher kannst du dir jede Seite im Browser ansehen, einen Trockenlauf machen (der
zeigt, was passieren würde, ohne etwas zu ändern), und wenn dir das Ergebnis nicht
gefällt, macht **Rückgängig** alles wieder weg.

Was du nicht tun musst: in Brightspace Seiten anlegen, den HTML-Editor bedienen,
Abgabeordner mit Notenelementen verknüpfen, Punkte eintragen.

---

## 2. Installation

### Voraussetzung: Python 3

bskitool ist ein Python-Programm ohne Zusatzpakete.

- **macOS**: Python 3 ist meist schon da. Öffne das Terminal (Programme → Dienstprogramme)
  und tippe `python3 --version`. Erscheint eine Version ab 3.8, bist du fertig. Sonst
  installiert macOS beim ersten Aufruf die Kommandozeilen-Werkzeuge – einfach bestätigen.
- **Windows**: Python von [python.org](https://www.python.org/downloads/) installieren.
  **Wichtig:** Im Installer den Haken **„Add python.exe to PATH“** setzen. Sonst findet
  die Startdatei Python nicht.
- **Linux**: `python3` ist installiert. Fertig.

### bskitool herunterladen

Auf der Projektseite auf **Code → Download ZIP** klicken, entpacken, den Ordner dorthin
legen, wo du deine Unterrichtsmaterialien hast (z. B. in deine Schul-Cloud). Wer `git`
benutzt: `git clone …`.

Der Ordner sieht so aus:

```
bskitool/
  bskitool starten.command   ← Mac: Doppelklick
  bskitool starten.bat       ← Windows: Doppelklick
  bskitool.py                ← Terminal: python3 bskitool.py
  kurse/                     ← hier liegen deine Kurse (einer je Unterordner)
    beispiel/kurs.md         ← ein vollständiges Beispiel
  ausgabe/                   ← hier landen gerenderte Seiten, Protokolle, Exporte
  daten/                     ← Zugangsdaten und Anmelde-Token (nur für dich)
  docs/                      ← diese Anleitung und die Referenzen
```

### Starten

- **Mac**: Doppelklick auf `bskitool starten.command`. Beim allerersten Mal blockt
  macOS eventuell („kann nicht geöffnet werden“): Rechtsklick → **Öffnen** → **Öffnen**.
  Danach reicht der Doppelklick.
- **Windows**: Doppelklick auf `bskitool starten.bat`.

Es öffnet sich ein Terminalfenster und der Browser mit `http://localhost:8765`. Das
Terminalfenster ist der Server – **lass es offen**, solange du arbeitest. Zum Beenden
schließt du es einfach.

Falls der Browser nicht von selbst aufgeht: die Adresse `http://localhost:8765` von Hand
eintippen.

---

## 3. Die Oberfläche kennenlernen (ohne Brightspace)

Bevor du dich mit Zugangsdaten beschäftigst, schau dir an, was bskitool baut. Dafür
brauchst du keine Anmeldung.

1. Reiter **Kurs bauen**. In der Liste steht *Beispielkurs – Excel Grundlagen*.
   Darunter siehst du die Struktur: Module, Seiten, Abgaben, Punkte.
2. Klick auf **Vorschau im Browser**. Es öffnet sich ein Inhaltsverzeichnis; jeder
   Seitentitel ist anklickbar. Öffne *Einstieg: Was ist eine Formel?* und klick dich
   durch den Selbstcheck.
3. Wechsle das Design auf **DV-Design** und mach wieder eine Vorschau – das ist die
   zweite Optik, falls eure Schule keine D2L-Vorlage nutzt.
4. Öffne nebenher die Datei `kurse/beispiel/kurs.md` in einem Texteditor und vergleiche:
   Was in der Datei steht, ist genau das, was du auf der Seite siehst.

Wenn du mit der Oberfläche spielen willst, ohne einen echten Kurs anzufassen: bskitool
im **Demo-Modus** starten. Im Terminal:

```
BSKITOOL_DEMO=1 python3 bskitool.py           (Mac/Linux)
set BSKITOOL_DEMO=1 && python bskitool.py     (Windows)
```

Dann tun alle Knöpfe so, als gäbe es ein Brightspace – Einspielen, Aufräumen, Rückgängig –
aber nichts verlässt deinen Rechner.

---

## 4. Deinen ersten Kurs schreiben

### Ordner anlegen

Lege in `kurse/` einen Ordner mit einem kurzen Namen ohne Leerzeichen an, z. B.
`kurse/mathe-9b/`. Darin eine Datei `kurs.md`. Bilder kommen in `kurse/mathe-9b/bilder/`,
Dateien zum Herunterladen in `kurse/mathe-9b/material/` (die Namen sind frei, sie
müssen nur zu dem passen, was du in der kurs.md schreibst).

Ein Texteditor, der Markdown kann, macht die Arbeit angenehmer (VS Code, Typora,
iA Writer, Obsidian …), aber jeder Editor geht – auch TextEdit, wenn du auf
„reinen Text“ umstellst.

### Der Kopf

Die ersten Zeilen beschreiben den Kurs:

```
titel: Mathematik 9b – Lineare Funktionen
design: d2l
fuss: Mathematik · Klasse 9b · Beispielschule
```

`design: d2l` ist die Optik der D2L-Vorlage (Bootstrap, Schrift Lato, Banner) – wähle
das, wenn eure Schule die HTML Template Library nutzt. `design: dv` ist ein
eigenständiges, ruhiges Design, das ohne Vorlage auskommt. Beides kannst du in der
Oberfläche jederzeit umschalten.

### Module und Seiten

```
# Woche 1 – Was ist eine lineare Funktion?
beschreibung: Steigung, y-Achsenabschnitt, erste Graphen

## Seite: Einstieg
kurz: Input · 10 Minuten

Hier steht der Text der Seite. Ganz normales Markdown:
**fett**, *kursiv*, Listen, Tabellen, Bilder.
```

- Eine Zeile mit **einer** Raute (`#`) ist ein **Modul**.
- `## Seite: …` ist eine **Seite** in diesem Modul. Alles bis zur nächsten `##`-Zeile mit
  Schlüsselwort gehört zu dieser Seite.
- Überschriften **innerhalb** der Seite schreibst du auch mit `##` oder `###`, aber ohne
  Schlüsselwort: `## Die Steigung` ist eine Überschrift, `## Seite: Die Steigung` eine
  neue Seite.

### Kästen

Kästen sind das, was eine Kursseite von einer Textwüste unterscheidet:

```
::: ziel
Am Ende der Stunde kannst du aus zwei Punkten die Steigung berechnen.
:::

::: input Input 1 · Die Steigung
Text, Listen, Tabellen – alles erlaubt.
:::

::: auftrag Arbeitsauftrag 1 · 15 Minuten
- [ ] Zeichne den Graphen von y = 2x + 1
- [ ] Lies die Steigung ab
:::

::: lösung
Die Steigung ist 2.
:::

::: merke
Steigung = Höhenunterschied geteilt durch Längenunterschied.
:::

::: geschafft
- der Graph ist gezeichnet
- die Steigung stimmt
:::
```

Die Arten: `ziel`, `merke`, `input`, `auftrag`, `geschafft`, `achtung`, `extra`, `info`,
`beispiel`. Drei Arten werden **eingeklappt** und lassen sich aufklappen: `lösung`,
`hinweis`, `tipp`. Hinter der Art kannst du einen Titel schreiben; ohne Titel bekommt der
Kasten seine Standardbeschriftung („Merke“, „Darum geht es“, …).

Häkchenlisten (`- [ ]`) sind echte Kästchen, die Schüler:innen anklicken können.

### Selbstchecks

Ein Selbstcheck ist ein kleines Quiz **in der Seite**. Es läuft im Browser, gibt sofort
Rückmeldung und zeigt den Punktestand – bewertet aber nichts in Brightspace. Genau
richtig, um Verständnis zu prüfen, ohne dass es „zählt“.

```
### Quiz: Selbstcheck – Steigung
Welche Steigung hat y = 3x – 2? (2 P)
- [x] 3
- [ ] –2
- [ ] 1
> Richtig: Die Zahl vor dem x ist die Steigung.
> Falsch: Schau dir den Merke-Kasten noch mal an.

Eine Gerade mit Steigung 0 ist waagerecht.
- [x] Wahr
- [ ] Falsch

Wie heißt die Zahl, bei der die Gerade die y-Achse schneidet?
= y-Achsenabschnitt
= Achsenabschnitt
```

- Eine Frage = Fragetext, dann Antworten, dann Leerzeile.
- Eine `[x]` → Einfachauswahl. Mehrere `[x]` → Mehrfachauswahl.
- Genau „Wahr“ und „Falsch“ → Wahr/Falsch-Frage.
- `= Antwort` → Kurzantwort (Groß/Klein egal; mehrere `=`-Zeilen = mehrere richtige
  Schreibweisen).
- `(2 P)` hinter der Frage = Punkte (sonst 1).
- `> Richtig:` / `> Falsch:` = Rückmeldung (optional).

Der Selbstcheck endet bei der nächsten Überschrift, einem `:::`-Kasten oder `---`.
Ein Kasten **nach** dem Quiz gehört also wieder zur Seite.

### Dateien, Links, Abgaben, Noten

```
## Datei: material/Arbeitsblatt.pdf
titel: Arbeitsblatt Steigung

## Link: GeoGebra
url: https://www.geogebra.org/calculator

## Abgabe: Abgabe 1 – Graphen
punkte: 10
faellig: 15.10.2026

Lade dein Foto oder deine PDF hoch. Bewertet werden Achsenbeschriftung (2 P),
drei richtige Graphen (6 P), Sauberkeit (2 P).

## Note: Mitarbeit Woche 1–3
punkte: 10
```

- **Datei** lädt die Datei in den Kurs hoch (Excel, Word, PDF, ZIP, Bilder …).
- **Abgabe** legt einen Abgabeordner an. Mit `punkte:` bekommt er ein Notenelement,
  die Punktzahl und wird im Modul verknüpft. Der Text darunter ist die Anweisung für
  die Schüler:innen – schlicht halten, Brightspace zeigt ihn in seinem eigenen Rahmen.
- **Note** legt nur ein Notenelement an (für mündliche Noten, Mitarbeit, …).

Die vollständige Referenz mit allen Schlüsseln steht in [FORMAT.md](FORMAT.md).

### Prüfen

Speichern, in der Oberfläche **Neu einlesen**, deinen Kurs wählen. Unter der Liste
erscheinen Warnungen, wenn etwas fehlt (z. B. ein Link ohne `url:`, eine Frage ohne
richtige Antwort). Dann **Vorschau im Browser** – so oft du willst, das kostet nichts.

---

## 5. Zugang zu Brightspace einrichten

Das machst du **einmal**. Danach meldet sich bskitool über Monate automatisch an.

bskitool spricht über die offizielle Brightspace-Schnittstelle (Valence API) mit eurem
System. Dafür braucht es eine registrierte „OAuth-2.0-Anwendung“. Die legst du entweder
selbst an (wenn dein Konto Zugriff auf *Manage Extensibility* hat) oder eure Brightspace-
Administration macht das für dich. Die genaue Klickfolge steht in
[OAUTH-EINRICHTEN.md](OAUTH-EINRICHTEN.md) – dort ist auch ein Textbaustein für die Mail
an die Admin.

Am Ende hast du drei Dinge: die Adresse eures Brightspace (z. B.
`meineschule.brightspace.com`), eine **Client-ID** und ein **Client-Secret**.

In bskitool: Reiter **Einstellungen & Anmeldung** → Adresse, Client-ID, Client-Secret
eintragen → **Speichern** → **Bei Brightspace anmelden**. Es öffnet sich ein
Browserfenster mit der normalen Brightspace-Anmeldung. Danach fragt Brightspace, ob die
Anwendung in deinem Namen arbeiten darf – bestätigen.

Beim Zurückleiten warnt der Browser vor dem Zertifikat von `localhost` („Diese Verbindung
ist nicht privat“). Das ist normal: bskitool hat sich gerade ein eigenes Zertifikat für
deinen Rechner erzeugt, weil Brightspace nur an eine https-Adresse zurückleitet. Klick auf
**Erweitert** → **Weiter zu localhost**. Dann steht „Geschafft“ auf der Seite, und in
bskitool oben rechts grün **angemeldet** mit deinem Namen.

Das Token liegt in `daten/token.json`, nur für dich lesbar. Wenn du den Ordner an jemanden
weitergibst, lösche vorher den Inhalt von `daten/` – oder gib gleich das Repository ohne
diesen Ordner weiter.

---

## 6. Einspielen: Trockenlauf, echt, rückgängig

1. Reiter **Kurs bauen**, deinen Kurs wählen.
2. **Kurse laden** → in der Liste *Ziel-Kurs* deinen Brightspace-Kurs wählen. Die Liste
   zeigt alle Kurse, in denen du eingeschrieben bist, mit Rolle.
3. **Trockenlauf**. Das Protokoll zeigt jede Aktion mit `[trocken]`. Nichts wird geändert.
   Lies es einmal durch: Stimmen die Reihenfolge, die Punkte, die Titel?
4. **Jetzt einspielen** → Sicherheitsabfrage bestätigen. Das Protokoll läuft live durch;
   jede Zeile bekommt `[ok]` mit der Brightspace-ID oder `[fehler]` mit dem Grund.
   Fehler brechen den Lauf nicht ab – alles andere wird trotzdem angelegt.
5. Am Ende: *X Objekte angelegt, Y Fehler* und ein Link **Was noch von Hand zu tun ist**.

**Wichtig:** Einspielen legt immer **neu** an. Wenn du denselben Kurs zweimal einspielst,
hast du alles doppelt. Für Änderungen: erst Rückgängig, dann neu einspielen (siehe 8).

### Rückgängig

**Letztes Einspielen rückgängig** zeigt dir die Liste dessen, was bskitool beim letzten
Lauf angelegt hat, und löscht genau das nach Bestätigung (du tippst `LOESCHEN`). Nichts
anderes im Kurs wird angefasst. Das Protokoll dafür liegt in
`ausgabe/<kurs>/protokoll.json`.

Zwei Dinge musst du wissen:

- **Inhaltsmodule und -themen** sind nach dem Löschen weg. Brightspace hat dafür keinen
  Papierkorb, den du selbst bedienen kannst (nur der D2L-Support kann sie zurückholen).
- **Abgabeordner, Notenelemente, Quizze** landen für rund 30 Tage im Papierkorb von
  Brightspace und lassen sich dort wiederherstellen.

Solange du auf frisch eingespielte, noch verborgene Inhalte klickst, ist das kein
Problem. Vorsicht erst, wenn Schüler:innen schon abgegeben haben.

---

## 7. Nach dem Einspielen: freigeben

Alles ist verborgen angelegt – Module, Seiten, Abgaben. In Brightspace:

1. **Inhalt** öffnen. Die neuen Module stehen unten mit dem Symbol „verborgen“.
2. Modul freigeben (Sichtbarkeit umschalten). Die Themen darin sind ebenfalls einzeln
   verborgen – gib die frei, die die Klasse jetzt sehen soll. So kannst du Lektion für
   Lektion freischalten.
3. Abgabeordner: unter **Aufgaben** ebenfalls sichtbar schalten, wenn die Klasse sie
   sehen soll. Fälligkeitsdatum ist gesetzt, Notenelement verknüpft – kontrollieren
   schadet nicht.
4. Reihenfolge: Brightspace hängt neue Module unten an. Umsortieren geht per Drag & Drop
   in der Inhaltsansicht.

Die Seite **Was noch von Hand zu tun ist** (`ausgabe/<kurs>/noch-zu-tun.html`) listet
genau das für deinen Kurs auf – plus alles, was im Protokoll ein `[fehler]` oder
`[hinweis]` bekommen hat.

---

## 8. Einen Kurs weiterentwickeln

Der Normalfall im Schuljahr: Du merkst nach der zweiten Stunde, dass Lektion 3 anders
werden muss. Zwei Wege:

**Weg A – kleiner Eingriff in Brightspace.** Für einen Tippfehler oder einen Satz mehr
ist der HTML-Editor in Brightspace schneller. Die Seiten, die bskitool anlegt, sind
normale HTML-Seiten; du kannst sie dort bearbeiten. Nachteil: Deine `kurs.md` weiß
davon nichts.

**Weg B – kurs.md ändern und neu einspielen.** Sauberer, wenn sich mehr ändert:

1. `kurs.md` ändern, Vorschau prüfen.
2. In bskitool **Letztes Einspielen rückgängig** – oder im Reiter Aufräumen nur das
   betroffene Modul löschen.
3. Neu einspielen. Freigaben musst du danach wieder setzen.

Tipp für laufende Kurse: Teile den Kurs in **mehrere kurs.md** – eine je Modul oder je
Quartal (`kurse/mathe-9b-q1/`, `kurse/mathe-9b-q2/`). Dann tauschst du nur das aus, was
sich ändert, und die Abgaben der Vergangenheit bleiben unangetastet.

---

## 9. Aufräumen: Module und Co. löschen

Reiter **Aufräumen** → Kurs wählen → **Inhalt anzeigen**. Du siehst vier Tabellen:
Inhalt (Module mit ihren Themen, eingerückt), Abgabeordner, Notenelemente, Quizze –
jeweils mit ID und Häkchen.

Häkchen setzen → **Ausgewählte löschen** → Liste prüfen → `LOESCHEN` tippen. Das
Protokoll zeigt jede Löschung. Wird ein Modul gelöscht, verschwinden seine Themen mit.

Das ist der schnellste Weg, um Reste eines alten Imports loszuwerden oder einen Kurs
für das nächste Schuljahr leer zu räumen. Es ist auch der gefährlichste Knopf im
Programm – deshalb die Tipp-Bestätigung.

---

## 10. Mit einem KI-Assistenten arbeiten

Das Format ist so gebaut, dass ein Sprachmodell es fehlerfrei schreiben kann. In
[KI-ASSISTENT.md](KI-ASSISTENT.md) steht ein fertiger Text, den du ChatGPT, Claude,
Copilot oder einem lokalen Modell als Anweisung gibst. Danach sagst du nur noch:

> „Schreib mir eine Doppelstunde zu linearen Funktionen für Klasse 9, Hauptschulniveau,
> mit zwei Inputs, drei Arbeitsaufträgen mit Lösung und einem Selbstcheck.“

Heraus kommt eine `kurs.md`, die du in deinen Kursordner legst, in der Vorschau
kontrollierst, nach deinem Geschmack umschreibst und einspielst.

Das eigentliche Werkzeug bleibt dabei dein Urteil: Ob der Input für deine Klasse passt,
weißt du. Der Assistent spart dir das Tippen und das Formatieren, nicht das Denken.

---

## 11. Gute Kurse schreiben – was sich bewährt hat

Aus dem Einsatz in berufsbildenden Klassen mit sehr unterschiedlichem Niveau:

- **Eine Seite pro Stunde.** Oben `::: ziel`, dann abwechselnd Input und Auftrag, unten
  `::: geschafft` und `::: extra` für die Schnellen. Die Schüler:innen wissen dann immer,
  wo sie sind.
- **Inputs kurz.** Zehn Minuten Input, dann arbeiten. Wer Inputs auf 25 Minuten
  streckt, verliert die Hälfte der Klasse.
- **Kontrollwerte statt Lösung.** Bei Excel-Aufgaben: das Ergebnis nennen („Kontrollwert:
  1.284“), die Formel eingeklappt in `::: lösung`. So sehen Schüler:innen sofort, *ob* sie
  richtig liegen, aber nicht *wie* – und müssen nicht warten, bis du bei ihnen bist.
- **Stumpfe Wiederholung ist erlaubt.** Fünf Aufgaben, die sich fast gleichen, sind für
  schwache Lerngruppen besser als eine clevere.
- **Häkchenlisten in Aufträgen.** Die Kästchen sind klickbar und geben ein Gefühl von
  Fortschritt.
- **Selbstchecks am Ende jeder Seite**, drei bis fünf Fragen, mit Rückmeldung bei
  falscher Antwort, die auf den richtigen Kasten zeigt.
- **Abgaben mit sichtbarem Bewertungsraster** in der Anweisung. Was 2 Punkte bringt, wird
  gemacht.
- **Lehrerskripte in ein eigenes Modul** `ZZ – Lehrkraft (VERBERGEN)`. So liegen Input-
  Skript, Musterlösung und Erwartungshorizont im Kurs, aber nie sichtbar.
- **Zwei Ebenen, nicht drei.** Modul → Themen. Untermodule kommen in Brightspace nicht
  sauber an.

---

## 12. Wenn etwas nicht klappt

Die häufigsten Fälle mit Lösung stehen in [FEHLERSUCHE.md](FEHLERSUCHE.md). Die drei
wichtigsten:

- **„Insufficient scope“ (403)** beim Einspielen: Die OAuth-Anwendung hat nicht alle
  Berechtigungen. Scopes in Brightspace **und** in den Einstellungen abgleichen,
  abmelden, neu anmelden.
- **„JSON Binding Error“ (400)**: Ein Feld passt nicht zu eurer API-Version. Die
  Protokollzeile in ein Issue kopieren – das lässt sich meist mit einer Zeile beheben.
- **Anmeldung hängt**: Steht im Browser eine Adresse mit `…/callback?code=…`? Dann die
  komplette Adresse in das Feld „Notausgang“ im Reiter Einstellungen einfügen.

Und wenn die API gar nicht mitspielt (Proxy, Netzwerk, Berechtigungen): **Als .imscc
exportieren** → Brightspace: Kursverwaltung → Import/Export/Kopieren → Komponenten
importieren. Seiten und Abgabeordner kommen so an; Dateien musst du dann per
Drag & Drop nachlegen, das steht in der Noch-zu-tun-Liste.
