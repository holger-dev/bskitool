# bskitool – Markdown → Brightspace

**bskitool** steht für *BrightSpace-KI-Tool*: Schreib deinen Brightspace-Kurs als eine
Markdown-Datei – selbst oder mit einem KI-Assistenten. bskitool baut daraus Seiten,
Selbstchecks, Abgaben und Notenelemente und spielt alles per Klick in deinen Kurs.

*bskitool turns one Markdown file into a complete D2L Brightspace course (content modules,
HTML pages with built-in self-checks, assignment folders with grade items, quizzes) and
pushes it through the Valence API. Pure Python standard library, local web UI, German-first.*

```
titel: Datenverarbeitung Klasse 11
design: d2l

# Lektion 1 – Erste Formeln          ← wird ein Inhaltsmodul
## Seite: Einstieg                   ← wird eine HTML-Seite
::: ziel
Heute lernst du, was eine Formel ist.
:::
### Quiz: Selbstcheck                ← läuft als Quiz direkt in der Seite
Womit beginnt jede Formel?
- [x] mit =
- [ ] mit +

## Abgabe: Verkaufstabelle           ← Abgabeordner + Notenelement
punkte: 10
faellig: 15.10.2026
```

Eine Datei wie diese – und in Brightspace steht ein Modul mit Seite, Selbstcheck,
Abgabeordner und Notenelement. Verborgen, bis du es freigibst.

## Warum

Kurse in Brightspace zusammenzuklicken dauert. Der Inhalt existiert meist längst als
Text – im Kopf, in Notizen oder als Ergebnis eines Gesprächs mit einem KI-Assistenten.
bskitool macht aus diesem Text den fertigen Kurs, ohne dass du in Brightspace eine
einzige Seite von Hand anlegst. Und weil das Format schlichtes Markdown ist, kann ein
KI-Assistent es direkt schreiben: `docs/KI-ASSISTENT.md` enthält die Anleitung dafür.

## Was bskitool kann

| In der kurs.md | In Brightspace |
|---|---|
| `# Titel` | Inhaltsmodul mit Beschreibung |
| `## Seite: Titel` + Markdown | HTML-Seite im Design der D2L-Vorlage (oder eigenes Design) |
| `::: merke` … `:::` | Kästen: Ziel, Merke, Input, Auftrag, Achtung, Geschafft, Extra, eingeklappte Lösung |
| `### Quiz:` in einer Seite | Selbstcheck mit Einfach-/Mehrfachauswahl, Wahr/Falsch, Kurzantwort, Rückmeldung, Punktestand |
| `## Datei: pfad.xlsx` | Datei-Thema (Excel, Word, PDF, ZIP …) |
| `## Link:` + `url:` | Link-Thema |
| `## Abgabe:` + `punkte:` + `faellig:` | Abgabeordner mit Bewertung, Notenelement, Verknüpfung im Modul |
| `## Note:` + `punkte:` | Notenelement |
| `## Quiz:` + `benotet: ja` | Notenelement, Quiz-Hülle, Fragen als D2L-CSV für die Fragensammlung |

Dazu: Vorschau im Browser, Trockenlauf, Live-Protokoll, **Rückgängig** (löscht genau das,
was gerade angelegt wurde), ein Aufräum-Reiter zum Löschen von Modulen, Themen, Abgaben,
Noten und Quizzen mit Häkchen, ein .imscc-Export als Rückfallweg und ein Demo-Modus
ohne Brightspace.

## Schnellstart

Voraussetzung: Python 3.8 oder neuer (macOS bringt es mit; Windows: python.org, Haken
„Add to PATH“). Keine weiteren Pakete.

1. Repository herunterladen oder klonen.
2. **Mac:** Doppelklick auf `bskitool starten.command` (beim ersten Mal Rechtsklick → Öffnen).
   **Windows:** Doppelklick auf `bskitool starten.bat`. **Terminal:** `python3 bskitool.py`
3. Der Browser öffnet `http://localhost:8765`. Reiter **Kurs bauen** → Beispielkurs →
   **Vorschau im Browser**. Das geht ohne jede Anmeldung.
4. Für den echten Einsatz einmalig eine OAuth-Anwendung in Brightspace registrieren
   (`docs/OAUTH-EINRICHTEN.md`), Zugangsdaten im Reiter **Einstellungen** eintragen,
   anmelden – fertig.

Ohne Brightspace ausprobieren: `BSKITOOL_DEMO=1 python3 bskitool.py` (Windows:
`set BSKITOOL_DEMO=1` davor).

## Dokumentation

| Datei | Für wen |
|---|---|
| [docs/ANLEITUNG.md](docs/ANLEITUNG.md) | **Lehrkräfte** – von der leeren Datei bis zum freigegebenen Kurs, Schritt für Schritt |
| [docs/FORMAT.md](docs/FORMAT.md) | Die komplette Referenz der kurs.md |
| [docs/OAUTH-EINRICHTEN.md](docs/OAUTH-EINRICHTEN.md) | Zugang zur Brightspace-API einrichten (einmalig, ggf. mit eurer Admin) |
| [docs/KI-ASSISTENT.md](docs/KI-ASSISTENT.md) | Anleitung, mit der ChatGPT, Claude & Co. fertige Kurse im bskitool-Format schreiben |
| [docs/FEHLERSUCHE.md](docs/FEHLERSUCHE.md) | Wenn etwas hakt: Anmeldung, 400/403, Port, Zertifikat, Proxy |
| [docs/ENTWICKLUNG.md](docs/ENTWICKLUNG.md) | Aufbau des Codes, Tests, Beiträge |

## Was die Brightspace-API nicht hergibt

- **Quizfragen** lassen sich nicht per API anlegen (D2L bietet dafür keinen Endpunkt).
  Selbstchecks in Seiten funktionieren trotzdem sofort – als JavaScript in der Seite,
  ohne Bewertung in Brightspace. Für benotete Quizze legt bskitool Notenelement und Hülle
  an und schreibt die Fragen als CSV, die du in die Fragensammlung importierst.
- **Untermodule** kommen beim Import erfahrungsgemäß nicht sauber an – bskitool arbeitet
  deshalb mit zwei Ebenen: Modul → Themen.
- Alles wird **verborgen** angelegt. Freigeben ist bewusst dein Klick.

## Sicherheit

Zugangsdaten und Token liegen nur lokal in `daten/` (per `.gitignore` ausgeschlossen, nur
für dich lesbar). Die Web-Oberfläche antwortet ausschließlich auf `localhost`. bskitool
spricht mit genau zwei Servern: deinem Brightspace und `auth.brightspace.com` für die
Anmeldung. Kein Telemetrie, kein Update-Check, keine Fremdbibliothek.

## Lizenz

MIT – siehe [LICENSE](LICENSE). Brightspace und D2L sind Marken von D2L Corporation;
bskitool ist ein unabhängiges Werkzeug ohne Verbindung zu D2L.
