# AutoLAB

Auto-fills college lab record `.docx` templates: AI generates the code, AutoLAB
**actually runs it**, renders terminal/VS Code "screenshots" from the real
output, and inserts everything (heading, code text, images) into the record.

## PDF editor

Open a `.pdf` and click any line to retype it. The text goes back on the page
at the same baseline in the same font, so nothing re-flows and the layout is
untouched — the old glyphs are redacted away and the new ones drawn in place.

The font is found automatically, best option first: reuse the page's own font
resource, else re-embed a copy of it, else a Base-14 lookalike matched to the
span's style, else the bundled CJK face. A rung is only skipped if it can't
draw every character typed, so a replacement never silently loses glyphs.
Anything lossy (substituted font, text shrunk to fit, undrawable characters)
is reported in the panel rather than left for you to find in the download.

Nothing is stored server-side: the file is re-sent on save and the edited PDF
comes straight back as a download.

Hosted, the editor takes PDFs up to 30 pages — `/api/pdf/parse` returns every
page as a preview image in one response (~0.13 MB/page) and Vercel caps a
function response at 4.5 MB. Locally or on the desktop build there is no such
cap: raise `AUTOLAB_PDF_MAX_PAGES`.

**Not yet:** editing scanned PDFs (no text layer to edit — it says so),
reordering/merging pages, images, and structure cleaning.

Also rebrands a finished record in one shot: find & replace swaps a register
number everywhere in the text **and inside the screenshots** (Gemini vision
finds it, the Gemini image model rewrites it in place — layout untouched).

## AI key (free)

All AI features use the Gemini API. Get a free key at
[aistudio.google.com](https://aistudio.google.com) (Google account, no card):

- **Desktop app:** Profile → Gemini API key → Save.
- **Web / Vercel:** paste the key into the tool form when a feature asks for it.

## Run

```
pip install -r requirements.txt

python -m uvicorn server:app --port 8000      # web mode (localhost/LAN)
python desktop.py                             # desktop mode (profile, AI key, organizer)
```

Desktop exe: `pyinstaller AutoLAB.spec` → `dist/AutoLAB.exe`.

## Deploy to Vercel

The repo is Vercel-ready (`vercel.json` + `api/index.py` wrap the FastAPI app).
Import the GitHub repo in Vercel and deploy — no settings needed. The hosted
version serves find & replace (with screenshot patching), document editing,
template fill, and full AI record generation (Gemini writes the code + output,
labshot renders the screenshots — no compilers needed); the solve pipeline
(actually running code) is desktop-only and hides itself automatically.

## Payments / credits (optional)

The site can run a prepaid-credits system (₹1 = 1 credit, Razorpay top-ups,
Supabase accounts + wallet). It is **off by default** — everything stays
BYO-key and free until you set these env vars on the server:

| Env var | From |
|---------|------|
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` | Supabase dashboard → Settings → API |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | Razorpay dashboard → API keys |
| `RAZORPAY_WEBHOOK_SECRET` | Razorpay dashboard → Webhooks (optional backup path) |
| `GEMINI_API_KEY` | the server-side key paid ops run on |

One-time DB setup: paste `supabase_setup.sql` into Supabase → SQL Editor →
Run. Sign-in is email OTP (change Supabase's magic-link email template to
contain `{{ .Token }}`).

Prices live in `billing.py` (`PRICES`). Text find & replace is always free;
any AI op is also free when the user brings their own Gemini key. Failed paid
ops auto-refund.

## What's inside

| File | Does |
|------|------|
| `server.py` | FastAPI backend — all `/api/*` endpoints |
| `autolab.py` | docx find/replace + block extraction/editing |
| `pdfedit.py` | PDF spans in/out — automatic font finding, in-place text replacement (`python pdfedit.py` self-checks) |
| `gemini.py` | Gemini API client + in-place screenshot patching |
| `billing.py` | Supabase auth + credit wallet + Razorpay (stdlib HTTP only) |
| `supabase_setup.sql` | one-time DB schema — paste into Supabase SQL Editor |
| `runner.py` | executes generated code (python/c/cpp/java) with timeouts; `run_pair` handles server+client socket labs |
| `labshot.py` | draws the screenshots — Windows terminal + VS Code windows, URK spoofing (`line`/`title`/`prompt`) |
| `assemble.py` | writes a solved question (heading, code block, images) into a docx |
| `make_template.py` | builds the neutral record template |
| `static/` | frontend (vanilla JS, no build step) |
| `api/index.py` | Vercel serverless entry point |

## Tests

Each `*_smoke.py` is a runnable check; the big one is the full pipeline:

```
python solved_smoke.py     # run → render → assemble → verify (prints PASS)
```
