"""AutoLAB runner — actually execute the generated code, capture real output.

The screenshots labshot.py draws must show *real* output, so we run the
program on the student's own machine (same trust level as them pasting the
code into an IDE themselves). Timeouts protect against the classic CN-lab
failure mode: a socket server that blocks forever.

Two modes:
    run_single(code, ...)              -> one program, optional scripted stdin
    run_pair(server_code, client_code) -> start server, run client, stop server
                                          (half of every networks lab)

Supported languages: python, c, cpp, java. Compilation errors come back as
ok=False with the compiler output — still renderable, but the caller should
surface it instead of pasting a broken record.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

LANGS = ("python", "c", "cpp", "java")

_EXT = {"python": ".py", "c": ".c", "cpp": ".cpp", "java": ".java"}


@dataclass
class RunResult:
    ok: bool
    output: str          # stdout+stderr merged, as a terminal would show it
    exit_code: int
    timed_out: bool
    command: str         # display command for the screenshot prompt line
    stage: str = "run"   # "run" | "compile"


def _java_class_name(code: str) -> str:
    m = re.search(r"public\s+class\s+([A-Za-z_]\w*)", code)
    if not m:
        m = re.search(r"class\s+([A-Za-z_]\w*)", code)
    return m.group(1) if m else "Main"


def _display_command(language: str, src_name: str, cls: str = "") -> str:
    stem = Path(src_name).stem
    if language == "python":
        return f"python {src_name}"
    if language in ("c", "cpp"):
        return f"{stem}.exe" if sys.platform == "win32" else f"./{stem}"
    return f"java {cls}"


def _compile(language: str, src: Path, workdir: Path) -> tuple[list[str] | None, RunResult | None]:
    """Return (run_argv, None) on success or (None, error RunResult) on failure."""
    stem = src.stem
    if language == "python":
        return [sys.executable, str(src)], None
    if language in ("c", "cpp"):
        compiler = "gcc" if language == "c" else "g++"
        exe = workdir / (stem + (".exe" if sys.platform == "win32" else ""))
        proc = subprocess.run(
            [compiler, str(src), "-o", str(exe)],
            capture_output=True, text=True, cwd=workdir, timeout=60,
        )
        if proc.returncode != 0:
            return None, RunResult(False, proc.stderr or proc.stdout, proc.returncode,
                                   False, f"{compiler} {src.name}", stage="compile")
        return [str(exe)], None
    if language == "java":
        proc = subprocess.run(
            ["javac", str(src)], capture_output=True, text=True, cwd=workdir, timeout=60,
        )
        if proc.returncode != 0:
            return None, RunResult(False, proc.stderr or proc.stdout, proc.returncode,
                                   False, f"javac {src.name}", stage="compile")
        return ["java", "-cp", str(workdir), _java_class_name(src.read_text(encoding="utf-8"))], None
    raise ValueError(f"language must be one of {LANGS}")


def run_single(
    code: str,
    *,
    language: str = "python",
    stdin_text: str = "",
    timeout: float = 15.0,
    filename: str | None = None,
) -> RunResult:
    """Compile if needed, run to completion, capture merged output."""
    if language not in LANGS:
        raise ValueError(f"language must be one of {LANGS}")
    src_name = filename or f"program{_EXT[language]}"
    if language == "java":
        src_name = _java_class_name(code) + ".java"

    with tempfile.TemporaryDirectory(prefix="autolab_run_") as td:
        workdir = Path(td)
        src = workdir / src_name
        src.write_text(code, encoding="utf-8")

        argv, err = _compile(language, src, workdir)
        if err is not None:
            return err
        display = _display_command(language, src_name, argv[-1] if language == "java" else "")

        try:
            proc = subprocess.run(
                argv, input=stdin_text, capture_output=True, text=True,
                cwd=workdir, timeout=timeout,
            )
            merged = _merge_with_stdin(proc.stdout, proc.stderr, stdin_text)
            return RunResult(proc.returncode == 0, merged, proc.returncode, False, display)
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or "") if isinstance(e.stdout, str) else (e.stdout or b"").decode(errors="replace")
            errout = (e.stderr or "") if isinstance(e.stderr, str) else (e.stderr or b"").decode(errors="replace")
            merged = _merge_with_stdin(out, errout, stdin_text)
            merged += f"\n[stopped after {int(timeout)}s]"
            return RunResult(False, merged, -1, True, display)


def _merge_with_stdin(stdout: str, stderr: str, stdin_text: str) -> str:
    """A real screenshot shows typed input interleaved with prompts. We can't
    reproduce exact interleaving from captured pipes, so if the program read
    stdin we simply append what was 'typed' after the first prompt-looking
    chunk is impossible to detect reliably — instead we show output as-is.
    Callers that want typed-input realism should put the values in the code
    (hardcode) or accept output-only. stderr is appended after stdout, which
    matches how a console displays them for sequential programs."""
    out = stdout or ""
    if stderr:
        out = out + ("" if out.endswith("\n") or not out else "\n") + stderr
    return out


def run_pair(
    server_code: str,
    client_code: str,
    *,
    language: str = "python",
    client_stdin: str = "",
    startup_delay: float = 0.8,
    client_timeout: float = 15.0,
    server_grace: float = 2.0,
    server_filename: str = "server.py",
    client_filename: str = "client.py",
) -> tuple[RunResult, RunResult]:
    """Run a server/client pair: start server, run client, stop server.

    Returns (server_result, client_result). Server output is whatever it
    printed before we terminated it — which is exactly what a student's
    server-window screenshot shows.
    """
    if language not in LANGS:
        raise ValueError(f"language must be one of {LANGS}")
    if language == "java":
        server_filename = _java_class_name(server_code) + ".java"
        client_filename = _java_class_name(client_code) + ".java"
    else:
        server_filename = Path(server_filename).stem + _EXT[language]
        client_filename = Path(client_filename).stem + _EXT[language]

    with tempfile.TemporaryDirectory(prefix="autolab_pair_") as td:
        workdir = Path(td)
        s_src = workdir / server_filename
        c_src = workdir / client_filename
        s_src.write_text(server_code, encoding="utf-8")
        c_src.write_text(client_code, encoding="utf-8")

        s_argv, s_err = _compile(language, s_src, workdir)
        if s_err is not None:
            return s_err, RunResult(False, "server failed to compile — client not run",
                                    -1, False, "-", stage="compile")
        c_argv, c_err = _compile(language, c_src, workdir)
        if c_err is not None:
            return (RunResult(False, "client failed to compile — server not run",
                              -1, False, "-", stage="compile"), c_err)

        s_display = _display_command(language, server_filename,
                                     s_argv[-1] if language == "java" else "")
        c_display = _display_command(language, client_filename,
                                     c_argv[-1] if language == "java" else "")

        server = subprocess.Popen(
            s_argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=workdir,
        )
        time.sleep(startup_delay)

        client = run_single_argv(c_argv, c_display, stdin_text=client_stdin,
                                 timeout=client_timeout, cwd=workdir)

        server_timed_out = False
        try:
            server.terminate()
            s_out, _ = server.communicate(timeout=server_grace)
        except subprocess.TimeoutExpired:
            server.kill()
            s_out, _ = server.communicate()
            server_timed_out = True

        server_result = RunResult(True, s_out or "", server.returncode or 0,
                                  server_timed_out, s_display)
        return server_result, client


def run_single_argv(argv: list[str], display: str, *, stdin_text: str = "",
                    timeout: float = 15.0, cwd: Path | None = None) -> RunResult:
    """Run an already-compiled argv (used by run_pair for the client)."""
    try:
        proc = subprocess.run(argv, input=stdin_text, capture_output=True,
                              text=True, cwd=cwd, timeout=timeout)
        merged = _merge_with_stdin(proc.stdout, proc.stderr, stdin_text)
        return RunResult(proc.returncode == 0, merged, proc.returncode, False, display)
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") if isinstance(e.stdout, str) else (e.stdout or b"").decode(errors="replace")
        merged = out + f"\n[stopped after {int(timeout)}s]"
        return RunResult(False, merged, -1, True, display)
