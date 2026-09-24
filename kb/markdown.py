# -*- coding: utf-8 -*-
"""Kleiner Markdown-nach-HTML-Umsetzer ohne Fremdbibliothek.

Unterstuetzt genau das, was Kursseiten brauchen:
  Ueberschriften, Absaetze, fett/kursiv/code, Links, Bilder, Listen (auch
  Haekchenlisten), nummerierte Listen, Tabellen, Codebloecke, Zitate,
  Trennlinien, Zeilenumbrueche, rohes HTML und Container ::: art ... :::

Container werden nicht hier gestaltet, sondern als <div class="kb-ART"> bzw.
<details> ausgegeben - das Aussehen legt das Theme fest.
"""

import html
import re

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<![*\w])\*(?!\*)(.+?)(?<!\*)\*(?![*\w])")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_KEYCAP = re.compile(r"\[\[([^\]]{1,24})\]\]")

CONTAINER_DETAILS = {"loesung", "hinweis", "tipp"}


def _ascii(t):
    return (t.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
             .replace("ß", "ss"))


def inline(text):
    """Inline-Markdown in einem Textstueck umsetzen (HTML-sicher)."""
    # Platzhalter fuer Code, damit darin nichts weiter interpretiert wird
    codes = []

    def _code(m):
        codes.append(html.escape(m.group(1)))
        return f"\x00{len(codes)-1}\x00"

    text = _INLINE_CODE.sub(_code, text)
    text = html.escape(text, quote=False)
    text = _IMG.sub(lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}">', text)
    text = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    text = _KEYCAP.sub(r"<kbd>\1</kbd>", text)
    text = re.sub(r"  $|\\$", "<br>", text)
    for i, c in enumerate(codes):
        text = text.replace(f"\x00{i}\x00", f"<code>{c}</code>")
    return text


def _table(rows):
    kopf = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    body = []
    for r in rows[2:]:
        body.append([c.strip() for c in r.strip().strip("|").split("|")])
    out = ['<table class="kb-tabelle"><thead><tr>']
    out += [f"<th>{inline(c)}</th>" for c in kopf]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


_LI = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_CHECK = re.compile(r"^\[( |x|X)\]\s+(.*)$")


def _lists(lines):
    """Verschachtelte Listen ueber Einrueckung (Unterliste liegt im <li>)."""
    out = []
    stack = []   # [indent, tag]

    def close_one():
        out.append(f"</{stack[-1][1]}>")
        stack.pop()
        if stack:
            out.append("</li>")

    def close_to(indent):
        while stack and stack[-1][0] > indent:
            close_one()

    def li(text):
        c = _CHECK.match(text)
        if c:
            checked = " checked" if c.group(1).lower() == "x" else ""
            return (f'<li class="kb-check"><label><input type="checkbox"{checked}> '
                    f"{inline(c.group(2))}</label></li>")
        return f"<li>{inline(text)}</li>"

    for ln in lines:
        m = _LI.match(ln)
        if not m:
            # Fortsetzungszeile
            if out and out[-1].endswith("</li>"):
                out[-1] = out[-1][:-5] + " " + inline(ln.strip()) + "</li>"
            continue
        indent = len(m.group(1).replace("\t", "    "))
        tag = "ol" if m.group(2)[0].isdigit() else "ul"
        text = m.group(3)
        if not stack:
            stack.append([indent, tag])
            out.append(f"<{tag}>")
        elif indent > stack[-1][0]:
            # Unterliste: letztes <li> wieder oeffnen
            if out and out[-1].endswith("</li>"):
                out[-1] = out[-1][:-5]
            stack.append([indent, tag])
            out.append(f"<{tag}>")
        else:
            close_to(indent)
            if not stack:
                stack.append([indent, tag])
                out.append(f"<{tag}>")
            elif stack[-1][1] != tag:
                out.append(f"</{stack[-1][1]}>")
                stack[-1][1] = tag
                out.append(f"<{tag}>")
        out.append(li(text))
    while stack:
        close_one()
    return "".join(out)


def to_html(md):
    """Kompletten Markdown-Text in HTML umsetzen."""
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    n = len(lines)
    para = []

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(s.strip() for s in para))}</p>")
            para.clear()

    while i < n:
        ln = lines[i]
        s = ln.strip()

        # Codeblock
        if s.startswith("```"):
            flush()
            lang = s[3:].strip()
            buf = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(buf))}</code></pre>")
            continue

        # Container ::: art [titel]
        if s.startswith(":::") and len(s) > 3:
            flush()
            kopf = s[3:].strip()
            art, _, titel = kopf.partition(" ")
            art = _ascii(art.lower())
            buf = []
            i += 1
            while i < n and lines[i].strip() != ":::":
                buf.append(lines[i])
                i += 1
            i += 1
            innen = to_html("\n".join(buf))
            if art in CONTAINER_DETAILS:
                label = titel or ("Lösung ansehen" if art.startswith("l") else art.capitalize())
                out.append(f'<details class="kb-{art}"><summary>{inline(label)}</summary>'
                           f'<div class="kb-inner">{innen}</div></details>')
            else:
                t = (f'<div class="kb-titel">{inline(titel)}</div>' if titel
                     else '<div class="kb-titel kb-std"></div>')
                out.append(f'<div class="kb-box kb-{art}">{t}{innen}</div>')
            continue

        # Leerzeile
        if not s:
            flush()
            i += 1
            continue

        # Platzhalter (z. B. eingebettetes Quiz) unveraendert durchreichen
        if s.startswith("\x01"):
            flush()
            out.append(s)
            i += 1
            continue

        # Rohes HTML (Zeile beginnt mit Tag)
        if s.startswith("<") and not s.startswith("<br"):
            flush()
            out.append(ln)
            i += 1
            continue

        # Ueberschrift
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", s)
        if m:
            flush()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        # Trennlinie
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush()
            out.append("<hr>")
            i += 1
            continue

        # Tabelle
        if s.startswith("|") and i + 1 < n and re.match(r"^\|?\s*:?-{2,}", lines[i + 1].strip()):
            flush()
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(_table(rows))
            continue

        # Zitat
        if s.startswith(">"):
            flush()
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f"<blockquote>{to_html(chr(10).join(buf))}</blockquote>")
            continue

        # Liste
        if _LI.match(ln):
            flush()
            buf = []
            while i < n and (_LI.match(lines[i]) or
                             (lines[i].strip() and lines[i].startswith((" ", "\t")))):
                buf.append(lines[i])
                i += 1
            out.append(_lists(buf))
            continue

        para.append(ln)
        i += 1

    flush()
    return "\n".join(out)
