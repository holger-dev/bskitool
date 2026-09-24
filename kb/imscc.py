"""
ccbuild.py - Minimaler Generator fuer IMS Common Cartridge 1.3 Pakete (.imscc),
die sich in D2L Brightspace importieren lassen.

Unterstuetzt:
  - Module / Untermodule (organizations)
  - HTML-Inhaltsseiten (webcontent)
  - Quizze (QTI 1.2, CC-Profil): multiple choice, multiple response,
    true/false, fill in the blank, essay
  - Abgabeordner (CC 1.3 assignment extension)
"""

import os
import shutil
import zipfile
from xml.sax.saxutils import escape

CC_NS = "http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p1"


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------

def esc(t):
    return escape(t, {'"': "&quot;", "'": "&apos;"})


def html_in_mattext(html):
    """HTML so kodieren, dass es als texttype=text/html in QTI passt."""
    return escape(html, {'"': "&quot;"})


# --------------------------------------------------------------------------
# Bausteine
# --------------------------------------------------------------------------

class Page:
    kind = "page"

    def __init__(self, ident, title, path, html):
        self.ident = ident
        self.title = title
        self.path = path          # z.B. "web_resources/m1/l1.html"
        self.html = html


class Quiz:
    kind = "quiz"

    def __init__(self, ident, title, questions, description="",
                 max_attempts="unlimited", shuffle=False):
        self.ident = ident
        self.title = title
        self.questions = questions
        self.description = description
        self.max_attempts = max_attempts
        self.shuffle = shuffle
        self.path = f"{ident}/assessment_qti.xml"


class Assignment:
    kind = "assignment"

    def __init__(self, ident, title, html, points=100):
        self.ident = ident
        self.title = title
        self.html = html
        self.points = points
        self.path = f"{ident}/assignment.xml"


class Asset:
    """Beliebige Datei (xlsx, docx, pdf ...), die im Kurs zum Download liegt."""
    kind = "asset"

    def __init__(self, ident, title, src, path):
        self.ident = ident
        self.title = title
        self.src = src        # Quelldatei auf der Platte
        self.path = path      # Zielpfad im Paket


class Item:
    """Knoten im Inhaltsbaum: entweder ein Modul (mit children) oder ein Verweis."""

    def __init__(self, title, resource=None, children=None):
        self.title = title
        self.resource = resource
        self.children = children or []


# --------------------------------------------------------------------------
# Fragen
# --------------------------------------------------------------------------

def mc(ident, text, options, correct, points=1, feedback_ok="", feedback_no=""):
    """Single Choice. options = Liste von Strings, correct = Index (0-basiert)."""
    return dict(kind="mc", ident=ident, text=text, options=options,
                correct=[correct], points=points,
                fb_ok=feedback_ok, fb_no=feedback_no)


def mr(ident, text, options, correct, points=1, feedback_ok="", feedback_no=""):
    """Multiple Response. correct = Liste von Indizes."""
    return dict(kind="mr", ident=ident, text=text, options=options,
                correct=list(correct), points=points,
                fb_ok=feedback_ok, fb_no=feedback_no)


def tf(ident, text, correct_true, points=1, feedback_ok="", feedback_no=""):
    return dict(kind="tf", ident=ident, text=text,
                options=["Wahr", "Falsch"],
                correct=[0 if correct_true else 1], points=points,
                fb_ok=feedback_ok, fb_no=feedback_no)


def fib(ident, text, answers, points=1, feedback_ok="", feedback_no=""):
    """Luecke. answers = Liste akzeptierter Antworten (Gross/Klein egal)."""
    return dict(kind="fib", ident=ident, text=text, answers=list(answers),
                points=points, fb_ok=feedback_ok, fb_no=feedback_no)


def essay(ident, text, points=1, sample=""):
    return dict(kind="essay", ident=ident, text=text, points=points,
                sample=sample, fb_ok="", fb_no="")


# --------------------------------------------------------------------------
# QTI-Erzeugung
# --------------------------------------------------------------------------

_LETTERS = "ABCDEFGHIJ"


