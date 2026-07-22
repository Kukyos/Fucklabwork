"""AutoLAB DBMS pipeline — run real SQL, capture real output, render clean
screenshots, drop a complete per-experiment output folder + filled record.

No pixel surgery, no hallucinated output: every screenshot is a real psql
session against the local PostgreSQL. Adding experiments 2..10 = append an
entry to EXPERIMENTS (a list of (question_no, [psql commands])).

    python Subjects/DBMS/dbms_lab.py 1a

Produces  Subjects/DBMS/output/Ex1A/
    ├─ ex1a.sql            (the script, as run)
    ├─ screenshots/q01.png … qNN.png   (real captures)
    └─ Ex1A_URK24CS1021.docx           (mam's template, filled)
"""
from __future__ import annotations

import io, os, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from assemble import add_code_block
import labshot

URK = "URK24CS1021"
PSQL = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"
DB, USER, HOST = "labdb", "postgres", "127.0.0.1"
PROMPT, CONT = f"{DB}=#", f"{DB}(#"
IMG_W = 6.4

# --- experiment specs: (question_no, [command strings]) -------------------
# commands are exactly what a student types at psql (SQL or \d meta). Multi-
# line SQL keeps its line breaks so the render shows continuation prompts.
P = URK  # table-name prefix

EX1A = {
    "title": "Ex1A", "date": "08/07/2026",
    "reset": [f"{P}_users", f"{P}_venue", f"{P}_event", f"{P}_ticket", f"{P}_location"],
    "questions": [
        (1, [
            f"CREATE TABLE {P}_users (\n    userid numeric(10) PRIMARY KEY,\n    name varchar(255),\n    email varchar(255),\n    password varchar(255),\n    phone varchar(20)\n);",
            f"CREATE TABLE {P}_venue (\n    venueid numeric(10) PRIMARY KEY,\n    name varchar(255),\n    address varchar(255),\n    city varchar(255),\n    state varchar(255),\n    country varchar(255)\n);",
            f"CREATE TABLE {P}_event (\n    eventid numeric(10) PRIMARY KEY,\n    name varchar(255),\n    eventdate date,\n    eventtime timestamp,\n    venueid numeric(10),\n    description varchar(500)\n);",
            f"CREATE TABLE {P}_ticket (\n    ticketid numeric(10) PRIMARY KEY,\n    eventid numeric(10) REFERENCES {P}_event(eventid),\n    userid numeric(10),\n    seatnumber varchar(20),\n    price numeric(10,2),\n    status varchar(50)\n);",
        ]),
        (2, [f"\\d {P}_users", f"\\d {P}_event", f"\\d {P}_venue", f"\\d {P}_ticket"]),
        (3, [f"ALTER TABLE {P}_users ADD COLUMN age numeric(3);"]),
        (4, [f"ALTER TABLE {P}_users DROP COLUMN age;"]),
        (5, [f"ALTER TABLE {P}_venue RENAME TO {P}_location;"]),
        (6, [f"ALTER TABLE {P}_event ALTER COLUMN description TYPE varchar(1000);"]),
        (7, [f"ALTER TABLE {P}_ticket DROP COLUMN seatnumber;"]),
        (8, [f"ALTER TABLE {P}_users ADD CONSTRAINT users_email_uq UNIQUE (email);"]),
        (9, [f"ALTER TABLE {P}_users RENAME COLUMN userid TO id;"]),
        (10, [f"ALTER TABLE {P}_ticket ADD COLUMN barcode varchar(50);"]),
        (11, [f"ALTER TABLE {P}_location ALTER COLUMN name TYPE varchar(300);"]),
        (12, [f"ALTER TABLE {P}_event ADD CONSTRAINT event_venue_fk\n    FOREIGN KEY (venueid) REFERENCES {P}_location(venueid);"]),
        (13, [f"ALTER TABLE {P}_users ADD CONSTRAINT users_id_chk CHECK (id BETWEEN 101 AND 105);"]),
        (14, [f"ALTER TABLE {P}_users ADD CONSTRAINT users_phone_uq UNIQUE (phone);"]),
        (15, [f"TRUNCATE TABLE {P}_users;"]),
    ],
    "template_glob": "Ex. No. 1A*Creating and Managing Tables.docx",
}
EXPERIMENTS = {"1a": EX1A}


