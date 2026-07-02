"""Smoke test the running web server's /api/replace endpoint."""

import urllib.request
import uuid
from pathlib import Path

from docx import Document
from autolab import iter_all_paragraphs

SRC = Path(r"C:\Users\Cleo\Desktop\Labs Sem4\CN\EX1.docx")
DST = Path(__file__).parent / "EX1_via_api.docx"
URL = "http://127.0.0.1:8765/api/replace"
FIND = "URK24CS1021"
REPL = "URK24CS9999"


def build_multipart(file_path: Path, find: str, repl: str):
    boundary = "----autolabboundary" + uuid.uuid4().hex
    parts = []
    parts.append(f"--{boundary}\r\n"
                 f'Content-Disposition: form-data; name="find"\r\n\r\n{find}\r\n')
    parts.append(f"--{boundary}\r\n"
                 f'Content-Disposition: form-data; name="replace"\r\n\r\n{repl}\r\n')
    head = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n")
    tail = f"\r\n--{boundary}--\r\n"
    body = ("".join(parts) + head).encode() + file_path.read_bytes() + tail.encode()
    return body, f"multipart/form-data; boundary={boundary}"


body, ctype = build_multipart(SRC, FIND, REPL)
req = urllib.request.Request(URL, data=body, method="POST", headers={"Content-Type": ctype})
with urllib.request.urlopen(req) as resp:
    print(f"POST {URL} -> {resp.status}")
    print(f"X-Replace-Count: {resp.headers.get('X-Replace-Count')}")
    print(f"Content-Disposition: {resp.headers.get('Content-Disposition')}")
    DST.write_bytes(resp.read())

print(f"Saved: {DST} ({DST.stat().st_size} bytes)")

doc = Document(str(DST))
text = "\n".join(p.text for p in iter_all_paragraphs(doc))
old, new = text.count(FIND), text.count(REPL)
print(f"In response: old hits={old}, new hits={new}")
print("PASS" if old == 0 and new >= 1 else "FAIL")