def _q_meta(profile, qtype, points):
    return f"""      <itemmetadata>
        <qtimetadata>
          <qtimetadatafield><fieldlabel>cc_profile</fieldlabel><fieldentry>{profile}</fieldentry></qtimetadatafield>
          <qtimetadatafield><fieldlabel>question_type</fieldlabel><fieldentry>{qtype}</fieldentry></qtimetadatafield>
          <qtimetadatafield><fieldlabel>points_possible</fieldlabel><fieldentry>{points}</fieldentry></qtimetadatafield>
          <qtimetadatafield><fieldlabel>original_answer_ids</fieldlabel><fieldentry></fieldentry></qtimetadatafield>
        </qtimetadata>
      </itemmetadata>
"""


def _feedback_blocks(q):
    out = ""
    if q.get("fb_ok"):
        out += f"""      <itemfeedback ident="correct_fb">
        <flow_mat><material><mattext texttype="text/html">{html_in_mattext('<p>' + q['fb_ok'] + '</p>')}</mattext></material></flow_mat>
      </itemfeedback>
"""
    if q.get("fb_no"):
        out += f"""      <itemfeedback ident="general_incorrect_fb">
        <flow_mat><material><mattext texttype="text/html">{html_in_mattext('<p>' + q['fb_no'] + '</p>')}</mattext></material></flow_mat>
      </itemfeedback>
"""
    return out


def _choice_item(q, profile, qtype):
    labels = ""
    for i, opt in enumerate(q["options"]):
        labels += f"""            <response_label ident="{_LETTERS[i]}">
              <material><mattext texttype="text/plain">{esc(opt)}</mattext></material>
            </response_label>
"""
    card = "Single" if q["kind"] in ("mc", "tf") else "Multiple"

    if q["kind"] in ("mc", "tf"):
        cond = f'<varequal respident="response1">{_LETTERS[q["correct"][0]]}</varequal>'
    else:
        parts = []
        for i in range(len(q["options"])):
            if i in q["correct"]:
                parts.append(f'<varequal respident="response1">{_LETTERS[i]}</varequal>')
            else:
                parts.append(f'<not><varequal respident="response1">{_LETTERS[i]}</varequal></not>')
        cond = "<and>" + "".join(parts) + "</and>"

    fb_ok = '\n            <displayfeedback feedbacktype="Response" linkrefid="correct_fb"/>' if q.get("fb_ok") else ""
    fb_no = ""
    if q.get("fb_no"):
        fb_no = """          <respcondition continue="Yes">
            <conditionvar><other/></conditionvar>
            <displayfeedback feedbacktype="Response" linkrefid="general_incorrect_fb"/>
          </respcondition>
"""

    return f"""    <item ident="{q['ident']}" title="{esc(q['text'][:60])}">
{_q_meta(profile, qtype, q['points'])}      <presentation>
        <material><mattext texttype="text/html">{html_in_mattext('<p>' + q['text'] + '</p>')}</mattext></material>
        <response_lid ident="response1" rcardinality="{card}">
          <render_choice>
{labels}          </render_choice>
        </response_lid>
      </presentation>
      <resprocessing>
        <outcomes><decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/></outcomes>
{fb_no}          <respcondition continue="No">
            <conditionvar>{cond}</conditionvar>
            <setvar action="Set" varname="SCORE">100</setvar>{fb_ok}
          </respcondition>
      </resprocessing>
{_feedback_blocks(q)}    </item>
"""


