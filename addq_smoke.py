"""Smoke test /api/document/add-question and the new shell layout."""

import json, urllib.request, uuid
from pathlib import Path
from docx import Document
from autolab import iter_all_paragraphs

BASE = "http://127.0.0.1:8765"
SRC = Path(r"C:\Users\Cleo\Desktop\Labs Sem4\CN\EX1.docx")
OUT = Path(__file__).parent / "EX1_addq_test.docx"


def multipart(file_path, fields):
    b = "----autolab" + uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{file_path.name}\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n".encode()
    )
    parts.append(file_path.read_bytes())
    parts.append(f"\r\n--{b}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={b}"


# capabilities — confirm version 0.4
with urllib.request.urlopen(f"{BASE}/api/capabilities") as r:
    caps = json.loads(r.read())
print(f"capabilities: desktop={caps['desktop']}  version={caps['version']}")

# add-question
body, ctype = multipart(SRC, {"number": "11", "title": "ipconfig /flushdns", "description": "Clears the DNS resolver cache. Useful when DNS records have changed and you want to force a refresh."})
req = urllib.request.Request(f"{BASE}/api/document/add-question", data=body, method="POST", headers={"content-type": ctype})
with urllib.request.urlopen(req) as resp:
    status = resp.status
    headers = dict(resp.headers)
    out_bytes = resp.read()
print(f"\nPOST /api/document/add-question -> {status}")
print(f"  X-Question-Added: {headers.get('x-question-added')}")
print(f"  Content-Disposition: {headers.get('Content-Disposition') or headers.get('content-disposition')}")
OUT.write_bytes(out_bytes)
print(f"  Saved: {OUT} ({len(out_bytes)} bytes)")

# Verify the new question is in the document
doc = Document(str(OUT))
all_text = "\n".join(p.text for p in iter_all_paragraphs(doc))
has_heading = "11. ipconfig /flushdns" in all_text
has_desc = "Clears the DNS resolver cache" in all_text
print(f"\nHeading present? {has_heading}")
print(f"Description present? {has_desc}")
print("PASS" if has_heading and has_desc else "FAIL")
