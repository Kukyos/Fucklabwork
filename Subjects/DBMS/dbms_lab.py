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
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt
from assemble import add_code_block
import labshot

HERE = Path(__file__).parent
MATERIALS = HERE / "materials"  # teacher-provided originals: templates, question PDFs/PPTX
URK = "URK24CS1021"
PSQL = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"
DB, USER, HOST = "labdb", "postgres", "127.0.0.1"
PROMPT, CONT = f"{DB}=#", f"{DB}(#"
IMG_W = 6.4
COURSE = "23CS2014 Database Systems Lab"
FONT = "Times New Roman"

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

# Ex1A leaves the schema mutated (venue->location, userid->id, seatnumber
# dropped, barcode added, + constraints). Later experiments need real rows to
# work with, so each recreates the 4 tables directly in that same final shape
# via TABLE_DDL (self-contained: doesn't depend on Ex1A having just been
# run); "reset" drops them first so reruns are clean.
TABLE_DDL = [
    f"CREATE TABLE {P}_users (\n"
    f"    id numeric(10) PRIMARY KEY CHECK (id BETWEEN 101 AND 105),\n"
    f"    name varchar(255), email varchar(255) UNIQUE,\n"
    f"    password varchar(255), phone varchar(20) UNIQUE\n);",
    f"CREATE TABLE {P}_location (\n"
    f"    venueid numeric(10) PRIMARY KEY, name varchar(300),\n"
    f"    address varchar(255), city varchar(255),\n"
    f"    state varchar(255), country varchar(255)\n);",
    f"CREATE TABLE {P}_event (\n"
    f"    eventid numeric(10) PRIMARY KEY, name varchar(255),\n"
    f"    eventdate date, eventtime timestamp,\n"
    f"    venueid numeric(10) REFERENCES {P}_location(venueid),\n"
    f"    description varchar(1000)\n);",
    f"CREATE TABLE {P}_ticket (\n"
    f"    ticketid numeric(10) PRIMARY KEY,\n"
    f"    eventid numeric(10) REFERENCES {P}_event(eventid),\n"
    f"    userid numeric(10), price numeric(10,2),\n"
    f"    status varchar(50), barcode varchar(50)\n);",
]

