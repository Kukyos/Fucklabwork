# WebTech pipeline — notes to self (Claude)

Maintained across sessions. If I learn something or change the pipeline, update this file — reconcile stale lines, don't just append.

## What this is
Cleo's Web Technologies lab, course **23CS2049 - Web Technology Lab**. Reg
no **URK24CS1021**.

**The course title was already IN the template all along** — I initially
missed it (see "Header gotcha" below) and asked Cleo for the course code;
she gave `23CS2049`, which matches exactly. Don't re-ask; it's baked into
`materials/Lab Record Format.docx` itself.

### Header gotcha (real bug, two layers, fixed 27/07/2026)
The header's course-title cell is a **Word content control (`w:sdt`) bound
via `w:dataBinding` to the document's `dc:title` core property** (in
`docProps/core.xml`), sitting in the same `<w:tr>` as a second, plain `<w:tc>`
holding the literal text `[regno]`. Two separate bugs stacked here:

1. **python-docx's table API can't see the sdt-wrapped cell at all.**
   `doc.sections[0].header.paragraphs` returns only an empty paragraph, and
   `doc.sections[0].header.tables[0].rows[0].cells` returns just
   `['[regno]']` — the cell lookup only finds `<w:tc>` that are *direct*
   children of `<w:tr>`, and the course-title cell is nested inside
   `<w:sdt><w:sdtContent>`. First pass at this, I concluded (wrongly) the
   header was blank and added my own `COURSE + "\t" + URK` line to it,
   producing a duplicate/wrong-wording line under the template's real one.
   **Fixed by not touching that cell** — just walking
   `header._element.iter(qn("w:t"))` for the literal `"[regno]"` run and
   setting its `.text` directly (`fill_header_regno()` in both build
   scripts), bypassing the table API entirely.

2. **The deeper bug: the bound `dc:title` property itself was stale.**
   Because it's a *data-bound* control, Word renders the LIVE property value
   at open time, not whatever cached text sits in the `<w:t>` run — and
   `docProps/core.xml`'s `dc:title` was still `"24CS2502 – MERN Full Stack
   Development Lab"` (`dc:creator` was `"Rose"`, `cp:lastModifiedBy` was
   `"난디 💜"`) — leftover from whatever course this template was originally
   built for, before someone repurposed it for WebTech by editing only the
   *visible cached text*, never the actual property. So every rebuild kept
   showing "MERN..." on every page in real Word, even though grep-ing the
   raw XML `<w:t>` runs showed the correct WebTech text — because that
   check doesn't reflect what Word actually renders for a bound control.
   Cleo caught this via a screenshot AND a File Explorer Properties pane
   screenshot (which reads the same `docProps/core.xml`), not by chance —
   worth remembering that a docx's Explorer-visible metadata is a real,
   fast way to sanity-check this class of bug.
   **Fixed:** `doc.core_properties.title = COURSE`,
   `doc.core_properties.author = URK`,
   `doc.core_properties.last_modified_by = URK`, set before
   `fill_header_regno()`, on every build.

**General lesson:** for ANY docx template inherited/reused from elsewhere,
check `docProps/core.xml` (`zipfile.read('docProps/core.xml')`) for stale
title/author/last-modified-by up front, not just the visible body content —
data-bound content controls make stale *properties* show up as if they were
live *content*, and python-docx's simple `.paragraphs`/`.tables` traversal
won't surface either the binding or the cell it's hiding in.

### Footer gotcha (same class of bug, fixed 27/07/2026)
The footer is a 2-column table too: `Ex. N | Title of exercise` on the left,
a real Word `PAGE` field on the right (leave that alone, Word recalculates
it). Same structure as the header, same mistakes made the first time round:
- `Ex. N` is **also** a content control, this time bound to the **extended**
  `Company` property in `docProps/app.xml` (not `docProps/core.xml` — a
  different properties part, and python-docx has **no high-level API for
  extended properties at all**, unlike `core_properties`). Fixed by patching
  `docProps/app.xml` directly with a post-`doc.save()` zip rewrite —
  `set_ex_number(out_path, "Ex. N")` in both build scripts. Also update the
  cached run text to match (walked via `w:t` again) in case some renderer
  doesn't resolve the binding.
