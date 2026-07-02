"""Smoke test the full solve pipeline offline: run -> render -> assemble.

Q1: bit stuffing (single program)         — the classic CN experiment
Q2: TCP echo (server/client pair mode)    — the blocking-server case
"""

from pathlib import Path
import shutil

from docx import Document

from autolab import iter_all_paragraphs, replace_in_docx
from assemble import add_solved_question
from labshot import render_code_shot, render_terminal_shot
from runner import run_pair, run_single

HERE = Path(__file__).parent
TEMPLATE = HERE / "template_empty.docx"
OUT = HERE / "EX_solved_test.docx"
URK = "URK24CS1021"

Q1_CODE = '''\
def bit_stuff(data: str) -> str:
    """Insert a 0 after every run of five consecutive 1s."""
    stuffed, count = [], 0
    for bit in data:
        stuffed.append(bit)
        count = count + 1 if bit == "1" else 0
        if count == 5:
            stuffed.append("0")
            count = 0
    return "".join(stuffed)


def bit_destuff(data: str) -> str:
    out, count, skip = [], 0, False
    for bit in data:
        if skip:
            skip = False
            count = 0
            continue
        out.append(bit)
        count = count + 1 if bit == "1" else 0
        if count == 5:
            skip = True
    return "".join(out)


frame = "0111111011111011111110"
stuffed = bit_stuff(frame)
print("Original frame :", frame)
print("Stuffed frame  :", stuffed)
print("De-stuffed     :", bit_destuff(stuffed))
print("Round-trip OK  :", bit_destuff(stuffed) == frame)
'''

Q2_SERVER = '''\
import socket

HOST, PORT = "127.0.0.1", 5051

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Server listening on {HOST}:{PORT} ...", flush=True)
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}", flush=True)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print("Received:", data.decode(), flush=True)
            conn.sendall(data)
    print("Client disconnected. Server closing.", flush=True)
'''

Q2_CLIENT = '''\
import socket

HOST, PORT = "127.0.0.1", 5051
messages = ["Hello Server", "Computer Networks Lab", "URK24CS1021"]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print(f"Connected to {HOST}:{PORT}")
    for msg in messages:
        s.sendall(msg.encode())
        echoed = s.recv(1024).decode()
        print(f"Sent: {msg!r}  ->  Echoed back: {echoed!r}")
print("All messages echoed correctly.")
'''

# --- 1. run everything for real ---------------------------------------------

r1 = run_single(Q1_CODE, language="python", filename="bitstuffing.py")
print(f"Q1 run: ok={r1.ok} exit={r1.exit_code} timed_out={r1.timed_out}")
assert r1.ok and "Round-trip OK  : True" in r1.output

srv, cli = run_pair(Q2_SERVER, Q2_CLIENT, language="python",
                    server_filename="echo_server.py", client_filename="echo_client.py")
print(f"Q2 server: ok={srv.ok} timed_out={srv.timed_out}")
print(f"Q2 client: ok={cli.ok} exit={cli.exit_code}")
assert cli.ok and "All messages echoed correctly." in cli.output
assert "Received: URK24CS1021" in srv.output

# --- 2. render screenshots ----------------------------------------------------

cwd = r"C:\Users\{urk}\Desktop\Labs Sem4\CN"
shots = {
    "q1_code": render_code_shot(Q1_CODE, language="python", filename="bitstuffing.py"),
    "q1_out": render_terminal_shot(r1.output, command=r1.command, cwd=cwd,
                                   urk=URK, urk_mode="line"),
    "q2_srv": render_terminal_shot(srv.output, command=srv.command, cwd=cwd,
                                   urk=URK, urk_mode="title", trailing_prompt=False),
    "q2_cli": render_terminal_shot(cli.output, command=cli.command, cwd=cwd,
                                   urk=URK, urk_mode="line"),
}
for name, png in shots.items():
    p = HERE / f"shot_{name}.png"
    p.write_bytes(png)
    print(f"rendered {p.name}: {len(png)} bytes")

# --- 3. fill template + assemble ---------------------------------------------

shutil.copyfile(TEMPLATE, OUT)
for find, repl in {
    "{{COURSE_TITLE}}": "Computer Networks Lab",
    "{{REGISTER_NUMBER}}": URK,
    "{{EX_NO}}": "1",
    "{{TITLE}}": "Framing and Socket Programming",
    "{{DATE}}": "02.07.2026",
}.items():
    replace_in_docx(OUT, OUT, find, repl)

doc = Document(str(OUT))
add_solved_question(
    doc, number="1", title="Bit Stuffing and De-stuffing",
    description="Implement bit stuffing: insert a 0 after five consecutive 1s "
                "in the frame, and verify de-stuffing recovers the original.",
    code=Q1_CODE, images=[shots["q1_code"], shots["q1_out"]],
)
add_solved_question(
    doc, number="2", title="TCP Echo Server and Client",
    description="Implement a TCP echo server and client using sockets. The "
                "client sends messages; the server echoes each back.",
    code=Q2_SERVER + "\n\n# ---- client ----\n\n" + Q2_CLIENT,
    images=[shots["q2_srv"], shots["q2_cli"]],
)
doc.save(str(OUT))

# --- 4. verify ----------------------------------------------------------------

doc = Document(str(OUT))
text = "\n".join(p.text for p in iter_all_paragraphs(doc))
checks = {
    "heading q1": "1. Bit Stuffing and De-stuffing" in text,
    "heading q2": "2. TCP Echo Server and Client" in text,
    "code as text": "def bit_stuff(data: str) -> str:" in text,
    "urk filled": URK in text,
    "images embedded": len(doc.inline_shapes) == 4,
}
for k, v in checks.items():
    print(f"  {k:16} -> {v}")
print(f"Saved: {OUT} ({OUT.stat().st_size} bytes)")
print("PASS" if all(checks.values()) else "FAIL")