EX2 = {
    "title": "Ex2", "name": "BASIC SQL", "date": "24/07/2026",
    "reset": [f"{P}_users", f"{P}_location", f"{P}_event", f"{P}_ticket"],
    "setup": list(TABLE_DDL),
    "aim": "To execute the given basic SQL queries.",
    "desc": ("DML (Data Manipulation Language) statements manipulate the data held "
             "within tables: INSERT adds rows, UPDATE changes existing rows, DELETE "
             "removes rows, and SELECT retrieves rows, optionally filtered with a "
             "WHERE clause (comparison, AND/OR, IS NULL, IN, LIKE, BETWEEN), grouped "
             "with GROUP BY, and ordered with ORDER BY."),
    "questions": [
        (1, "Insert all the fields given in the ticket reservation schema.", [
            f"INSERT INTO {P}_users (id, name, email, password, phone) VALUES\n"
            f"    (101, 'Alice Johnson', 'alice@mail.com', 'pass1', '9000000001'),\n"
            f"    (102, 'Bob Smith', 'bob@mail.com', 'pass2', '9000000002'),\n"
            f"    (103, 'Carol Lee', 'carol@mail.com', 'pass3', '9000000003'),\n"
            f"    (104, 'David Kim', 'david@mail.com', 'pass4', '9000000004'),\n"
            f"    (105, 'Emma Watson', 'emma@mail.com', 'pass5', '9000000005');",
            f"INSERT INTO {P}_location (venueid, name, address, city, state, country) VALUES\n"
            f"    (1, 'Madison Square Garden', '4 Pennsylvania Plaza', 'New York', 'NY', 'USA'),\n"
            f"    (2, 'Wembley Stadium', 'Wembley', 'London', 'England', 'UK'),\n"
            f"    (3, 'Marina Bay Sands', '10 Bayfront Ave', 'Singapore', 'Singapore', 'Singapore');",
            f"INSERT INTO {P}_event (eventid, name, eventdate, eventtime, venueid, description) VALUES\n"
            f"    (1, 'Rock Fest', '2023-08-15', '2023-08-15 19:00:00', 1, 'Outdoor rock concert'),\n"
            f"    (2, 'Tech Conference', '2023-07-20', '2023-07-20 09:00:00', 2, 'Annual tech meetup'),\n"
            f"    (3, 'Jazz Night', '2023-09-05', '2023-09-05 20:00:00', 3, 'Live jazz performance'),\n"
            f"    (4, 'Startup Summit', '2023-06-10', '2023-06-10 10:00:00', 1, 'Startup pitch day');",
            f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode) VALUES\n"
            f"    (1, 1, 101, 150.00, 'confirmed', 'BC1001'),\n"
            f"    (2, 1, 102, 150.00, 'confirmed', 'BC1002'),\n"
            f"    (3, 2, 103, 200.00, 'cancelled', 'BC1003'),\n"
            f"    (4, 3, 104, 120.00, 'confirmed', 'BC1004'),\n"
            f"    (5, 3, 105, 120.00, 'confirmed', 'BC1005'),\n"
            f"    (6, 4, 101, 90.00, 'cancelled', 'BC1006'),\n"
            f"    (7, 2, 102, 200.00, 'confirmed', 'BC1007');",
        ]),
        (2, "Display all the fields in User, Events, Venue and Ticket tables.", [
            f"SELECT * FROM {P}_users;", f"SELECT * FROM {P}_event;",
            f"SELECT * FROM {P}_location;", f"SELECT * FROM {P}_ticket;",
        ]),
        (3, "Retrieve all venues ordered by city and then by country.",
         [f"SELECT * FROM {P}_location ORDER BY city, country;"]),
        (4, "Retrieve total number of users.",
         [f"SELECT COUNT(*) AS total_users FROM {P}_users;"]),
        (5, "Retrieve all events ordered by date and time in descending order.",
         [f"SELECT * FROM {P}_event ORDER BY eventdate DESC, eventtime DESC;"]),
        (6, "Get the average price of tickets for each event.",
         [f"SELECT eventid, AVG(price) AS avg_price\nFROM {P}_ticket GROUP BY eventid;"]),
        (7, "Get the total price and count of tickets for each event.",
         [f"SELECT eventid, SUM(price) AS total_price, COUNT(*) AS ticket_count\n"
          f"FROM {P}_ticket GROUP BY eventid;"]),
        (8, "Count the number of tickets for each event.",
         [f"SELECT eventid, COUNT(*) AS ticket_count\nFROM {P}_ticket GROUP BY eventid;"]),
        (9, "Retrieve a distinct number of users.",
         [f"SELECT COUNT(DISTINCT id) AS distinct_users FROM {P}_users;"]),
        (10, "Retrieve the events conducted after 30/07/2023.",
         [f"SELECT * FROM {P}_event WHERE eventdate > '2023-07-30';"]),
        (11, "Calculate the sum of prices for all confirmed tickets.",
         [f"SELECT SUM(price) AS confirmed_total\nFROM {P}_ticket WHERE status = 'confirmed';"]),
        (12, "Concatenate the user's name and email for display.",
         [f"SELECT name || ' <' || email || '>' AS display FROM {P}_users;"]),
        (13, "Retrieve the venue from the city New York and country USA.",
         [f"SELECT * FROM {P}_location\nWHERE city = 'New York' AND country = 'USA';"]),
        (14, "Retrieve all cities ordered by Country in ascending order.",
         [f"SELECT city, country FROM {P}_location ORDER BY country ASC;"]),
        (15, "Delete the cancelled ticket in the ticket table.",
         [f"DELETE FROM {P}_ticket WHERE status = 'cancelled';"]),
    ],
}

