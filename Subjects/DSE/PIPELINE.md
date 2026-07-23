# DSE pipeline — notes to self (Claude)

Maintained across sessions. If I learn something or change the pipeline, update this file.

## What this is
Cleo's **DSE = Data Science Ecosystem Lab**, course **23CS2025**. **Python (NumPy / Pandas), not SQL.** Reg no **URK24CS1021**.

The teacher is thorough and assigns a **different scenario per student**. The `Question Bank …docx` is a table: `S.No | Reg.No | Question`. **Look up Cleo's row by Reg.No.**
- Ex-1 → row 20, URK24CS1021 = **"Manufacturing Quality Control"** (defect-rate array: create/index/slice/reshape/iterate/join/split/critical/sort/filter, then Pandas Series + DataFrame).

## How to run
```
python Subjects/DSE/build_dse_ex1.py
```
→ `Subjects/DSE/output/Ex1/` = { qc_numpy.py, qc_pandas.py, screenshots/, Ex1_URK24CS1021.docx }

Runs the real Python, captures real stdout, renders terminal screenshots (`labshot.render_terminal_shot`, style=cmd), builds the docx.

## The whole point
Same philosophy as DBMS: **run for real, capture real output.** numpy 2.4.3 / pandas 2.3.3 are installed.

## Record layout — built FROM SCRATCH
There is **no editable template** — only `Record Guidelines.pdf` (a spec). The builder constructs the docx to match it:
- Header: `23CS2025 DATA SCIENCE ECOSYSTEM LAB` (left) + reg no (right), bottom border.
- Table: `Ex. No. N | <TITLE>` / `Date of Exercise | <date>`.
- **Aim** (fixed text from guideline) · **Description** · **Question:** (full assigned scenario) · **Sample Code:** + **Sample Output:** (repeat per part) · **CODE EXPLANATION LINK:** · **Preparation course certificate** · **RESULT** (fixed sentence).
- Footer: `EX-N: <TITLE>`.

## Decisions / conventions
- **Structure:** one scenario with ~12 ops → presented as **two Sample Code/Output pairs** (NumPy block, Pandas block), not one block per bullet. If the teacher wants each bullet separate, split them.
- **Reproducibility:** seed `np.random.seed(1021)` so re-runs give identical output (values are unique-ish per Cleo, not the default 42 everyone would use).
- **Student-supplied placeholders left BLANK:** `CODE EXPLANATION LINK` (their YouTube/Drive) and `Preparation course certificate` (their cert image). Never fabricate these.
- Student-style code: lowercase, short comments, no over-engineering.

## Extra deliverables (asked for, now part of the builder)
Besides the docx + screenshots, `build_dse_ex1.py` also emits into `output/Ex1/`:
- **`Ex1_QualityControl.ipynb`** — a real Jupyter notebook. Cells live in `NB_CELLS` (kind, source, spoken-note). Built WITHOUT jupyter installed: `_run_cell` execs each code cell in one shared namespace like a kernel, capturing stdout as `stream` and a trailing bare expression as `execute_result` (repr; DataFrames also get `text/html`). So outputs are genuine, not typed in.
  - **Style: student, not AI.** Light lowercase comments, bare-expression outputs (`defects`, `df`), natural flow — NOT the heavily `# 1.`-numbered style of the `.py` files. Keep it that way; don't over-comment or add docstrings/type hints.
- **`video_script.md`** — spoken script for the CODE EXPLANATION LINK video. Cleo talks through the notebook cell by cell in simple terms. Aim **~5 minutes**, first person, casual. Generated from the per-cell `note` field so notebook + script stay in sync. Name is a `[name]` placeholder (don't guess Cleo's real name).

## Gotchas already hit (don't repeat)
- **python-docx variable shadowing:** don't name a local `run` if you also call a `run()` function — the loop's `run = p.add_run()` shadows it (`UnboundLocalError`). Use `cr` for cell runs.
- Question cell text uses `•`/unicode — keep as-is when copying into the Question section.
- **Word file lock:** if a rebuild dies with `PermissionError` on the `.docx`, a stray `WINWORD.exe` (from a prior PDF render) is holding it — `Stop-Process -Name WINWORD -Force` then rebuild.
- Notebook style vs docx: the docx "Sample Code" uses the commented `.py` files; the notebook is lighter. That's fine (record = cleaned code, notebook = working file).

## To do more DSE experiments
Pull Cleo's row from that experiment's question bank → write + run the Python → reuse the builder pattern (parametrise TITLE / EX number / question text / code files).
