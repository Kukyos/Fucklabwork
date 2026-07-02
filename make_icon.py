"""Generate static/icon.ico — a B&W 'A' mark for the window + taskbar."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "static" / "icon.ico"
SIZES = [256, 128, 64, 48, 32, 16]


def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (10, 10, 10, 255))
    draw = ImageDraw.Draw(img)
    pt = max(int(size * 0.72), 10)
    font = None
    for candidate in ("arialbd.ttf", "arial.ttf", "segoeuib.ttf"):
        try:
            font = ImageFont.truetype(f"C:/Windows/Fonts/{candidate}", pt)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    text = "A"
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1] - max(int(size * 0.02), 1)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    images = [render(s) for s in SIZES]
    # Pillow writes multi-resolution ICO from the largest, appending the rest
    images[0].save(OUT, format="ICO", sizes=[(s, s) for s in SIZES], append_images=images[1:])
    print(f"Wrote {OUT}  sizes: {SIZES}")


if __name__ == "__main__":
    main()
