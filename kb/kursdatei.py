# -*- coding: utf-8 -*-
"""Liest eine kurs.md und baut daraus ein Kursmodell.

Aufbau der Datei
----------------
Kopf (vor dem ersten #):        kurs: 12345 / titel: ... / design: d2l|dv / ...

# Modultitel                    ein Modul (oder: # Modul: Titel)
beschreibung: ...               optional, direkt unter der Ueberschrift

## Seite: Titel                 HTML-Seite, Markdown-Inhalt folgt
## Datei: pfad/zur/datei.xlsx   Datei als Thema (titel: ... optional)
## Link: Titel                  Verweis (url: https://...)
## Abgabe: Titel                Abgabeordner (punkte:, faellig:, Anweisung als Inhalt)
## Note: Titel                  Notenelement (punkte:)
## Quiz: Titel                  eigenstaendiges Quiz (Seite mit Selbstcheck + CSV/Huelle)

### Quiz: Titel                 Quiz innerhalb einer Seite (endet bei der naechsten
                                Ueberschrift, einem ::: Kasten oder ---)

Alle anderen Ueberschriften (##, ###, ...) sind normaler Inhalt.

Fragen in einem Quiz
--------------------
Fragetext (2 P)                 Punkte optional in Klammern
- [ ] Antwort                   eine [x] = Single Choice, mehrere = Multiselect
- [x] Antwort                   genau "Wahr"/"Falsch" = Wahr/Falsch-Frage
= Antwort                       Kurzantwort, mehrere = Zeilen erlaubt
> Richtig: Rueckmeldung         optional
> Falsch: Rueckmeldung          optional
"""

import re
from dataclasses import dataclass, field

STRUKTUR = re.compile(r"^(#{1,3})\s+(?:(Modul|Seite|Datei|Link|Abgabe|Note|Quiz)\s*:\s*)?(.+?)\s*$")
EIGENSCHAFT = re.compile(r"^([a-zäöüA-ZÄÖÜ_]+)\s*:\s*(.*)$")

BEKANNTE_SCHLUESSEL = {
    "kurs", "titel", "design", "beschreibung", "kurz", "punkte", "faellig",
    "fällig", "benotet", "versuche", "sichtbar", "url", "datei", "start",
    "ende", "mischen", "anzeigen", "kategorie", "banner", "fuss", "fuß",
    "einheit", "ordner",
}

OPTION = re.compile(r"^-\s+\[( |x|X)\]\s+(.*)$")
KURZ = re.compile(r"^=\s+(.*)$")
FEEDBACK = re.compile(r"^>\s*(Richtig|Falsch)\s*:\s*(.*)$", re.I)
PUNKTE = re.compile(r"\((\d+(?:[.,]\d+)?)\s*P(?:unkte?)?\.?\)\s*$")


@dataclass
class Frage:
    text: str
    typ: str = "mc"                 # mc | ms | tf | sa
    optionen: list = field(default_factory=list)   # [(text, richtig)]
    antworten: list = field(default_factory=list)  # Kurzantwort
    punkte: float = 1.0
    fb_ok: str = ""
    fb_no: str = ""


@dataclass
class Quiz:
    titel: str
    ident: str
    fragen: list = field(default_factory=list)
    props: dict = field(default_factory=dict)
    einleitung: str = ""

    @property
    def benotet(self):
        return str(self.props.get("benotet", "nein")).lower() in ("ja", "yes", "1", "true")

    @property
    def punkte(self):
        return sum(f.punkte for f in self.fragen)


@dataclass
class Item:
    art: str                       # seite | datei | link | abgabe | note | quiz
    titel: str
    ident: str
    props: dict = field(default_factory=dict)
    body: str = ""
    quizze: list = field(default_factory=list)    # eingebettete Quizze (nur seite)
    quiz: Quiz = None                             # bei art == quiz


@dataclass
class Modul:
    titel: str
    ident: str
    props: dict = field(default_factory=dict)
    items: list = field(default_factory=list)

    @property
    def beschreibung(self):
        return self.props.get("beschreibung", "")


@dataclass
class Kurs:
    titel: str = ""
    props: dict = field(default_factory=dict)
    module: list = field(default_factory=list)
    quelle: str = ""

    @property
    def kurs_id(self):
        v = str(self.props.get("kurs", "")).strip()
        return int(v) if v.isdigit() else None

    @property
    def design(self):
        d = self.props.get("design", "d2l").lower()
        return "d2l" if d in ("bs28", "d2l", "vorlage", "template") else d

    def alle_items(self):
        for m in self.module:
            for it in m.items:
                yield m, it


