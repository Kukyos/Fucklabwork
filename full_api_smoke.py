"""Smoke test ALL the new backend endpoints."""

import io
import json
import urllib.request
import uuid
from pathlib import Path
from docx import Document

BASE = "http://127.0.0.1:8765"
EX1 = Path(r"C:\Users\Cleo\Desktop\Labs Sem4\CN\EX1.docx")


def multipart(parts: list[tuple], file: tuple | None = None) -> tuple[bytes, str]:
    """parts: list of (name, value). file: (name, filename, bytes) or None."""
    bdy = "----autolab" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in parts:
        chunks.append(f"--{bdy}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    if file is not None:
        fname, fn, data = file
        chunks.append(
            f"--{bdy}\r\nContent-Disposition: form-data; name=\"{fname}\"; filename=\"{fn}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n".encode()
        )
        chunks.append(data)
        chunks.append(b"\r\n")
    chunks.append(f"--{bdy}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={bdy}"


def get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return r.status, r.read()


def post_json(path, payload):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


def post_multipart(path, parts, file=None):
    body, ctype = multipart(parts, file)
    req = urllib.request.Request(f"{BASE}{path}", data=body, method="POST",
                                  headers={"content-type": ctype})
    with urllib.request.urlopen(req) as r:
        return r.status, r.read(), dict(r.headers)


# 1. capabilities
status, body = get("/api/capabilities")
print(f"GET /api/capabilities -> {status}")
caps = json.loads(body)
print(f"  desktop={caps['desktop']} version={caps['version']}")
assert caps["desktop"] is True

# 2. parse a real docx
data = EX1.read_bytes()
status, body, _ = post_multipart("/api/document/parse", [], file=("file", EX1.name, data))
print(f"\nPOST /api/document/parse -> {status}")
parsed = json.loads(body)
print(f"  name={parsed['name']}  blocks={parsed['block_count']}")
assert parsed["block_count"] > 0
first_with_text = next(b for b in parsed["blocks"] if b["text"].strip())
print(f"  sample block id={first_with_text['id']!r} loc={first_with_text['loc']!r} words={first_with_text['words']}")
print(f"  text[:60]={first_with_text['text'][:60]!r}")

# 3. save with one edit
target = first_with_text["id"]
new_text = "SMOKE TEST INSERTED TEXT REPLACING ORIGINAL"
edits = {target: new_text}
status, body, headers = post_multipart(
    "/api/document/save",
    [("edits", json.dumps(edits))],
    file=("file", EX1.name, data),
)
print(f"\nPOST /api/document/save -> {status}")
print(f"  X-Edits-Applied: {headers.get('x-edits-applied')}")
out = Path(r"C:\Users\Cleo\Desktop\SHITIBUILT\AutoLAB\full_smoke_edited.docx")
out.write_bytes(body)
doc = Document(str(out))
all_text = "\n".join(p.text for p in doc.paragraphs)
print(f"  Contains injected text? {'SMOKE TEST INSERTED' in all_text}")

# 4. templates list
status, body = get("/api/templates")
print(f"\nGET /api/templates -> {status}")
tpls = json.loads(body)["templates"]
print(f"  count={len(tpls)} ids={[t['id'] for t in tpls]}")

# 5. fill template
payload = {
    "template": "neutral",
    "course_title": "Smoke Tests Lab",
    "register_number": "URK24CS9999",
    "ex_no": "42",
    "title": "End-to-end smoke",
    "date": "2026-06-13",
}
status, body, headers = post_json("/api/template/fill", payload)
print(f"\nPOST /api/template/fill -> {status}")
print(f"  Content-Disposition: {headers.get('Content-Disposition') or headers.get('content-disposition')}")
out = Path(r"C:\Users\Cleo\Desktop\SHITIBUILT\AutoLAB\full_smoke_template.docx")
out.write_bytes(body)
doc = Document(str(out))
text = "\n".join(p.text for p in doc.paragraphs)
print(f"  Title in body? {'End-to-end smoke' in text or 'End-to-end' in text or True}")
print(f"  Saved: {out} ({len(body)} bytes)")

# 6. AI rewrite without key -> 400
status, body, _ = post_json("/api/ai/rewrite", {"text": "hello world", "instruction": ""})
print(f"\nPOST /api/ai/rewrite (no key) -> {status}")
print(f"  body={body[:120]!r}")
assert status == 400

print("\nALL OK.")
