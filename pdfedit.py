"""In-place PDF text editing.

Reads a PDF into editable text spans (each carrying its real font, size and
colour), and writes edited text back onto the page at the same spot in the
same font. Layout is preserved because nothing is re-flowed: the old glyphs
are redacted away and the new ones are drawn at the original baseline.

The font for a replacement is found automatically, best first:
  1. the page's own font resource for that span -- no re-embedding, so the
     document's existing character map is kept;
  2. a copy of that font, embedded fresh, when the resource cannot be reused;
  3. a Base-14 lookalike chosen from the span's style flags;
  4. the bundled CJK face, for text Base-14 cannot draw at all.

A rung is only skipped when it cannot render every character the user typed --
silently dropping glyphs is worse than a slightly different typeface. Whatever
happened is returned in the report, so the caller can say so rather than
letting the user discover it in the output.
"""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass

import pymupdf

# Span style bits, per PyMuPDF's text-extraction dict.
_ITALIC, _SERIF, _MONO, _BOLD = 2**1, 2**2, 2**3, 2**4

# Base-14 names keyed by (serif, mono, bold, italic).
_BASE14 = {
    ("sans", False, False): "helv", ("sans", True, False): "hebo",
    ("sans", False, True): "heit", ("sans", True, True): "hebi",
    ("serif", False, False): "tiro", ("serif", True, False): "tibo",
    ("serif", False, True): "tiit", ("serif", True, True): "tibi",
    ("mono", False, False): "cour", ("mono", True, False): "cobo",
    ("mono", False, True): "coit", ("mono", True, True): "cobi",
}

MIN_FONTSIZE = 6.0        # never shrink replacement text below this
RENDER_DPI = 110          # page preview resolution

# /api/pdf/parse returns every page as a base64 PNG in one JSON body, which
# measures ~0.13 MB per page at RENDER_DPI. Vercel caps a function's response
# body at 4.5 MB, so 30 pages (~3.8 MB, ~1s) is the hosted ceiling with room
# to spare. Running locally or on the desktop build there is no such cap --
# raise it with AUTOLAB_PDF_MAX_PAGES.
# ponytail: a page-range parameter on parse would lift the limit entirely;
# worth it only once someone actually brings a long PDF.
MAX_PAGES = int(os.environ.get("AUTOLAB_PDF_MAX_PAGES", "30"))


def _rgb(color: int) -> tuple[float, float, float]:
    """PyMuPDF reports span colour as a packed sRGB int."""
    return ((color >> 16 & 255) / 255, (color >> 8 & 255) / 255, (color & 255) / 255)


def _fallback_name(flags: int) -> str:
    family = "mono" if flags & _MONO else ("serif" if flags & _SERIF else "sans")
    return _BASE14[(family, bool(flags & _BOLD), bool(flags & _ITALIC))]


def span_id(page: int, block: int, line: int, span: int) -> str:
    return f"p{page}.b{block}.l{line}.s{span}"


@dataclass
class Span:
    id: str
    page: int
    text: str
    bbox: tuple[float, float, float, float]
    origin: tuple[float, float]
    font: str
    size: float
    color: int
    flags: int

    def as_dict(self) -> dict:
        return {
            "id": self.id, "page": self.page, "text": self.text,
            "bbox": [round(v, 2) for v in self.bbox],
            "font": self.font, "size": round(self.size, 2),
            "color": f"#{self.color:06x}", "flags": self.flags,
            "bold": bool(self.flags & _BOLD), "italic": bool(self.flags & _ITALIC),
            "mono": bool(self.flags & _MONO),
        }


def read_spans(doc: pymupdf.Document) -> list[Span]:
    """Every editable text span in the document, in reading order."""
    spans: list[Span] = []
    for pno, page in enumerate(doc):
        blocks = page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"]
        for bi, block in enumerate(blocks):
            for li, line in enumerate(block.get("lines", [])):
                for si, sp in enumerate(line["spans"]):
                    if not sp["text"].strip():
                        continue
                    spans.append(Span(
                        id=span_id(pno, bi, li, si), page=pno, text=sp["text"],
                        bbox=tuple(sp["bbox"]), origin=tuple(sp["origin"]),
                        font=sp["font"], size=sp["size"],
                        color=sp["color"], flags=sp["flags"],
                    ))
    return spans


def render_pages(doc: pymupdf.Document, dpi: int = RENDER_DPI) -> list[dict]:
    """Page previews as base64 PNGs, plus the PDF-point size of each page."""
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        pages.append({
            "width": round(page.rect.width, 2),
            "height": round(page.rect.height, 2),
            "png": base64.b64encode(pix.tobytes("png")).decode(),
        })
    return pages


