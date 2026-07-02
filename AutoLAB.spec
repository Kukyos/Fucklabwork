# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for AutoLAB — single-file Windows build.

Build:   pyinstaller AutoLAB.spec --clean --noconfirm
Output:  dist/AutoLAB.exe
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = [
    ("static", "static"),
]
# python-docx ships with XML templates it loads at runtime
datas += collect_data_files("docx")

hiddenimports = [
    # uvicorn does dynamic imports of its loop/protocol/lifespan plugins
    *collect_submodules("uvicorn"),
    # pywebview's Windows backends
    "webview.platforms.edgechromium",
    "webview.platforms.mshtml",
    "clr",
    # pydantic v2 occasionally needs a nudge under PyInstaller
    "pydantic.deprecated.decorator",
    # lazily imported by server.py
    "make_template",
]

a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",  # we dropped the Tk UI
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "pytest",
        "IPython",
        "notebook",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AutoLAB",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="static/icon.ico",
)