def psql(cmd: str) -> str:
    env = {**os.environ, "PGPASSWORD": "postgres"}
    r = subprocess.run([PSQL, "-U", USER, "-h", HOST, "-d", DB, "-c", cmd],
                       capture_output=True, text=True, env=env)
    return (r.stdout + r.stderr).rstrip("\n")


def format_cmd(cmd: str, out: str) -> list[str]:
    cl = cmd.strip("\n").split("\n")
    lines = [f"{PROMPT} {cl[0]}"] + [f"{CONT} {c}" for c in cl[1:]]
    if out:
        lines += out.split("\n")
    return lines


def run_question(commands: list[str]) -> tuple[str, bytes]:
    """Execute all commands of one question; return (code_text, screenshot)."""
    transcript: list[str] = []
    for c in commands:
        transcript += format_cmd(c, psql(c))
        transcript.append("")
    transcript.append(PROMPT)                       # trailing cursor prompt
    png = labshot.render_console_text("\n".join(transcript),
                                      title=f"psql — {DB}")
    code_text = "\n".join(c.rstrip(";") + (";" if not c.startswith("\\") else "")
                          for c in commands)
    return code_text, png


def fill_docx(spec: dict, results: list[tuple[str, bytes]], out_path: Path) -> None:
    tmpl = next((REPO / "Subjects").glob(spec["template_glob"]))
    doc = Document(str(tmpl))
    hp = doc.sections[0].header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.add_run(URK).bold = True
    title = next(p for p in doc.paragraphs if p.style.name == "Heading 1")
    dp = title.insert_paragraph_before(); title._p.addnext(dp._p)
    dp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = dp.add_run(f"Date: {spec['date']}"); r.bold = True; r.font.size = Pt(12)
    for p in list(doc.paragraphs):
        t = p.text.strip()
        if t in ("<Query>", "<Output screenshot>"):
            p._p.getparent().remove(p._p)
        elif p.style.name in ("List Paragraph", "Body Text") and not t:
            p._p.getparent().remove(p._p)
    qs = [p for p in doc.paragraphs if p.style.name == "List Paragraph" and p.text.strip()]
    assert len(qs) == len(results), (len(qs), len(results))
    for q, (code, png) in zip(qs, results):
        q.paragraph_format.keep_with_next = True
        marker = len(doc.paragraphs)
        add_code_block(doc, code)
        ip = doc.add_paragraph(); ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ip.paragraph_format.space_after = Pt(10)
        ip.add_run().add_picture(io.BytesIO(png), width=Inches(IMG_W))
        cp = doc.paragraphs[marker]
        q._p.addnext(ip._p); q._p.addnext(cp._p)
    res = next((p for p in doc.paragraphs if p.text.strip().startswith("Result")), None)
    if res:
        res.runs[0].bold = True
        s = res.insert_paragraph_before(); res._p.addnext(s._p)
        s.add_run("The DDL commands were executed and the desired output was obtained.")
    doc.save(str(out_path))


def build(exp_key: str) -> Path:
    spec = EXPERIMENTS[exp_key]
    for t in spec["reset"]:
        psql(f"DROP TABLE IF EXISTS {t} CASCADE;")
    outdir = Path(__file__).parent / "output" / spec["title"]
    shots = outdir / "screenshots"; shots.mkdir(parents=True, exist_ok=True)
    results, sql_lines = [], []
    for n, cmds in spec["questions"]:
        code, png = run_question(cmds)
        (shots / f"q{n:02d}.png").write_bytes(png)
        results.append((code, png))
        sql_lines.append(f"-- {n}\n" + "\n".join(cmds))
    (outdir / f"{spec['title'].lower()}.sql").write_text(
        "\n\n".join(sql_lines), encoding="utf8")
    docx_path = outdir / f"{spec['title']}_{URK}.docx"
    fill_docx(spec, results, docx_path)
    print("wrote", outdir)
    print("  screenshots:", len(results), "| docx:", docx_path.name)
    return outdir


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "1a")