def _fib_item(q):
    conds = "".join(
        f'<varequal respident="response1" case="No">{esc(a)}</varequal>'
        for a in q["answers"]
    )
    cond = f"<or>{conds}</or>" if len(q["answers"]) > 1 else conds
    fb_ok = '\n            <displayfeedback feedbacktype="Response" linkrefid="correct_fb"/>' if q.get("fb_ok") else ""
    fb_no = ""
    if q.get("fb_no"):
        fb_no = """          <respcondition continue="Yes">
            <conditionvar><other/></conditionvar>
            <displayfeedback feedbacktype="Response" linkrefid="general_incorrect_fb"/>
          </respcondition>
"""
    return f"""    <item ident="{q['ident']}" title="{esc(q['text'][:60])}">
{_q_meta('cc.fib.v0p1', 'short_answer_question', q['points'])}      <presentation>
        <material><mattext texttype="text/html">{html_in_mattext('<p>' + q['text'] + '</p>')}</mattext></material>
        <response_str ident="response1" rcardinality="Single">
          <render_fib><response_label ident="answer1" rshuffle="No"/></render_fib>
        </response_str>
      </presentation>
      <resprocessing>
        <outcomes><decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/></outcomes>
{fb_no}          <respcondition continue="No">
            <conditionvar>{cond}</conditionvar>
            <setvar action="Set" varname="SCORE">100</setvar>{fb_ok}
          </respcondition>
      </resprocessing>
{_feedback_blocks(q)}    </item>
"""


def _essay_item(q):
    sample = ""
    if q.get("sample"):
        sample = f"""      <itemfeedback ident="general_fb">
        <flow_mat><material><mattext texttype="text/html">{html_in_mattext('<p>' + q['sample'] + '</p>')}</mattext></material></flow_mat>
      </itemfeedback>
"""
    return f"""    <item ident="{q['ident']}" title="{esc(q['text'][:60])}">
{_q_meta('cc.essay.v0p1', 'essay_question', q['points'])}      <presentation>
        <material><mattext texttype="text/html">{html_in_mattext('<p>' + q['text'] + '</p>')}</mattext></material>
        <response_str ident="response1" rcardinality="Single">
          <render_fib><response_label ident="answer1" rshuffle="No"/></render_fib>
        </response_str>
      </presentation>
      <resprocessing>
        <outcomes><decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/></outcomes>
        <respcondition continue="No">
          <conditionvar><other/></conditionvar>
        </respcondition>
      </resprocessing>
{sample}    </item>
"""


def quiz_xml(quiz):
    items = ""
    for q in quiz.questions:
        if q["kind"] == "mc":
            items += _choice_item(q, "cc.multiple_choice.v0p1", "multiple_choice_question")
        elif q["kind"] == "tf":
            items += _choice_item(q, "cc.true_false.v0p1", "true_false_question")
        elif q["kind"] == "mr":
            items += _choice_item(q, "cc.multiple_response.v0p1", "multiple_answers_question")
        elif q["kind"] == "fib":
            items += _fib_item(q)
        elif q["kind"] == "essay":
            items += _essay_item(q)
        else:
            raise ValueError(q["kind"])

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/ims_qtiasiv1p2 http://www.imsglobal.org/profile/cc/ccv1p3/ccv1p3_qtiasiv1p2p1_v1p0.xsd">
  <assessment ident="{quiz.ident}" title="{esc(quiz.title)}">
    <qtimetadata>
      <qtimetadatafield><fieldlabel>cc_profile</fieldlabel><fieldentry>cc.exam.v0p1</fieldentry></qtimetadatafield>
      <qtimetadatafield><fieldlabel>qmd_assessmenttype</fieldlabel><fieldentry>Examination</fieldentry></qtimetadatafield>
      <qtimetadatafield><fieldlabel>cc_maxattempts</fieldlabel><fieldentry>{quiz.max_attempts}</fieldentry></qtimetadatafield>
    </qtimetadata>
    <rubric>
      <material><mattext texttype="text/html">{html_in_mattext(quiz.description or '')}</mattext></material>
    </rubric>
    <section ident="root_section">
{items}    </section>
  </assessment>
</questestinterop>
"""


def assignment_xml(a):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<assignment xmlns="http://www.imsglobal.org/xsd/imscc_extensions/assignment"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/imscc_extensions/assignment http://www.imsglobal.org/profile/cc/ccv1p3/ccv1p3_assignment_v1p0.xsd"
  identifier="{a.ident}">
  <title>{esc(a.title)}</title>
  <text texttype="text/html">{html_in_mattext(a.html)}</text>
  <gradable points_possible="{a.points}">true</gradable>
  <submission_formats>
    <format type="file"/>
  </submission_formats>
</assignment>
"""


