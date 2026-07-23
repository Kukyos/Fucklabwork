"""Build Cleo's DSE Ex-1 record (NumPy & Pandas) from scratch per the
Record Guidelines: run the real Python, capture real output, render terminal
screenshots, assemble the .docx exactly in the guideline's layout.

    python Subjects/DSE/build_dse_ex1.py
"""
from __future__ import annotations

import io, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from assemble import add_code_block
import labshot

HERE = Path(__file__).parent
OUT = HERE / "output" / "Ex1"
URK = "URK24CS1021"
DATE = "23/07/2026"
COURSE = "23CS2025 DATA SCIENCE ECOSYSTEM LAB"
TITLE = "WORKING WITH NUMPY AND PANDAS"
FONT = "Times New Roman"

AIM = ("To develop and implement Python programs that solves real-world problems in "
       "various industries such as HR, logistics, retail, finance, and security using "
       "Numpy and Pandas.")
DESC = ("NumPy (Numerical Python) is a library for efficient numerical computing. It "
        "provides the ndarray, an n-dimensional array object, together with vectorized "
        "operations for indexing, slicing, reshaping and mathematical computation that "
        "are much faster than native Python lists. Pandas is built on top of NumPy and "
        "provides two main data structures \u2014 the Series (a one-dimensional labelled "
        "array) and the DataFrame (a two-dimensional labelled table) \u2014 for handling "
        "and analysing structured, tabular data.")
QUESTION = (
    "Manufacturing Quality Control\n"
    "Analyze hourly defect rates (%) for 24-hour production:\n"
    "\u2022 Create array of defects (random 0.1-5.0)\n"
    "\u2022 Get rate at hour 12 (indexing)\n"
    "\u2022 Slice night shift (20-6)\n"
    "\u2022 Reshape into (3,8) for shift analysis\n"
    "\u2022 Iterate to find problem hours (>3%)\n"
    "\u2022 Join with temp/humidity array (random 24 values)\n"
    "\u2022 Split into 3 shifts\n"
    "\u2022 Find critical defects (>4%)\n"
    "\u2022 Sort defects in ascending order\n"
    "\u2022 Filter acceptable range (0.5-1.5%)\n"
    "Pandas:\n"
    "\u2022 Convert list of products [\"Widget A\", \"Widget B\", \"Gadget\"] to Series\n"
    "\u2022 Convert {\"Product\": [\"Tool X\", \"Tool Y\"], \"Tolerance\": [0.1, 0.2]} to DataFrame")
RESULT = "The exercise shown above has been successfully executed and the output has been verified."


def run(pyfile: str) -> str:
    r = subprocess.run([sys.executable, str(OUT / pyfile)], capture_output=True, text=True)
    return (r.stdout + r.stderr).rstrip("\n")


def shot(pyfile: str, output: str) -> bytes:
    return labshot.render_terminal_shot(
        output, command=f"python {pyfile}", cwd=r"C:\DSE\Ex1", style="cmd",
        urk_mode="none", show_banner=False, trailing_prompt=True, width=1500)


# ---- docx helpers ---------------------------------------------------------
def rfonts(el, name=FONT):
    rpr = el.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rf.set(qn(a), name)


def cell_border(cell):
    pr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for s in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{s}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "6")
        e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
        b.append(e)
    pr.append(b)


def label(doc, text, size=12, space_before=8):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.name = FONT; r.font.size = Pt(size)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(3)
    return p


def body(doc, text, italic=False):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.name = FONT; r.font.size = Pt(12); r.italic = italic
    p.paragraph_format.space_after = Pt(4)
    return p


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "screenshots").mkdir(exist_ok=True)
    np_out, pd_out = run("qc_numpy.py"), run("qc_pandas.py")
    np_png, pd_png = shot("qc_numpy.py", np_out), shot("qc_pandas.py", pd_out)
    (OUT / "screenshots" / "numpy_output.png").write_bytes(np_png)
    (OUT / "screenshots" / "pandas_output.png").write_bytes(pd_png)

    doc = Document()
    normal = doc.styles["Normal"]; normal.font.name = FONT; normal.font.size = Pt(12)
    rfonts(normal.element)
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for m in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(sec, m, Inches(1.0))

    # header: course (left) + reg no (right), bold
    h = sec.header.paragraphs[0]
    h.paragraph_format.tab_stops.add_tab_stop(Cm(15.9), WD_TAB_ALIGNMENT.RIGHT)
    r = h.add_run(COURSE); r.bold = True
    h.add_run("\t"); r2 = h.add_run(URK); r2.bold = True
    pbdr = h._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr"); bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single"); bot.set(qn("w:sz"), "12")
    bot.set(qn("w:space"), "1"); bot.set(qn("w:color"), "000000")
    bd.append(bot); pbdr.append(bd)
    # footer
    f = sec.footer.paragraphs[0]; f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = f.add_run(f"EX-1: {TITLE}"); fr.bold = True

    # Ex.No / Title table
    t = doc.add_table(rows=2, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    rows = [("Ex. No. 1", TITLE), ("Date of Exercise", DATE)]
    widths = (Inches(1.9), Inches(4.35))
    for ri, (a, b) in enumerate(rows):
        for ci, txt in enumerate((a, b)):
            c = t.rows[ri].cells[ci]; c.width = widths[ci]
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = c.paragraphs[0]
            if ri == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cr = p.add_run(txt); cr.font.name = FONT; cr.font.size = Pt(12)
            cr.bold = (ci == 0 or ri == 0)
            cell_border(c)
    doc.add_paragraph()

    label(doc, "Aim"); body(doc, AIM)
    label(doc, "Description (About Numpy & Pandas)"); body(doc, DESC)
    label(doc, "Question:"); body(doc, QUESTION)

    label(doc, "Sample Code:")
    add_code_block(doc, (OUT / "qc_numpy.py").read_text())
    label(doc, "Sample Output:")
    _img(doc, np_png)

    label(doc, "Sample Code:")
    add_code_block(doc, (OUT / "qc_pandas.py").read_text())
    label(doc, "Sample Output:")
    _img(doc, pd_png)

    label(doc, "CODE EXPLANATION LINK:")
    body(doc, "(Youtube / Drive Link)", italic=True)
    label(doc, "Preparation course certificate")
    doc.add_paragraph()  # space for the certificate image
    label(doc, "RESULT"); body(doc, RESULT)

    out_docx = OUT / f"Ex1_{URK}.docx"
    doc.save(str(out_docx))
    print("wrote", OUT)
    print("  screenshots: 2 | docx:", out_docx.name)


def _img(doc, png, width_in=6.2):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    p.add_run().add_picture(io.BytesIO(png), width=Inches(width_in))


if __name__ == "__main__":
    build()
