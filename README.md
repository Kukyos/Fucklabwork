# AutoLAB

Auto-fills college lab record `.docx` templates: AI generates the code, AutoLAB
**actually runs it**, renders terminal/VS Code "screenshots" from the real
output, and inserts everything (heading, code text, images) into the record.

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