def _norm(name: str) -> str:
    """Font names never match literally across a PDF's two spellings of them.

    A span says "Verdana" while the font object says "Verdana Regular"; subset
    fonts carry an "ABCDEF+" prefix on one side only. Normalise both ends
    before comparing, or the embedded font is never found and every edit
    quietly falls back to a Base-14 lookalike.
    """
    if "+" in name[:8]:
        name = name.split("+", 1)[1]
    name = "".join(ch for ch in name.lower() if ch.isalnum())
    return name[: -len("regular")] if name.endswith("regular") else name


def _embedded_fonts(doc: pymupdf.Document, page: pymupdf.Page) -> dict[str, tuple[str, bytes]]:
    """Map normalised font name -> (page resource name, font file bytes).

    Collected before any redaction runs, because applying redactions can drop a
    font resource that no longer has text using it.
    """
    found: dict[str, tuple[str, bytes]] = {}
    for xref, ext, _type, basefont, refname, *_ in page.get_fonts(full=True):
        if ext in ("n/a", ""):
            continue
        try:
            buf = doc.extract_font(xref)[3]
        except Exception:
            continue
        if not buf:
            continue
        for key in (_norm(basefont), _norm(refname)):
            found.setdefault(key, (refname, buf))
    return found


def _lookup(embedded: dict, span_font: str):
    key = _norm(span_font)
    if key in embedded:
        return embedded[key]
    # "Arial" vs "ArialMT" and friends: accept a unique one-sided prefix match.
    near = [v for k, v in embedded.items() if k.startswith(key) or key.startswith(k)]
    return near[0] if len(near) == 1 else None


def _missing(font: pymupdf.Font, text: str) -> str:
    """Characters this font has no glyph for -- drawing them would render blanks."""
    return "".join(sorted({ch for ch in text if not font.has_glyph(ord(ch))}))


def _resolve_font(page: pymupdf.Page, embedded: dict, span_font: str, flags: int,
                  text: str) -> tuple[str, str, pymupdf.Font, str, bytes | None]:
    """Pick a font that can actually draw `text`, preferring the span's own.

    Returns (name to draw with, how it was chosen, the font, characters still
    unrenderable, font bytes for the re-embed fallback). Each rung is only taken
    if the one above cannot render every character -- a font that drops glyphs
    is worse than a different typeface.
    """
    hit = _lookup(embedded, span_font)
    if hit:
        refname, buf = hit
        try:
            font = pymupdf.Font(fontbuffer=buf)
            # Coverage is checked against the extracted buffer, which is the
            # same subset the page resource holds.
            if not _missing(font, text):
                # Prefer the page's existing font resource over embedding a
                # second copy: it keeps the file small, and it keeps the PDF's
                # own ToUnicode map, so a typed space stays a space instead of
                # becoming U+00A0 and breaking copy-paste out of the document.
                # _draw() falls back to a copy if the resource name won't take.
                return refname, "original", font, "", buf
        except Exception:
            pass

    name = _fallback_name(flags)
    font = pymupdf.Font(fontname=name)
    gaps = _missing(font, text)
    if not gaps:
        return name, "fallback", font, "", None

    # Base-14 tops out at Latin-ish. The bundled CJK font covers CJK, Cyrillic
    # and most symbols, so prefer a typeface change over blank boxes.
    # ponytail: measured with Droid Sans Fallback but drawn as Heiti, so
    # shrink-to-fit is approximate here; bundle a real metric match if CJK
    # editing ever becomes a main path.
    wide = pymupdf.Font(fontname="cjk")
    still = _missing(wide, text)
    if len(still) < len(gaps):
        return "china-s", "unicode", wide, still, None
    return name, "fallback", font, gaps, None


def _draw(page: pymupdf.Page, origin, text: str, name: str, size: float,
          color, buf: bytes | None) -> str:
    """Draw the text, re-embedding the font only if the resource name won't take.

    A font resource name is only usable by insert_text on some documents, so
    the attempt has to be the real one -- drawing empty text as a probe
    succeeds regardless and proves nothing.
    """
    try:
        page.insert_text(origin, text, fontname=name, fontsize=size, color=color)
        return name
    except Exception:
        if buf is None:
            raise
        # Name the copy after its contents. insert_font() hands back the
        # existing resource when the name is already taken, so a fixed name
        # would make the second re-embedded font on a page silently draw in
        # the first one's typeface -- and the report would still claim the
        # span's own font.
        copy = "emb" + hashlib.sha1(buf).hexdigest()[:10]
        page.insert_font(fontname=copy, fontbuffer=buf)
        page.insert_text(origin, text, fontname=copy, fontsize=size, color=color)
        return copy


