# -*- coding: utf-8 -*-
"""Rueckfallwege, wenn die API nicht (ganz) mitspielt.

  imscc_export()   kompletter Kurs als Common-Cartridge-Paket zum Importieren
  quiz_csv()       Fragen im D2L-CSV-Format fuer die Fragensammlung
  manuell_liste()  Was danach von Hand in Brightspace zu tun bleibt (HTML)
"""

import csv
import html
import io
import pathlib
import shutil

from . import imscc, markdown


# --------------------------------------------------------------------------
# D2L-Fragen-CSV
# --------------------------------------------------------------------------

def quiz_csv(quiz):
    """Fragen eines Quiz als D2L-CSV (Kurs -> Fragensammlung -> Importieren)."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    for n, f in enumerate(quiz.fragen, 1):
        typ = {"mc": "MC", "ms": "MS", "tf": "TF", "sa": "SA"}[f.typ]
        w.writerow(["NewQuestion", typ, "", "", ""])
        w.writerow(["ID", f"{quiz.ident}-{n}", "", "", ""])
        w.writerow(["Title", f.text[:60], "", "", ""])
        w.writerow(["QuestionText", f.text, "", "", ""])
        w.writerow(["Points", ("%g" % f.punkte), "", "", ""])
        w.writerow(["Difficulty", "1", "", "", ""])
        if f.typ == "mc":
            w.writerow(["Scoring", "RightAnswers", "", "", ""])
            for t, r in f.optionen:
                w.writerow(["Option", "100" if r else "0", t, "", f.fb_ok if r else f.fb_no])
        elif f.typ == "ms":
            w.writerow(["Scoring", "AllOrNothing", "", "", ""])
            for t, r in f.optionen:
                w.writerow(["Option", "1" if r else "0", t, "", ""])
        elif f.typ == "tf":
            wahr = next((r for t, r in f.optionen if t.strip().lower() == "wahr"), False)
            w.writerow(["TRUE", "100" if wahr else "0", f.fb_ok if wahr else f.fb_no, "", ""])
            w.writerow(["FALSE", "0" if wahr else "100", f.fb_no if wahr else f.fb_ok, "", ""])
        else:
            w.writerow(["InputBox", "3", "40", "", ""])
            for a in f.antworten:
                w.writerow(["Answer", "100", a, "", ""])
        if f.fb_no and f.typ in ("ms", "sa"):
            w.writerow(["Feedback", f.fb_no, "", "", ""])
        w.writerow(["", "", "", "", ""])
    return buf.getvalue()


def alle_quiz_csv(kurs, ausgabe):
    """Schreibt fuer jedes Quiz eine CSV nach <ausgabe>/fragen/. Liefert [(quiz, pfad)]."""
    ordner = pathlib.Path(ausgabe) / "fragen"
    out = []
    for m, it in kurs.alle_items():
        for q in it.quizze + ([it.quiz] if it.quiz else []):
            if not q.fragen:
                continue
            ordner.mkdir(parents=True, exist_ok=True)
            p = ordner / f"{q.ident}.csv"
            p.write_text(quiz_csv(q), encoding="utf-8-sig")
            out.append((q, p))
    return out


# --------------------------------------------------------------------------
# Common Cartridge
# --------------------------------------------------------------------------

def imscc_export(kurs, plan, ausgabe, name=None):
    """Baut aus dem gerenderten Plan ein .imscc. Liefert (pfad, anzahl)."""
    ausgabe = pathlib.Path(ausgabe)
    name = name or (kurs.titel or "kurs")
    baum = []
    n = 0
    for modul in kurs.module:
        kinder = []
        for e in [x for x in plan if x["modul"] == modul.ident]:
            n += 1
            ident = f"R{n:04d}"
            if e["art"] in ("seite", "quiz"):
                p = pathlib.Path(e["datei"])
                kinder.append(imscc.Item(e["titel"], imscc.Page(
                    ident, e["titel"], f"web_resources/{modul.ident}/{p.name}",
                    p.read_text(encoding="utf-8"))))
            elif e["art"] == "datei":
                p = pathlib.Path(e["datei"])
                if p.is_file():
                    kinder.append(imscc.Item(e["titel"], imscc.Asset(
                        ident, e["titel"], str(p), f"web_resources/{modul.ident}/{p.name}")))
            elif e["art"] == "abgabe":
                pkt = e["props"].get("punkte") or "0"
                kinder.append(imscc.Item(e["titel"], imscc.Assignment(
                    ident, e["titel"], e.get("anweisung") or "", points=pkt)))
            elif e["art"] == "link":
                url = e["props"].get("url", "")
                seite = (f'<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" '
                         f'content="0; url={html.escape(url)}"></head><body><p><a href="{html.escape(url)}">'
                         f'{html.escape(e["titel"])}</a></p></body></html>')
                kinder.append(imscc.Item(e["titel"], imscc.Page(
                    ident, e["titel"], f"web_resources/{modul.ident}/{ident}.html", seite)))
            # Notenelemente gibt es im CC-Format nicht
        baum.append(imscc.Item(modul.titel, children=kinder))
    bau = ausgabe / "_imscc"
    ziel = ausgabe / (_dateiname(name) + ".imscc")
    pfad, anzahl = imscc.build(kurs.titel or name, baum, str(bau), str(ziel))
    shutil.rmtree(bau, ignore_errors=True)
    return pfad, anzahl


def _dateiname(t):
    return "".join(c if c.isalnum() or c in "-_ " else "_" for c in t).strip().replace(" ", "_") or "kurs"


# --------------------------------------------------------------------------
# Was bleibt von Hand
# --------------------------------------------------------------------------

def manuell_liste(kurs, plan, protokoll=None, quiz_csvs=None):
    """HTML-Checkliste: was bskitool nicht automatisch erledigen kann."""
    punkte = []
    quiz_csvs = quiz_csvs or []
    for q, p in quiz_csvs:
        punkte.append(f"Fragen fuer <b>{html.escape(q.titel)}</b> importieren: Kurs &rarr; Quizze &rarr; "
                      f"Fragensammlung &rarr; Importieren &rarr; Datei hochladen: <code>{html.escape(str(p))}</code>. "
                      f"Danach die Fragen dem Quiz hinzufuegen.")
    for e in plan:
        if e["art"] == "abgabe":
            punkte.append(f"Abgabe <b>{html.escape(e['titel'])}</b>: Faelligkeit und Sichtbarkeit pruefen, "
                          f"ggf. im Modul ueber „Vorhandene Aktivitaeten“ verknuepfen.")
    if protokoll:
        for z in protokoll:
            if z.get("status") in ("fehler", "hinweis"):
                punkte.append(f"{html.escape(z.get('schritt', ''))}: {html.escape(z.get('text', ''))}")
    punkte.append("Alles ist <b>verborgen</b> angelegt - Module und Themen zur jeweiligen Stunde freigeben.")
    lis = "".join(f"<li>{p}</li>" for p in punkte)
    return f"<h2>Noch von Hand in Brightspace</h2><ol>{lis}</ol>"
