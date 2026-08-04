from PIL import Image, ImageDraw
import wave
import math
import struct

fav = Image.new("RGB", (32, 32), (255, 140, 0))
fd = ImageDraw.Draw(fav)
fd.polygon([(4, 26), (16, 8), (28, 26)], fill=(34, 139, 34))
fav.save("favicon.png")

rate = 22050
duration = 1.5
freq = 392.0
n = int(rate * duration)
frames = bytearray()
for i in range(n):
    t = i / rate
    fade = min(1.0, (n - i) / (rate * 0.3), i / (rate * 0.1))
    val = int(8000 * fade * math.sin(2 * math.pi * freq * t))
    frames += struct.pack("<h", val)

with wave.open("postcard-chime.wav", "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(rate)
    f.writeframes(bytes(frames))

print("assets done")
