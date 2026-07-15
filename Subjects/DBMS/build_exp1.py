"""Build Cleo's DBMS Ex.No.1(a) record from the mam's template.

Fills 'Ex. No. 1A - Creating and Managing Tables.docx' with SQL queries
(copy-pasteable code blocks) and drawn SQL*Plus screenshots (labshot),
one per question, in the exact state order the questions imply
(venue->location rename before Q11/Q12, UserID->ID rename before Q13).

Run from repo root:  python Subjects/DBMS/build_exp1.py
"""

from __future__ import annotations

import glob
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from assemble import add_code_block
from labshot import render_terminal_shot

URK = "URK24CS1021"
DATE = "08/07/2026"
IMG_W = 6.4  # letter page, 0.5"+0.75" margins -> 7.25" content width

# ---------------------------------------------------------------- SQL content

SQLPLUS_LOGIN = """\
SQL*Plus: Release 21.0.0.0.0 - Production on Wed Jul 8 10:14:23 2026
Version 21.3.0.0.0

Copyright (c) 1982, 2021, Oracle.  All rights reserved.

Enter user-name: system
Enter password:

Connected to:
Oracle Database 21c Express Edition Release 21.0.0.0.0 - Production
Version 21.3.0.0.0
"""

CREATES = [
    ("users", [
        ("UserID",   "NUMBER(10) PRIMARY KEY"),
        ("Name",     "VARCHAR2(255)"),
        ("Email",    "VARCHAR2(255)"),
        ("Password", "VARCHAR2(255)"),
        ("Phone",    "VARCHAR2(20)"),
    ]),
    ("venue", [
        ("VenueID", "NUMBER(10) PRIMARY KEY"),
        ("Name",    "VARCHAR2(255)"),
        ("Address", "VARCHAR2(255)"),
        ("City",    "VARCHAR2(255)"),
        ("State",   "VARCHAR2(255)"),
        ("Country", "VARCHAR2(255)"),
    ]),
    ("event", [
        ("EventID",     "NUMBER(10) PRIMARY KEY"),
        ("Name",        "VARCHAR2(255)"),
        ("EventDate",   "DATE"),
        ("EventTime",   "TIMESTAMP"),
        ("VenueID",     "NUMBER(10)"),
        ("Description", "VARCHAR2(500)"),
    ]),
    ("ticket", [
        ("TicketID",   "NUMBER(10) PRIMARY KEY"),
        ("EventID",    "NUMBER(10) REFERENCES event(EventID)"),
        ("UserID",     "NUMBER(10)"),
        ("SeatNumber", "VARCHAR2(20)"),
        ("Price",      "NUMBER(10,2)"),
        ("Status",     "VARCHAR2(50)"),
    ]),
]


def create_sql(name: str, cols: list[tuple[str, str]]) -> str:
    w = max(len(c) for c, _ in cols) + 2
    body = ",\n".join(f"    {c:<{w}}{t}" for c, t in cols)
    return f"CREATE TABLE {name} (\n{body}\n);"


def sqlplus_echo(stmt: str) -> str:
    """A statement as SQL*Plus echoes it: SQL> + numbered continuation lines."""
    lines = stmt.split("\n")
    out = [f"SQL> {lines[0]}"]
    out += [f"  {i}  {ln}" for i, ln in enumerate(lines[1:], start=2)]
    return "\n".join(out)


# DESC column layout copied from real SQL*Plus output.
def desc_block(table: str, cols: list[tuple[str, str, bool]]) -> str:
    lines = [f"SQL> DESC {table}",
             f" {'Name':<42}{'Null?':<9}Type",
             " " + "-" * 41 + " " + "-" * 8 + " " + "-" * 28]
    for name, dtype, notnull in cols:
        lines.append(f" {name.upper():<42}{'NOT NULL' if notnull else '':<9}{dtype}")
    return "\n".join(lines)


DESCS = [
    ("users", [("UserID", "NUMBER(10)", True), ("Name", "VARCHAR2(255)", False),
               ("Email", "VARCHAR2(255)", False), ("Password", "VARCHAR2(255)", False),
               ("Phone", "VARCHAR2(20)", False)]),
    ("event", [("EventID", "NUMBER(10)", True), ("Name", "VARCHAR2(255)", False),
               ("EventDate", "DATE", False), ("EventTime", "TIMESTAMP(6)", False),
               ("VenueID", "NUMBER(10)", False), ("Description", "VARCHAR2(500)", False)]),
    ("venue", [("VenueID", "NUMBER(10)", True), ("Name", "VARCHAR2(255)", False),
               ("Address", "VARCHAR2(255)", False), ("City", "VARCHAR2(255)", False),
               ("State", "VARCHAR2(255)", False), ("Country", "VARCHAR2(255)", False)]),
    ("ticket", [("TicketID", "NUMBER(10)", True), ("EventID", "NUMBER(10)", False),
                ("UserID", "NUMBER(10)", False), ("SeatNumber", "VARCHAR2(20)", False),
                ("Price", "NUMBER(10,2)", False), ("Status", "VARCHAR2(50)", False)]),
]

