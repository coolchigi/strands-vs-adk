"""Same question, same AWS docs server, two answers.

The steps are the tool calls (search_documentation, read_documentation) from one traced run of each side on 29 September 2026
(examples/mcp_strands.py and examples/mcp_adk.py): Claude searched once and answered 5 TB,
Gemini searched, read the S3 FAQ page and searched again, and answered 50 TB.
"""
import os
from PIL import Image, ImageDraw, ImageFont

SS = 4
OUT = 1.5
W, H = 900 * SS, 430 * SS
BG = (58, 24, 58); DIM = (140, 100, 136); LINE = (104, 54, 104); WHITE = (250, 238, 248); MUTED = (200, 168, 196)
STRANDS = (255, 168, 38); ADK = (96, 158, 255)
def font(s): return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", s * SS)
F_T, F_N, F_L, F_TAG = font(21), font(12), font(13), font(11)
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def text_c(d, xy, s, f, fill):
    x, y = xy; bb = d.textbbox((0, 0), s, font=f)
    d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]), s, font=f, fill=fill)

def pill(d, cx, cy, label, state, col):
    """state: 0 not reached, 1 lit now, 2 done"""
    bb = d.textbbox((0, 0), label, font=F_N); w, h = bb[2] - bb[0], bb[3] - bb[1]
    box = [cx - w / 2 - 11 * SS, cy - h / 2 - 8 * SS, cx + w / 2 + 11 * SS, cy + h / 2 + 8 * SS]
    if state == 1:
        d.rounded_rectangle(box, radius=7 * SS, fill=col, outline=col, width=2 * SS)
        text_c(d, (cx, cy), label, F_N, BG)
    else:
        d.rounded_rectangle(box, radius=7 * SS, fill=BG, outline=col if state == 2 else DIM, width=2 * SS)
        text_c(d, (cx, cy), label, F_N, WHITE if state == 2 else DIM)

SIDES = [
    ("STRANDS  ·  Claude Sonnet 4.6", STRANDS,
     ["search docs", "answer: 5 TB"],
     "searched once, got 5 TB and 50 TB back, picked 5 TB"),
    ("ADK  ·  Gemini 3.8 Flash", ADK,
     ["search docs", "read page", "search docs", "answer: 50 TB"],
     "kept searching, read the S3 FAQ page, answered 50 TB"),
]
STEP = 8                      # frames per step
LONGEST = max(len(s[2]) for s in SIDES)
FR = STEP * (LONGEST + 3)     # hold the finished picture for a moment

def panel(d, y, name, col, steps, cap, k):
    text_c(d, (W // 2, y - 42 * SS), name, F_L, col)
    gap = min(W / (len(steps) + 1), 225 * SS)
    xs = [W / 2 + (i - (len(steps) - 1) / 2) * gap for i in range(len(steps))]
    def half(s):
        bb = d.textbbox((0, 0), s, font=F_N); return (bb[2] - bb[0]) / 2 + 11 * SS
    for i in range(len(steps) - 1):
        a, b = xs[i] + half(steps[i]) + 6 * SS, xs[i + 1] - half(steps[i + 1]) - 6 * SS
        d.line([a, y, b, y], fill=LINE, width=2 * SS)
        d.polygon([(b, y), (b - 8 * SS, y - 4 * SS), (b - 8 * SS, y + 4 * SS)], fill=LINE)
    now = k // STEP
    for i, s in enumerate(steps):
        state = 1 if i == now or (i == len(steps) - 1 and now >= i) else (2 if i < now else 0)
        pill(d, xs[i], y, s, state, col)
    text_c(d, (W // 2, y + 40 * SS), cap if now >= len(steps) - 1 else "", F_TAG, mix(BG, col, 0.9))

frames = []
for k in range(FR):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    text_c(d, (W // 2, 30 * SS), "Same question, same AWS docs server:", F_T, WHITE)
    text_c(d, (W // 2, 56 * SS), "how big can a single S3 object be?", F_T, WHITE)
    for j, (name, col, steps, cap) in enumerate(SIDES):
        panel(d, (150 + j * 170) * SS, name, col, steps, cap, k)
    d.line([(90 * SS, 235 * SS), (810 * SS, 235 * SS)], fill=LINE, width=1 * SS)
    text_c(d, (W // 2, 412 * SS), "AWS's page says: each object can be up to 50 TB in size", F_TAG, MUTED)
    img = img.resize((int(900 * OUT), int(430 * OUT)), Image.LANCZOS)
    frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=64))
out = os.path.join(os.path.dirname(__file__), "same-question.gif")
frames[0].save(out, save_all=True, append_images=frames[1:], duration=160, loop=0, optimize=True, disposal=2)
print(out, os.path.getsize(out) // 1024, "KB")
