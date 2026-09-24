# Das Format der kurs.md

Eine Datei = ein Kurs. Markdown, mit wenigen festen Regeln.

## Kopf (vor der ersten Überschrift)

```
titel: Datenverarbeitung Klasse 11
kurs: 12345          orgUnitId in Brightspace (optional, sonst beim Einspielen wählen)
design: d2l          d2l = D2L HTML Template Library (Standard) | dv = eigenständiges Design
fuss: Text unten auf jeder Seite (optional)
```

## Struktur

| Zeile | Bedeutung |
|---|---|
| `# Titel` oder `# Modul: Titel` | ein Modul (Brightspace-Inhaltsmodul) |
| `## Seite: Titel` | eine HTML-Seite; darunter Markdown |
| `## Datei: pfad/datei.xlsx` | Datei als Thema hochladen (`titel:` optional) |
| `## Link: Titel` | Verweis, braucht `url:` |
| `## Abgabe: Titel` | Abgabeordner; `punkte:` legt zusätzlich ein Notenelement an; `faellig:`; Text darunter = Anweisung |
| `## Note: Titel` | nur ein Notenelement (`punkte:`) |
| `## Quiz: Titel` | eigenständiges Quiz (Selbstcheck-Seite; mit `benotet: ja` zusätzlich Notenelement + Quiz-Hülle + Fragen-CSV) |
| `### Quiz: Titel` | Selbstcheck **innerhalb** einer Seite, an genau dieser Stelle |

Alle anderen Überschriften (`##`, `###` ohne Schlüsselwort) sind normaler Text.
Nur zwei Ebenen: Modul → Themen. Untermodule kommen in Brightspace nicht sauber an.

**Eigenschaften** stehen direkt unter der Überschrift, eine pro Zeile, `schlüssel: wert`:
`beschreibung`, `kurz` (Untertitel der Seite), `punkte`, `faellig` (15.10.2026 oder 2026-10-15),
`benotet`, `versuche`, `sichtbar: ja` (sonst verborgen), `url`, `datei`, `titel`.

`## Seite:` mit `datei: seiten/fertig.html` übernimmt eine fertige HTML-Seite unverändert.

## Text in Seiten

Markdown wie gewohnt: `**fett**`, `*kursiv*`, `` `Code` ``, Listen, `1.` Listen,
`- [ ]` Häkchenlisten, Tabellen mit `|`, `![Alt](bilder/x.png)` (wird eingebettet),
`[Text](https://…)`, `[[F4]]` für eine Taste, ` ``` ` Codeblöcke, `>` Zitate, `---`.

### Kästen

```
::: merke Optionaler Titel
Text, Listen, Tabellen …
:::
```

Arten: `ziel` · `merke` · `input` · `auftrag` (oder `aufgabe`) · `geschafft` · `achtung` ·
`extra` · `info` · `beispiel` · `lehrkraft`. Ohne Titel bekommt der Kasten seine
Standardbeschriftung. Eingeklappt (zum Aufklappen): `lösung`, `hinweis`, `tipp`.

### Fragen (in `### Quiz:` und `## Quiz:`)

```
Fragetext (2 P)                 Punkte optional, sonst 1
- [x] richtige Antwort          eine [x] = Single Choice
- [ ] falsche Antwort           mehrere [x] = Mehrfachauswahl
> Richtig: Rückmeldung          optional
> Falsch: Rückmeldung           optional

Aussage.                        genau "Wahr"/"Falsch" = Wahr/Falsch-Frage
- [x] Wahr
- [ ] Falsch

Frage mit Kurzantwort?
= MITTELWERT                    jede = Zeile ist eine akzeptierte Antwort
= Mittelwert
```

Fragen trennt eine Leerzeile. Text vor der ersten Frage ist die Einleitung.
Ein Quizblock endet bei der nächsten Überschrift, einem `:::`-Kasten oder `---`.

## Was Brightspace damit macht

- Seite → Datei-Thema (HTML) im Modul, Selbstchecks laufen als JavaScript in der Seite
  (keine Bewertung in Brightspace).
- Abgabe → Abgabeordner (+ Notenelement, wenn `punkte:`), Verknüpfung im Modul.
- Quiz benotet → Notenelement, Quiz-Hülle (wenn die Instanz es erlaubt), Fragen als
  CSV in `ausgabe/<kurs>/fragen/` für die Fragensammlung.
- Alles verborgen, außer `sichtbar: ja`.
