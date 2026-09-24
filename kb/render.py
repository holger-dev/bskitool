# -*- coding: utf-8 -*-
"""Kursmodell -> HTML-Seiten in zwei Designs.

  d2l   Standard: D2L HTML Template Library V3 (Bootstrap, Lato), wie sie viele
        Schulen als Brightspace-Vorlage nutzen. Zusaetzlich ein kleiner Inline-
        Stil fuer Kaesten, Haekchenlisten und Selbstchecks, damit die Seite
        auch ausserhalb von Brightspace (Vorschau) vernuenftig aussieht.
  dv    Eigenstaendiges Design mit komplettem Inline-CSS (Datenverarbeitung).

Alles ohne Fremdbibliotheken.
"""

import base64
import html
import json
import mimetypes
import pathlib
import re

from . import markdown

# --------------------------------------------------------------------------
# Gemeinsame Bausteine (Kaesten, Selbstcheck)
# --------------------------------------------------------------------------

# Farbschema der Container-Arten: (Rahmen, Hintergrund, Beschriftung)
BOX_ARTEN = {
    "merke":     ("#5b6b7c", "#f4f6f9", "Merke"),
    "ziel":      ("#1f5fa9", "#eaf2fb", "Darum geht es"),
    "input":     ("#a86300", "#fdf3e2", "Input"),
    "auftrag":   ("#1f5fa9", "#eaf2fb", "Arbeitsauftrag"),
    "aufgabe":   ("#1f5fa9", "#eaf2fb", "Aufgabe"),
    "geschafft": ("#1c7a4a", "#e8f6ee", "Geschafft, wenn ..."),
    "achtung":   ("#b3261e", "#fdecec", "Achtung"),
    "warnung":   ("#b3261e", "#fdecec", "Achtung"),
    "extra":     ("#6b3fa0", "#f1ebfa", "Schon fertig? Dann das hier:"),
    "info":      ("#1f5fa9", "#eaf2fb", "Info"),
    "beispiel":  ("#5b6b7c", "#f4f6f9", "Beispiel"),
    "lehrkraft": ("#6b3fa0", "#f1ebfa", "Nur für die Lehrkraft"),
}

def _box_css():
    out = [
        ".kb-box{border-left:5px solid #5b6b7c;background:#f4f6f9;border-radius:0 8px 8px 0;"
        "padding:12px 18px;margin:18px 0}",
        ".kb-box>.kb-titel{font-size:12px;letter-spacing:.1em;text-transform:uppercase;"
        "font-weight:700;margin-bottom:4px}",
        ".kb-box p:first-child,.kb-box .kb-titel+p{margin-top:.2em}",
        ".kb-box p:last-child,.kb-box ul:last-child,.kb-box ol:last-child{margin-bottom:0}",
    ]
    out.append(".kb-titel.kb-std{margin:0}")
    for art, (rahmen, bg, label) in BOX_ARTEN.items():
        out.append(f".kb-{art}{{border-left-color:{rahmen};background:{bg}}}"
                   f".kb-{art}>.kb-titel{{color:{rahmen}}}"
                   f".kb-{art}>.kb-std{{margin-bottom:4px}}"
                   f'.kb-{art}>.kb-std::before{{content:"{label}"}}')
    out += [
        "details.kb-loesung,details.kb-hinweis,details.kb-tipp{border:1px solid #dde4ec;"
        "border-radius:8px;margin:14px 0;background:#fff}",
        "details.kb-loesung>summary,details.kb-hinweis>summary,details.kb-tipp>summary{"
        "cursor:pointer;padding:10px 16px;font-weight:700;background:#f4f6f9;border-radius:8px}",
        "details[open]>summary{border-radius:8px 8px 0 0;border-bottom:1px solid #dde4ec}",
        "details>.kb-inner{padding:12px 16px}",
        ".kb-inner p:last-child{margin-bottom:0}",
        "li.kb-check{list-style:none;margin-left:-1.2em}",
        "li.kb-check label{display:flex;gap:8px;align-items:flex-start;cursor:pointer;margin:0}",
        "li.kb-check input{margin-top:.35em}",
        "table.kb-tabelle{border-collapse:collapse;margin:14px 0;width:auto}",
        "table.kb-tabelle th,table.kb-tabelle td{border:1px solid #dde4ec;padding:6px 12px;"
        "text-align:left;vertical-align:top}",
        "table.kb-tabelle th{background:#f4f6f9}",
        "kbd{border:1px solid #c9d1da;border-bottom-width:2px;border-radius:4px;padding:0 6px;"
        "font-size:.9em;background:#fff;font-family:inherit}",
        "pre{background:#f4f6f9;border:1px solid #dde4ec;border-radius:8px;padding:12px 14px;"
        "overflow-x:auto}",
        "img{max-width:100%;height:auto}",
    ]
    return "\n".join(out)


