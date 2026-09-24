# -*- coding: utf-8 -*-
"""Web-Oberflaeche fuer bskitool - http.server, ohne Fremdbibliotheken.

Start:  python3 bskitool.py            (oeffnet http://localhost:8765)
"""

import json
import mimetypes
import os
import pathlib
import threading
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import fallback, kursdatei, push, render
from .api import ApiFehler, Verbindung

HIER = pathlib.Path(__file__).resolve().parent.parent
UI = HIER / "ui"
KURSE = HIER / "kurse"
AUSGABE = HIER / "ausgabe"
DATEN = HIER / "daten"


class Zustand:
    def __init__(self):
        if os.environ.get("BSKITOOL_DEMO") == "1":
            from .demo import DemoVerbindung
            self.verb = DemoVerbindung(DATEN, protokoll=self.log)
            self.demo = True
        else:
            self.verb = Verbindung(DATEN, protokoll=self.log)
            self.demo = False
        self.zeilen = []          # Live-Protokoll
        self.lauf = None          # laufender Thread
        self.lauf_info = {}
        self.lock = threading.Lock()

    def log(self, text):
        with self.lock:
            self.zeilen.append(text)

    def start(self, name, fn):
        if self.lauf and self.lauf.is_alive():
            raise ApiFehler("Es laeuft schon ein Vorgang - bitte warten.")
        self.zeilen = []
        self.lauf_info = {"name": name, "fertig": False, "fehler": None, "ergebnis": None}

        def _run():
            try:
                self.lauf_info["ergebnis"] = fn()
            except Exception as f:      # noqa - alles anzeigen
                self.lauf_info["fehler"] = str(f)
                self.log("FEHLER: " + str(f))
                traceback.print_exc()
            finally:
                self.lauf_info["fertig"] = True
        self.lauf = threading.Thread(target=_run, daemon=True)
        self.lauf.start()


Z = Zustand()


# --------------------------------------------------------------------------
# Kursdateien
# --------------------------------------------------------------------------

def kurse_finden():
    """Alle .md unter kurse/ (ein Ordner je Kurs oder einzelne Dateien)."""
    out = []
    if not KURSE.exists():
        KURSE.mkdir(parents=True, exist_ok=True)
    for p in sorted(KURSE.rglob("*.md")):
        if p.name.upper().startswith(("LIESMICH", "README")):
            continue
        try:
            k = kursdatei.lesen(p.read_text(encoding="utf-8"), str(p))
            titel = k.titel or p.stem
            kid = k.kurs_id
        except Exception:
            titel, kid = p.stem + " (Fehler beim Lesen)", None
        out.append({"pfad": str(p.relative_to(HIER)), "titel": titel, "kurs_id": kid,
                    "ordner": str(p.parent.relative_to(HIER))})
    return out


def kurs_laden(rel):
    p = (HIER / rel).resolve()
    if HIER not in p.parents or not p.is_file():
        raise ApiFehler("Kursdatei nicht gefunden.")
    return kursdatei.lesen(p.read_text(encoding="utf-8"), str(p)), p


def ausgabe_ordner(p):
    name = p.parent.name if p.parent != KURSE else p.stem
    return AUSGABE / name


def uebersicht(k):
    module = []
    for m in k.module:
        items = []
        for it in m.items:
            z = {"art": it.art, "titel": it.titel, "props": it.props}
            if it.quizze:
                z["quizze"] = [{"titel": q.titel, "fragen": len(q.fragen), "punkte": q.punkte} for q in it.quizze]
            if it.quiz:
                z["quiz"] = {"titel": it.quiz.titel, "fragen": len(it.quiz.fragen),
                             "punkte": it.quiz.punkte, "benotet": it.quiz.benotet}
            items.append(z)
        module.append({"titel": m.titel, "beschreibung": m.beschreibung, "props": m.props, "items": items})
    return {"titel": k.titel, "kurs_id": k.kurs_id, "design": k.design, "props": k.props,
            "module": module, "meldungen": kursdatei.pruefen(k)}


# --------------------------------------------------------------------------
# API-Routen
# --------------------------------------------------------------------------

