# Entwicklung

## Grundsätze

- **Nur Python-Standardbibliothek.** Lehrkräfte sollen das Werkzeug per Doppelklick
  starten können, ohne `pip`. Wer eine Fremdbibliothek braucht, braucht ein sehr gutes
  Argument.
- **Deutsch im Code und in der Oberfläche.** Zielgruppe sind deutschsprachige Schulen;
  Bezeichner wie `modul_anlegen` sind Absicht. API-Feldnamen bleiben natürlich englisch.
- **Nichts passiert ohne Bestätigung.** Anlegen fragt, Löschen verlangt `LOESCHEN`,
  alles wird verborgen angelegt.
- **Fehler brechen nicht ab.** Ein 400 bei einer Seite darf nicht den Rest des Kurses
  verhindern; jede Zeile im Protokoll trägt ihren Status.

## Aufbau

```
bskitool.py         Einstieg: Kommandozeile und Start der Oberfläche
kb/kursdatei.py     kurs.md -> Kursmodell (Kurs, Modul, Item, Quiz, Frage); pruefen()
kb/markdown.py      Markdown-Teilmenge -> HTML, inkl. ::: Kästen und Häkchenlisten
kb/render.py        Kursmodell -> HTML-Seiten (Designs d2l/dv), Selbstcheck-JS,
                    Bilder als data:-URI, index.html für die Vorschau
kb/api.py           Brightspace Valence API: Einstellungen, OAuth (Auth-Code, optional
                    PKCE, lokaler TLS-Empfänger), Lesen, Anlegen, Löschen
kb/push.py          Einspieler: Reihenfolge, Protokoll, protokoll.json, rueckgaengig()
kb/fallback.py      .imscc-Export, D2L-Fragen-CSV, Noch-zu-tun-Liste
kb/imscc.py         Common-Cartridge-1.3-Paket (webcontent, assignment, QTI 1.2)
kb/server.py        http.server mit JSON-Routen unter /api/ und Auslieferung von ui/
kb/demo.py          DemoVerbindung mit derselben Schnittstelle wie Verbindung
ui/index.html       Oberfläche (eine Datei, Vanilla JS, kein Build)
tests/test_alles.py unittest, läuft ohne Brightspace (DemoVerbindung)
```

Datenfluss beim Einspielen:

```
kurs.md ──kursdatei.lesen──▶ Kurs ──render.kurs_rendern──▶ ausgabe/<kurs>/seiten/*.html + Plan
                                                             │
                                          push.Einspieler ◀──┘
                                             │  1. Notenelemente (Note, Abgabe mit punkte, Quiz benotet)
                                             │  2. je Modul: Modul, dann Themen in Reihenfolge
                                             ▼
                                   Verbindung (api.py) ──▶ Brightspace
                                             │
                                             ▼
                                   ausgabe/<kurs>/protokoll.json  (für rueckgaengig)
```

## Tests

```
python3 -m unittest tests.test_alles
```

Deckt Parser, Markdown, beide Designs, Einspielen/Rückgängig gegen die Demo-Verbindung
und den .imscc-Export ab. Läuft in unter zwei Sekunden. Bitte vor jedem Pull Request.

Oberfläche von Hand: `BSKITOOL_DEMO=1 python3 bskitool.py` und alle Knöpfe einmal drücken.

## API-Versionen

`v_lp` (1.43) und `v_le` (1.80) stehen in den Einstellungen. Die Anfragekörper sind
gegen die D2L-Dokumentation dieser Versionen gebaut
(https://docs.valence.desire2learn.com/). Felder, die erst in späteren Versionen
existieren (z. B. `Weight` bei Notenelementen ab LE 1.89), gehören **nicht** in den
Körper – D2L antwortet sonst mit „JSON Binding Error“. Quiz-Anlage probiert mehrere
Versionen durch, weil sich die Struktur dort öfter ändert.

Bekannte Eigenheiten:

- Datei-Themen brauchen `Url` unter dem Kursinhalt-Pfad, der aus `GET /lp/courses/{ou}`
  (`Path`) kommt, z. B. `/content/enforced/12345-CODE/`. Mit der bloßen orgUnitId
  antwortet D2L `400 {"Errors": []}`.
- Notennamen dürfen `/ " * < > + = | , %` nicht enthalten → `api.notenname()`.
- Es gibt keinen Endpunkt zum Anlegen von Quizfragen. Deshalb Selbstchecks als JS und
  CSV-Export für die Fragensammlung.

## Beiträge

Issues mit der kompletten Protokollzeile (`[fehler] …`) und der API-Version aus
„Erreichbarkeit prüfen“ sind am hilfreichsten. Pull Requests: klein, ein Thema, Tests
grün, keine neuen Abhängigkeiten.

Ideen, die noch offen sind:

- Aktualisieren statt neu anlegen (Themen anhand des Titels wiederfinden und ersetzen)
- Bilder als eigene Datei-Themen statt data:-URI, wenn sie groß sind
- Weitere Frage-Typen in der CSV (Zuordnung, Reihenfolge)
- Englische Oberfläche als Sprachdatei