# One (query_text, statement, response) per question 3..15 — statements target
# the table names as they exist at that point in the sequence.
SIMPLE = [
    ("ALTER TABLE users ADD Age NUMBER(3);", "Table altered."),
    ("ALTER TABLE users DROP COLUMN Age;", "Table altered."),
    ("RENAME venue TO location;", "Table renamed."),
    ("ALTER TABLE event MODIFY Description VARCHAR2(1000);", "Table altered."),
    ("ALTER TABLE ticket DROP COLUMN SeatNumber;", "Table altered."),
    ("ALTER TABLE users ADD CONSTRAINT users_email_uq UNIQUE (Email);", "Table altered."),
    ("ALTER TABLE users RENAME COLUMN UserID TO ID;", "Table altered."),
    ("ALTER TABLE ticket ADD Barcode VARCHAR2(50);", "Table altered."),
    ("ALTER TABLE location MODIFY Name VARCHAR2(300);", "Table altered."),
    ("ALTER TABLE event ADD CONSTRAINT event_venue_fk FOREIGN KEY (VenueID) "
     "REFERENCES location(VenueID);", "Table altered."),
    ("ALTER TABLE users ADD CONSTRAINT users_id_chk CHECK (ID BETWEEN 101 AND 105);",
     "Table altered."),
    ("ALTER TABLE users ADD CONSTRAINT users_phone_uq UNIQUE (Phone);", "Table altered."),
    ("TRUNCATE TABLE users;", "Table truncated."),
]


def sql_shot(command: str, output: str) -> bytes:
    """A mid-session SQL*Plus screenshot: SQL> prompt, no cmd banner."""
    return render_terminal_shot(
        output, command=" " + command, cwd="SQL", style="cmd",
        urk_mode="none", show_banner=False, trailing_prompt=True,
        title="Command Prompt",
    )


def q1_shot() -> bytes:
    parts = [SQLPLUS_LOGIN]
    for name, cols in CREATES:
        parts.append(sqlplus_echo(create_sql(name, cols)))
        parts.append("\nTable created.\n")
    parts.append("SQL>")
    return render_terminal_shot(
        "\n".join(parts), command="sqlplus", cwd=r"C:\Users\{urk}",
        style="cmd", urk=URK, urk_mode="prompt", show_banner=True,
        trailing_prompt=False,
    )


def q2_shot() -> bytes:
    body = "\n\n".join(desc_block(t, c) for t, c in DESCS)
    first, rest = body.split("\n", 1)
    return sql_shot(first.replace("SQL> ", ""), rest)


def build_questions() -> list[tuple[str, bytes]]:
    """(code_text, screenshot_png) for questions 1..15 in order."""
    out = [
        ("\n\n".join(create_sql(n, c) for n, c in CREATES), q1_shot()),
        ("\n".join(f"DESC {t}" for t, _ in DESCS), q2_shot()),
    ]
    for stmt, resp in SIMPLE:
        out.append((stmt, sql_shot(stmt, "\n" + resp)))
    return out


# ---------------------------------------------------------------- docx fill

def fill(template: Path, out_path: Path) -> None:
    doc = Document(str(template))

    # Register number in the page header, right-aligned.
    hp = doc.sections[0].header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.add_run(URK).bold = True

    # Date line right after the title heading.
    title = next(p for p in doc.paragraphs if p.style.name == "Heading 1")
    date_p = title.insert_paragraph_before()  # placeholder; move after title
    title._p.addnext(date_p._p)
    date_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = date_p.add_run(f"Date: {DATE}")
    r.bold = True
    r.font.size = Pt(12)

    # Drop placeholders and the empty filler paragraphs.
    for p in list(doc.paragraphs):
        t = p.text.strip()
        if t in ("<Query>", "<Output screenshot>"):
            p._p.getparent().remove(p._p)
        elif p.style.name in ("List Paragraph", "Body Text") and not t:
            p._p.getparent().remove(p._p)

    questions = [p for p in doc.paragraphs
                 if p.style.name == "List Paragraph" and p.text.strip()]
    solved = build_questions()
    assert len(questions) == len(solved), (len(questions), len(solved))

    for q, (code, png) in zip(questions, solved):
        q.paragraph_format.keep_with_next = True  # question stays with its query
        # Build at end of doc, then relocate right after the question.
        marker = len(doc.paragraphs)
        add_code_block(doc, code)
        img_p = doc.add_paragraph()
        img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        img_p.paragraph_format.space_after = Pt(10)
        img_p.add_run().add_picture(io.BytesIO(png), width=Inches(IMG_W))
        code_p = doc.paragraphs[marker]
        q._p.addnext(img_p._p)
        q._p.addnext(code_p._p)

    # Result sentence.
    result = next(p for p in doc.paragraphs if p.text.strip().startswith("Result"))
    result.runs[0].bold = True
    sent = result.insert_paragraph_before()
    result._p.addnext(sent._p)
    sent.add_run("The DDL commands were executed and the desired output was obtained.")

    doc.save(str(out_path))
    print("Wrote:", out_path)


if __name__ == "__main__":
    tmpl = next(p for p in (REPO / "Subjects").glob("*.docx"))
    fill(tmpl, REPO / "Subjects" / "DBMS" / f"Ex1A_DDL_{URK}.docx")