BOX_CSS = _box_css()

# Selbstcheck ---------------------------------------------------------------

SC_CSS = """
.sc{border:1px solid #dde4ec;border-radius:10px;margin:22px 0;overflow:hidden;background:#fff}
.sc>.sc-top{background:#eef7f1;color:#1c7a4a;border-bottom:1px solid #dde4ec;padding:11px 18px;
    font-weight:700;font-size:15px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.sc>.sc-body{padding:16px 18px}
.sc .sc-einl{margin:0 0 14px;color:#5b6b7c}
.sc .q{margin:0 0 22px}
.sc .q:last-of-type{margin-bottom:6px}
.sc .qt{font-weight:600;margin:0 0 10px}
.sc .qt .pt{font-weight:400;color:#5b6b7c;font-size:.9em}
.sc .opt{display:block;width:100%;box-sizing:border-box;text-align:left;border:1px solid #dde4ec;background:#fff;
    border-radius:8px;padding:10px 14px;margin:6px 0;cursor:pointer;font-family:inherit;
    font-size:15px;color:#15202b;line-height:1.45}
.sc .opt:hover{background:#f4f6f9}
.sc .opt.ok{background:#e8f6ee;border-color:#1c7a4a;font-weight:600}
.sc .opt.no{background:#fdecec;border-color:#b3261e}
.sc .opt.dim{opacity:.55}
.sc label.opt{display:flex;gap:10px;align-items:flex-start}
.sc label.opt input{margin-top:.3em}
.sc .sc-btn{border:1px solid #1f5fa9;background:#1f5fa9;color:#fff;border-radius:8px;
    padding:8px 16px;font-weight:700;cursor:pointer;font-family:inherit;font-size:14px;margin-top:6px}
.sc .sc-btn:disabled{opacity:.5;cursor:default}
.sc input.sa{border:1px solid #c9d1da;border-radius:8px;padding:9px 12px;font-size:15px;
    font-family:inherit;width:100%;max-width:420px;display:block;margin:6px 0}
.sc input.sa.ok{border-color:#1c7a4a;background:#e8f6ee}
.sc input.sa.no{border-color:#b3261e;background:#fdecec}
.sc .fb{margin-top:9px;font-size:14px;padding:9px 13px;border-radius:8px;display:none}
.sc .fb.show{display:block}
.sc .fb.ok{background:#e8f6ee;color:#1c7a4a}
.sc .fb.no{background:#fdecec;color:#b3261e}
.sc .score{border-top:1px solid #dde4ec;padding-top:12px;margin-top:6px;font-weight:700;font-size:15px}
"""