- ` | Title of exercise` is a **plain, non-bound run** right next to that
  content control in the same paragraph — this is the one that actually
  needed simple text replacement, and my first attempt never touched it: I
  wrote `doc.sections[0].footer.paragraphs[0]` and appended a brand new bold
  run to it, which is a *completely different, unrelated empty paragraph*
  that sits below the whole footer table (`<w:p><w:pPr><w:pStyle
  w:val="Footer"/></w:pPr></w:p>`, the very last element in `word/footer1.xml`).
  That produced an inert extra paragraph while the real placeholder sat
  untouched — Cleo caught it from a screenshot showing literal "Title of
  exercise" still there. Fixed the same way as `fill_header_regno`: walk
  `footer._element.iter(qn("w:t"))` for the exact placeholder text
  (`fill_footer_title()`), don't trust `.paragraphs`/`.tables` on this
  template at all.
- **Compounding lesson: `doc.sections[0].footer.paragraphs[0]` (or
  `.header.paragraphs[0]`) is not a safe way to "find the footer/header text"
  on a template you didn't author.** It grabs whatever paragraph happens to
  be first/structurally simplest, which on a table-based header/footer is
  usually a trailing empty spacer paragraph, not the visible content. Always
  verify against the raw XML (`zipfile` + regex on `word/header1.xml` /
  `word/footer1.xml`) before writing into a header or footer on an unfamiliar
  template — for both of these it took actually reading the XML to find the
  real structure; guessing via the high-level API was wrong both times.

