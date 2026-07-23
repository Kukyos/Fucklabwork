# DBMS pipeline — notes to self (Claude)

Maintained across sessions. If I learn something or change the pipeline, update this file.

## What this is
Cleo's **DBMS lab** = course header **"23CS2014 Database Systems Lab"** (question-set PDFs also say "20CS2016L … B1" — different batch, ignore). Reg no **URK24CS1021**. Generate Cleo's records directly; don't route through the website user flow.

## Engine decision (locked)
**PostgreSQL.** Cleo chose PG over Oracle/MySQL on 22/07/2026. Do NOT switch without asking.
- psql: `C:\Program Files\PostgreSQL\17\bin\psql.exe`
- db `labdb`, user/pw `postgres` / `postgres`, host `127.0.0.1` (set `PGPASSWORD` env).
- The lab's *reference* flavor is Oracle SQL*Plus, but we render **real PostgreSQL** output — it's genuine, reproducible, and Cleo is fine with the PG look.

## How to run
```
python Subjects/DBMS/dbms_lab.py 1a
```
→ `Subjects/DBMS/output/Ex1A/` = { ex1a.sql, screenshots/qNN.png, Ex1A_URK24CS1021.docx }

**Add experiment 2..10** = append one entry to the `EXPERIMENTS` dict in `dbms_lab.py`:
`(question_no, [psql command strings])`. Multi-line SQL keeps line breaks so the render shows `labdb(#` continuation prompts. Meta commands like `\d table` work via `psql -c`. Also need that experiment's numbered-question **.docx template** in this folder + its `template_glob`.

## The whole point
Run real SQL → capture real stdout → render clean psql screenshots (`labshot.render_console_text`) → assemble docx. **No pixel-patching, no fabricated output.** Satisfies the sir's "no hallucination" rule by construction.

## Postgres port rules (from Cleo's Oracle-style scripts)
- `NUMBER` → `NUMERIC`, `VARCHAR2` → `VARCHAR`
- `RENAME x TO y` → `ALTER TABLE x RENAME TO y`
- `MODIFY col type` → `ALTER COLUMN col TYPE …`
- `DESC t` → `\d t`

## Gotchas already hit (don't repeat)
- **PG folds unquoted identifiers to lowercase** — `\d URK24CS1021_users` shows `urk24cs1021_users`. That's authentic; leave it.
- Table naming convention Cleo uses: **`URK24CS1021_<name>`** prefix. Sequence mutates schema: after Q5 `venue`→`location`; after Q9 `userid`→`id`. Later answers must target the renamed objects.
- Oracle reserved-word traps if ever porting back: `user` (ORA-00903) → `users`; `date`/`time` cols → `eventdate`/`eventtime`.
- `build()` **drops the tables first** (reset list) so re-runs are clean.
- Template lives **in this folder** now (moved out of `Subjects/` root). `dbms_lab.py` globs it via `Path(__file__).parent` — keep it that way.
- `assemble.add_code_block` = one paragraph w/ soft breaks (stays together). `keep_with_next` on each question so it doesn't split from its query across pages.

## Deprecated / don't use
- `build_exp1.py` — OLD Oracle-flavored **fake-screenshot** builder (drawn, not run). Superseded by `dbms_lab.py`. Keep only if someone specifically wants the Oracle SQL*Plus look.
- scratchpad `patch.py` — one-off URK1030→1021 rebrand of another student's MariaDB record (monospace NCC + native-glyph paste). Worked but fragile; the real answer is "run it yourself" (this pipeline).
