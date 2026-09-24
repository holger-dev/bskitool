# -*- coding: utf-8 -*-
"""Schnelltest ohne Brightspace:  python3 -m unittest tests.test_alles"""

import json
import pathlib
import sys
import tempfile
import unittest

HIER = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))

from kb import fallback, kursdatei, markdown, push, render   # noqa: E402
from kb.demo import DemoVerbindung                            # noqa: E402

BEISPIEL = HIER / "kurse" / "beispiel" / "kurs.md"


class Parser(unittest.TestCase):
    def setUp(self):
        self.k = kursdatei.lesen(BEISPIEL.read_text(encoding="utf-8"))

    def test_struktur(self):
        self.assertEqual(self.k.titel, "Beispielkurs – Excel Grundlagen")
        self.assertEqual(len(self.k.module), 2)
        arten = [it.art for _, it in self.k.alle_items()]
        self.assertEqual(arten, ["seite", "datei", "link", "abgabe", "seite", "quiz", "note"])

    def test_quiz_in_seite(self):
        seite = self.k.module[0].items[0]
        self.assertEqual(len(seite.quizze), 1)
        q = seite.quizze[0]
        self.assertEqual([f.typ for f in q.fragen], ["mc", "tf", "ms", "sa"])
        self.assertEqual(q.punkte, 6)
        self.assertIn("\x01QUIZ:", seite.body)
        # Kasten nach dem Quiz gehoert NICHT mehr zum Quiz
        self.assertIn("::: geschafft", seite.body)

    def test_benotetes_quiz(self):
        q = self.k.module[1].items[1].quiz
        self.assertTrue(q.benotet)
        self.assertEqual(q.props.get("versuche"), "2")
        self.assertTrue(q.einleitung.startswith("Zehn Minuten"))

    def test_pruefen(self):
        stufen = [s for s, _ in kursdatei.pruefen(self.k)]
        self.assertNotIn("fehler", stufen)

    def test_fehler_ohne_richtige_antwort(self):
        k = kursdatei.lesen("# M\n## Quiz: Q\nFrage?\n- [ ] a\n- [ ] b\n")
        self.assertIn("fehler", [s for s, _ in kursdatei.pruefen(k)])


class Markdown(unittest.TestCase):
    def test_inline(self):
        self.assertEqual(markdown.inline("**a** *b* `c<d>`"),
                         "<strong>a</strong> <em>b</em> <code>c&lt;d&gt;</code>")

    def test_listen(self):
        h = markdown.to_html("- a\n  - b\n- [x] c")
        self.assertIn("<li>a<ul><li>b</li></ul></li>", h)
        self.assertIn('class="kb-check"', h)

    def test_container(self):
        h = markdown.to_html("::: merke Titel\nText\n:::\n\n::: lösung\nx\n:::")
        self.assertIn('class="kb-box kb-merke"', h)
        self.assertIn('<details class="kb-loesung">', h)

    def test_tabelle(self):
        h = markdown.to_html("| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertIn("<th>a</th>", h)
        self.assertIn("<td>2</td>", h)


class Rendern(unittest.TestCase):
    def test_beide_designs(self):
        k = kursdatei.lesen(BEISPIEL.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as d:
            for design in ("d2l", "dv"):
                meld = []
                plan = render.kurs_rendern(k, BEISPIEL.parent, d, design=design, meldungen=meld)
                self.assertEqual([m for m in meld if m[0] == "fehler"], [])
                html = pathlib.Path(plan[0]["datei"]).read_text(encoding="utf-8")
                self.assertIn("kbPick", html)
                self.assertIn("data:image/png;base64", html)     # Bild eingebettet
                self.assertIn("kb-geschafft", html)
                if design == "d2l":
                    self.assertIn("HTML-Template-Library", html)
                else:
                    self.assertIn('class="dv"', html)
            self.assertTrue((pathlib.Path(d) / "index.html").exists())


class Einspielen(unittest.TestCase):
    def test_demo_lauf_und_rueckgaengig(self):
        k = kursdatei.lesen(BEISPIEL.read_text(encoding="utf-8"))
        verb = DemoVerbindung()
        with tempfile.TemporaryDirectory() as d:
            e = push.Einspieler(verb, k, BEISPIEL.parent, d, 10452, trocken=True)
            e.lauf()
            self.assertEqual(e.angelegt, [])
            e = push.Einspieler(verb, k, BEISPIEL.parent, d, 10452)
            e.lauf()
            self.assertEqual([z for z in e.protokoll if z["status"] == "fehler"], [])
            arten = sorted(o["art"] for o in e.angelegt)
            self.assertEqual(arten.count("note"), 3)      # Abgabe, Quiz, Note
            self.assertEqual(arten.count("modul"), 2)
            self.assertEqual(arten.count("abgabe"), 1)
            self.assertEqual(arten.count("quiz"), 1)
            prot = pathlib.Path(d) / "protokoll.json"
            self.assertTrue(prot.exists())
            self.assertTrue((pathlib.Path(d) / "fragen").is_dir())
            erg = push.rueckgaengig(verb, prot)
            self.assertTrue(all(r[3] in ("geloescht", "schon weg") for r in erg))
            self.assertEqual(json.loads(prot.read_text())["angelegt"], [])
            self.assertEqual(verb.notenelemente(10452), [])

    def test_export(self):
        k = kursdatei.lesen(BEISPIEL.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as d:
            plan = render.kurs_rendern(k, BEISPIEL.parent, d)
            pfad, n = fallback.imscc_export(k, plan, d)
            self.assertTrue(pathlib.Path(pfad).exists())
            self.assertGreaterEqual(n, 5)
            csv = fallback.quiz_csv(k.module[1].items[1].quiz)
            self.assertIn("NewQuestion,MC", csv)
            self.assertIn("NewQuestion,SA", csv)


if __name__ == "__main__":
    unittest.main()
