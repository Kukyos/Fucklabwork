# Subjects — overall pipeline notes to self (Claude)

Maintained across sessions, same as each subject's own `PIPELINE.md`. This file
holds only what's genuinely shared across subjects — reconcile stale lines
when the pattern changes, don't let subject-specific detail creep in here
(that belongs in `<Subject>/PIPELINE.md`).

## What `Subjects/` is
Cleo's own lab records, generated **directly** for her — not the general
AutoLAB product (the `autolab.py`/`server.py`/web-app stack at the repo root,
built for ~500 other students to self-serve). Different audience, different
code path: `Subjects/` is a personal pipeline, skip the site user flow
entirely when working here.

Reg no is always **URK24CS1021**. Each subject gets its own folder:
```
Subjects/
  PIPELINE.md          — this file
  DSE/PIPELINE.md, DBMS/PIPELINE.md, ...  — one per subject
```

## The shared philosophy: run for real, capture real output
Every subject's builder actually executes the code/SQL and captures genuine
stdout — never hand-writes or guesses what output "should" look like. This is
a hard rule from the teachers, not a style preference: content must not sound
AI-written and must contain no hallucinated output. Concretely:
- Code/SQL actually runs (subprocess or in-process `exec`), stdout is
  captured, and a terminal/editor-style PNG is rendered from that real text
  via `labshot.py` (repo root). No pixel-patching, no fabricated screenshots.
- Student-style code: lowercase, light comments, no over-engineering, no
  AI-tell phrasing. Mam/sir are aware Claude is involved — the ask is that
  the *artifact* still reads like something a student organically typed, not
  that it hide its origin.
- Where a question needs data that doesn't naturally exist (e.g. nulls to
  demonstrate imputation on a clean dataset), it's fine to construct it —
  but do it visibly in the code/SQL shown, and keep the fabrication scoped
  to that one demonstration, never as a substitute for a real run.

## Shared building blocks (repo root, used by every subject)
- `labshot.py` — renders real captured text as PNGs: `render_terminal_shot`
  (Windows cmd/PowerShell console look), `render_console_text` (pre-composed
  transcript, auto-fit width — used for psql), `render_code_shot` (VS Code
  editor look).
- `assemble.py` — `add_code_block()` writes code into a docx as one shaded
  monospace paragraph (soft line breaks, so it survives edits/reflow as a
  single block).
- Each subject's builder does its own docx assembly on top of these two —
  either filling a teacher-provided template, or (when none exists) building
  the record from scratch with matching layout conventions: header
  (course + reg no, bottom border), footer (`EX-N: TITLE`), Ex.No/Date table,
  Aim/Description/Question, then one Sample Code + Sample Output pair per
  question, RESULT. See `DSE/build_dse_ex1.py` or
  `DBMS/dbms_lab.py:build_docx_scratch` for the concrete pattern to copy.

## Output layout convention
Every subject writes to `<Subject>/output/Ex<N>/`, always containing at
least: the real script/SQL as run, `screenshots/` (real PNGs), and the
filled `.docx`. Some subjects add more (DSE also emits a Jupyter notebook +
a video cue-card script for the code-explanation requirement).

`labshot.py` renders terminal/editor-style PNGs for subjects whose "real
output" is stdout (DSE, DBMS). WebTech's real output is a browser render, so
its screenshots come from actually loading the page via `claude-in-chrome`
and capturing it — same "real capture, not synthesized" principle, different
tool for the job. Don't reach for `labshot` there.

## Folder hygiene
Keep each subject's root to just its `PIPELINE.md` + active builder
script(s) + `output/`. Put teacher-provided originals (templates, question
PDFs/PPTX) in a `materials/` subfolder, and superseded/deprecated stuff in
an `archive/` subfolder — don't leave deprecated docx/scripts loose at the
subject root where they're easy to mistake for the current output (this is
what DBMS looked like before the 24/07/2026 cleanup; DSE never had the
problem since it started clean).

## Per-subject specifics
Don't duplicate these here — read the subject's own file:
- `DSE/PIPELINE.md` — Data Science Ecosystem Lab (23CS2025), Python
  NumPy/Pandas, per-student question bank, notebook + video-script
  deliverables, the "reg no printed first in every notebook cell" rule
  (from Ex-2 onward).
- `DBMS/PIPELINE.md` — Database Systems Lab (23CS2014), PostgreSQL (chosen
  over Oracle/MySQL), `dbms_lab.py` single builder for all experiments,
  table-naming/schema-mutation history, the from-scratch record path for
  experiments with no teacher template.
- `WebTech/PIPELINE.md` — Web Technologies lab, HTML5/CSS(/JS later),
  "run for real" means actually rendering in a browser via the
  `claude-in-chrome` tools (`file://` is blocked, serve over
  `http://127.0.0.1`) and screenshotting that; fills mam's real
  `Lab Record Format.docx` template rather than building from scratch. Site
  theme: online gaming community ("Respawn Point"), orange+green palette.
