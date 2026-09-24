# -*- coding: utf-8 -*-
"""Brightspace-Valence-API - nur Standardbibliothek.

Uebernommen und umgebaut aus brightspace.py (LF7-Brightspace-Werkzeug):
statt sys.exit gibt es Ausnahmen (ApiFehler), statt print ein Protokoll-
Callback, damit Kommandozeile und Web-Oberflaeche denselben Code nutzen.

Einstellungen liegen in <ordner>/einstellungen.json:
    host, client_id, client_secret, redirect, scopes, pkce
Das Token in <ordner>/token.json (nur fuer den Benutzer lesbar).
"""

import base64
import hashlib
import http.server
import json
import mimetypes
import os
import secrets
import socket
import ssl
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

AUTH_ENDPUNKT = "https://auth.brightspace.com/oauth2/auth"
TOKEN_ENDPUNKT = "https://auth.brightspace.com/core/connect/token"

STANDARD = {
    "host": "",
    "client_id": "",
    "client_secret": "",
    "redirect": "https://localhost:8080/callback",
    "scopes": "core:*:* content:*:* grades:*:* dropbox:*:*",
    "pkce": False,
    "v_lp": "1.43",
    "v_le": "1.80",
}

# Scopes, die die einzelnen Funktionen brauchen (fuer Hinweise)
SCOPE_HINWEIS = {
    "content": "content:*:*", "grades": "grades:*:*",
    "dropbox": "dropbox:*:*", "quizzes": "quizzing:*:*",
}


_VERBOTEN = '/"*<>+=|,%'


def notenname(titel):
    """D2L erlaubt in Notennamen kein / \" * < > + = | , % - ersetzen, max. 128 Zeichen."""
    t = titel.replace("+", " und ").replace("=", " ist ").replace("/", "-")
    t = "".join(" " if c in _VERBOTEN else c for c in t)
    return " ".join(t.split())[:128]


class ApiFehler(Exception):
    def __init__(self, text, status=None, antwort=None):
        super().__init__(text)
        self.status = status
        self.antwort = antwort