# Ex1B: no docx/PDF template was ever given for this one (materials/ only has
# reference PPTX slides) and Cleo confirmed the teacher never handed out a
# fixed record format for it either -- she mainly wants clean, real
# screenshots. So: from-scratch record like Exp2, but kept minimal; the
# effort goes into correct SQL, not record polish.
#
# The guideline's own placeholder values ("UserID 123", "EventID 456") don't
# fit our schema (users.id is CHECK'd to 101-105) -- adapted to real seeded
# ids instead of forcing 123/456 to exist. TCL questions (11-13) need
# transaction state (BEGIN/SAVEPOINT/COMMIT) to survive across statements,
# which only holds within one psql connection -- so each of those is passed
# as ONE multi-statement command string (one psql() call = one session),
# not a list of separate commands like everywhere else.
EX1B = {
    "title": "Ex1B", "name": "MANAGING TABLES USING DML, DCL AND TCL COMMANDS",
    "date": "24/07/2026",
    "reset": [f"{P}_users", f"{P}_location", f"{P}_event", f"{P}_ticket"],
    "setup": TABLE_DDL + [
        f"INSERT INTO {P}_users (id, name, email, password, phone) VALUES\n"
        f"    (101, 'John Carter', 'john.c@mail.com', 'pass1', '9000000010'),\n"
        f"    (102, 'Mary Ann', 'mary.ann@mail.com', 'pass2', '9000000011');",
        f"INSERT INTO {P}_location (venueid, name, address, city, state, country) VALUES\n"
        f"    (1, 'City Arena', '1 Main St', 'Chicago', 'IL', 'USA');",
        f"INSERT INTO {P}_event (eventid, name, eventdate, eventtime, venueid, description) VALUES\n"
        f"    (401, 'Comic Con', '2023-10-01', '2023-10-01 10:00:00', 1, 'Annual comic convention');",
        f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode) VALUES\n"
        f"    (901, 401, 101, 100.00, 'confirmed', 'BCX001');",
    ],
    "aim": "To execute all commands of Data Manipulation Language, Data Control "
           "Language, and Transaction Control Language to get the desired output.",
    "desc": ("DML statements (INSERT/UPDATE/DELETE) manipulate row data. DCL "
             "statements (GRANT/REVOKE) control access privileges on database "
             "objects for specific roles. TCL statements (COMMIT/ROLLBACK/"
             "SAVEPOINT) control transaction boundaries — COMMIT makes changes "
             "permanent, SAVEPOINT marks a point to roll back to within an open "
             "transaction, and ROLLBACK TO undoes work back to that point without "
             "discarding the whole transaction."),
    "questions": [
        (1, 'Insert a new user into the "User" table.',
         [f"INSERT INTO {P}_users (id, name, email, password, phone)\n"
          f"VALUES (103, 'Nina Patel', 'nina@mail.com', 'pass3', '9000000012');"]),
        (2, "Update the email address of a user with UserID 102.",
         [f"UPDATE {P}_users SET email = 'mary.ann.new@mail.com' WHERE id = 102;"]),
        (3, 'Delete a user with the email "example@example.com".',
         [f"INSERT INTO {P}_users (id, name, email, password, phone)\n"
          f"VALUES (104, 'Temp User', 'example@example.com', 'pass4', '9000000013');",
          f"DELETE FROM {P}_users WHERE email = 'example@example.com';"]),
        (4, 'Insert a new event into the "Event" table.',
         [f"INSERT INTO {P}_event (eventid, name, eventdate, eventtime, venueid, description)\n"
          f"VALUES (402, 'Food Festival', '2023-11-05', '2023-11-05 12:00:00', 1, 'Street food festival');"]),
        (5, "Update the description of an event with EventID 401.",
         [f"UPDATE {P}_event SET description = 'Annual comic convention, now with a cosplay contest'\n"
          f"WHERE eventid = 401;"]),
        (6, 'Grant SELECT privileges on the "User" table to a user named "john".',
         [f"CREATE ROLE john LOGIN;", f"GRANT SELECT ON {P}_users TO john;"]),
        (7, 'Revoke INSERT privileges on the "Event" table from a user named "mary".',
         [f"CREATE ROLE mary LOGIN;", f"GRANT INSERT ON {P}_event TO mary;",
          f"REVOKE INSERT ON {P}_event FROM mary;"]),
        (8, 'Create a new user with the username "jane" and grant them all '
            'privileges on the "Ticket" table.',
         [f"CREATE ROLE jane LOGIN;", f"GRANT ALL PRIVILEGES ON {P}_ticket TO jane;"]),
        (9, "Grant EXECUTE privileges on a stored procedure to a role named \"admin\".",
         [f"CREATE ROLE admin;",
          f"CREATE OR REPLACE PROCEDURE {P}_ticket_count() LANGUAGE sql AS $$ SELECT 1; $$;",
          f"GRANT EXECUTE ON PROCEDURE {P}_ticket_count() TO admin;"]),
        (10, "Revoke all privileges from a user named \"guest\" on all tables in the schema.",
         [f"CREATE ROLE guest LOGIN;",
          f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM guest;"]),
        (11, "Perform commit a transaction in the database.",
         [f"BEGIN;\n"
          f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode)\n"
          f"VALUES (902, 401, 102, 80.00, 'confirmed', 'BCX002');\n"
          f"COMMIT;"]),
        (12, "Perform roll back a transaction to a specific savepoint.",
         [f"BEGIN;\n"
          f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode)\n"
          f"VALUES (903, 401, 103, 95.00, 'confirmed', 'BCX003');\n"
          f"SAVEPOINT sp1;\n"
          f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode)\n"
          f"VALUES (904, 401, 104, 95.00, 'confirmed', 'BCX004');\n"
          f"ROLLBACK TO SAVEPOINT sp1;\n"
          f"COMMIT;\n"
          f"SELECT ticketid FROM {P}_ticket WHERE ticketid IN (903, 904);"]),
        (13, "Perform set a savepoint within a transaction.",
         [f"BEGIN;\n"
          f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode)\n"
          f"VALUES (905, 401, 105, 70.00, 'confirmed', 'BCX005');\n"
          f"SAVEPOINT sp2;\n"
          f"SELECT COUNT(*) AS tickets_so_far FROM {P}_ticket;\n"
          f"COMMIT;"]),
        (14, "Enable autocommit mode in the database.", ["\\set AUTOCOMMIT on"]),
        (15, "Disable autocommit mode in the database.", ["\\set AUTOCOMMIT off"]),
    ],
}
EXPERIMENTS = {"1a": EX1A, "2": EX2, "1b": EX1B}


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
    tmpl = next(MATERIALS.glob(spec["template_glob"]))
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