SC_JS = r"""
(function(){
  function norm(s){return String(s||"").trim().toLowerCase().replace(/\s+/g," ").replace(",",".");}
  function box(el){var b=el;while(b&&!(b.classList&&b.classList.contains("sc")))b=b.parentNode;return b;}
  function q(el){var b=el;while(b&&!(b.classList&&b.classList.contains("q")))b=b.parentNode;return b;}
  function done(qe,win,pt){
    var b=box(qe);
    b.dataset.done=(parseInt(b.dataset.done||"0")+1);
    b.dataset.pt=(parseFloat(b.dataset.pt||"0")+(win?pt:0));
    var s=b.querySelector(".score");
    s.textContent="Beantwortet: "+b.dataset.done+" von "+b.dataset.total+
      "  |  Punkte: "+(+b.dataset.pt).toLocaleString("de-DE")+" von "+
      (+b.dataset.max).toLocaleString("de-DE");
    var fb=qe.querySelector(".fb");
    fb.className="fb show "+(win?"ok":"no");
    fb.textContent=(win?(qe.dataset.fbok||"Richtig!"):(qe.dataset.fbno||"Leider nicht."));
  }
  window.kbPick=function(btn){
    var qe=q(btn); if(qe.dataset.done==="1")return; qe.dataset.done="1";
    var right=qe.dataset.right, opts=qe.querySelectorAll(".opt");
    for(var i=0;i<opts.length;i++){opts[i].className="opt "+(opts[i].dataset.i===right?"ok":"dim");}
    var win=btn.dataset.i===right; if(!win)btn.className="opt no";
    done(qe,win,parseFloat(qe.dataset.pt));
  };
  window.kbCheckMs=function(b){
    var qe=q(b); if(qe.dataset.done==="1")return; qe.dataset.done="1"; b.disabled=true;
    var right=qe.dataset.right.split(","), cbs=qe.querySelectorAll("input[type=checkbox]"), win=true;
    for(var i=0;i<cbs.length;i++){
      var soll=right.indexOf(cbs[i].dataset.i)>=0, lab=cbs[i].parentNode;
      if(soll)lab.className="opt ok"; else if(cbs[i].checked)lab.className="opt no"; else lab.className="opt dim";
      if(soll!==cbs[i].checked)win=false; cbs[i].disabled=true;
    }
    done(qe,win,parseFloat(qe.dataset.pt));
  };
  window.kbCheckSa=function(b){
    var qe=q(b); if(qe.dataset.done==="1")return;
    var inp=qe.querySelector("input.sa"), ok=false, ant=JSON.parse(qe.dataset.answers);
    for(var i=0;i<ant.length;i++){if(norm(ant[i])===norm(inp.value))ok=true;}
    qe.dataset.done="1"; b.disabled=true; inp.disabled=true; inp.className="sa "+(ok?"ok":"no");
    if(!ok){var fb=qe.querySelector(".fb"); qe.dataset.fbno=(qe.dataset.fbno||"Leider nicht.")+" Richtig: "+ant[0];}
    done(qe,ok,parseFloat(qe.dataset.pt));
  };
  window.kbEnter=function(e,b){if(e.key==="Enter"){e.preventDefault();kbCheckSa(b);}};
})();
"""


def _attr(s):
    return html.escape(str(s), quote=True)


def _pt(p):
    return ("%g" % p).replace(".", ",")