class Verbindung:
    def __init__(self, ordner, protokoll=None):
        self.ordner = Path(ordner)
        self.ordner.mkdir(parents=True, exist_ok=True)
        self.einst_datei = self.ordner / "einstellungen.json"
        self.token_datei = self.ordner / "token.json"
        self.zert = self.ordner / "localhost-cert.pem"
        self.schluessel = self.ordner / "localhost-key.pem"
        self.log = protokoll or (lambda *a: None)
        self.einst = dict(STANDARD)
        self.laden()
        self._anmeldung = None      # laufender Login (Web-Oberflaeche)

    # ------------------------------------------------------------------
    # Einstellungen
    # ------------------------------------------------------------------

    def laden(self):
        if self.einst_datei.exists():
            try:
                self.einst.update(json.loads(self.einst_datei.read_text(encoding="utf-8")))
            except ValueError:
                pass
        # Alte .env aus dem LF7-Werkzeug uebernehmen, falls vorhanden
        env = self.ordner / ".env"
        if env.exists() and not self.einst.get("client_id"):
            self.env_uebernehmen(env)

    def env_uebernehmen(self, env_pfad):
        m = {"BS_HOST": "host", "BS_CLIENT_ID": "client_id", "BS_CLIENT_SECRET": "client_secret",
             "BS_REDIRECT": "redirect", "BS_SCOPES": "scopes"}
        for z in Path(env_pfad).read_text(encoding="utf-8").splitlines():
            z = z.strip()
            if "=" in z and not z.startswith("#"):
                k, v = z.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k in m:
                    self.einst[m[k]] = v
                elif k == "BS_PKCE":
                    self.einst["pkce"] = v == "1"

    def speichern(self, neu=None):
        if neu:
            self.einst.update(neu)
        self.einst_datei.write_text(json.dumps(self.einst, indent=1, ensure_ascii=False), encoding="utf-8")
        try:
            os.chmod(self.einst_datei, 0o600)
        except OSError:
            pass

    @property
    def basis(self):
        return f"https://{self.einst['host']}"

    @property
    def konfiguriert(self):
        return bool(self.einst.get("host") and self.einst.get("client_id") and self.einst.get("client_secret"))

    @property
    def angemeldet(self):
        return self.token_datei.exists()

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def anfrage(self, url, methode="GET", daten=None, kopf=None, roh=False, zeit=60):
        kopf = dict(kopf or {})
        koerper = None
        if daten is not None:
            if roh:
                koerper = daten
            else:
                koerper = json.dumps(daten).encode("utf-8")
                kopf.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(url, data=koerper, method=methode, headers=kopf)
        try:
            with urllib.request.urlopen(req, timeout=zeit) as antwort:
                inhalt = antwort.read()
                try:
                    return antwort.status, json.loads(inhalt) if inhalt else None
                except ValueError:
                    return antwort.status, inhalt.decode("utf-8", "replace")
        except urllib.error.HTTPError as f:
            inhalt = f.read().decode("utf-8", "replace")
            try:
                return f.code, json.loads(inhalt)
            except ValueError:
                return f.code, inhalt
        except urllib.error.URLError as f:
            raise ApiFehler(f"{self.einst['host']} nicht erreichbar - {f.reason}")
        except (socket.timeout, TimeoutError):
            raise ApiFehler("Zeitueberschreitung - der Server antwortet nicht.")

    def erreichbar(self):
        """(ok, text) - Erreichbarkeit und API-Versionen ohne Login."""
        try:
            status, antwort = self.anfrage(
                f"{self.basis}/d2l/api/versions/", zeit=15)
        except ApiFehler as f:
            return False, str(f)
        if status != 200 or not isinstance(antwort, list):
            return False, f"Antwort {status}: {str(antwort)[:200]}"
        info = {e.get("ProductCode"): e.get("LatestVersion") for e in antwort}
        return True, f"API erreichbar. Neueste Versionen: " + ", ".join(f"{k} {v}" for k, v in info.items())

    # ------------------------------------------------------------------
    # OAuth
    # ------------------------------------------------------------------

    def _zertifikat_sichern(self):
        if self.zert.exists() and self.schluessel.exists():
            return
        self.log("Erzeuge einmalig ein Zertifikat fuer localhost ...")
        e = subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-sha256", "-days", "3650", "-nodes",
            "-keyout", str(self.schluessel), "-out", str(self.zert), "-subj", "/CN=localhost",
            "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"], capture_output=True, text=True)
        if e.returncode != 0:
            raise ApiFehler("openssl konnte kein Zertifikat erzeugen:\n" + e.stderr)
        os.chmod(self.schluessel, 0o600)

    def anmeldung_starten(self):
        """Startet den Rueckruf-Empfaenger und liefert die Anmelde-Adresse.

        Danach anmeldung_status() abfragen, bis 'fertig' oder 'fehler'.
        """
        if not self.konfiguriert:
            raise ApiFehler("Brightspace-Adresse, Client-ID und Client-Secret fehlen in den Einstellungen.")
        redirect = self.einst["redirect"]
        r = urllib.parse.urlparse(redirect)
        port = r.port or (443 if r.scheme == "https" else 80)
        tls = r.scheme == "https"

        zustand = secrets.token_urlsafe(16)
        werte = {"response_type": "code", "client_id": self.einst["client_id"],
                 "redirect_uri": redirect, "scope": self.einst["scopes"], "state": zustand}
        pruefer = None
        if self.einst.get("pkce"):
            pruefer = base64.urlsafe_b64encode(secrets.token_bytes(40)).decode().rstrip("=")
            werte["code_challenge"] = base64.urlsafe_b64encode(
                hashlib.sha256(pruefer.encode()).digest()).decode().rstrip("=")
            werte["code_challenge_method"] = "S256"
        url = AUTH_ENDPUNKT + "?" + urllib.parse.urlencode(werte)

        probe = socket.socket()
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            raise ApiFehler(f"Port {port} ist belegt. Beende das Programm, das ihn benutzt "
                            f"(Terminal: lsof -i :{port}), oder trag in Brightspace und hier "
                            f"eine Redirect-Adresse mit freiem Port ein.")
        finally:
            probe.close()

        zustand_box = {"code": None, "state": None, "fehler": None}

        class Rueckruf(http.server.BaseHTTPRequestHandler):
            def do_GET(s):
                teile = urllib.parse.urlparse(s.path)
                w = urllib.parse.parse_qs(teile.query)
                if "code" not in w and "error" not in w:
                    s.send_response(204); s.end_headers(); return
                zustand_box["code"] = w.get("code", [None])[0]
                zustand_box["state"] = w.get("state", [None])[0]
                zustand_box["fehler"] = w.get("error", [None])[0]
                s.send_response(200)
                s.send_header("Content-Type", "text/html; charset=utf-8")
                s.end_headers()
                text = ("<h2>Geschafft.</h2><p>Du kannst dieses Fenster schliessen und zu bskitool "
                        "zurueckgehen.</p>")
                if zustand_box["fehler"]:
                    text = f"<h2>Brightspace meldet einen Fehler</h2><p><b>{zustand_box['fehler']}</b></p>"
                s.wfile.write(f"<html><body style='font-family:system-ui;padding:60px'>{text}</body></html>".encode())

            def log_message(s, *_):
                pass

        class Server(http.server.ThreadingHTTPServer):
            daemon_threads = True

            def handle_error(s, *_):
                pass

        server = Server(("localhost", port), Rueckruf)
        if tls:
            self._zertifikat_sichern()
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(certfile=str(self.zert), keyfile=str(self.schluessel))
            server.socket = ctx.wrap_socket(server.socket, server_side=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self._anmeldung = {"server": server, "box": zustand_box, "state": zustand,
                           "pruefer": pruefer, "url": url, "start": time.time(), "tls": tls,
                           "ergebnis": None}
        return url

    def anmeldung_code_einreichen(self, adresse):
        """Notausgang: die komplette Rueckleitungs-Adresse von Hand einreichen."""
        if not self._anmeldung:
            raise ApiFehler("Keine Anmeldung gestartet.")
        w = urllib.parse.parse_qs(urllib.parse.urlparse(adresse.strip()).query)
        box = self._anmeldung["box"]
        box["code"] = w.get("code", [None])[0]
        box["state"] = w.get("state", [None])[0]
        box["fehler"] = w.get("error", [None])[0]
        if not box["code"]:
            raise ApiFehler("In der Adresse steckt kein 'code='.")
        return self.anmeldung_status()

    def anmeldung_status(self):
        """'wartet' | 'fertig' | 'fehler: ...'"""
        a = self._anmeldung
        if not a:
            return "fehler: keine Anmeldung gestartet"
        if a["ergebnis"]:
            return a["ergebnis"]
        box = a["box"]
        if not box["code"] and not box["fehler"]:
            if time.time() - a["start"] > 600:
                a["server"].shutdown()
                a["ergebnis"] = "fehler: Zeit abgelaufen (10 Minuten)"
                return a["ergebnis"]
            return "wartet"
        a["server"].shutdown()
        if box["fehler"]:
            a["ergebnis"] = (f"fehler: Brightspace lehnt ab: {box['fehler']} - meist ist ein Scope "
                             f"nicht registriert oder die Redirect-Adresse weicht ab.")
            return a["ergebnis"]
        if box["state"] != a["state"]:
            a["ergebnis"] = "fehler: state stimmt nicht ueberein"
            return a["ergebnis"]
        formular = {"grant_type": "authorization_code", "code": box["code"],
                    "redirect_uri": self.einst["redirect"], "client_id": self.einst["client_id"],
                    "client_secret": self.einst["client_secret"]}
        if a["pruefer"]:
            formular["code_verifier"] = a["pruefer"]
        try:
            status, antwort = self.anfrage(TOKEN_ENDPUNKT, "POST",
                                           urllib.parse.urlencode(formular).encode(),
                                           {"Content-Type": "application/x-www-form-urlencoded"}, roh=True)
        except ApiFehler as f:
            a["ergebnis"] = f"fehler: {f}"
            return a["ergebnis"]
        if status != 200:
            a["ergebnis"] = f"fehler: Token-Abruf fehlgeschlagen ({status}): {antwort}"
            return a["ergebnis"]
        self._token_schreiben(antwort)
        self.log(f"Angemeldet. Erteilte Scopes: {antwort.get('scope', '?')}")
        a["ergebnis"] = "fertig"
        return "fertig"

    def anmelden_konsole(self, oeffnen=True):
        """Kompletter Login fuer die Kommandozeile (blockiert bis fertig)."""
        import webbrowser
        url = self.anmeldung_starten()
        print("\nEs oeffnet sich ein Browserfenster. Melde dich dort an und bestaetige.")
        if self._anmeldung["tls"]:
            print("Der Browser warnt beim Zurueckleiten vor dem Zertifikat - das ist normal:")
            print("'Erweitert' -> 'Weiter zu localhost'.")
        print("\nFalls sich nichts oeffnet, diese Adresse von Hand aufrufen:\n\n" + url + "\n")
        if oeffnen:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        print("Warte auf die Rueckleitung ... (Strg-C bricht ab)")
        for schritt in range(240):
            st = self.anmeldung_status()
            if st != "wartet":
                break
            time.sleep(0.5)
            if schritt == 120:
                print("  ... immer noch nichts. Haengt der Browser auf localhost?")
        else:
            print("\nKeine Rueckleitung angekommen. Notausgang: Steht im Browser eine Adresse,")
            print(f"die mit {self.einst['redirect']}?code=... beginnt? Dann hier einfuegen.")
            adr = input("Adresse (leer = Abbruch): ").strip()
            if not adr:
                raise ApiFehler("Anmeldung abgebrochen.")
            st = self.anmeldung_code_einreichen(adr)
        if st != "fertig":
            raise ApiFehler(st)
        print("Angemeldet.\n")

    def _token_schreiben(self, daten):
        self.token_datei.write_text(json.dumps(daten, indent=1), encoding="utf-8")
        try:
            os.chmod(self.token_datei, 0o600)
        except OSError:
            pass

    def abmelden(self):
        if self.token_datei.exists():
            self.token_datei.unlink()

    _token_cache = None

    def token(self):
        if not self.token_datei.exists():
            raise ApiFehler("Noch nicht angemeldet.")
        daten = json.loads(self.token_datei.read_text(encoding="utf-8"))
        if self._token_cache and self._token_cache[1] > time.time():
            return self._token_cache[0]
        status, _ = self.anfrage(f"{self.basis}/d2l/api/lp/{self.einst['v_lp']}/users/whoami",
                                 kopf={"Authorization": f"Bearer {daten['access_token']}"}, zeit=20)
        if status != 401:
            self._token_cache = (daten["access_token"], time.time() + 300)
            return daten["access_token"]
        status, neu = self.anfrage(TOKEN_ENDPUNKT, "POST", urllib.parse.urlencode({
            "grant_type": "refresh_token", "refresh_token": daten.get("refresh_token", ""),
            "client_id": self.einst["client_id"], "client_secret": self.einst["client_secret"],
        }).encode(), {"Content-Type": "application/x-www-form-urlencoded"}, roh=True)
        if status != 200:
            self.abmelden()
            raise ApiFehler("Die Anmeldung ist abgelaufen - bitte neu anmelden.")
        self._token_schreiben(neu)
        self._token_cache = (neu["access_token"], time.time() + 300)
        return neu["access_token"]

    def api(self, pfad, methode="GET", daten=None, produkt="le", version=None, roh=None):
        version = version or self.einst["v_le" if produkt == "le" else "v_lp"]
        url = f"{self.basis}/d2l/api/{produkt}/{version}{pfad}"
        kopf = {"Authorization": f"Bearer {self.token()}"}
        if roh:
            kopf["Content-Type"] = roh
            return self.anfrage(url, methode, daten, kopf, roh=True)
        return self.anfrage(url, methode, daten, kopf)

    def _pruefen(self, status, antwort, was):
        if status in (200, 201, 204):
            return antwort
        text = antwort if isinstance(antwort, str) else json.dumps(antwort, ensure_ascii=False)
        if status == 403:
            text += "  (403: fehlende Berechtigung - Scope in Brightspace UND Einstellungen pruefen, dann neu anmelden)"
        elif status == 400 and "json-binding-error" in text:
            text += "  (400: Feld passt nicht zur API-Version - bitte diese Zeile weitergeben, dann wird der Aufruf angepasst)"
        raise ApiFehler(f"{was} fehlgeschlagen ({status}): {text[:400]}", status, antwort)

    # ------------------------------------------------------------------
    # Lesen
    # ------------------------------------------------------------------

    def wer(self):
        s, a = self.api("/users/whoami", produkt="lp")
        return self._pruefen(s, a, "whoami")

    def kurse(self):
        """[{id, name, rolle}] aller Kurse, in denen der Nutzer eingeschrieben ist."""
        out = []
        bookmark = ""
        while True:
            s, a = self.api(f"/enrollments/myenrollments/?orgUnitTypeId=3{bookmark}", produkt="lp")
            self._pruefen(s, a, "Kursliste")
            for e in a.get("Items", []):
                ou = e.get("OrgUnit", {})
                out.append({"id": ou.get("Id"), "name": ou.get("Name", ""), "code": ou.get("Code", ""),
                            "rolle": (e.get("Access", {}) or {}).get("ClasslistRoleName") or ""})
            pi = a.get("PagingInfo", {})
            if not pi.get("HasMoreItems") or not pi.get("Bookmark"):
                break
            bookmark = f"&bookmark={pi['Bookmark']}"
        out.sort(key=lambda k: k["name"].lower())
        return out

    def toc(self, kurs):
        """Flache Liste: [{art: modul|thema, id, titel, tiefe, typ, hidden}]"""
        s, a = self.api(f"/{kurs}/content/toc")
        self._pruefen(s, a, "Inhaltsverzeichnis")
        zeilen = []

        def gehe(knoten, tiefe):
            for m in knoten.get("Modules", []) or []:
                zeilen.append({"art": "modul", "id": m.get("ModuleId"), "titel": m.get("Title", ""),
                               "tiefe": tiefe, "hidden": m.get("IsHidden")})
                for t in m.get("Topics", []) or []:
                    zeilen.append({"art": "thema", "id": t.get("TopicId"), "titel": t.get("Title", ""),
                                   "tiefe": tiefe + 1, "typ": t.get("TypeIdentifier") or t.get("ActivityType"),
                                   "hidden": t.get("IsHidden"), "url": t.get("Url")})
                gehe(m, tiefe + 1)
        gehe(a if isinstance(a, dict) else {}, 0)
        return zeilen

    def abgabeordner(self, kurs):
        s, a = self.api(f"/{kurs}/dropbox/folders/")
        self._pruefen(s, a, "Abgabeordner")
        return [{"id": f.get("Id"), "titel": f.get("Name", ""), "note_id": f.get("GradeItemId"),
                 "hidden": f.get("IsHidden")} for f in (a or [])]

    def notenelemente(self, kurs):
        s, a = self.api(f"/{kurs}/grades/")
        self._pruefen(s, a, "Notenelemente")
        return [{"id": g.get("Id"), "titel": g.get("Name", ""), "punkte": g.get("MaxPoints"),
                 "typ": g.get("GradeType")} for g in (a or [])]

    def quizze(self, kurs):
        s, a = self.api(f"/{kurs}/quizzes/")
        if s == 404:
            return []
        self._pruefen(s, a, "Quizliste")
        items = a.get("Objects", a) if isinstance(a, dict) else a
        return [{"id": q.get("QuizId"), "titel": q.get("Name", ""), "aktiv": q.get("IsActive")}
                for q in (items or [])]

    # ------------------------------------------------------------------
    # Anlegen
    # ------------------------------------------------------------------

    def modul_anlegen(self, kurs, titel, beschreibung="", sichtbar=False):
        koerper = {"Title": titel, "ShortTitle": titel[:30], "Type": 0,
                   "ModuleStartDate": None, "ModuleEndDate": None, "ModuleDueDate": None,
                   "IsHidden": not sichtbar, "IsLocked": False,
                   "Description": {"Content": beschreibung or "", "Type": "Html"}}
        s, a = self.api(f"/{kurs}/content/root/", "POST", koerper)
        return self._pruefen(s, a, f"Modul '{titel}'")

    _pfade = {}

    def inhaltspfad(self, kurs):
        """Pfad des Kursinhalts, z. B. /content/enforced/12345-KURSCODE/ (aus dem Kursobjekt)."""
        if kurs in self._pfade:
            return self._pfade[kurs]
        pfad = None
        s, a = self.api(f"/courses/{kurs}", produkt="lp")
        if s == 200 and isinstance(a, dict):
            pfad = a.get("Path")
            if not pfad and a.get("Code"):
                pfad = f"/content/enforced/{kurs}-{a['Code']}/"
        if not pfad:
            pfad = f"/content/enforced/{kurs}/"
            self.log(f"Hinweis: Kurspfad nicht ermittelbar, nehme {pfad}")
        if not pfad.endswith("/"):
            pfad += "/"
        self._pfade[kurs] = pfad
        return pfad

    def datei_thema_anlegen(self, kurs, modul_id, titel, pfad, sichtbar=False, unterordner=""):
        """Datei (HTML, xlsx, pdf ...) als Thema hochladen (multipart/mixed)."""
        pfad = Path(pfad)
        if not pfad.is_file():
            raise ApiFehler(f"Datei fehlt: {pfad}")
        basis = self.inhaltspfad(kurs) + (unterordner.strip("/") + "/" if unterordner else "")
        beschreibung = {"Title": titel, "ShortTitle": titel[:30], "Type": 1, "TopicType": 1,
                        "Url": basis + pfad.name,
                        "StartDate": None, "EndDate": None, "DueDate": None,
                        "IsHidden": not sichtbar, "IsLocked": False}
        grenze = uuid.uuid4().hex
        typ = mimetypes.guess_type(pfad.name)[0] or "application/octet-stream"
        teile = [f"--{grenze}".encode(), b"Content-Type: application/json", b"",
                 json.dumps(beschreibung).encode("utf-8"),
                 f"--{grenze}".encode(),
                 f'Content-Disposition: form-data; name=""; filename="{pfad.name}"'.encode("utf-8"),
                 f"Content-Type: {typ}".encode(), b"", pfad.read_bytes(), f"--{grenze}--".encode()]
        koerper = b"\r\n".join(teile)
        ziel = f"/{kurs}/content/modules/{modul_id}/structure/?renameFileIfExists=true"
        s, a = self.api(ziel, "POST", koerper, roh=f"multipart/mixed; boundary={grenze}")
        if s == 400 and unterordner:
            # Unterordner wird evtl. nicht angelegt - direkt in den Kursinhalt
            beschreibung["Url"] = self.inhaltspfad(kurs) + pfad.name
            teile[3] = json.dumps(beschreibung).encode("utf-8")
            s, a = self.api(ziel, "POST", b"\r\n".join(teile), roh=f"multipart/mixed; boundary={grenze}")
        if s == 400:
            a = f"{a}  [Url war {beschreibung['Url']}]"
        return self._pruefen(s, a, f"Thema '{titel}'")

    def link_thema_anlegen(self, kurs, modul_id, titel, url, sichtbar=False, extern=True):
        koerper = {"Title": titel, "ShortTitle": titel[:30], "Type": 1, "TopicType": 3,
                   "Url": url, "StartDate": None, "EndDate": None, "DueDate": None,
                   "IsHidden": not sichtbar, "IsLocked": False,
                   "OpenAsExternalResource": extern}
        s, a = self.api(f"/{kurs}/content/modules/{modul_id}/structure/", "POST", koerper)
        return self._pruefen(s, a, f"Link '{titel}'")

    def notenelement_anlegen(self, kurs, titel, punkte, kategorie_id=None):
        name = notenname(titel)
        koerper = {"MaxPoints": float(punkte), "CanExceedMaxPoints": False, "IsBonus": False,
                   "ExcludeFromFinalGradeCalculation": False, "GradeSchemeId": None,
                   "Name": name, "ShortName": name[:30], "GradeType": "Numeric",
                   "CategoryId": kategorie_id, "Description": {"Content": "", "Type": "Html"}}
        s, a = self.api(f"/{kurs}/grades/", "POST", koerper)
        return self._pruefen(s, a, f"Notenelement '{titel}'")

    def abgabeordner_anlegen(self, kurs, titel, anweisung="", punkte=None, note_id=None,
                             faellig=None, sichtbar=False):
        koerper = {"CategoryId": None, "Name": titel,
                   "CustomInstructions": {"Content": anweisung or "", "Type": "Html"},
                   "Availability": None, "GroupTypeId": None, "DueDate": faellig,
                   "DisplayInCalendar": False, "NotificationEmail": None,
                   "IsHidden": not sichtbar, "Assessment": None, "GradeItemId": None}
        if punkte:
            koerper["Assessment"] = {"ScoreDenominator": float(punkte)}
        if note_id:
            koerper["GradeItemId"] = note_id
        s, a = self.api(f"/{kurs}/dropbox/folders/", "POST", koerper)
        if s == 400:
            # Aeltere Instanzen: nur die Pflichtfelder
            minimal = {"Name": titel, "CustomInstructions": koerper["CustomInstructions"],
                       "Availability": None, "GroupTypeId": None, "DueDate": faellig,
                       "DisplayInCalendar": False, "NotificationEmail": None, "IsHidden": not sichtbar}
            s2, a2 = self.api(f"/{kurs}/dropbox/folders/", "POST", minimal)
            if s2 in (200, 201):
                if punkte or note_id:
                    self.log(f"Hinweis: '{titel}' ohne Punkte/Notenverknuepfung angelegt - bitte in Brightspace nachtragen.")
                return a2
        return self._pruefen(s, a, f"Abgabeordner '{titel}'")

    def quiz_anlegen(self, kurs, titel, beschreibung="", note_id=None, versuche=1, sichtbar=False,
                     faellig=None):
        """Quiz-Huelle (ohne Fragen - dafuer gibt es keine API). Versucht mehrere LE-Versionen."""
        koerper = {
            "Name": titel, "IsActive": sichtbar, "SortOrder": 0, "AutoExportToGrades": bool(note_id),
            "GradeItemId": note_id, "IsAutoSetGraded": True,
            "Instructions": {"Text": {"Content": "", "Type": "Html"}, "IsDisplayed": False},
            "Description": {"Text": {"Content": beschreibung or "", "Type": "Html"}, "IsDisplayed": bool(beschreibung)},
            "Header": {"Text": {"Content": "", "Type": "Html"}, "IsDisplayed": False},
            "Footer": {"Text": {"Content": "", "Type": "Html"}, "IsDisplayed": False},
            "StartDate": None, "EndDate": None, "DueDate": faellig,
            "DisplayInCalendar": False,
            "AttemptsAllowed": {"IsUnlimited": versuche == 0, "NumberOfAttemptsAllowed": versuche or None},
            "LateSubmissionInfo": {"LateSubmissionOption": 0, "LateLimitMinutes": None},
            "SubmissionTimeLimit": {"IsEnforced": False, "ShowClock": False, "TimeLimitValue": 120},
            "SubmissionGracePeriod": 5, "Password": None, "NotificationEmail": None,
            "CalcTypeId": 1, "RestrictIPAddressRange": [], "CategoryId": None,
            "PreventMovingBackwards": False, "Shuffle": False, "AllowHints": False,
            "DisableRightClick": False, "DisablePagerAndAlerts": False,
            "ActivityId": None, "AllowOnlyUsersWithSpecialAccess": False,
            "IsRetakeIncorrectOnly": False, "PagingTypeId": 0, "DeductionPercentage": None,
            "StudyGuideId": None,
        }
        fehler = None
        for v in ("1.84", "1.83", "1.82", "1.81", "1.80", self.einst["v_le"]):
            s, a = self.api(f"/{kurs}/quizzes/", "POST", koerper, version=v)
            if s in (200, 201):
                return a
            fehler = (s, a)
            if s == 403:
                break
        raise ApiFehler(f"Quiz '{titel}' fehlgeschlagen ({fehler[0]}): {str(fehler[1])[:300]}", *fehler)

    # ------------------------------------------------------------------
    # Loeschen
    # ------------------------------------------------------------------

    def modul_loeschen(self, kurs, modul_id):
        s, a = self.api(f"/{kurs}/content/modules/{modul_id}", "DELETE")
        return self._pruefen(s, a, f"Modul {modul_id} loeschen")

    def thema_loeschen(self, kurs, thema_id):
        s, a = self.api(f"/{kurs}/content/topics/{thema_id}", "DELETE")
        return self._pruefen(s, a, f"Thema {thema_id} loeschen")

    def abgabeordner_loeschen(self, kurs, ordner_id):
        s, a = self.api(f"/{kurs}/dropbox/folders/{ordner_id}", "DELETE")
        return self._pruefen(s, a, f"Abgabeordner {ordner_id} loeschen")

    def notenelement_loeschen(self, kurs, note_id):
        s, a = self.api(f"/{kurs}/grades/{note_id}", "DELETE")
        return self._pruefen(s, a, f"Notenelement {note_id} loeschen")

    def quiz_loeschen(self, kurs, quiz_id):
        s, a = self.api(f"/{kurs}/quizzes/{quiz_id}", "DELETE")
        return self._pruefen(s, a, f"Quiz {quiz_id} loeschen")
