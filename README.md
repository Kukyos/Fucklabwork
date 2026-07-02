# AutoLAB

Auto-fills college lab record `.docx` templates: AI generates the code, AutoLAB
**actually runs it**, renders terminal/VS Code "screenshots" from the real
output, and inserts everything (heading, code text, images) into the record.

## Run

```
pip install -r requirements.txt

python -m uvicorn server:app --port 8000      # web mode (localhost/LAN)
python desktop.py                             # desktop mode (profile, AI key, organizer)
```

Desktop exe: `pyinstaller AutoLAB.spec` → `dist/AutoLAB/AutoLAB.exe`.

## What's inside

| File | Does |
|------|------|
| `server.py` | FastAPI backend — all `/api/*` endpoints |
| `autolab.py` | docx find/replace + block extraction/editing |
| `runner.py` | executes generated code (python/c/cpp/java) with timeouts; `run_pair` handles server+client socket labs |
| `labshot.py` | draws the screenshots — Windows terminal + VS Code windows, URK spoofing (`line`/`title`/`prompt`) |
| `assemble.py` | writes a solved question (heading, code block, images) into a docx |
| `make_template.py` | builds the neutral record template |
| `static/` | frontend (vanilla JS, no build step) |

## Tests

Each `*_smoke.py` is a runnable check; the big one is the full pipeline:

```
python solved_smoke.py     # run → render → assemble → verify (prints PASS)
```