def selfcheck_html(quiz, scid):
    """Quiz-Objekt -> Selbstcheck-HTML (Bewertung nur clientseitig)."""
    body = ""
    for n, f in enumerate(quiz.fragen, 1):
        qid = f"{scid}-q{n}"
        pt = f'<span class="pt">({_pt(f.punkte)} P)</span>' if f.punkte != 1 else ""
        kopf = f'<p class="qt">{n}. {markdown.inline(f.text)} {pt}</p>'
        attrs = (f'id="{qid}" data-pt="{f.punkte}" data-fbok="{_attr(f.fb_ok)}" '
                 f'data-fbno="{_attr(f.fb_no)}"')
        if f.typ in ("mc", "tf"):
            right = next((i for i, (_, r) in enumerate(f.optionen) if r), 0)
            opts = "".join(
                f'<button type="button" class="opt" data-i="{i}" onclick="kbPick(this)">'
                f'{markdown.inline(t)}</button>' for i, (t, _) in enumerate(f.optionen))
            body += f'<div class="q" {attrs} data-right="{right}">{kopf}{opts}<div class="fb"></div></div>'
        elif f.typ == "ms":
            right = ",".join(str(i) for i, (_, r) in enumerate(f.optionen) if r)
            opts = "".join(
                f'<label class="opt"><input type="checkbox" data-i="{i}"> '
                f'<span>{markdown.inline(t)}</span></label>' for i, (t, _) in enumerate(f.optionen))
            body += (f'<div class="q" {attrs} data-right="{right}">{kopf}'
                     f'<p style="margin:2px 0 6px;font-size:.9em;color:#5b6b7c">Mehrere Antworten können richtig sein.</p>'
                     f'{opts}<button type="button" class="sc-btn" onclick="kbCheckMs(this)">Prüfen</button>'
                     f'<div class="fb"></div></div>')
        else:  # sa
            ans = _attr(json.dumps(f.antworten, ensure_ascii=False))
            body += (f'<div class="q" {attrs} data-answers="{ans}">{kopf}'
                     f'<input class="sa" type="text" placeholder="Deine Antwort" '
                     f'onkeydown="kbEnter(event,this.nextElementSibling)">'
                     f'<button type="button" class="sc-btn" onclick="kbCheckSa(this)">Prüfen</button>'
                     f'<div class="fb"></div></div>')
    einl = f'<p class="sc-einl">{markdown.inline(quiz.einleitung)}</p>' if quiz.einleitung else ""
    n = len(quiz.fragen)
    return (f'<div class="sc" data-total="{n}" data-max="{quiz.punkte}">'
            f'<div class="sc-top"><span>{html.escape(quiz.titel)}</span>'
            f'<span style="font-weight:400;font-size:13px">{n} Fragen &middot; {_pt(quiz.punkte)} Punkte</span></div>'
            f'<div class="sc-body">{einl}{body}'
            f'<div class="score">Beantwortet: 0 von {n}</div></div></div>')


# --------------------------------------------------------------------------
# Bilder einbetten
# --------------------------------------------------------------------------

_SRC = re.compile(r'(<img[^>]*\ssrc=")([^"]+)(")')


def bilder_einbetten(html_text, basis, meldungen=None):
    """Relative Bildpfade als data:-URI einbetten (Brightspace nimmt keine Anhaenge mit)."""
    def _rep(m):
        src = m.group(2)
        if src.startswith(("http://", "https://", "data:", "/")):
            return m.group(0)
        p = pathlib.Path(basis) / src
        if not p.is_file():
            if meldungen is not None:
                meldungen.append(("warnung", f"Bild nicht gefunden: {src}"))
            return m.group(0)
        mt = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        daten = p.read_bytes()
        if len(daten) > 1_500_000 and meldungen is not None:
            meldungen.append(("warnung", f"Bild {src} ist gross ({len(daten)//1024} KB) - Seite wird schwer."))
        return m.group(1) + f"data:{mt};base64," + base64.b64encode(daten).decode() + m.group(3)
    return _SRC.sub(_rep, html_text)


# --------------------------------------------------------------------------
# Designs
# --------------------------------------------------------------------------

