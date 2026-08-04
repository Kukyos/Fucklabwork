import textwrap
from PIL import Image, ImageDraw, ImageFont

PAGE_W, PAGE_H = 1240, 1754
MARGIN = 70

FONT_DIR = "C:/Windows/Fonts/"
title_font = ImageFont.truetype(FONT_DIR + "arialbd.ttf", 40)
h2_font = ImageFont.truetype(FONT_DIR + "arialbd.ttf", 28)
body_font = ImageFont.truetype(FONT_DIR + "arial.ttf", 22)
code_font = ImageFont.truetype(FONT_DIR + "consola.ttf", 18)


def new_page():
    img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    return img, ImageDraw.Draw(img)


pages = []

img, d = new_page()
d.text((MARGIN, 140), "HTML Website Design Assignment", font=title_font, fill="black")
d.text((MARGIN, 220), "Theme: Travel Diary", font=h2_font, fill="black")
d.text((MARGIN, 270), "Page: index.html  (Home / Diary page)", font=h2_font, fill="black")
d.text((MARGIN, 340), "Name: A M Armaan", font=body_font, fill="black")
d.text((MARGIN, 375), "Register No: URK24CS1021", font=body_font, fill="black")
pages.append(img)

with open("index.html", encoding="utf-8") as f:
    raw_lines = f.read().splitlines()

code_lines = []
for raw in raw_lines:
    wrapped = textwrap.wrap(raw, width=95, subsequent_indent="    ", break_long_words=False, break_on_hyphens=False)
    code_lines.extend(wrapped or [""])

line_h = 24
lines_per_page = (PAGE_H - MARGIN * 2 - 60) // line_h

for start in range(0, len(code_lines), lines_per_page):
    chunk = code_lines[start:start + lines_per_page]
    img, d = new_page()
    d.text((MARGIN, 40), "Code: index.html", font=h2_font, fill="black")
    y = 100
    for line in chunk:
        d.text((MARGIN, y), line, font=code_font, fill="black")
        y += line_h
    pages.append(img)

shot_names = ["output_1_top.jpg", "output_2_photos.jpg", "output_3_media.jpg", "output_4_bottom.jpg"]
for i, name in enumerate(shot_names):
    shot = Image.open(name)
    ratio = (PAGE_W - MARGIN * 2) / shot.width
    new_size = (int(shot.width * ratio), int(shot.height * ratio))
    shot = shot.resize(new_size)

    img, d = new_page()
    label = "Output: index.html" if i == 0 else "Output: index.html (continued)"
    d.text((MARGIN, 40), label, font=h2_font, fill="black")
    paste_y = 100
    if paste_y + shot.height > PAGE_H - MARGIN:
        shot = shot.crop((0, 0, shot.width, PAGE_H - MARGIN - paste_y))
    img.paste(shot, (MARGIN, paste_y))
    pages.append(img)

pages[0].save("Assignment1_URK24CS1021.pdf", save_all=True, append_images=pages[1:])
print(f"wrote PDF with {len(pages)} pages")