# --------------------------------------------------------------------------

def _slug(text, n=40):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()
               .replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
               .replace("ß", "ss")).strip("-")
    return s[:n] or "x"


def _eigenschaften(lines, i):
    """Liest zusammenhaengende schluessel: wert Zeilen ab i. Gibt (props, neues i)."""
    props = {}
    while i < len(lines):
        m = EIGENSCHAFT.match(lines[i].strip())
        if not m or m.group(1).lower() not in BEKANNTE_SCHLUESSEL:
            break
        k = m.group(1).lower().replace("ä", "ae").replace("ü", "ue").replace("ö", "oe").replace("ß", "ss")
        props[k] = m.group(2).strip()
        i += 1
    return props, i


def _fragen_parsen(block):
    """Quizblock (Text nach den Eigenschaften) -> (einleitung, [Frage])"""
    fragen = []
    einleitung = []
    akt = None
    text_buf = []

    def abschluss():
        nonlocal akt
        if akt is None:
            return
        # Typ bestimmen
        if akt.antworten and not akt.optionen:
            akt.typ = "sa"
        else:
            richtig = sum(1 for _, r in akt.optionen if r)
            texte = [t.strip().lower() for t, _ in akt.optionen]
            if len(akt.optionen) == 2 and sorted(texte) == ["falsch", "wahr"]:
                akt.typ = "tf"
            elif richtig > 1:
                akt.typ = "ms"
            else:
                akt.typ = "mc"
        fragen.append(akt)
        akt = None

    for raw in block.split("\n"):
        ln = raw.rstrip()
        s = ln.strip()
        if not s:
            if akt is not None and (akt.optionen or akt.antworten):
                abschluss()
            elif akt is None and text_buf:
                # Text ohne Antworten vor der ersten Frage = Einleitung
                einleitung.extend(text_buf)
                text_buf.clear()
            continue
        mo = OPTION.match(s)
        mk = KURZ.match(s)
        mf = FEEDBACK.match(s)
        if mo or mk:
            if akt is None:
                if not text_buf:
                    continue          # Antworten ohne Frage: ignorieren
                text = " ".join(text_buf).strip()
                text_buf.clear()
                pm = PUNKTE.search(text)
                punkte = 1.0
                if pm:
                    punkte = float(pm.group(1).replace(",", "."))
                    text = text[:pm.start()].rstrip()
                akt = Frage(text=text, punkte=punkte)
            if mo:
                akt.optionen.append((mo.group(2).strip(), mo.group(1).lower() == "x"))
            else:
                akt.antworten.append(mk.group(1).strip())
            continue
        if mf and akt is not None:
            if mf.group(1).lower() == "richtig":
                akt.fb_ok = mf.group(2).strip()
            else:
                akt.fb_no = mf.group(2).strip()
            continue
        # normaler Text
        if akt is not None and (akt.optionen or akt.antworten):
            abschluss()
        text_buf.append(s)

    if akt is not None:
        abschluss()
    if text_buf and not fragen:
        einleitung.extend(text_buf)
    return "\n".join(einleitung).strip(), fragen


def _quiz_bauen(titel, ident, lines):
    props, j = _eigenschaften(lines, 0)
    einleitung, fragen = _fragen_parsen("\n".join(lines[j:]))
    q = Quiz(titel=titel, ident=ident, fragen=fragen, props=props,
             einleitung=einleitung)
    return q