DV_CSS = """
:root{--ink:#15202b;--muted:#5b6b7c;--line:#dde4ec;--blue:#1f5fa9;--grey-bg:#f4f6f9}
*{box-sizing:border-box}
body{margin:0;background:#fff}
.dv{font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);line-height:1.6;
    font-size:16px;max-width:900px;margin:0 auto;padding:8px 16px 40px}
.dv h1,.dv h2,.dv h3,.dv h4{line-height:1.25;margin:1.2em 0 .4em}
.dv h2{font-size:22px;border-bottom:1px solid var(--line);padding-bottom:4px}
.dv h3{font-size:18px}
.dv p{margin:.6em 0}
.dv ul,.dv ol{margin:.5em 0;padding-left:1.4em}
.dv li{margin:.35em 0}
.dv code{background:var(--grey-bg);padding:.1em .35em;border-radius:4px;
    font-family:Consolas,"Courier New",monospace;font-size:.93em}
.dv pre code{background:none;padding:0}
.dv a{color:var(--blue)}
.dv blockquote{border-left:4px solid var(--line);margin:1em 0;padding:.2em 1em;color:var(--muted)}
.hd{border-bottom:3px solid var(--ink);padding-bottom:14px;margin-bottom:22px}
.hd .kick{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:700}
.hd h1{font-size:30px;margin:6px 0 0}
.hd .sub{color:var(--muted);margin-top:8px;font-size:15px}
.ft{margin-top:34px;padding-top:14px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
"""

BS28_KOPF = """<!DOCTYPE html>
<html lang="en"><head>
   <meta charset="utf-8">
   <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
   <link rel="stylesheet" href="/shared/HTML-Template-Library/HTML-Templates-V3/pages/../_assets/thirdpartylib/bootstrap-4.3.1/css/bootstrap.min.css">
   <link rel="stylesheet" href="/shared/HTML-Template-Library/HTML-Templates-V3/pages/../_assets/thirdpartylib/fontawesome-free-5.9.0-web/css/all.min.css">
   <link rel="stylesheet" href="/shared/HTML-Template-Library/HTML-Templates-V3/pages/../_assets/css/styles.min.css">
   <link rel="stylesheet" href="/shared/HTML-Template-Library/HTML-Templates-V3/pages/../_assets/css/custom.css">
   <link rel="stylesheet" href="https://s.brightspace.com/lib/fonts/0.6.1/fonts.css">
   <title>{titel}</title>
<style>
body{{font-family:Lato,"Segoe UI",Helvetica,Arial,sans-serif;line-height:1.6;color:#202122;margin:0}}
.kb-seite{{max-width:960px;margin:0 auto;padding:12px 16px 40px}}
.kb-seite h1{{font-size:2rem;margin:.3em 0 .2em}}
.kb-seite h2{{font-size:1.5rem;margin:1.2em 0 .4em}}
.kb-seite h3{{font-size:1.2rem;margin:1em 0 .4em}}
.kb-kick{{font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:#6c757d;font-weight:700}}
.kb-sub{{color:#6c757d;margin-bottom:1.2em}}
.kb-fuss{{margin-top:34px;padding-top:12px;border-top:1px solid #dee2e6;font-size:13px;color:#6c757d}}
code{{background:#f4f6f9;padding:.1em .35em;border-radius:4px;font-size:.93em}}
pre code{{background:none;padding:0}}
blockquote{{border-left:4px solid #dee2e6;margin:1em 0;padding:.2em 1em;color:#6c757d}}
{box}{sc}
</style>
</head><body><div class="container-fluid">
<div class="row"><div class="col-12 banner-img"><img src="/shared/HTML-Template-Library/HTML-Templates-V3/pages/../_assets/img/banner_01.jpg" alt="banner" style="width:100%" onerror="this.parentNode.style.display='none'"></div></div>
<div class="row"><div class="col-sm-10 offset-sm-1 kb-seite">
"""

BS28_FUSS = """</div></div></div>
<script src="/shared/HTML-Template-Library/HTML-Templates-V3/pages/../_assets/thirdpartylib/jquery/jquery-3.3.1.slim.min.js"></script>
<script src="/shared/HTML-Template-Library/HTML-Templates-V3/pages/../_assets/thirdpartylib/popper-js/popper.min.js"></script>
<script src="/shared/HTML-Template-Library/HTML-Templates-V3/pages/../_assets/thirdpartylib/bootstrap-4.3.1/js/bootstrap.min.js"></script>
<script src="/shared/HTML-Template-Library/HTML-Templates-V3/pages/../_assets/js/scripts.min.js"></script>
<script>{sc}</script>
</body></html>
"""