# --------------------------------------------------------------------------
# Manifest + Paket
# --------------------------------------------------------------------------

RES_TYPE = {
    "page": "webcontent",
    "asset": "webcontent",
    "quiz": "imsqti_xmlv1p2/imscc_xmlv1p1/assessment",
    "assignment": "assignment_xmlv1p0",
}


def _items_xml(items, counter, indent=6):
    out = ""
    pad = " " * indent
    for it in items:
        counter[0] += 1
        iid = f"ITEM-{counter[0]:04d}"
        if it.resource is not None:
            out += f'{pad}<item identifier="{iid}" identifierref="{it.resource.ident}">\n'
            out += f"{pad}  <title>{esc(it.title)}</title>\n"
            out += f"{pad}</item>\n"
        else:
            out += f'{pad}<item identifier="{iid}">\n'
            out += f"{pad}  <title>{esc(it.title)}</title>\n"
            out += _items_xml(it.children, counter, indent + 2)
            out += f"{pad}</item>\n"
    return out


def _collect(items, acc):
    for it in items:
        if it.resource is not None:
            acc.append(it.resource)
        _collect(it.children, acc)
    return acc


def build(course_title, tree, outdir, outfile):
    """tree = Liste von Item(). Schreibt outdir/ und packt outfile (.imscc)."""
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir)

    resources = _collect(tree, [])

    # Dateien schreiben
    for r in resources:
        full = os.path.join(outdir, r.path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        if r.kind == "asset":
            shutil.copyfile(r.src, full)
            continue
        if r.kind == "page":
            content = r.html
        elif r.kind == "quiz":
            content = quiz_xml(r)
        elif r.kind == "assignment":
            content = assignment_xml(r)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

    # Ressourcen-Block
    res_xml = ""
    for r in resources:
        rtype = RES_TYPE[r.kind]
        if r.kind == "quiz":
            res_xml += f'    <resource identifier="{r.ident}" type="{rtype}">\n'
            res_xml += f'      <file href="{r.path}"/>\n'
            res_xml += "    </resource>\n"
        else:
            res_xml += f'    <resource identifier="{r.ident}" type="{rtype}" href="{r.path}">\n'
            res_xml += f'      <file href="{r.path}"/>\n'
            res_xml += "    </resource>\n"

    org_items = _items_xml(tree, [0])

    manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="MANIFEST-KURSBAU"
  xmlns="http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p1"
  xmlns:lom="http://ltsc.ieee.org/xsd/imsccv1p3/LOM/resource"
  xmlns:lomimscc="http://ltsc.ieee.org/xsd/imsccv1p3/LOM/manifest"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p1 http://www.imsglobal.org/profile/cc/ccv1p3/ccv1p3_imscp_v1p2_v1p0.xsd http://ltsc.ieee.org/xsd/imsccv1p3/LOM/resource http://www.imsglobal.org/profile/cc/ccv1p3/LOM/ccv1p3_lomresource_v1p0.xsd http://ltsc.ieee.org/xsd/imsccv1p3/LOM/manifest http://www.imsglobal.org/profile/cc/ccv1p3/LOM/ccv1p3_lommanifest_v1p0.xsd">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.3.0</schemaversion>
    <lomimscc:lom>
      <lomimscc:general>
        <lomimscc:title><lomimscc:string language="de-DE">{esc(course_title)}</lomimscc:string></lomimscc:title>
      </lomimscc:general>
    </lomimscc:lom>
  </metadata>
  <organizations>
    <organization identifier="ORG-1" structure="rooted-hierarchy">
      <item identifier="ROOT">
{org_items}      </item>
    </organization>
  </organizations>
  <resources>
{res_xml}  </resources>
</manifest>
"""

    with open(os.path.join(outdir, "imsmanifest.xml"), "w", encoding="utf-8") as f:
        f.write(manifest)

    with zipfile.ZipFile(outfile, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(outdir):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, outdir))

    return outfile, len(resources)
