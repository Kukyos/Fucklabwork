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
  - **Structure change, Ex-3 onward (06/08/2026):** mam told the class the video should be **you teaching juniors**, not narrating code. So the cues are no longer one-line-per-cell in cell order. Each block is **question → why this tool/chart and not another → then the code**, plus an opening hook (why do this at all) and a closing takeaway per concept. Keep cue-style (glance, don't read) — only the *shape* changed.

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

## Ex-3 specifics (`build_dse_ex3.py` → `output/Ex3/`)
- **Data Visualization**, matplotlib 3.11.1 + seaborn 0.13.2 (installed 06/08/2026). Title `DATA VISUALIZATION`, aim adapted from the guideline's ("…using Matplotlib and Seaborn" instead of Numpy/Pandas) since the PDF's aim is written for Ex-1.
- Question doc is `URK23CS1021_EXP3.docx` — **note the reg no reads URK23CS1021, not Cleo's URK24CS1021.** Flagged to Cleo; the plot list is almost certainly common to everyone and only the dataset varies, so the dataset lives in one `CSV` string constant → `output/Ex3/admissions.csv`. If it's the wrong student's dataset, edit that constant and re-run, nothing else changes.
- `matplotlib.use("Agg")` at module top — headless build. `plt.show()` is a no-op under Agg (it warns on stderr, harmless) so the figure is still alive afterwards; `_grab_figure()` saves `plt.gcf()` then `plt.close("all")`.
- **Sample Output is the plot PNG, not a terminal shot.** A section can emit both: if it printed anything it gets a terminal shot *and* its plot (`q04a`/`q04b`). Only the load section and the bar-plot's rate table print.
- `_run_cell` needed the same fix for the notebook — a plot cell has no stdout and no trailing expression, so without a `display_data` grab every plot cell would look like it was never run. **Copy that into any future builder that plots.**
- Derived column gotcha: "admission rate" isn't a column — `groupby(...)["Admitted"].apply(lambda s: (s == "Yes").mean())`. Histogram of a 0–5 integer column needs explicit `bins=range(0, 7), align="left"` and integer `yticks`, or the automatic binning/half-student ticks look broken.

## Ex-4 specifics (`build_dse_ex4.py` → `output/Ex4/`)
- **Descriptive statistics + correlation**, 15 questions, **same `fanspeed.csv` as Ex-2** (copied from `output/Ex2/`, not re-fetched — PIPELINE already records the link works, a fresh download only adds a failure mode). Title `DESCRIPTIVE STATISTICS AND CORRELATION`. Needed `scipy` (installed 07/08/2026) — pandas' `corr(method="spearman")` and seaborn's `regplot` both import it lazily, so the failure shows up mid-run, not at import.
- **The dataset makes four questions degenerate — answer them honestly, don't dress them up.** Only 2 numeric columns and 0 categorical ones: the correlation matrix is 2×2 ("which pairs" has one candidate), the heatmap is nearly content-free, the pair plot is a 2×2 grid. Built all of them anyway (they're assigned); the limitation is stated in the video script, not in the docx.
- **Mode is the interesting one:** all 100 readings are unique, so `mode()` returns 100 tied values per column. That IS the answer to "any columns with multiple modes?" — yes, degenerately, because mode is a categorical tool. Print `len(modes)` + `.head(3)`, never the 100 values. Then `pd.cut` a Temp_Band categorical (clearly commented as derived) and take the mode of that.
- Facts confirmed by the run, don't re-derive: Pearson 0.9852 vs Spearman 0.9841, **0 outliers** under 1.5×IQR in either column, fan-speed skew −0.0609 (symmetric). Temperature is `linspace(5,35,100)` — a flat uniform ramp, so **histogram Fan Speed, not Temperature**, or the shape question has no answer.
- `sns.pairplot` makes its own figure but it's the most recent one, so `plt.gcf()` in `_grab_figure()` catches it fine — verified, no `g.figure` special case needed.