_ERSTES_WORT = re.compile(r"(<p>)(\w[\w.,;:'\"-]*)")


def _kopfzeile(kurs, modul, item):
    kick = html.escape(kurs.titel or "")
    sub = html.escape(item.props.get("kurz", "") or modul.titel)
    return kick, sub


def seite_html(kurs, modul, item, body_html, design=None):
    """Fertige HTML-Seite fuer ein Item (Body ist schon HTML)."""
    design = (design or kurs.design or "d2l").lower()
    if design in ("bs28", "vorlage", "template"):
        design = "d2l"
    titel = html.escape(item.titel)
    kick, sub = _kopfzeile(kurs, modul, item)
    fuss = html.escape(kurs.props.get("fuss", "") or kurs.titel or "")
    if design == "dv":
        return (f'<!DOCTYPE html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
                f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                f'<title>{titel}</title>\n<style>{DV_CSS}{BOX_CSS}{SC_CSS}</style>\n</head>\n<body>\n'
                f'<div class="dv">\n<div class="hd"><div class="kick">{kick}</div><h1>{titel}</h1>'
                f'<div class="sub">{sub}</div></div>\n{body_html}\n'
                f'<div class="ft">{fuss}</div>\n</div>\n<script>{SC_JS}</script>\n</body>\n</html>\n')
    # d2l: Hausregeln der Vorlage - h2 linksbuendig, erstes Wort des Einstiegs fett und gruen
    body_html = re.sub(r"<h2>", '<h2 style="text-align: left;">', body_html)
    body_html = _ERSTES_WORT.sub(r'\1<strong style="color: #45818e;">\2</strong>', body_html, count=1)
    kopf = BS28_KOPF.format(titel=titel, box=BOX_CSS, sc=SC_CSS)
    return (kopf + f'<div class="kb-kick">{kick}</div>\n<h1>{titel}</h1>\n<div class="kb-sub">{sub}</div>\n'
            + body_html + f'\n<div class="kb-fuss">{fuss}</div>\n' + BS28_FUSS.format(sc=SC_JS))


# --------------------------------------------------------------------------
# Kurs rendern
# --------------------------------------------------------------------------

def _body_mit_quizzen(item, scid_basis):
    body = markdown.to_html(item.body)
    for q in item.quizze:
        body = body.replace(f"\x01QUIZ:{q.ident}\x01", selfcheck_html(q, q.ident))
    return body


def item_html(kurs, modul, item, basis=".", meldungen=None, design=None):
    """HTML fuer ein Item: Seite/Quiz -> volle Seite, Abgabe -> schlichte Anweisung."""
    if item.art == "seite":
        fertig = item.props.get("datei", "")
        if fertig:
            # Fertige HTML-Seite unveraendert uebernehmen (nur Bilder einbetten)
            p = pathlib.Path(basis) / fertig
            if not p.is_file():
                if meldungen is not None:
                    meldungen.append(("fehler", f"HTML-Datei nicht gefunden: {fertig}"))
                return ""
            return bilder_einbetten(p.read_text(encoding="utf-8"), p.parent, meldungen)
        body = _body_mit_quizzen(item, item.ident)
        body = bilder_einbetten(body, basis, meldungen)
        return seite_html(kurs, modul, item, body, design)
    if item.art == "quiz":
        q = item.quiz
        hinweis = ""
        if q.benotet:
            hinweis = ('<div class="kb-box kb-info"><div class="kb-titel">Hinweis</div>'
                       '<p>Dieses Quiz wird in Brightspace bewertet. Hier kannst du vorher üben.</p></div>')
        body = hinweis + selfcheck_html(q, q.ident)
        return seite_html(kurs, modul, item, body, design)
    if item.art == "abgabe":
        # Brightspace zeigt die Anweisung im eigenen Rahmen: nur schlichtes HTML
        return markdown.to_html(item.body) if item.body else ""
    return ""


