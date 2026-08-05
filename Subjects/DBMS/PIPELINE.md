# DBMS pipeline — notes to self (Claude)

Maintained across sessions. If I learn something or change the pipeline, update this file — reconcile stale lines, don't just append under them.

## What this is
Cleo's **DBMS lab** = course header **"23CS2014 Database Systems Lab"** (question-set PDFs also say "20CS2016L … B1" — different batch, ignore). Reg no **URK24CS1021**. Generate Cleo's records directly; don't route through the website user flow.

## Engine decision (locked)
**PostgreSQL.** Cleo chose PG over Oracle/MySQL on 22/07/2026. Do NOT switch without asking.
- psql: `C:\Program Files\PostgreSQL\17\bin\psql.exe`
- db `labdb`, user/pw `postgres` / `postgres`, host `127.0.0.1` (set `PGPASSWORD` env).
- The lab's *reference* flavor is Oracle SQL*Plus, but we render **real PostgreSQL** output — it's genuine, reproducible, and Cleo is fine with the PG look.

## Folder layout (reorganized 05/08/2026)
```
Subjects/DBMS/
  PIPELINE.md
  dbms_lab.py          — current, real-run builder. Run everything through this.
  materials/            — teacher-provided originals: templates, question PDFs/PPTX,
                          + "dbms  Record Template.docx" (note the DOUBLE SPACE in the
                          shipped filename — glob it, never type it).
                          dbms_lab.py globs templates from here (MATERIALS = HERE / "materials").
  output/ExN/           — the loose per-experiment writeup (our own layout)
                          { ExN_URK24CS1021.docx + .pdf, exN.sql, exN_commands.txt,
                            screenshots/qNN.png }
  records/ExN/          — the record, in mam's record template's format
                          { ExN_Record_URK24CS1021.docx + .pdf }
  others/URK24CS1006/   — work done for another student. Frozen; nothing here is
                          maintained any more (Cleo: "not 1006 anymore, just my 1021").
  archive/              — deprecated/superseded outputs, kept for history, nothing reads these.
```

**Output vs record — two different artefacts, don't conflate them.**
- *Output* = our own layout: header/footer, Ex.No table, per-question code + screenshot.
  No teacher format was ever imposed on it; the current shape is just what Cleo is happy with.
- *Record* = `materials/dbms  Record Template.docx`, filled. One 2×3 table: header row
  (Ex No + Date | Title | Register Number) and a **single merged body cell** holding
  Aim / Description / Questions / Result. Everything goes inside that one cell —
  python-docx cells duck-type as documents for `add_paragraph`, so `add_code_block`
  works on a cell unchanged. Headings 14pt bold, content 12pt, Times New Roman.

## How to run
```
python Subjects/DBMS/dbms_lab.py 3            # full: runs SQL, then output + record + PDFs
python Subjects/DBMS/dbms_lab.py docs 1a 1b 2 # record + commands.txt + PDFs only, no DB
```
`build()` **drops the experiment's tables** before running, so never re-run an
already-built experiment just to regenerate paperwork — that's what `docs` is for.
It rebuilds query text from the spec and reads the PNGs already in `output/ExN/screenshots/`.

**PDF** = the installed Word via COM (`to_pdf()`, `win32com` + `FileFormat=17`), one
`DispatchEx` instance for the whole batch so an already-open Word isn't hijacked.
Absolute paths only — relative ones fail opaquely. No LibreOffice on this machine.

**Add experiment N** = append one entry to the `EXPERIMENTS` dict in `dbms_lab.py`. Two shapes, pick by whether a teacher template exists:
- **Has a template** (like Ex1A): `"questions": [(question_no, [psql command strings]), ...]`, plus `"template_glob"` pointing at the `.docx` in `materials/`. Goes through `fill_docx()`.
- **No template** (like Exp2 — only a question-set PDF, or nothing at all): `"questions": [(question_no, "question text", [psql command strings]), ...]`, plus `"aim"` / `"desc"` / `"name"` strings. Goes through `build_docx_scratch()`, which builds the record layout from nothing (same header/footer/Ex.No-table conventions as the DSE from-scratch builders). `build()` tells the two shapes apart by tuple length (2 vs 3), automatically.