# ---- from-scratch docx (used when there's no editable teacher template,
# e.g. Exp2 only has a question-set PDF) — same layout conventions as the
# DSE from-scratch builders: header/footer, Ex.No/title table, Aim/
# Description/Question, then one code+screenshot pair per question.
def _rfonts(el, name=FONT):
    rpr = el.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rf.set(qn(a), name)


def _cell_border(cell):
    pr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for s in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{s}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "6")
        e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
        b.append(e)
    pr.append(b)


def _label(doc, text, size=12, space_before=8):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.name = FONT; r.font.size = Pt(size)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(3)
    return p


def _body(doc, text, italic=False):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.name = FONT; r.font.size = Pt(12); r.italic = italic
    p.paragraph_format.space_after = Pt(4)
    return p


def build_docx_scratch(spec: dict, results: list[tuple[str, str, bytes]], out_path: Path) -> None:
    title = spec["title"].upper()
    doc = Document()
    normal = doc.styles["Normal"]; normal.font.name = FONT; normal.font.size = Pt(12)
    _rfonts(normal.element)
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for m in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(sec, m, Inches(1.0))

    h = sec.header.paragraphs[0]
    h.paragraph_format.tab_stops.add_tab_stop(Cm(15.9), WD_TAB_ALIGNMENT.RIGHT)
    r = h.add_run(COURSE); r.bold = True
    h.add_run("\t"); r2 = h.add_run(URK); r2.bold = True
    pbdr = h._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr"); bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single"); bot.set(qn("w:sz"), "12")
    bot.set(qn("w:space"), "1"); bot.set(qn("w:color"), "000000")
    bd.append(bot); pbdr.append(bd)
    f = sec.footer.paragraphs[0]; f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = f.add_run(f"{title}: {spec['name']}"); fr.bold = True

    t = doc.add_table(rows=2, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    rows = [(f"Ex. No. {spec['title'][2:]}", spec["name"]), ("Date of Exercise", spec["date"])]
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
            _cell_border(c)
    doc.add_paragraph()

    _label(doc, "Aim"); _body(doc, spec["aim"])
    _label(doc, "Description"); _body(doc, spec["desc"])

    for n, qtext, code, png in results:
        _label(doc, f"{n}. {qtext}")
        _label(doc, "Sample Code:", size=12, space_before=2)
        add_code_block(doc, code)
        _label(doc, "Sample Output:", size=12, space_before=2)
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        p.add_run().add_picture(io.BytesIO(png), width=Inches(IMG_W))

    _label(doc, "RESULT")
    _body(doc, "The SQL queries were executed and the desired output was obtained.")
    doc.save(str(out_path))


def build(exp_key: str) -> Path:
    spec = EXPERIMENTS[exp_key]
    for t in spec["reset"]:
        psql(f"DROP TABLE IF EXISTS {t} CASCADE;")
    for cmd in spec.get("setup", []):
        psql(cmd)  # silent schema/data setup, not one of the graded questions

    outdir = Path(__file__).parent / "output" / spec["title"]
    shots = outdir / "screenshots"; shots.mkdir(parents=True, exist_ok=True)
    results, sql_lines = [], []
    if spec.get("setup"):
        sql_lines.append("-- setup (schema/data, not itself a graded question)\n"
                          + "\n".join(spec["setup"]))
    has_qtext = len(spec["questions"][0]) == 3
    for entry in spec["questions"]:
        n, qtext, cmds = entry if has_qtext else (entry[0], None, entry[1])
        code, png = run_question(cmds)
        (shots / f"q{n:02d}.png").write_bytes(png)
        results.append((n, qtext, code, png) if has_qtext else (code, png))
        sql_lines.append(f"-- {n}\n" + "\n".join(cmds))
    (outdir / f"{spec['title'].lower()}.sql").write_text(
        "\n\n".join(sql_lines), encoding="utf8")

    docx_path = outdir / f"{spec['title']}_{URK}.docx"
    if "template_glob" in spec:
        fill_docx(spec, results, docx_path)
    else:
        build_docx_scratch(spec, results, docx_path)
    print("wrote", outdir)
    print("  screenshots:", len(results), "| docx:", docx_path.name)
    return outdir


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "1a")
