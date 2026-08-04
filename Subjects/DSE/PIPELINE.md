# DSE pipeline — notes to self (Claude)

Maintained across sessions. If I learn something or change the pipeline, update this file.

## What this is
Cleo's **DSE = Data Science Ecosystem Lab**, course **23CS2025**. **Python (NumPy / Pandas), not SQL.** Reg no **URK24CS1021**.

The teacher is thorough and assigns a **different scenario per student**. The `Question Bank …docx` is a table: `S.No | Reg.No | Question`. **Look up Cleo's row by Reg.No.**
- Ex-1 → row 20, URK24CS1021 = **"Manufacturing Quality Control"** (defect-rate array: create/index/slice/reshape/iterate/join/split/critical/sort/filter, then Pandas Series + DataFrame).
- Ex-2 → row 20, URK24CS1021 = dataset link `fanspeed.csv` (Temperature vs Observed Fan Speed, 100 rows, no nulls as downloaded). This question bank is a *list of pandas operations* (import/head/tail/info/nulls/slicing/add-column/add-delete-row/sort/group/pivot/rank), not a per-student scenario — the doc's own title says "Experiment No: 3" even though the filename and folder say 2; went with 2 (matches filename + Cleo's own folder naming). Confirmed the link is actually reachable off-campus (curl 200, byte-identical to the file Cleo pre-downloaded) — campus-wifi restriction isn't real, or isn't enforced from this network.

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
- **`video_script.md`** — **cue cards, NOT a read-aloud script.** Cleo records the CODE EXPLANATION video looking at the notebook and must not sound like they're reading. So it's a few terse prompts per cell (`CUES` list) + open/close cues — glance and say it in your own words. Aim ~5 min. (Learned 23/07/2026: the first version was full paragraphs — Cleo pushed back that reading verbatim is obvious. Keep it cue-style.)

## Gotchas already hit (don't repeat)
- **python-docx variable shadowing:** don't name a local `run` if you also call a `run()` function — the loop's `run = p.add_run()` shadows it (`UnboundLocalError`). Use `cr` for cell runs.
- Question cell text uses `•`/unicode — keep as-is when copying into the Question section.
- **Word file lock:** if a rebuild dies with `PermissionError` on the `.docx`, a stray `WINWORD.exe` (from a prior PDF render) is holding it — `Stop-Process -Name WINWORD -Force` then rebuild.
- Notebook style vs docx: the docx "Sample Code" uses the commented `.py` files; the notebook is lighter. That's fine (record = cleaned code, notebook = working file).

## Notebook rule — from Ex-2 onward
Teacher requires **every notebook code cell to print the reg no (URK24CS1021) before anything else** — a plain `print("URK24CS1021")` as the first line is enough. She said Ex-1 (which didn't have this) is fine as a one-off exception, but it's required starting Ex-2. `build_notebook()` in `build_dse_ex2.py` does this by prepending the print to `src` before `_run_cell` executes it, so it shows up both in the cell's source and as the first line of its output — do the same one-line prepend in every future `build_dse_ExN.py`.

## Ex-2 specifics (`build_dse_ex2.py` → `output/Ex2/`)
- Guideline says "(Follow the same for all the questions)" — read literally as **one Sample Code/Output pair per top-level question**, not lumped into 1-2 blocks like Ex-1. `SECTIONS` list is `(heading, code)`; each gets its own screenshot (`q01_output.png` …). Ended up 11 pairs (merged first-10/last-8 rows into one, since they're the same trivial op).
- Sections run **cumulatively in one shared namespace** (`exec`, like the Ex-1 notebook's `_run_cell`) so state (added columns etc.) carries forward realistically — not 11 independent subprocess runs.
- **Gotcha (real bug caught by advisor review, don't repeat):** the "examine/impute null values" question needs nulls to demonstrate on, but the real dataset has none. First attempt planted `None` into 3 rows of the *live* `df` and imputed with the column mean — that silently corrupted those rows for every section afterward (a low-temperature row ended up with the *global mean* fan speed, producing a physically nonsensical "high fan speed at low temperature" cell in the groupby/pivot). **Fix: do the null-plant-and-impute demo on `demo = df.copy()`, never on the live `df`.** Applies to any future experiment that needs to demonstrate null-handling on a dataset that doesn't actually have nulls.
- Same extra deliverables as Ex-1 (`Ex2_FanSpeed.ipynb`, `video_script.md`, same cue-card style), self-contained builder script per the pattern below (no shared module extracted — see next section).

## To do more DSE experiments
Pull Cleo's row from that experiment's question bank → write + run the Python → reuse the builder pattern (parametrise TITLE / EX number / question text / code files). Each `build_dse_ExN.py` is currently self-contained (docx helpers + notebook helpers copy-pasted from the previous one) rather than sharing a module — fine at 2 experiments, reconsider extracting a shared helper if a 3rd/4th repeats the same ~150 lines unchanged.