## `dse_record.py` — the shared builder (Ex-5 onward)
Ex1–4 each carried a byte-identical copy of the docx helpers, the notebook kernel and the ~120-line docx skeleton. **Extracted at Ex-5** into `dse_record.py`: an `Exp` dataclass (num / title / date / out / aim / desc / question / preamble / sections / nb_cells / video / script+notebook names / shot command+cwd) plus `build(exp)`, which does everything ex4's `build()` did. A `build_dse_ExN.py` is now **content only**.
- **ex1–4 were deliberately left untouched** — they already ran and their output is checked in. Don't retrofit them.
- `run_sections`, `_grab_figure`, `_run_cell`, `build_notebook` moved across unchanged, including the `display_data` figure grab and the reg-no prepend.
- `extra_files={name: text_or_bytes}` on `Exp` writes anything else into `output/ExN/` before the run.

## Ex-5/6/7 question banks — the format changed
From Ex-5 the **question bank docx has no per-student table**: it's one common list of operations for everyone. The per-student assignment moved into a separate **`Dataset_N.xlsx`** (`S. No | Reg. No | [Target to Predict] | Dataset Link`). Look Cleo up there (row 20, URK24CS1021), not in the docx.
- Same off-by-one as Ex-2: the docs' own titles read "Experiment No: 6 / 6 / 8" for files named 5 / 6 / 7. Went with the filename + folder numbering again.
- **Kaggle downloads need no auth:** `curl -sL https://www.kaggle.com/api/v1/datasets/download/<owner>/<slug>` returns the zip, 200, no credentials. Verified for all three. `kaggle` CLI is not installed and isn't needed.
- `openpyxl` (read the xlsx) and `scikit-learn` 1.9.1 installed 11/09/2026.
- Cleo's assignments: **Ex-5** india-rental-house-price, target *Price per Square Foot*. **Ex-6** music-genre-classification. **Ex-7** human-cognitive-performance-analysis.

