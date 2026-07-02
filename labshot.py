"""AutoLAB labshot — render code & terminal output as screenshot-grade PNGs.

The point: students never take real screenshots. We run their code for real
(runner.py), then *draw* the screenshot — a Windows terminal window for the
output, a VS Code editor window for the code. Pixel output is deterministic,
always crisp, and never contains a stray taskbar or notification.

URK spoofing (teachers ask for the register number inside the screenshot):
    urk_mode="title"   -> window title is the URK (like running `title URK...`)
    urk_mode="line"    -> an `echo URK...` command + its output precede the run
    urk_mode="prompt"  -> the prompt path becomes C:\\Users\\{URK}\\...
    urk_mode="none"    -> off

Pure functions, bytes out. No UI. server.py and the smoke tests import this.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from pygments.util import ClassNotFound

# ---------------------------------------------------------------------------
# Fonts: prefer the user's Windows console fonts, fall back to DejaVu (Linux).

_FONT_CANDIDATES: list[tuple[str, str]] = [
    ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf"),
    ("C:/Windows/Fonts/CascadiaMono.ttf", "C:/Windows/Fonts/CascadiaMono.ttf"),
    ("C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/courbd.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
    ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Menlo.ttc"),
]

_UI_FONT_CANDIDATES: list[str] = [
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _mono_fonts(size: int) -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    for regular, bold in _FONT_CANDIDATES:
        if Path(regular).exists():
            reg = ImageFont.truetype(regular, size)
            bld = ImageFont.truetype(bold if Path(bold).exists() else regular, size)
            return reg, bld
    f = ImageFont.load_default()
    return f, f  # last resort; ugly but never crashes


def _ui_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _UI_FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _char_width(font: ImageFont.FreeTypeFont) -> float:
    box = font.getbbox("MMMMMMMMMM")
    return (box[2] - box[0]) / 10.0


def _line_height(font: ImageFont.FreeTypeFont) -> int:
    ascent, descent = font.getmetrics()
    return int((ascent + descent) * 1.18)


def _wrap(text: str, cols: int) -> list[str]:
    """Hard-wrap like a real terminal: split at exactly `cols` characters."""
    out: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.expandtabs(4)
        if line == "":
            out.append("")
            continue
        while len(line) > cols:
            out.append(line[:cols])
            line = line[cols:]
        out.append(line)
    return out


# ---------------------------------------------------------------------------
# Window chrome shared by both renderers.

@dataclass
class _Chrome:
    width: int
    titlebar_h: int
    title: str
    title_color: str
    bar_color: str
    body_color: str
    corner_radius: int = 12
    border_color: str = "#3c3c3c"

    def draw(self, total_h: int, ui_font: ImageFont.FreeTypeFont) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGBA", (self.width, total_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle(
            (0, 0, self.width - 1, total_h - 1),
            radius=self.corner_radius, fill=self.body_color, outline=self.border_color, width=2,
        )
        # Title bar: rounded on top, square at its bottom edge.
        d.rounded_rectangle(
            (0, 0, self.width - 1, self.titlebar_h + self.corner_radius),
            radius=self.corner_radius, fill=self.bar_color,
        )
        d.rectangle((0, self.titlebar_h, self.width - 1, self.titlebar_h + self.corner_radius),
                    fill=self.body_color)
        d.line((0, self.titlebar_h, self.width - 1, self.titlebar_h), fill=self.border_color)
        # Title text, left-aligned like Windows console windows.
        d.text((20, self.titlebar_h // 2), self.title, font=ui_font,
               fill=self.title_color, anchor="lm")
        self._buttons(d)
        return img, d

    def _buttons(self, d: ImageDraw.ImageDraw) -> None:
        """Minimize / maximize / close glyphs, right-aligned, vector-drawn."""
        cy = self.titlebar_h // 2
        slot = 62
        x_close = self.width - slot // 2 - 8
        x_max = x_close - slot
        x_min = x_max - slot
        g = 9  # glyph half-size
        c = self.title_color
        d.line((x_min - g, cy, x_min + g, cy), fill=c, width=2)
        d.rectangle((x_max - g, cy - g, x_max + g, cy + g), outline=c, width=2)
        d.line((x_close - g, cy - g, x_close + g, cy + g), fill=c, width=2)
        d.line((x_close - g, cy + g, x_close + g, cy - g), fill=c, width=2)


# ---------------------------------------------------------------------------
# Terminal renderer.

_WIN_BANNER = [
    "Microsoft Windows [Version 10.0.26100.4202]",
    "(c) Microsoft Corporation. All rights reserved.",
    "",
]

_PS_BANNER = [
    "Windows PowerShell",
    "Copyright (C) Microsoft Corporation. All rights reserved.",
    "",
]

_STYLES = {
    "cmd": dict(body="#0C0C0C", bar="#202020", text="#CCCCCC", prompt_suffix=">",
                default_title="Command Prompt", banner=_WIN_BANNER, ps_prefix=""),
    "powershell": dict(body="#012456", bar="#01173a", text="#EEEDF0", prompt_suffix=">",
                       default_title="Windows PowerShell", banner=_PS_BANNER, ps_prefix="PS "),
}


def render_terminal_shot(
    output: str,
    *,
    command: str = "python q1.py",
    cwd: str = r"C:\Users\{urk}\Desktop\Lab",
    style: str = "cmd",
    urk: str = "",
    urk_mode: str = "line",
    title: str | None = None,
    show_banner: bool = True,
    trailing_prompt: bool = True,
    width: int = 1400,
    font_size: int = 22,
    max_lines: int = 90,
) -> bytes:
    """Render terminal output as a Windows console window PNG (bytes)."""
    if style not in _STYLES:
        raise ValueError(f"style must be one of {sorted(_STYLES)}")
    st = _STYLES[style]

    # Resolve URK behaviour.
    user = urk if (urk and urk_mode == "prompt") else "Student"
    cwd_final = cwd.replace("{urk}", user).replace("{URK}", user)
    win_title = title or (urk if (urk and urk_mode == "title") else st["default_title"])

    reg, _bold = _mono_fonts(font_size)
    ui = _ui_font(int(font_size * 0.82))
    ch_w = _char_width(reg)
    pad = 26
    cols = max(20, int((width - 2 * pad) / ch_w))
    prompt = f"{st['ps_prefix']}{cwd_final}{st['prompt_suffix']}"

    lines: list[str] = []
    if show_banner:
        lines += st["banner"]
    if urk and urk_mode == "line":
        lines += _wrap(f"{prompt}echo {urk}", cols)
        lines.append(urk)
        lines.append("")
    lines += _wrap(f"{prompt}{command}", cols)
    body = _wrap(output.rstrip("\n"), cols) if output.strip() else []
    if len(body) > max_lines:
        kept = max_lines
        body = body[:kept] + [f"... ({len(body) - kept} more lines)"]
    lines += body
    if trailing_prompt:
        lines += ["", prompt]

    lh = _line_height(reg)
    titlebar_h = int(font_size * 2.0)
    total_h = titlebar_h + pad + lh * len(lines) + pad

    chrome = _Chrome(width=width, titlebar_h=titlebar_h, title=win_title,
                     title_color="#CCCCCC", bar_color=st["bar"], body_color=st["body"])
    img, d = chrome.draw(total_h, ui)

    y = titlebar_h + pad
    for line in lines:
        d.text((pad, y), line, font=reg, fill=st["text"])
        y += lh

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Code editor renderer (VS Code Dark+ look).

_DARKPLUS: list[tuple[object, str]] = [
    (Token.Comment, "#6A9955"),
    (Token.Keyword.Constant, "#569CD6"),
    (Token.Keyword.Type, "#569CD6"),
    (Token.Keyword.Declaration, "#569CD6"),
    (Token.Keyword, "#C586C0"),
    (Token.Operator.Word, "#C586C0"),
    (Token.Name.Function, "#DCDCAA"),
    (Token.Name.Class, "#4EC9B0"),
    (Token.Name.Namespace, "#4EC9B0"),
    (Token.Name.Builtin, "#DCDCAA"),
    (Token.Name.Decorator, "#DCDCAA"),
    (Token.Name.Exception, "#4EC9B0"),
    (Token.Name, "#9CDCFE"),
    (Token.Literal.String, "#CE9178"),
    (Token.Literal.Number, "#B5CEA8"),
    (Token.Operator, "#D4D4D4"),
    (Token.Punctuation, "#D4D4D4"),
]


def _token_color(ttype: object) -> str:
    while ttype is not Token:
        for t, color in _DARKPLUS:
            if ttype is t:
                return color
        ttype = ttype.parent  # type: ignore[attr-defined]
    return "#D4D4D4"


_LANG_TAB_DOTS = {"python": "#3572A5", "c": "#555555", "cpp": "#F34B7D",
                  "java": "#B07219", "javascript": "#F1E05A"}


def render_code_shot(
    code: str,
    *,
    language: str = "python",
    filename: str = "q1.py",
    width: int = 1400,
    font_size: int = 22,
    max_lines: int = 200,
) -> bytes:
    """Render source code as a VS Code-style editor window PNG (bytes)."""
    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        lexer = get_lexer_by_name("text")

    reg, _bold = _mono_fonts(font_size)
    ui = _ui_font(int(font_size * 0.82))
    ch_w = _char_width(reg)
    lh = _line_height(reg)

    titlebar_h = int(font_size * 1.9)
    tabbar_h = int(font_size * 2.0)
    pad = 24
    gutter_chars = 4

    # Tokenize into per-line colored segments.
    src_lines = code.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while src_lines and src_lines[-1].strip() == "":
        src_lines.pop()
    src_lines = src_lines[:max_lines]
    rendered: list[list[tuple[str, str]]] = [[] for _ in src_lines]
    row = 0
    for ttype, value in lex("\n".join(src_lines), lexer):
        color = _token_color(ttype)
        parts = value.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                row += 1
            if part and row < len(rendered):
                rendered[row].append((part.expandtabs(4), color))
    gutter_w = int(pad + gutter_chars * ch_w + pad * 0.6)
    body_h = pad + lh * max(1, len(rendered)) + pad
    total_h = titlebar_h + tabbar_h + body_h

    chrome = _Chrome(width=width, titlebar_h=titlebar_h,
                     title=f"{filename} - Visual Studio Code",
                     title_color="#ABABAB", bar_color="#323233", body_color="#1E1E1E")
    img, d = chrome.draw(total_h, ui)

    # Tab strip with one active tab.
    d.rectangle((1, titlebar_h + 1, width - 2, titlebar_h + tabbar_h), fill="#252526")
    tab_w = int(ch_w * (len(filename) + 7))
    d.rectangle((1, titlebar_h + 1, tab_w, titlebar_h + tabbar_h), fill="#1E1E1E")
    dot_color = _LANG_TAB_DOTS.get(language, "#888888")
    cy = titlebar_h + tabbar_h // 2
    d.ellipse((18, cy - 7, 32, cy + 7), fill=dot_color)
    d.text((44, cy), filename, font=ui, fill="#FFFFFF", anchor="lm")
    d.text((tab_w - 24, cy), "×", font=ui, fill="#ABABAB", anchor="mm")

    # Gutter + code.
    y = titlebar_h + tabbar_h + pad
    for i, segments in enumerate(rendered, start=1):
        d.text((gutter_w - int(pad * 0.6), y), str(i).rjust(gutter_chars),
               font=reg, fill="#6E7681", anchor="ra")
        x = float(gutter_w + pad * 0.4)
        for text, color in segments:
            d.text((x, y), text, font=reg, fill=color)
            x += ch_w * len(text)
        y += lh

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
