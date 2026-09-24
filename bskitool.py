#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bskitool - Brightspace-Kurse aus Markdown bauen und einspielen.

Ohne Argumente startet die Web-Oberflaeche. Sonst:

  python3 bskitool.py pruefen    kurse/x/kurs.md          Datei lesen, Warnungen zeigen
  python3 bskitool.py bauen      kurse/x/kurs.md [dv]     Seiten rendern nach ausgabe/
  python3 bskitool.py export     kurse/x/kurs.md          .imscc + Fragen-CSV bauen
  python3 bskitool.py login                               bei Brightspace anmelden
  python3 bskitool.py wer                                 wer bin ich
  python3 bskitool.py kurse                               meine Kurse (orgUnitId)
  python3 bskitool.py themen     <orgUnitId>              Inhalt eines Kurses mit IDs
  python3 bskitool.py einspielen kurse/x/kurs.md [--kurs 12345] [--trocken]
  python3 bskitool.py rueckgaengig ausgabe/x/protokoll.json
  python3 bskitool.py ui [--port 8765] [--kein-browser]

Nur Python-Standardbibliothek (3.8+).
"""

import pathlib
import sys

HIER = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))

from kb import fallback, kursdatei, push, render          # noqa: E402
from kb.api import ApiFehler, Verbindung                  # noqa: E402


def _kurs(pfad):
    p = pathlib.Path(pfad)
    if not p.is_file():
        sys.exit(f"Kursdatei nicht gefunden: {p}")
    k = kursdatei.lesen(p.read_text(encoding="utf-8"), str(p))
    aus = HIER / "ausgabe" / (p.parent.name if p.parent.name != "kurse" else p.stem)
    return k, p, aus


def _meldungen(m):
    for stufe, text in m:
        print(f"  [{stufe}] {text}")


def main(argv):
    if not argv or argv[0] == "ui":
        from kb import server
        port = 8765
        oeffnen = "--kein-browser" not in argv
        if "--port" in argv:
            port = int(argv[argv.index("--port") + 1])
        server.starten(port, oeffnen)
        return

    was, rest = argv[0], argv[1:]
    verb = Verbindung(HIER / "daten", protokoll=print)

    try:
        if was == "pruefen":
            k, p, aus = _kurs(rest[0])
            print(f"\n{k.titel or '(ohne Titel)'} - {len(k.module)} Module, "
                  f"{sum(len(m.items) for m in k.module)} Eintraege")
            for m in k.module:
                print(f"  # {m.titel}")
                for it in m.items:
                    z = f"    {it.art:<7} {it.titel}"
                    if it.quizze:
                        z += f"  [+{len(it.quizze)} Selbstcheck]"
                    if it.quiz:
                        z += f"  [{len(it.quiz.fragen)} Fragen]"
                    print(z)
            print()
            _meldungen(kursdatei.pruefen(k))

        elif was == "bauen":
            k, p, aus = _kurs(rest[0])
            meld = []
            render.kurs_rendern(k, p.parent, aus, design=rest[1] if len(rest) > 1 else None, meldungen=meld)
            _meldungen(meld)
            print(f"Vorschau: {aus / 'index.html'}")

        elif was == "export":
            k, p, aus = _kurs(rest[0])
            meld = []
            plan = render.kurs_rendern(k, p.parent, aus, meldungen=meld)
            _meldungen(meld)
            pfad, n = fallback.imscc_export(k, plan, aus)
            print(f"Paket: {pfad} ({n} Ressourcen)")
            for q, c in fallback.alle_quiz_csv(k, aus):
                print(f"Fragen-CSV: {c}")

        elif was == "login":
            verb.anmelden_konsole()

        elif was == "wer":
            w = verb.wer()
            print(f"\n  {w.get('FirstName')} {w.get('LastName')}  ({w.get('UniqueName')})\n")

        elif was == "kurse":
            print(f"\n  {'orgUnitId':<10} {'Rolle':<16} Kurs")
            print("  " + "-" * 64)
            for c in verb.kurse():
                print(f"  {str(c['id']):<10} {c['rolle']:<16} {c['name']}")
            print()

        elif was == "themen":
            ou = int(rest[0])
            print(f"\n  Kursinhalt-Pfad: {verb.inhaltspfad(ou)}")
            print(f"\n  {'Art':<6} {'Id':<9} Titel")
            print("  " + "-" * 64)
            for z in verb.toc(ou):
                print(f"  {z['art']:<6} {str(z['id']):<9} {'  ' * z['tiefe']}{z['titel']}"
                      + ("  (verborgen)" if z.get("hidden") else ""))
            print("\n  Abgabeordner:")
            for a in verb.abgabeordner(ou):
                print(f"    {a['id']:<8} {a['titel']}")
            print("  Notenelemente:")
            for n in verb.notenelemente(ou):
                print(f"    {n['id']:<8} {n['titel']} ({n['punkte']} P)")
            print()

        elif was == "einspielen":
            k, p, aus = _kurs(rest[0])
            trocken = "--trocken" in rest
            kurs_id = k.kurs_id
            if "--kurs" in rest:
                kurs_id = int(rest[rest.index("--kurs") + 1])
            if not kurs_id:
                sys.exit("Kein Ziel-Kurs: 'kurs:' in der Datei oder --kurs <orgUnitId>")
            if not trocken:
                antw = input(f"Kurs '{k.titel}' in orgUnitId {kurs_id} anlegen? [j/n] ").strip().lower()
                if antw not in ("j", "y"):
                    print("Abgebrochen.")
                    return
            e = push.Einspieler(verb, k, p.parent, aus, kurs_id, trocken=trocken, log=print)
            e.lauf()
            print(f"\nProtokoll: {aus / 'protokoll.json'}\nNoch zu tun: {aus / 'noch-zu-tun.html'}")

        elif was == "rueckgaengig":
            prot = pathlib.Path(rest[0])
            liste = push.rueckgaengig(verb, prot, nur_zeigen=True)
            if not liste:
                print("Nichts rueckgaengig zu machen.")
                return
            for art, ident, titel, _ in liste:
                print(f"  {art:<7} {str(ident):<8} {titel}")
            print("\n  ACHTUNG: Inhaltsmodule/-themen lassen sich nicht wiederherstellen.")
            if input("  Alles loeschen? Tippe LOESCHEN: ").strip() != "LOESCHEN":
                print("Abgebrochen.")
                return
            push.rueckgaengig(verb, prot, log=print)

        else:
            print(__doc__)
    except ApiFehler as f:
        sys.exit(f"\nFehler: {f}\n")
    except IndexError:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
