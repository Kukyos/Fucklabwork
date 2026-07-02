"""Gemini API client + docx image patching.

All AI calls in AutoLAB go through here. Uses the free-tier Gemini API
(https://aistudio.google.com -> Get API key, no card needed).
"""

from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
import zipfile

TEXT_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"
_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def gemini_call(
    parts: list[dict],
    *,
    api_key: str,
    model: str = TEXT_MODEL,
    system: str | None = None,
    max_tokens: int = 4000,
    timeout: int = 90,
    want_image: bool = False,
    force_json: bool = False,
) -> tuple[str, bytes | None]:
    """One generateContent call. Returns (text, image_bytes_or_None)."""
    gen_cfg: dict = {"maxOutputTokens": max_tokens}
    if want_image:
        gen_cfg["responseModalities"] = ["TEXT", "IMAGE"]
    if force_json:
        gen_cfg["responseMimeType"] = "application/json"
    payload: dict = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": gen_cfg,
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    req = urllib.request.Request(
        f"{_BASE}/{model}:generateContent",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "x-goog-api-key": api_key,
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read())
    text, image = "", None
    for part in body.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "text" in part and not text:
            text = part["text"].strip()
        blob = part.get("inlineData") or part.get("inline_data")
        if blob and image is None:
            image = base64.b64decode(blob["data"])
    return text, image


def strip_fences(text: str) -> str:
    """Remove markdown code fences Gemini sometimes wraps JSON in."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return text


# --- docx image patching ------------------------------------------------------

_IMG_EXTS = (".png", ".jpg", ".jpeg")
_MIN_BYTES = 2048  # skip icons/bullets


def patch_docx_images(
    docx_bytes: bytes, find: str, replace: str, api_key: str, max_images: int = 25
) -> tuple[bytes, int, int]:
    """Rewrite `find` -> `replace` inside images embedded in a docx.

    Each media file is scanned with Gemini vision; matches are re-rendered by
    the Gemini image model and written back under the SAME zip entry name, so
    the document layout/relationships are untouched.

    Returns (new_docx_bytes, patched_count, scanned_count).
    """
    zin = zipfile.ZipFile(io.BytesIO(docx_bytes))
    media = [
        n for n in zin.namelist()
        if n.startswith("word/media/") and n.lower().endswith(_IMG_EXTS)
    ][:max_images]

    patched: dict[str, bytes] = {}
    scanned = 0
    for name in media:
        data = zin.read(name)
        if len(data) < _MIN_BYTES:
            continue
        scanned += 1
        mime = "image/png" if name.lower().endswith(".png") else "image/jpeg"
        img_part = {"inlineData": {"mimeType": mime, "data": base64.b64encode(data).decode()}}

        verdict, _ = gemini_call(
            [img_part, {"text": f'Does this image contain the exact text "{find}"? Answer only YES or NO.'}],
            api_key=api_key, max_tokens=10, timeout=45,
        )
        if not verdict.upper().startswith("YES"):
            continue

        _, new_img = gemini_call(
            [img_part, {"text": (
                f'Edit this image: replace every occurrence of the text "{find}" '
                f'with "{replace}". Keep everything else pixel-identical — same '
                "font, size, colors, background, and layout. Output the edited image."
            )}],
            api_key=api_key, model=IMAGE_MODEL, want_image=True, timeout=120,
        )
        if not new_img:
            continue
        if mime == "image/jpeg":
            # Gemini returns PNG; keep the original entry's format.
            from PIL import Image
            buf = io.BytesIO()
            Image.open(io.BytesIO(new_img)).convert("RGB").save(buf, "JPEG", quality=92)
            new_img = buf.getvalue()
        patched[name] = new_img

    if not patched:
        return docx_bytes, 0, scanned

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, patched.get(item.filename, zin.read(item.filename)))
    return out.getvalue(), len(patched), scanned