## Ex-5 specifics (`build_dse_ex5.py` → `output/Ex5/`)
- **The assigned target column is 100% empty.** `priceSqFt` has 0 non-null values in all three city files, so the target is **derived**: `price / size_sqft`. Said in a code comment *in the Sample Code*, not just the video script — it's a deviation from the assigned target, so it has to be visible in the record. Flagged to Cleo too.
- The download ships **three CSVs, one per city** (Delhi 5000 / Mumbai 5000 / Pune 3910). Concatenated → 13,910 rows, and `city` goes from a constant to a real 3-level feature. (There are 8 stray `Hisar` rows inside the Mumbai file — left alone, it's real data.)
- **Leakage is the teaching point:** `price` must NOT be a feature, because target = price/size and size *is* a feature. Also dropped `SecurityDeposit` (≈ one month's rent → same leak one step removed), `description` (huge free text, stripped before staging the csv), `verificationDate` ("Posted a year ago"), `isNegotiable` (96% null), `currency`.
- `house_size` is text (`"1,020 sq ft"`); bedrooms parse out of `house_type` (`"2 BHK…"` → 2). `location` has 702 levels → top 30 + "Other".
- Results, don't re-derive: Simple 0.1609 / Multiple 0.3837 / Poly-2 0.3840 (39 features → 819) / Lasso 0.3827 / Ridge 0.3837. **Feature choice moved R² by 0.22, model choice by <0.01** — that's the interpretation.

## Ex-6 specifics (`build_dse_ex6.py` → `output/Ex6/`)
- `train.csv` from the download (the only labelled file) → `music_genre.csv`. 17,996 rows, 11 imbalanced classes (largest 27.5%, which is the baseline every model must beat).
- **`duration_in min/ms` is genuinely mixed-unit** — 2,580 rows in minutes, 15,416 in ms, same column. `np.where(dur < 100, dur, dur / 60000)`. Found it from `describe()`: min 0.5, max 1.4M.
- Real nulls to impute (Popularity 428 / key 2014 / instrumentalness 4377) → median. No `demo = df.copy()` dance needed here, unlike Ex-2.
- **Sampled to 5000 rows** (`random_state=1021`) because SVC is O(n²–n³); all five classifiers run on the *same* sample or the comparative table is meaningless. `stratify=y` on the split.
- **The dataset hands you the overfit/underfit lesson for free** (the question asks for it): Random Forest train 0.9768 / test 0.487 = textbook **overfitting**; Logistic Regression train 0.4525 / test 0.462 = textbook **underfitting** (train ≤ test, both low). KNN 0.362, DT 0.398, SVM 0.480. Diagnose from the **gap**, not the height.
- `_model_section(label, var, ctor, note)` generates the five near-identical model blocks — fit, train/test accuracy, classification report, confusion matrix, heatmap, append to `results`.

## Ex-7 specifics (`build_dse_ex7.py` → `output/Ex7/`)
- 80,000 rows. **Agglomerative and Spectral both build an n×n matrix** — at 80k that's ~51 GB and a MemoryError, not slowness. `df.sample(n=2000, random_state=1021)` once, all three algorithms on that same sample. `silhouette_score` is quadratic too.
- Dropped `User_ID` (unique key) and **`AI_Predicted_Score`** — it correlates **0.9924** with `Cognitive_Score`, so keeping it feeds the same information in twice and doubles its vote in every distance. `StandardScaler` is mandatory (caffeine 0–500 vs sleep 4–9).
- k=3 used, though the **silhouette actually peaks at k=2 (0.1556)** — stated openly in the interpretation, justified because k=3 additionally separates by stress. Don't quietly pick k and pretend the sweep agreed.
- Metrics (no labels, so internal only): silhouette ↑, Calinski-Harabasz ↑, Davies-Bouldin ↓. K-means 0.1201 / 301.0 / 2.3715, Agglomerative 0.0672 / 196.5 / 3.0694, Spectral 0.1086 / 276.9 / 2.4291. Note in the record that silhouette + CH both reward compact round clusters, i.e. exactly what k-means optimises.
- **Low silhouette ≠ meaningless clusters.** The profile table is the payoff: centres are 1.68–1.86 std apart on Cognitive_Score / Stress_Level / Reaction_Time and <0.3 on age, sleep, screen time, caffeine. Real grouping on 3 of 8 columns, noise on 5 — and silhouette averages over all 8.
- **Measure cluster-centre spread in standard deviations, not raw units**, or caffeine (0–500) looks important next to sleep (4–9) purely because its numbers are bigger. First draft got this wrong.
- "Display the clusters" → PCA to 2D, one scatter panel per algorithm. Say in the video that PCA did no clustering — it only compresses 8D to 2D for drawing, and keeps well under half the variation.

## Gotchas from Ex-5/6/7 (don't repeat)
- **The CSVs are staged by hand, once, and committed.** Unlike Ex-4 (which `shutil.copyfile`d fanspeed.csv on every build), the Ex-5/6/7 builders only *read* `output/ExN/*.csv`. Delete one and the builder dies. The Kaggle zips were unpacked in a session scratchpad that is long gone, so re-staging means re-downloading with the no-auth API URL above. `Exp.extra_files` is the hook if this ever needs to be self-healing.
- **Never use `.to_string()` on a wide DataFrame in a section.** `to_string()` ignores `display.width` and emits one 226-char line; `labshot` then hard-wraps it mid-value and the last column ends up orphaned on its own line (Ex-6's 17-column `head(10)` split `Class` into "Clas" / "s" / the digit). Plain `print(df.head(10))` lets pandas wrap into labelled blocks with backslash continuation markers, which is both readable and what a real terminal shows. Set `display.width=100` + `max_colwidth=20` in the preamble. Keep `.to_string()` only for narrow result tables where truncation is the worry.
- **Don't label a plot "the best model" unless it plots the model the table calls best.** First draft of Ex-5 printed "Best R2: Polynomial" and then captioned a multiple-linear plot "best model". Name the model in the heading instead.

## To do more DSE experiments
Pull Cleo's row from that experiment's `Dataset_N.xlsx` → download the Kaggle zip with the no-auth API URL above → write + run the Python → write a content-only `build_dse_ExN.py` against `dse_record.Exp` / `build`.