Multi-line SQL keeps line breaks so the render shows `labdb(#` continuation prompts. Meta commands like `\d table` and `\set VAR val` work via `psql -c`. An optional `"setup"` list on the spec runs silently before the numbered questions (schema/data prep that isn't itself a graded question — see Exp2/Ex1B). `TABLE_DDL` is the one shared constant (the post-Ex1A schema shape) — reuse it in `"setup"` rather than re-typing the CREATE TABLEs a 3rd time. If a question needs transaction state (BEGIN/SAVEPOINT/COMMIT) to survive across statements, put the whole sequence in **one** command string (one `psql()` call = one session) instead of separate list entries — see Ex1B Q11-13.

## The whole point
Run real SQL → capture real stdout → render clean psql screenshots (`labshot.render_console_text`) → assemble docx. **No pixel-patching, no fabricated output.** Satisfies the sir's "no hallucination" rule by construction.

## Postgres port rules (from Cleo's Oracle-style scripts)
- `NUMBER` → `NUMERIC`, `VARCHAR2` → `VARCHAR`
- `RENAME x TO y` → `ALTER TABLE x RENAME TO y`
- `MODIFY col type` → `ALTER COLUMN col TYPE …`
- `DESC t` → `\d t`
- A Postgres `timestamp` column needs a full `'YYYY-MM-DD HH:MM:SS'` value, not a bare time — bit me on Exp2 (see gotchas).

## Gotchas already hit (don't repeat)
- **PG folds unquoted identifiers to lowercase** — `\d URK24CS1021_users` shows `urk24cs1021_users`. That's authentic; leave it.
- Table naming convention Cleo uses: **`URK24CS1021_<name>`** prefix. Ex1A's sequence mutates the schema: after Q5 `venue`→`location`; after Q9 `userid`→`id`; `seatnumber` dropped, `barcode` added, plus UNIQUE/CHECK constraints on `users`. Exp2 needs that end-state schema populated with real rows, but rather than depending on Ex1A having *just* been run, its own `"setup"` recreates the 4 tables directly in that final shape (self-contained, reruns are clean via `"reset"`).
- **A single multi-row `INSERT ... VALUES (...), (...), ...;` is all-or-nothing.** One bad row (e.g. a bare `'19:00:00'` into a `timestamp` column) fails the *entire* statement, inserting zero rows — which then cascades into FK errors on whatever references that table. Caught this on Exp2 Q1 by actually reading the rendered screenshot, not just checking the docx assembled; row counts in the live DB after a build are a cheap sanity check (`SELECT COUNT(*)` per table).
- Oracle reserved-word traps if ever porting back: `user` (ORA-00903) → `users`; `date`/`time` cols → `eventdate`/`eventtime`.
- `build()` **drops the tables first** (reset list) so re-runs are clean.
- `assemble.add_code_block` = one paragraph w/ soft breaks (stays together). `keep_with_next` on each question so it doesn't split from its query across pages.
- `exN.sql` prepends the silent `"setup"` block (under a `-- setup` comment) ahead of the numbered questions, so it *is* standalone-runnable. `exN_commands.txt` covers the same ground in log form — setup, then each question's text as a comment above the commands as typed.
- A spec can set `"strict": True` (Ex3 does) — `build()` then asserts each question's psql output contains no `ERROR` and no `(0 rows)`. That's the cheap guard against gotcha #2 above: a query that silently answers nothing is as wrong as one that errors, and it also catches seed data that doesn't discriminate.

## Ex1B specifics — DML + DCL + TCL (built 24/07/2026)
No docx/PDF template was ever given for Ex1B — the PPTX in `materials/` is just DML reference slides; the actual question set (15 DML/DCL/TCL questions) came from Cleo separately, no fixed record format attached. **Cleo confirmed the teacher never gave a fixed record format for it and mainly cares about proper (real, unedited) screenshots** — so this one goes through `build_docx_scratch()` like Exp2, but the effort went into correct SQL, not record polish.
- Own `"setup"` = `TABLE_DDL` (shared with Exp2, factored out once it was needed twice) + a small seed dataset (2 users, 1 venue, 1 event, 1 ticket) — self-contained, doesn't depend on Exp2/Ex1A's live data.
- The guideline's placeholder values ("UserID 123", "EventID 456") don't fit our schema (`users.id` is CHECK'd to 101–105) — adapted to real seeded ids (102, 401) instead of forcing nonexistent ones.
- **DCL** (GRANT/REVOKE) needs the target role to exist first — `CREATE ROLE x LOGIN;` before granting/revoking to/from it, otherwise Postgres errors. Verified by querying `pg_roles` and `\dp` after the build (all 5 roles created, `mary`'s INSERT grant correctly shows revoked on `\dp`).
- **TCL** (BEGIN/SAVEPOINT/ROLLBACK TO/COMMIT) only holds transaction state within one connection. Since `run_question()` gives each element of a question's command list to its own `psql()` call (= its own connection), a TCL question packs its whole BEGIN…COMMIT sequence as **one multi-statement string** (one list element, newline-separated) instead of separate command strings — same trick Ex1A's Q1 already used for a single multi-line `CREATE TABLE`, just extended to multiple statements. psql prints each statement's result in order within that one session, so the render is still authentic. Verified: ticket 904 (inserted after the savepoint) is correctly absent after `ROLLBACK TO SAVEPOINT sp1`, while 903 (inserted before it) survived.
- Q14/15 (`\set AUTOCOMMIT on/off`) are psql meta-commands, not SQL — produce no output line, which is authentic (not a bug).

## Exp3 specifics — Advanced SQL (built 05/08/2026)
Question set = `materials/Exp No 3 Advanced SQL.pdf` (12 questions, aggregates + GROUP BY + ORDER BY). No record template of its own → the *output* docx goes through `build_docx_scratch()`; the *record* goes through the shared record template like every other experiment.
- The question set assumes two columns the live schema doesn't have: `ticket.seatnumber` (Q7 — Ex1A Q7 dropped it) and an event **end** time (Q4 "time taken", Q6 "more than 10 hours" — the base schema only has a start `eventtime`). Setup restores both with visible `ALTER TABLE`s after `TABLE_DDL` rather than quietly rewording the questions. Both show up in `ex3.sql` / `ex3_commands.txt`.
- Seed is picked so every query *discriminates* — this is the real work, not the SQL:
  - one 2024 event ("Book Fair") among four 2023 ones, so Q2's count means something;
  - three `'reserved'` tickets, so Q8 isn't empty (Exp2's seed only had confirmed/cancelled);
  - three tickets priced ≤ 30 (25.00, 28.50, 30.00), so Q10's 4% branch visibly fires next to the 2% one.
- Q10 renders SELECT → single `CASE` UPDATE → SELECT in one screenshot, so the before/after prices prove the change instead of asserting it.
- Q11 read plainly (`SELECT country, name, address … ORDER BY country`); no GROUP BY/`string_agg` gymnastics — "in each country" is a sort, not an aggregation.

## Deprecated / don't use
- `archive/build_exp1.py` — OLD Oracle-flavored **fake-screenshot** builder (drawn, not run). Superseded by `dbms_lab.py`. Keep only if someone specifically wants the Oracle SQL*Plus look.
- `archive/1A_URK24CS1021.docx`, `archive/1A_URK24CS1030.docx`, `archive/Ex1A_DDL_URK24CS1021.docx` — outputs from the old `build_exp1.py` / the deprecated URK1030→1021 rebrand hack. Superseded by `output/Ex1A/Ex1A_URK24CS1021.docx`. Kept for history only.
- scratchpad `patch.py` — one-off URK1030→1021 rebrand of another student's MariaDB record (monospace NCC + native-glyph paste). Worked but fragile; the real answer is "run it yourself" (this pipeline).