def route(pfad, methode, daten):
    v = Z.verb
    q = daten or {}

    # --- Einstellungen / Anmeldung
    if pfad == "/api/status":
        return {"konfiguriert": v.konfiguriert, "angemeldet": v.angemeldet, "host": v.einst["host"],
                "demo": Z.demo,
                "einstellungen": {k: ("" if k == "client_secret" else val) for k, val in v.einst.items()},
                "secret_gesetzt": bool(v.einst.get("client_secret")),
                "lauf": Z.lauf_info, "zeilen": Z.zeilen[-400:]}
    if pfad == "/api/einstellungen" and methode == "POST":
        neu = {k: q[k] for k in ("host", "client_id", "redirect", "scopes", "v_le", "v_lp") if k in q}
        if q.get("client_secret"):
            neu["client_secret"] = q["client_secret"]
        if "pkce" in q:
            neu["pkce"] = bool(q["pkce"])
        neu["host"] = neu.get("host", v.einst["host"]).replace("https://", "").strip("/ ")
        v.speichern(neu)
        return {"ok": True}
    if pfad == "/api/pruefen":
        ok, text = v.erreichbar()
        return {"ok": ok, "text": text}
    if pfad == "/api/anmelden" and methode == "POST":
        url = v.anmeldung_starten()
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return {"url": url}
    if pfad == "/api/anmelden/status":
        return {"status": v.anmeldung_status() if v._anmeldung else "keine"}
    if pfad == "/api/anmelden/code" and methode == "POST":
        return {"status": v.anmeldung_code_einreichen(q.get("adresse", ""))}
    if pfad == "/api/abmelden" and methode == "POST":
        v.abmelden()
        return {"ok": True}
    if pfad == "/api/wer":
        w = v.wer()
        return {"name": f"{w.get('FirstName', '')} {w.get('LastName', '')}".strip(),
                "benutzer": w.get("UniqueName", "")}
    if pfad == "/api/kurse":
        return {"kurse": v.kurse()}

    # --- Kursdateien
    if pfad == "/api/kursdateien":
        return {"kurse": kurse_finden()}
    if pfad == "/api/kurs/uebersicht":
        k, p = kurs_laden(q["pfad"])
        return uebersicht(k)
    if pfad == "/api/kurs/vorschau" and methode == "POST":
        k, p = kurs_laden(q["pfad"])
        meld = []
        aus = ausgabe_ordner(p)
        render.kurs_rendern(k, p.parent, aus, design=q.get("design") or None, meldungen=meld)
        return {"url": "/ausgabe/" + urllib.parse.quote(str(aus.relative_to(AUSGABE))) + "/index.html",
                "meldungen": meld}
    if pfad == "/api/kurs/export" and methode == "POST":
        k, p = kurs_laden(q["pfad"])
        meld = []
        aus = ausgabe_ordner(p)
        plan = render.kurs_rendern(k, p.parent, aus, design=q.get("design") or None, meldungen=meld)
        pfad_cc, n = fallback.imscc_export(k, plan, aus)
        csvs = fallback.alle_quiz_csv(k, aus)
        return {"datei": str(pfad_cc), "anzahl": n, "meldungen": meld,
                "url": "/ausgabe/" + urllib.parse.quote(str(pathlib.Path(pfad_cc).relative_to(AUSGABE))),
                "csv": [str(c[1]) for c in csvs]}
    if pfad == "/api/kurs/einspielen" and methode == "POST":
        k, p = kurs_laden(q["pfad"])
        kurs_id = q.get("kurs_id") or k.kurs_id
        if not kurs_id:
            raise ApiFehler("Kein Ziel-Kurs gewaehlt.")
        trocken = bool(q.get("trocken"))
        aus = ausgabe_ordner(p)

        def _lauf():
            e = push.Einspieler(v, k, p.parent, aus, int(kurs_id), trocken=trocken, log=Z.log)
            e.lauf(design=q.get("design") or None)
            return {"protokoll": str(aus / "protokoll.json"), "angelegt": len(e.angelegt),
                    "fehler": sum(1 for z in e.protokoll if z["status"] == "fehler"),
                    "todo": "/ausgabe/" + urllib.parse.quote(str(aus.relative_to(AUSGABE))) + "/noch-zu-tun.html"}
        Z.start("Trockenlauf" if trocken else "Einspielen", _lauf)
        return {"ok": True}
    if pfad == "/api/kurs/rueckgaengig" and methode == "POST":
        k, p = kurs_laden(q["pfad"])
        prot = ausgabe_ordner(p) / "protokoll.json"
        if not prot.exists():
            raise ApiFehler("Kein Protokoll vom letzten Einspielen gefunden.")
        if q.get("nur_zeigen"):
            return {"liste": push.rueckgaengig(v, prot, nur_zeigen=True)}
        if q.get("bestaetigung") != "LOESCHEN":
            raise ApiFehler("Bestaetigung fehlt.")
        Z.start("Rueckgaengig", lambda: {"liste": push.rueckgaengig(v, prot, log=Z.log)})
        return {"ok": True}

    # --- Aufraeumen
    if pfad == "/api/inhalt":
        ou = int(q["kurs_id"])
        out = {"toc": v.toc(ou), "abgaben": [], "noten": [], "quizze": [], "probleme": []}
        for name, fn in (("abgaben", v.abgabeordner), ("noten", v.notenelemente), ("quizze", v.quizze)):
            try:
                out[name] = fn(ou)
            except ApiFehler as f:
                out["probleme"].append(f"{name}: {f}")
        return out
    if pfad == "/api/loeschen" and methode == "POST":
        if q.get("bestaetigung") != "LOESCHEN":
            raise ApiFehler("Bestaetigung fehlt.")
        ou = int(q["kurs_id"])
        objekte = q.get("objekte", [])

        def _lauf():
            erg = []
            for o in objekte:
                art, ident = o["art"], o["id"]
                try:
                    {"modul": v.modul_loeschen, "thema": v.thema_loeschen, "abgabe": v.abgabeordner_loeschen,
                     "note": v.notenelement_loeschen, "quiz": v.quiz_loeschen}[art](ou, ident)
                    Z.log(f"geloescht: {art} {ident} {o.get('titel', '')}")
                    erg.append({**o, "status": "geloescht"})
                except ApiFehler as f:
                    txt = "schon weg" if f.status == 404 else str(f)
                    Z.log(f"{art} {ident} {o.get('titel', '')}: {txt}")
                    erg.append({**o, "status": txt})
            return {"ergebnis": erg}
        Z.start("Loeschen", _lauf)
        return {"ok": True}

    raise ApiFehler(f"Unbekannter Pfad: {pfad}")


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _json(self, obj, status=200):
        b = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _datei(self, p):
        p = pathlib.Path(p)
        if not p.is_file():
            self.send_error(404)
            return
        typ = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        if typ.startswith("text/") or typ in ("application/json", "application/javascript"):
            typ += "; charset=utf-8"
        b = p.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _verteilen(self, methode):
        u = urllib.parse.urlparse(self.path)
        pfad = urllib.parse.unquote(u.path)
        # nur lokale Aufrufe
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            self.send_error(403)
            return
        if pfad.startswith("/api/"):
            daten = {}
            if methode == "POST":
                n = int(self.headers.get("Content-Length") or 0)
                if n:
                    try:
                        daten = json.loads(self.rfile.read(n).decode("utf-8"))
                    except ValueError:
                        daten = {}
            else:
                daten = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            try:
                self._json(route(pfad, methode, daten))
            except ApiFehler as f:
                self._json({"fehler": str(f)}, 400)
            except Exception as f:      # noqa
                traceback.print_exc()
                self._json({"fehler": f"{type(f).__name__}: {f}"}, 500)
            return
        if pfad == "/" or pfad == "/index.html":
            return self._datei(UI / "index.html")
        if pfad.startswith("/ausgabe/"):
            ziel = (AUSGABE / pfad[len("/ausgabe/"):]).resolve()
            if AUSGABE.resolve() not in ziel.parents:
                self.send_error(403)
                return
            return self._datei(ziel)
        if pfad.startswith("/ui/"):
            ziel = (UI / pfad[4:]).resolve()
            if UI.resolve() not in ziel.parents:
                self.send_error(403)
                return
            return self._datei(ziel)
        self.send_error(404)

    def do_GET(self):
        self._verteilen("GET")

    def do_POST(self):
        self._verteilen("POST")


def starten(port=8765, oeffnen=True):
    for p in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            break
        except OSError:
            continue
    else:
        raise SystemExit("Kein freier Port gefunden.")
    url = f"http://localhost:{server.server_address[1]}/"
    print(f"\nbskitool laeuft auf {url}\nZum Beenden Strg-C druecken (oder das Fenster schliessen).\n")
    if oeffnen:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
