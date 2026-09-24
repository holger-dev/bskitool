# -*- coding: utf-8 -*-
"""Kurs nach Brightspace einspielen - mit Trockenlauf, Protokoll und Rueckgaengig.

Reihenfolge:
  1. Notenelemente (fuer Note:, Abgabe: mit punkte, Quiz: benotet)
  2. je Modul: Modul anlegen, dann Themen in Dateireihenfolge
       Seite  -> Datei-Thema (HTML)
       Datei  -> Datei-Thema (xlsx, pdf ...)
       Link   -> Link-Thema
       Abgabe -> Abgabeordner (+ Notenelement) + Link-Thema im Modul
       Quiz   -> Selbstcheck-Seite als Thema; bei benotet zusaetzlich Quiz-Huelle
                 (ohne Fragen - Fragen als CSV fuer die Fragensammlung)
       Note   -> (schon in 1.)
Alles wird VERBORGEN angelegt, ausser 'sichtbar: ja' steht am Modul/Item.

Das Protokoll (ausgabe/protokoll.json) merkt sich alle angelegten IDs, damit
'rueckgaengig' sie wieder loeschen kann.
"""

import json
import pathlib
import time

from . import fallback, render
from .api import ApiFehler


def _ja(v):
    return str(v).strip().lower() in ("ja", "yes", "1", "true", "wahr")


def _datum(v):
    """'2026-10-15' oder '15.10.2026' -> ISO-UTC fuer die API (Ende des Tages, 23:59 MEZ)."""
    v = (v or "").strip()
    if not v:
        return None
    try:
        if "." in v:
            t, m, j = v.split(".")
            v = f"{j}-{int(m):02d}-{int(t):02d}"
        return f"{v}T22:59:00.000Z"
    except ValueError:
        return None