def kurs_rendern(kurs, basis, ausgabe, design=None, meldungen=None):
    """Schreibt alle Seiten nach <ausgabe>/seiten/ und eine index.html zur Vorschau.

    Liefert eine Liste von Eintraegen (dict) fuer Push/Export:
      art, titel, ident, modul, datei (Pfad der HTML/Datei), props, ...
    """
    basis = pathlib.Path(basis)
    ausgabe = pathlib.Path(ausgabe)
    seiten = ausgabe / "seiten"
    seiten.mkdir(parents=True, exist_ok=True)
    meldungen = meldungen if meldungen is not None else []
    plan = []
    for modul in kurs.module:
        for item in modul.items:
            e = {"art": item.art, "titel": item.titel, "ident": item.ident,
                 "modul": modul.ident, "props": dict(item.props)}
            if item.art in ("seite", "quiz"):
                p = seiten / f"{item.ident}.html"
                p.write_text(item_html(kurs, modul, item, basis, meldungen, design), encoding="utf-8")
                e["datei"] = str(p)
                if item.art == "quiz":
                    e["quiz"] = item.quiz
            elif item.art == "datei":
                pfad = item.props.get("datei") or item.titel
                p = basis / pfad
                if not p.is_file():
                    meldungen.append(("fehler", f"Datei nicht gefunden: {pfad} (Modul '{modul.titel}')"))
                e["datei"] = str(p)
                e["titel"] = item.props.get("titel") or p.name
            elif item.art == "abgabe":
                e["anweisung"] = item_html(kurs, modul, item, basis, meldungen, design)
            plan.append(e)
    _index_schreiben(kurs, plan, ausgabe)
    return plan


def _index_schreiben(kurs, plan, ausgabe):
    """Inhaltsverzeichnis fuer die Offline-Vorschau."""
    teile = [f"<h1>{html.escape(kurs.titel or 'Kurs')}</h1>"]
    for modul in kurs.module:
        teile.append(f"<h2>{html.escape(modul.titel)}</h2>")
        if modul.beschreibung:
            teile.append(f"<p class='kb-sub'>{html.escape(modul.beschreibung)}</p>")
        teile.append("<ul>")
        for e in [x for x in plan if x["modul"] == modul.ident]:
            art = e["art"]
            if art in ("seite", "quiz"):
                rel = "seiten/" + pathlib.Path(e["datei"]).name
                teile.append(f'<li><b>{art.capitalize()}:</b> <a href="{rel}" target="vorschau">{html.escape(e["titel"])}</a></li>')
            elif art == "datei":
                teile.append(f'<li><b>Datei:</b> {html.escape(e["titel"])} <code>{html.escape(e["datei"])}</code></li>')
            elif art == "link":
                teile.append(f'<li><b>Link:</b> <a href="{html.escape(e["props"].get("url",""))}">{html.escape(e["titel"])}</a></li>')
            elif art == "abgabe":
                teile.append(f'<li><b>Abgabe:</b> {html.escape(e["titel"])} ({e["props"].get("punkte","-")} P)'
                             f'<div style="margin:6px 0 0 12px;padding:6px 10px;border-left:3px solid #dde4ec">{e.get("anweisung","")}</div></li>')
            elif art == "note":
                teile.append(f'<li><b>Notenelement:</b> {html.escape(e["titel"])} ({e["props"].get("punkte","-")} P)</li>')
        teile.append("</ul>")
    body = "\n".join(teile)
    seite = (f'<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><title>{html.escape(kurs.titel)}</title>'
             f'<style>{DV_CSS}{BOX_CSS}</style></head><body><div class="dv">{body}</div></body></html>')
    (pathlib.Path(ausgabe) / "index.html").write_text(seite, encoding="utf-8")
