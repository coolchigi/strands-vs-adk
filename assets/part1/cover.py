"""Part 1 cover image, sized for Dev.to so nothing important gets cropped.

Dev.to renders covers at 1000x420 with fit=cover, so anything that is not
roughly 2.38:1 loses its top and bottom. This is drawn at that ratio.
"""
import os
from PIL import Image, ImageDraw, ImageFont

SS = 4                      # supersample, then downsample for antialiasing
CW, CH = 1000, 420          # Dev.to's cover box
OUT = 2                     # retina
W, H = CW * SS, CH * SS

BG = (58, 24, 58); LINE = (104, 54, 104); WHITE = (250, 238, 248); MUTED = (200, 168, 196)
STRANDS = (255, 168, 38); ADK = (96, 158, 255)

def font(sz):
    return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", sz * SS)

F_BIG, F_VS, F_SUB, F_TAG = font(54), font(26), font(19), font(15)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def text_c(xy, s, f, fill):
    x, y = xy
    b = d.textbbox((0, 0), s, font=f)
    d.text((x - (b[2]-b[0])/2 - b[0], y - (b[3]-b[1])/2 - b[1]), s, font=f, fill=fill)

# one continuous divider rather than two floating stubs
d.line([(500*SS, 78*SS), (500*SS, 236*SS)], fill=LINE, width=2*SS)

# the two framework names, the article's whole shape in one line
text_c((295*SS, 148*SS), "Strands", F_BIG, STRANDS)
text_c((705*SS, 148*SS), "ADK",     F_BIG, ADK)

# "vs" sits on the divider, with the background knocked out behind it
b = d.textbbox((0, 0), "vs", font=F_VS)
vw, vh = b[2]-b[0], b[3]-b[1]
d.rectangle([500*SS - vw/2 - 14*SS, 148*SS - vh/2 - 10*SS,
             500*SS + vw/2 + 14*SS, 148*SS + vh/2 + 10*SS], fill=BG)
text_c((500*SS, 148*SS), "vs", F_VS, MUTED)

text_c((295*SS, 212*SS), "the Agent owns the loop", F_TAG, MUTED)
text_c((705*SS, 212*SS), "the Runner coordinates events", F_TAG, MUTED)

d.line([(390*SS, 264*SS), (610*SS, 264*SS)], fill=LINE, width=2*SS)
text_c((500*SS, 302*SS), "Building the same agent twice", F_SUB, WHITE)
text_c((500*SS, 342*SS), "Part 1: Hello World", F_TAG, MUTED)

img = img.resize((CW*OUT, CH*OUT), Image.LANCZOS)
out = os.path.join(os.path.dirname(__file__), "cover.png")
img.save(out, optimize=True)
print(out, os.path.getsize(out)//1024, "KB", img.size)
