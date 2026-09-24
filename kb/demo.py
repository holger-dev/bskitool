# -*- coding: utf-8 -*-
"""Demo-Verbindung: tut so, als waere Brightspace da (fuer Ausprobieren und Tests).

Aktivieren:  BSKITOOL_DEMO=1 python3 bskitool.py
Alles bleibt im Arbeitsspeicher; nichts wird wirklich gesendet.
"""

import time

from .api import ApiFehler


class DemoVerbindung:
    def __init__(self, ordner=None, protokoll=None):
        self.log = protokoll or (lambda *a: None)
        self.einst = {"host": "demo.brightspace.local", "client_id": "demo", "client_secret": "demo",
                      "redirect": "https://localhost:8080/callback", "scopes": "core:*:*", "pkce": False,
                      "v_lp": "1.43", "v_le": "1.80"}
        self._angemeldet = True
        self._n = 1000
        self._anmeldung = None
        self.kurse_daten = [{"id": 10452, "name": "Datenverarbeitung Klasse 11 (Demo)", "code": "DV11", "rolle": "Lehrkraft"},
                            {"id": 10777, "name": "Informatik Grundkurs (Demo)", "code": "INF-GK", "rolle": "Lehrkraft"}]
        self.inhalt = {ou: {"module": [], "abgaben": [], "noten": [], "quizze": []} for ou in (10452, 10777)}
        m = self._modul_roh(10452, "Altes Modul aus dem Import", "Beispiel")
        self._thema_roh(10452, m["Id"], "Alte Seite", 1)

    # Einstellungen
    def laden(self): pass
    def speichern(self, neu=None):
        if neu: self.einst.update(neu)
    @property
    def konfiguriert(self): return True
    @property
    def angemeldet(self): return self._angemeldet
    def erreichbar(self): return True, "Demo-Modus: keine echte Verbindung."
    def anmeldung_starten(self):
        self._angemeldet = True
        self._anmeldung = {"x": 1}
        return "about:blank"
    def anmeldung_status(self): return "fertig"
    def anmeldung_code_einreichen(self, a): return "fertig"
    def anmelden_konsole(self, oeffnen=True): self._angemeldet = True
    def abmelden(self): self._angemeldet = False

    def _id(self):
        self._n += 1
        return self._n

    def _pruef(self):
        if not self._angemeldet:
            raise ApiFehler("Noch nicht angemeldet.")
        time.sleep(0.05)

    # Lesen
    def wer(self):
        self._pruef()
        return {"FirstName": "Demo", "LastName": "Lehrkraft", "UniqueName": "demo"}
    def kurse(self):
        self._pruef()
        return list(self.kurse_daten)
    def toc(self, ou):
        self._pruef()
        z = []
        for m in self.inhalt[ou]["module"]:
            z.append({"art": "modul", "id": m["Id"], "titel": m["Title"], "tiefe": 0, "hidden": m["IsHidden"]})
            for t in m["themen"]:
                z.append({"art": "thema", "id": t["Id"], "titel": t["Title"], "tiefe": 1, "typ": t["typ"], "hidden": t["IsHidden"]})
        return z
    def abgabeordner(self, ou):
        self._pruef()
        return [{"id": a["Id"], "titel": a["Name"], "note_id": a.get("GradeItemId"), "hidden": a["IsHidden"]} for a in self.inhalt[ou]["abgaben"]]
    def notenelemente(self, ou):
        self._pruef()
        return [{"id": n["Id"], "titel": n["Name"], "punkte": n["MaxPoints"], "typ": "Numeric"} for n in self.inhalt[ou]["noten"]]
    def quizze(self, ou):
        self._pruef()
        return [{"id": q["Id"], "titel": q["Name"], "aktiv": q["IsActive"]} for q in self.inhalt[ou]["quizze"]]

    # Anlegen
    def _modul_roh(self, ou, titel, beschr="", sichtbar=False):
        m = {"Id": self._id(), "Title": titel, "IsHidden": not sichtbar, "themen": []}
        self.inhalt[ou]["module"].append(m)
        return m
    def _thema_roh(self, ou, mid, titel, typ, sichtbar=False):
        for m in self.inhalt[ou]["module"]:
            if m["Id"] == mid:
                t = {"Id": self._id(), "Title": titel, "typ": "File" if typ == 1 else "Link", "IsHidden": not sichtbar}
                m["themen"].append(t)
                return t
        raise ApiFehler(f"Modul {mid} nicht gefunden", 404)
    def modul_anlegen(self, ou, titel, beschreibung="", sichtbar=False):
        self._pruef()
        return self._modul_roh(ou, titel, beschreibung, sichtbar)
    def datei_thema_anlegen(self, ou, mid, titel, pfad, sichtbar=False, unterordner="bskitool"):
        self._pruef()
        return self._thema_roh(ou, mid, titel, 1, sichtbar)
    def link_thema_anlegen(self, ou, mid, titel, url, sichtbar=False, extern=True):
        self._pruef()
        return self._thema_roh(ou, mid, titel, 3, sichtbar)
    def notenelement_anlegen(self, ou, titel, punkte, kategorie_id=None):
        self._pruef()
        n = {"Id": self._id(), "Name": titel, "MaxPoints": punkte}
        self.inhalt[ou]["noten"].append(n)
        return n
    def abgabeordner_anlegen(self, ou, titel, anweisung="", punkte=None, note_id=None, faellig=None, sichtbar=False):
        self._pruef()
        a = {"Id": self._id(), "Name": titel, "GradeItemId": note_id, "IsHidden": not sichtbar}
        self.inhalt[ou]["abgaben"].append(a)
        return a
    def quiz_anlegen(self, ou, titel, beschreibung="", note_id=None, versuche=1, sichtbar=False, faellig=None):
        self._pruef()
        q = {"Id": self._id(), "Name": titel, "IsActive": sichtbar}
        self.inhalt[ou]["quizze"].append(q)
        return q

    # Loeschen
    def _weg(self, liste, ident):
        for i, o in enumerate(liste):
            if o["Id"] == ident:
                del liste[i]
                return {}
        raise ApiFehler("nicht gefunden", 404)
    def modul_loeschen(self, ou, ident):
        self._pruef()
        return self._weg(self.inhalt[ou]["module"], ident)
    def thema_loeschen(self, ou, ident):
        self._pruef()
        for m in self.inhalt[ou]["module"]:
            try:
                return self._weg(m["themen"], ident)
            except ApiFehler:
                pass
        raise ApiFehler("nicht gefunden", 404)
    def abgabeordner_loeschen(self, ou, ident):
        self._pruef()
        return self._weg(self.inhalt[ou]["abgaben"], ident)
    def notenelement_loeschen(self, ou, ident):
        self._pruef()
        return self._weg(self.inhalt[ou]["noten"], ident)
    def quiz_loeschen(self, ou, ident):
        self._pruef()
        return self._weg(self.inhalt[ou]["quizze"], ident)