Theme (Cleo's choice): **online gaming community**, "like Discord" —
implemented as "Respawn Point", a single-page site. Reuse this theme for
later WebTech exercises unless Cleo says otherwise, so the site can plausibly
grow across the semester as one evolving project (Ex2 adding CSS3, Ex3 adding
JS, etc. — typical for this kind of lab sequence).

## The whole point, adapted for frontend
Same run-for-real philosophy as DSE/DBMS, but here "run" means "actually
render it in a browser" — no synthesized/drawn screenshots:
1. Hand-write `index.html` for real (+ any real local assets, e.g.
   `banner.png` generated with PIL — no network image fetches).
2. Serve the output folder locally (`python -m http.server`, from inside
   `output/ExN/`) and load it via the `claude-in-chrome` MCP tools.
   **`file://` URLs are blocked by the extension** — always serve over
   `http://127.0.0.1:<port>`, don't waste a round-trip rediscovering that.
3. Screenshot the real render. There's no single "capture full page" tool
   here (resize_window is capped to visible screen bounds; the
   Ctrl+Shift+P → "Capture full size screenshot" DevTools command doesn't
   register through the automation extension). What works: scroll in a few
   large steps and take `computer` screenshots with `save_to_disk: true` at
   each stop, picking stops so the frames cover the page with **no gaps**
   (slight overlap is fine, gaps are not — check each frame against the
   previous one before moving on). Copy the saved temp files into
   `output/ExN/` and use 2-4 of them as the record's Output images instead
   of one impossible full-page shot.
4. `build_webtech_ExN.py` only assembles the docx around files that already
   exist for real (`index.html`, the screenshots) — it doesn't render or
   screenshot anything itself, that part is inherently an interactive step
   I do once via the browser tools, not a repeatable pure-Python build step
   like DSE/DBMS.

## Deploy repo (set up 27/07/2026)
Submission instructions in `materials/Exercise 1.docx` require pushing
`index.html` to a real GitHub repo, enabling GitHub Pages, and pasting the
deployed URL into the record. This is now automated:
- **Local clone lives OUTSIDE this repo**, as a sibling: `C:\Users\Cleo\Desktop\SHITIBUILT\WebTechLab`
  (separate git history from AutoLAB — don't nest it inside AutoLAB's tree).
  Remote: `https://github.com/Kukyos/WebTechLab.git`, branch `main`.
- **One folder per experiment** (`Ex1/`, `Ex2/`, ...), each holding exactly
  the deployable files (`index.html` + any local assets like `banner.png` —
  NOT the `.docx` record or the process screenshots, those stay in
  `Subjects/WebTech/output/`). A root `index.html` at the repo root links to
  each experiment folder so the bare Pages URL isn't a 404.
- **GitHub Pages only needs enabling ONCE**, at the repo root (`gh api -X
  POST repos/Kukyos/WebTechLab/pages -f "source[branch]=main" -f
  "source[path]=/"`) — each experiment then gets its own URL for free via
  its folder path (`https://kukyos.github.io/WebTechLab/Ex1/index.html`,
  `.../Ex2/index.html`, ...). No per-experiment Pages config exists in
  GitHub's model; "separate URL per experiment" == "separate folder", not
  "separate Pages site".
- To add a new experiment: copy its deployable files into a new `ExN/`
  folder in the WebTechLab clone, add a link on the root `index.html`,
  commit, push. Then set `GITHUB_LINK` in that experiment's
  `build_webtech_ExN.py` to the real deployed URL and rebuild the docx —
  don't leave the GitHub Host Link cell blank once the real URL is known
  (see feedback note below).
- Verify a deploy actually landed before calling it done: poll
  `gh api repos/Kukyos/WebTechLab/pages/builds/latest --jq '.status'` until
  `built`, then `curl -o /dev/null -w '%{http_code}'` each real URL
  (including local assets like `banner.png`) to confirm 200, not just that
  `git push` succeeded.

**Standing lesson:** when a lab's own submission instructions require an
external action (a repo push, enabling Pages, etc.), surface that to Cleo
proactively when the record is built — don't just leave the placeholder
blank and say nothing. She had to point out I'd read right past it in
`Exercise 1.docx`. Do the push myself if she's given (or previously given) a
repo to push to; otherwise say explicitly "this needs a GitHub push + Pages
enabled, want me to do that" rather than silently deferring it.

## Record: fill mam's actual template, don't build from scratch
Unlike DBMS's Exp2/Ex1B, WebTech **does** have a real fill-in template —
`materials/Lab Record Format.docx` (Ex.No/Title/Date/GitHub-Host-Link table,
then Aim/Description/Procedure/Program/Output/Result, each a bold label
paragraph immediately followed by a `[bracketed placeholder]` paragraph).
`build_webtech_ex1.py` locates each label by exact text, replaces the
placeholder paragraph right after it (`set_placeholder`), and for
Program/Output (which need real inserted content, not just text) clears the
placeholder and inserts the code block / images right after it
(`clear_placeholder` + anchor `.addnext()`).
- **Multi-line placeholder text (e.g. Procedure's numbered steps) needs
  actual line breaks to render in Word, not literal `\n` in `run.text`.**
  Turned out python-docx 1.2.0 auto-converts `\n` in an assigned `run.text`
  into `<w:br/>` elements — verified by counting `w:br` in the saved docx
  (9 breaks for a 10-line procedure). Don't assume this holds on other
  python-docx versions; verify with the same br-count check if it ever looks
  flat/run-together after a version bump.
- Footer must be set explicitly (`EX-N: <Title>`) — the template's own
  "Kindly Note" paragraph says to do this by hand; the note paragraph itself
  gets deleted once the footer is actually set, same as removing instruction
  text from any other template.
- **`index.html` references `banner.png` by relative path — when Cleo pushes to GitHub for the Pages link, `banner.png` has to go in the same repo/directory, not just `index.html`.** Pushing only the HTML file means the live graded page shows a broken image. Flag this to her explicitly every time there's a local asset, don't assume it's obvious.
- **GitHub Host Link cell is filled with the real deployed URL** (a
  `GITHUB_LINK` constant near the top of each `build_webtech_ExN.py`) now
  that the deploy repo exists — see "Deploy repo" below. Before the repo
  existed this was left blank as student-supplied, same category as DSE's
  `CODE EXPLANATION LINK`; now that it's automated, always fill it for real,
  never leave it blank without saying so.

## No-AI-look, applied to a webpage instead of code/SQL
Same standing rule as every other subject ([[dbms-lab-workflow]]): must not
read as AI-written. For a website specifically that means avoiding the usual
tells — no marketing-fluff hero copy ("🚀 Elevate your gaming experience"),
no emoji spam, no glassmorphism/gradient-soup cliché, no Lorem Ipsum, modest
scope rather than an over-produced multi-page site for a single-page HTML5
exercise. Content should read like a student's actual community, with small
personality/specificity (e.g. the footer's "not an actual gaming company"
aside) rather than generic corporate copy.

## Scope rule: only what was taught up to that exercise (03/08/2026)
Cleo's teacher told the class **not to overcomplicate Ex1** — use only what
had been taught by then. Ex1 is the *plain HTML5* exercise, so the original
build's internal `<style>` block (CSS variables, sticky nav, hover states,
flex centering, `max-width`) and the `viewport` meta were both out of scope
and got stripped.

**But "no CSS" can't mean zero here** — `materials/Exercise 1.docx` step 6
explicitly says *"Apply a background color and change text color using inline
or internal CSS."* That's the graded rubric. Resolution: **inline `style`
attributes, colors only** — `<body style="background-color:…; color:…">` plus
a `style="color:…"` on each heading, link and table header cell. No layout
CSS at all. Don't use `<body bgcolor>` / `<font>` — obsolete in HTML5, and
the sheet names CSS specifically. Everything else that isn't CSS stays fair
game (`border`/`cellpadding` on `<table>`, `width` on `<img>`, `type="a"` on
`<ol>`, `<hr>`, `<b>`/`<i>`/`<small>`).

Ex2 is where CSS3 legitimately arrives — leave it alone. **When touching Ex1,
keep it CSS-free apart from those inline colors**, and check the same for any
future exercise: cross-reference its own question paper before reaching for a
technique from a later week.

## Color scheme convention
Cleo asked for **orange + green, "like a carrot"** — read as: dark neutral
base (not a bright/white page), carrot-orange as the primary accent
(headings, nav border, hover), a muted leaf-green as the secondary accent
(links, subheadings), used sparingly rather than covering the page — that's
the "subtle" part. Keep this palette for later WebTech exercises unless
Cleo asks to change it, for visual continuity across the semester's site.

## Folder layout
```
Subjects/WebTech/
  PIPELINE.md
  build_webtech_ex1.py, build_webtech_ex2.py
  materials/            — teacher-provided: Exercise 1.docx (question paper),
                          Ex 2 Sample.docx (sample code, not a full question
                          paper), Lab Record Format.docx (the fill-in template,
                          reused across all experiments)
  output/Ex1/            — index.html (no CSS bar inline colors), banner.png,
                          output_*.jpg (real browser
                          screenshots), Ex1_URK24CS1021.docx
  output/Ex2/            — index.html, output_*.jpg, Ex2_URK24CS1021.docx
```

## Assignment1 — different from the Ex1/Ex2 exercises (04/08/2026)
Assignment1 (`output/Assignment1/`) is a separate teacher deliverable, not part of
the Ex1/Ex2 "Respawn Point" sequence — own theme (**Travel Diary**, Cleo's
choice), own submission format:
- **Zero CSS at all**, not even inline colors — `materials/Assignment 1.docx`
  says "Use only HTML (no CSS or JavaScript)", stricter than Ex1's inline-color
  carve-out. Background color and the "framed" photo table use legacy
  presentational HTML attributes instead (`bgcolor` on `<body>`/`<table>`,
  `border` on `<img>`) — these are just HTML attributes, not CSS, so they don't
  violate the rule, but flag this distinction to Cleo if she's surprised by how
  the color got there.
- **Real name required in on-page text**, not the "Cleo" handle — see
  [[user-role]] memory. Cleo's actual name is A M Armaan; use that in any
  visible deliverable content (footer credit, "Hi, I am ___" line, etc).
- **Real photos/video**: Cleo dropped her own trip photos (`travpic1-3.jpeg`)
  and a video (`travvid.mp4`, though it turned out to be gameplay footage, not
  an actual trip clip — worth double-checking with her if a similarly odd file
  shows up again) straight into `output/Assignment1/`, no generation needed for
  those. Only the favicon and a short placeholder audio chime are
  Python-generated (`generate_assets.py`); no local video-encoding lib is
  available (no ffmpeg/opencv/moviepy installed), so a real trip video with no
  ffmpeg would have to fall back to an external sample clip instead.
- **Submission is a single PDF** (code snippets + screenshots per page), not
  the `Lab Record Format.docx` template — `assemble_pdf.py` builds it directly
  with PIL (renders code as text pages + resized screenshots, saved as a
  multi-page PDF), no reportlab/fpdf dependency needed.
- Single HTML page with anchor-based `<nav>`, not multiple linked pages — the
  assignment allows multiple pages but doesn't require them.

## To do more WebTech experiments
Same theme/site unless told otherwise. Write the real HTML/CSS(/JS once that
starts), serve + screenshot for real via claude-in-chrome, then reuse
`set_placeholder`/`clear_placeholder` against that experiment's own template
(confirm whether a per-exercise template exists in `materials/`, or whether
`Lab Record Format.docx` is meant to be reused as-is for every exercise —
looks that way from the "change Ex No / Title in the footer" note aimed at
manual reuse of one template).
