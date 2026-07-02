"""AutoLAB desktop launcher.

Runs the FastAPI server inside the same process on a random localhost port,
then opens a native window pointing at it. Sets AUTOLAB_DESKTOP=1 so the
desktop-only endpoints (saved URKs, preferences, future app linking) unlock.

Dev:    python desktop.py
Frozen: dist/AutoLAB/AutoLAB.exe  (built by AutoLAB.spec)
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path


def _bootstrap_path() -> None:
    """Make sure the source dir is importable in dev mode."""
    if not getattr(sys, "frozen", False):
        here = Path(__file__).resolve().parent
        if str(here) not in sys.path:
            sys.path.insert(0, str(here))


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _icon_path() -> str | None:
    """Resolve the app icon, whether frozen or running from source."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent
    candidate = base / "static" / "icon.ico"
    return str(candidate) if candidate.exists() else None


class JsApi:
    """Bridge exposed to the front-end as window.pywebview.api.*"""

    def pick_folder(self):
        try:
            import webview
            wins = webview.windows
            if not wins:
                return None
            result = wins[0].create_file_dialog(webview.FOLDER_DIALOG, allow_multiple=False)
            if not result:
                return None
            return result[0] if isinstance(result, (list, tuple)) else str(result)
        except Exception:
            return None


def main() -> int:
    os.environ["AUTOLAB_DESKTOP"] = "1"
    _bootstrap_path()

    # Import AFTER setting the env var so server.DESKTOP_MODE reads it.
    import uvicorn
    import webview
    from server import app  # direct import — avoids uvicorn's string-based discovery

    port = _free_port()
    cfg = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(cfg)

    t = threading.Thread(target=server.run, daemon=True)
    t.start()

    # Wait briefly for the loop to come up
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and not server.started:
        time.sleep(0.05)
    if not server.started:
        print("Server failed to start within 5 seconds.", file=sys.stderr)
        return 1

    create_kwargs = dict(
        title="AutoLAB",
        url=f"http://127.0.0.1:{port}",
        width=1000,
        height=740,
        min_size=(420, 600),
        background_color="#ffffff",
        js_api=JsApi(),
    )
    webview.create_window(**create_kwargs)
    try:
        webview.start(icon=_icon_path())
    finally:
        server.should_exit = True
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