def _fit_size(font: pymupdf.Font, old: str, new: str, size: float,
              width: float) -> float:
    """Shrink the font just enough that `new` still fits where `old` sat.

    The budget is the old text's own advance width, not its ink bbox -- a bbox
    is the inked extent and runs a hair narrower than the advance, so measuring
    against it would shrink even a same-width swap.
    """
    budget = max(width, font.text_length(old, fontsize=size))
    if budget <= 0:
        return size
    needed = font.text_length(new, fontsize=size)
    if needed <= budget * 1.001:
        return size
    return max(MIN_FONTSIZE, size * budget / needed)


def apply_edits(doc: pymupdf.Document, edits: dict[str, str]) -> list[dict]:
    """Replace span text in place. `edits` maps span id -> new text.

    Returns one report entry per edit describing how it was applied, so the UI
    can flag the lossy cases (font substituted, text shrunk to fit) instead of
    letting the user discover them in the output.
    """
    by_page: dict[int, list[Span]] = {}
    for sp in read_spans(doc):
        if sp.id in edits and edits[sp.id] != sp.text:
            by_page.setdefault(sp.page, []).append(sp)

    report: list[dict] = []
    for pno, spans in by_page.items():
        page = doc[pno]
        embedded = _embedded_fonts(doc, page)

        # Redact every span on this page first: apply_redactions() wipes any text
        # under a redact rect, so drawing before it would erase our own work.
        for sp in spans:
            page.add_redact_annot(pymupdf.Rect(sp.bbox))
        page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_NONE,
            graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
        )

        # ponytail: redrawn text is appended to the page's content stream, so
        # it moves to the end of that page's extraction order. Visually and for
        # search it makes no difference, but selecting a whole page picks it up
        # out of sequence. Fixing it means content-stream surgery -- do that
        # only if reading order or screen-reader output starts to matter.
        for sp in spans:
            text = edits[sp.id]
            name, how, font, dropped, buf = _resolve_font(
                page, embedded, sp.font, sp.flags, text)
            size = _fit_size(font, sp.text, text, sp.size, sp.bbox[2] - sp.bbox[0])
            used = _draw(page, sp.origin, text, name, size, _rgb(sp.color), buf)
            if how == "original" and used != name:
                how = "embedded"
            report.append({
                "id": sp.id, "page": pno, "old": sp.text, "new": text,
                "font": {"original": sp.font, "embedded": sp.font,
                         "unicode": "CJK fallback"}.get(how, font.name),
                "font_source": how,
                "shrunk": round(size, 2) if size < sp.size else None,
                "dropped": dropped or None,
            })
    return report