class Einspieler:
    def __init__(self, verb, kurs, basis, ausgabe, kurs_id, trocken=False, log=None):
        self.verb = verb
        self.kurs = kurs
        self.basis = pathlib.Path(basis)
        self.ausgabe = pathlib.Path(ausgabe)
        self.kurs_id = int(kurs_id)
        self.trocken = trocken
        self.log = log or (lambda *a: None)
        self.protokoll = []     # [{zeit, schritt, status, text, art, id}]
        self.angelegt = []      # [{art, id, titel}] fuer rueckgaengig
        self.noten = {}         # titel -> GradeItemId
        self.meldungen = []

    def _p(self, schritt, status, text="", art=None, ident=None):
        z = {"zeit": time.strftime("%H:%M:%S"), "schritt": schritt, "status": status, "text": text}
        if art:
            z["art"] = art
            z["id"] = ident
        self.protokoll.append(z)
        self.log(f"[{status}] {schritt}" + (f" - {text}" if text else ""))
        return z

    def _tu(self, schritt, fn, art=None):
        """Fuehrt fn() aus (oder tut so). Liefert die Antwort oder None bei Fehler."""
        if self.trocken:
            self._p(schritt, "trocken")
            return {"Id": None}
        try:
            a = fn()
        except ApiFehler as f:
            self._p(schritt, "fehler", str(f))
            return None
        ident = None
        if isinstance(a, dict):
            ident = a.get("Id") or a.get("ModuleId") or a.get("TopicId") or a.get("QuizId")
        if art and ident:
            self.angelegt.append({"art": art, "id": ident, "titel": schritt})
        self._p(schritt, "ok", f"Id {ident}" if ident else "", art, ident)
        return a

    # ------------------------------------------------------------------

    def lauf(self, design=None):
        k, ou = self.kurs, self.kurs_id
        self._p("Rendern", "info", f"Kurs '{k.titel}' -> {self.ausgabe}")
        plan = render.kurs_rendern(k, self.basis, self.ausgabe, design=design, meldungen=self.meldungen)
        for stufe, text in self.meldungen:
            self._p("Rendern", "hinweis" if stufe != "fehler" else "fehler", text)
        csvs = fallback.alle_quiz_csv(k, self.ausgabe)
        plan_je_modul = {}
        for e in plan:
            plan_je_modul.setdefault(e["modul"], []).append(e)

        # 1. Notenelemente
        for modul in k.module:
            for it in modul.items:
                punkte = it.props.get("punkte")
                benotet = it.art == "note" or (it.art == "abgabe" and punkte) or \
                          (it.art == "quiz" and it.quiz and it.quiz.benotet)
                if not benotet:
                    continue
                punkte = float(str(punkte or (it.quiz.punkte if it.quiz else 0)).replace(",", "."))
                if punkte <= 0:
                    self._p(f"Notenelement '{it.titel}'", "hinweis", "keine Punkte - uebersprungen")
                    continue
                a = self._tu(f"Notenelement '{it.titel}' ({punkte:g} P)",
                             lambda: self.verb.notenelement_anlegen(ou, it.titel, punkte), art="note")
                if a and a.get("Id"):
                    self.noten[it.titel] = a["Id"]

        # 2. Module und Themen
        for modul in k.module:
            sichtbar = _ja(modul.props.get("sichtbar", ""))
            a = self._tu(f"Modul '{modul.titel}'",
                         lambda: self.verb.modul_anlegen(ou, modul.titel, modul.beschreibung, sichtbar),
                         art="modul")
            if a is None:
                self._p(f"Modul '{modul.titel}'", "hinweis", "Themen dieses Moduls uebersprungen")
                continue
            mid = a.get("Id")
            for e in plan_je_modul.get(modul.ident, []):
                self._thema(mid, e, ou, sichtbar_modul=sichtbar)

        # Protokoll sichern
        self.ausgabe.mkdir(parents=True, exist_ok=True)
        (self.ausgabe / "protokoll.json").write_text(json.dumps({
            "kurs_id": ou, "titel": k.titel, "zeit": time.strftime("%Y-%m-%d %H:%M"),
            "trocken": self.trocken, "protokoll": self.protokoll, "angelegt": self.angelegt,
        }, indent=1, ensure_ascii=False), encoding="utf-8")
        liste = fallback.manuell_liste(k, plan, self.protokoll, csvs)
        (self.ausgabe / "noch-zu-tun.html").write_text(
            f'<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><title>Noch zu tun</title>'
            f'<style>{render.DV_CSS}</style></head><body><div class="dv">{liste}</div></body></html>',
            encoding="utf-8")
        fehler = sum(1 for z in self.protokoll if z["status"] == "fehler")
        self._p("Fertig", "info", f"{len(self.angelegt)} Objekte angelegt, {fehler} Fehler"
                if not self.trocken else "Trockenlauf - nichts geaendert")
        return self.protokoll

    def _thema(self, mid, e, ou, sichtbar_modul=False):
        art, titel, props = e["art"], e["titel"], e["props"]
        sichtbar = _ja(props.get("sichtbar", "")) or sichtbar_modul
        if art in ("seite", "quiz"):
            self._tu(f"Seite '{titel}'",
                     lambda: self.verb.datei_thema_anlegen(ou, mid, titel, e["datei"], sichtbar), art="thema")
            if art == "quiz" and e.get("quiz") and e["quiz"].benotet:
                q = e["quiz"]
                note_id = self.noten.get(titel)
                versuche = int(props.get("versuche", "1") or 1)
                r = self._tu(f"Quiz-Huelle '{titel}'",
                             lambda: self.verb.quiz_anlegen(ou, titel, q.einleitung, note_id, versuche,
                                                            sichtbar, _datum(props.get("faellig"))),
                             art="quiz")
                self._p(f"Quiz '{titel}'", "hinweis",
                        "Fragen koennen nicht per API angelegt werden - CSV aus ausgabe/fragen/ in die "
                        "Fragensammlung importieren und dem Quiz zuordnen."
                        + ("" if r else " Die Quiz-Huelle bitte von Hand anlegen."))
        elif art == "datei":
            self._tu(f"Datei '{titel}'",
                     lambda: self.verb.datei_thema_anlegen(ou, mid, titel, e["datei"], sichtbar),
                     art="thema")
        elif art == "link":
            self._tu(f"Link '{titel}'",
                     lambda: self.verb.link_thema_anlegen(ou, mid, titel, props.get("url", ""), sichtbar),
                     art="thema")
        elif art == "abgabe":
            punkte = props.get("punkte")
            note_id = self.noten.get(titel)
            r = self._tu(f"Abgabeordner '{titel}'",
                         lambda: self.verb.abgabeordner_anlegen(
                             ou, titel, e.get("anweisung", ""), punkte, note_id,
                             _datum(props.get("faellig")), sichtbar), art="abgabe")
            if r and r.get("Id") and not self.trocken:
                url = f"/d2l/lms/dropbox/user/folder_submit_files.d2l?db={r['Id']}&grpid=0&ou={ou}"
                self._tu(f"Link im Modul -> Abgabe '{titel}'",
                         lambda: self.verb.link_thema_anlegen(ou, mid, titel, url, sichtbar, extern=False),
                         art="thema")
            elif self.trocken:
                self._p(f"Link im Modul -> Abgabe '{titel}'", "trocken")
        elif art == "note":
            pass  # schon in Schritt 1


# --------------------------------------------------------------------------
# Rueckgaengig
# --------------------------------------------------------------------------

def rueckgaengig(verb, protokoll_datei, log=None, nur_zeigen=False):
    """Loescht alles, was laut Protokoll angelegt wurde (in umgekehrter Reihenfolge)."""
    log = log or (lambda *a: None)
    d = json.loads(pathlib.Path(protokoll_datei).read_text(encoding="utf-8"))
    ou = d["kurs_id"]
    erg = []
    for o in reversed(d.get("angelegt", [])):
        art, ident, titel = o["art"], o["id"], o["titel"]
        if nur_zeigen:
            erg.append((art, ident, titel, "wuerde geloescht"))
            continue
        try:
            if art == "modul":
                verb.modul_loeschen(ou, ident)
            elif art == "thema":
                verb.thema_loeschen(ou, ident)
            elif art == "abgabe":
                verb.abgabeordner_loeschen(ou, ident)
            elif art == "note":
                verb.notenelement_loeschen(ou, ident)
            elif art == "quiz":
                verb.quiz_loeschen(ou, ident)
            erg.append((art, ident, titel, "geloescht"))
            log(f"geloescht: {art} {ident} {titel}")
        except ApiFehler as f:
            # Themen sind mit dem Modul oft schon weg - das ist kein Problem
            txt = "schon weg" if f.status == 404 else str(f)
            erg.append((art, ident, titel, txt))
            log(f"{art} {ident}: {txt}")
    if not nur_zeigen:
        d["rueckgaengig"] = time.strftime("%Y-%m-%d %H:%M")
        d["angelegt"] = []
        pathlib.Path(protokoll_datei).write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    return erg