def lesen(text, quelle=""):
    lines = text.replace("\r\n", "\n").split("\n")
    kurs = Kurs(quelle=quelle)
    i = 0

    # Kopf
    kopf, i = _eigenschaften(lines, 0)
    kurs.props.update(kopf)
    kurs.titel = kopf.get("titel", "")

    modul = None
    item = None
    body = []           # Zeilen des aktuellen Items
    quiz_lines = None   # Zeilen eines eingebetteten Quiz
    quiz_titel = None
    zaehler = {"m": 0, "i": 0, "q": 0}
    in_code = False

    def quiz_abschluss():
        nonlocal quiz_lines, quiz_titel
        if quiz_lines is None or item is None:
            return
        zaehler["q"] += 1
        q = _quiz_bauen(quiz_titel, f"quiz-{zaehler['q']:02d}-{_slug(quiz_titel)}", quiz_lines)
        item.quizze.append(q)
        # Platzhalter im Body, damit das Quiz an der richtigen Stelle landet
        body.append(f"\x01QUIZ:{q.ident}\x01")
        quiz_lines = None
        quiz_titel = None

    def item_abschluss():
        nonlocal item, body
        quiz_abschluss()
        if item is not None:
            item.body = "\n".join(body).strip("\n")
            if item.art == "quiz":
                zaehler["q"] += 1
                item.quiz = _quiz_bauen(item.titel, f"quiz-{zaehler['q']:02d}-{_slug(item.titel)}",
                                        item.body.split("\n"))
                item.quiz.props = {**item.props, **item.quiz.props}
                item.body = ""
        item = None
        body = []

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if s.startswith("```"):
            in_code = not in_code
        if in_code:
            (quiz_lines if quiz_lines is not None else body).append(ln)
            i += 1
            continue

        m = STRUKTUR.match(ln) if ln.startswith("#") else None
        if m:
            raute, art, titel = m.group(1), (m.group(2) or "").lower(), m.group(3)
            if raute == "#":
                item_abschluss()
                zaehler["m"] += 1
                props, i = _eigenschaften(lines, i + 1)
                modul = Modul(titel=titel, ident=f"m{zaehler['m']:02d}-{_slug(titel)}", props=props)
                kurs.module.append(modul)
                continue
            if raute == "##" and art:
                item_abschluss()
                if modul is None:
                    modul = Modul(titel=kurs.titel or "Inhalt", ident="m01-inhalt")
                    kurs.module.append(modul)
                zaehler["i"] += 1
                props, i = _eigenschaften(lines, i + 1)
                item = Item(art=art, titel=titel,
                            ident=f"{modul.ident}-{zaehler['i']:03d}-{_slug(titel)}",
                            props=props)
                modul.items.append(item)
                continue
            if raute == "###" and art == "quiz" and item is not None and item.art == "seite":
                quiz_abschluss()
                quiz_titel = titel
                quiz_lines = []
                i += 1
                continue

        # Inhalt
        if quiz_lines is not None:
            # Ein Quizblock endet bei der naechsten Ueberschrift, einem Kasten (:::)
            # oder einer Trennlinie (---)
            if ln.startswith("#") or s.startswith(":::") or s.startswith("---"):
                quiz_abschluss()
                body.append(ln)
            else:
                quiz_lines.append(ln)
        elif item is not None:
            body.append(ln)
        elif modul is not None and s:
            # Text direkt unter dem Modul ohne Item -> Beschreibung ergaenzen
            modul.props["beschreibung"] = (modul.props.get("beschreibung", "") + " " + s).strip()
        i += 1

    item_abschluss()
    return kurs


def pruefen(kurs):
    """Liefert eine Liste (stufe, text) mit Warnungen und Fehlern."""
    meld = []
    if not kurs.titel:
        meld.append(("warnung", "Kein 'titel:' im Kopf der Datei."))
    if kurs.kurs_id is None:
        meld.append(("hinweis", "Kein 'kurs:' im Kopf - der Kurs wird beim Einspielen ausgewaehlt."))
    if not kurs.module:
        meld.append(("fehler", "Kein einziges Modul (# Ueberschrift) gefunden."))
    for m in kurs.module:
        if not m.items:
            meld.append(("warnung", f"Modul '{m.titel}' ist leer."))
        for it in m.items:
            if it.art == "seite" and it.props.get("datei") and it.body.strip():
                meld.append(("warnung", f"Seite '{it.titel}' hat datei: - der Markdown-Text darunter wird ignoriert."))
            if it.art == "datei" and not (it.props.get("datei") or it.titel):
                meld.append(("fehler", f"Datei-Thema ohne Pfad in Modul '{m.titel}'."))
            if it.art == "link" and not it.props.get("url"):
                meld.append(("fehler", f"Link '{it.titel}' hat keine url:."))
            if it.art in ("abgabe", "note") and not it.props.get("punkte"):
                meld.append(("warnung", f"'{it.titel}' hat keine punkte: - wird ohne Bewertung angelegt."))
            for q in (it.quizze + ([it.quiz] if it.quiz else [])):
                if not q.fragen:
                    meld.append(("warnung", f"Quiz '{q.titel}' hat keine Fragen."))
                for f in q.fragen:
                    if f.typ in ("mc", "ms", "tf") and not any(r for _, r in f.optionen):
                        meld.append(("fehler", f"Frage ohne richtige Antwort: '{f.text[:50]}'"))
    return meld