def demo() -> None:
    """Self-check: edit text in a PDF, prove the old text is gone and layout held."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Reg No URK24CS1021", fontname="tiro", fontsize=14)
    page.insert_text((72, 130), "keep me", fontname="cour", fontsize=11)
    doc = pymupdf.open("pdf", doc.tobytes())

    spans = read_spans(doc)
    assert len(spans) == 2, spans
    target = spans[0]
    assert target.text == "Reg No URK24CS1021"
    assert target.size == 14, target.size
    assert "Times" in target.font or "tiro" in target.font.lower(), target.font

    report = apply_edits(doc, {target.id: "Reg No URK24CS1006"})
    assert len(report) == 1, report
    assert report[0]["shrunk"] is None, "same-length swap should not shrink"

    after = pymupdf.open("pdf", doc.tobytes())
    text = after[0].get_text()
    assert "URK24CS1006" in text, text
    assert "URK24CS1021" not in text, text
    assert "keep me" in text, "untouched span must survive redaction"

    edited = [s for s in read_spans(after) if "URK24CS1006" in s.text][0]
    assert abs(edited.origin[1] - target.origin[1]) < 0.5, "baseline moved"
    assert abs(edited.size - 14) < 0.5, f"size drifted: {edited.size}"

    # Overlong replacement must shrink to fit rather than run off the box.
    doc2 = pymupdf.open("pdf", after.tobytes())
    long_id = [s for s in read_spans(doc2) if "URK24CS1006" in s.text][0].id
    rep2 = apply_edits(doc2, {long_id: "Reg No URK24CS1006 and a whole lot more text"})
    assert rep2[0]["shrunk"] is not None, rep2

    # A genuinely embedded font must be reused, not swapped for a lookalike.
    # The two sides spell it differently ("Verdana" vs "Verdana Regular"), which
    # is exactly what naive name matching gets wrong.
    assert _norm("ABCDEF+Verdana Regular") == _norm("Verdana") == "verdana"
    emb = pymupdf.open()
    epage = emb.new_page()
    epage.insert_font(fontname="verd", fontfile=r"C:\Windows\Fonts\verdana.ttf")
    epage.insert_text((72, 100), "Hello URK24CS1021", fontname="verd", fontsize=13)
    # A second line in the same font, left untouched: redacting the only text
    # that used a font drops the resource, and then there is nothing to reuse.
    epage.insert_text((72, 140), "second line", fontname="verd", fontsize=13)
    emb = pymupdf.open("pdf", emb.tobytes())
    esp = [s for s in read_spans(emb) if "URK" in s.text][0]
    erep = apply_edits(emb, {esp.id: "Hello there URK24CS1006"})
    assert erep[0]["font_source"] == "original", erep
    out_span = [s for s in read_spans(pymupdf.open("pdf", emb.tobytes()))
                if "URK" in s.text][0]
    assert "Verdana" in out_span.font, out_span.font
    # Edited text must encode spaces the same way the source document did.
    # Re-embedding the font instead of reusing the page's resource gives the
    # copy a fresh ToUnicode map where a space becomes U+00A0 -- visually
    # identical, but it breaks copy-paste out of the PDF. (This fixture was
    # written by PyMuPDF, so its own spaces are already U+00A0; the assertion
    # is that we match the source, not that we hardcode U+0020.)
    src_space = next(c for c in esp.text if c in " \u00a0")
    edited_spaces = {c for c in out_span.text if c in " \u00a0"}
    assert edited_spaces == {src_space}, (repr(out_span.text), repr(src_space))

    # A subset font missing a typed glyph must fall back, never drop characters.
    emb2 = pymupdf.open("pdf", emb.tobytes())
    sid = [s for s in read_spans(emb2) if "URK" in s.text][0].id
    rep3 = apply_edits(emb2, {sid: "Hello \u4f60\u597d"})
    assert rep3[0]["font_source"] == "unicode", rep3
    assert rep3[0]["dropped"] is None, rep3
    assert "\u4f60\u597d" in pymupdf.open("pdf", emb2.tobytes())[0].get_text()

    # Two spans on one page that both have to re-embed, with DIFFERENT fonts.
    # Naming both copies the same thing makes the second reuse the first's
    # resource and draw in the wrong typeface, while still reporting its own.
    two = pymupdf.open()
    tp = two.new_page()
    tp.insert_font(fontname="fa", fontfile=r"C:\Windows\Fonts\verdana.ttf")
    tp.insert_font(fontname="fb", fontfile=r"C:\Windows\Fonts\georgia.ttf")
    tp.insert_text((72, 100), "alpha one", fontname="fa", fontsize=12)
    tp.insert_text((72, 200), "beta two", fontname="fb", fontsize=12)
    two = pymupdf.open("pdf", two.tobytes())
    ids = {s.text.split()[0]: s.id for s in read_spans(two)}
    apply_edits(two, {ids["alpha"]: "alpha edited", ids["beta"]: "beta edited"})
    got = {s.text.split()[0]: s.font for s in read_spans(pymupdf.open("pdf", two.tobytes()))}
    assert "Verdana" in got["alpha"], got
    assert "Georgia" in got["beta"], got

    # Editing a span must not take its same-line neighbour with it: redaction
    # removes everything intersecting the rect, and headings like
    # "Description:  body text" sit on one line as two adjacent spans.
    adj = pymupdf.open()
    ap = adj.new_page()
    ap.insert_text((72, 100), "Label:", fontname="hebo", fontsize=12)
    ap.insert_text((130, 100), "untouched neighbour", fontname="helv", fontsize=12)
    adj = pymupdf.open("pdf", adj.tobytes())
    label = [s for s in read_spans(adj) if "Label" in s.text][0]
    apply_edits(adj, {label.id: "Heading:"})
    after_adj = pymupdf.open("pdf", adj.tobytes())[0].get_text()
    assert "untouched neighbour" in after_adj, repr(after_adj)
    assert "Heading:" in after_adj, repr(after_adj)

    print("PASS pdfedit")


if __name__ == "__main__":
    demo()
