import math, os
from PIL import Image, ImageDraw, ImageFont

SS = 4          # supersample factor while drawing
OUT = 1.5         # final size multiplier (2x = retina at 900 CSS px)
W, H = 900 * SS, 400 * SS
BG = (58, 24, 58)
DIM = (140, 100, 136)
LINE = (104, 54, 104)
WHITE = (250, 238, 248)
MUTED = (200, 168, 196)
STRANDS = (255, 168, 38)
ADK = (96, 158, 255)

def font(sz, bold=False):
    return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", sz * SS)

F_TITLE, F_NODE = font(22, True), font(13, True)
F_LABEL, F_SUB, F_TAG = font(14, True), font(12), font(11, True)
F_BIG = font(30, True)

def mix(c1, c2, a):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))

LEFT  = {"cx": 230*SS, "cy": 208*SS, "r": 96*SS, "color": STRANDS,
         "nodes": ["Agent", "Model", "Tool"],
         "name": "STRANDS", "sub": "the Agent owns the loop"}
RIGHT = {"cx": 670*SS, "cy": 208*SS, "r": 96*SS, "color": ADK,
         "nodes": ["Runner", "Agent", "Model", "Tool", "Event"],
         "name": "ADK", "sub": "the Runner coordinates events"}

TRACK = 54*SS  # dot orbits inside the node ring, so they never collide

def pt(cx, cy, r, t):
    a = -math.pi / 2 + 2 * math.pi * t
    return (cx + r * math.cos(a), cy + r * math.sin(a))

def text_c(d, xy, s, f, fill):
    x, y = xy
    b = d.textbbox((0, 0), s, font=f)
    d.text((x - (b[2]-b[0])/2 - b[0], y - (b[3]-b[1])/2 - b[1]), s, font=f, fill=fill)

def pill(d, cx, cy, label, f, fg, border, bgfill):
    b = d.textbbox((0, 0), label, font=f)
    w, h = b[2]-b[0], b[3]-b[1]
    d.rounded_rectangle([cx-w/2-12*SS, cy-h/2-8*SS, cx+w/2+12*SS, cy+h/2+8*SS],
                        radius=7*SS, fill=bgfill, outline=border, width=2*SS)
    text_c(d, (cx, cy), label, f, fg)

def draw_panel(d, p, t):
    n = len(p["nodes"])
    cx, cy, col = p["cx"], p["cy"], p["color"]
    d.ellipse([cx-TRACK, cy-TRACK, cx+TRACK, cy+TRACK], outline=LINE, width=2*SS)
    text_c(d, (cx, cy-10*SS), str(n), F_BIG, col)
    text_c(d, (cx, cy+14*SS), "hops", F_TAG, MUTED)

    # the node the pulse is currently on
    active = int((t * n + 0.5) % n)
    for i, name in enumerate(p["nodes"]):
        x, y = pt(cx, cy, p["r"], i / n)
        hot = (i == active)
        pill(d, x, y, name, F_NODE,
             fg=BG if hot else WHITE,
             border=col if hot else DIM,
             bgfill=col if hot else BG)
        # spoke from ring to node, lit when active
        sx, sy = pt(cx, cy, TRACK, i / n)
        gx, gy = pt(cx, cy, p["r"] - 26*SS, i / n)
        d.line([sx, sy, gx, gy], fill=col if hot else LINE, width=(2 if hot else 1)*SS)

    # fading trail behind the pulse
    for j in range(10, 0, -1):
        tx, ty = pt(cx, cy, TRACK, t - j * 0.012)
        a = (1 - j / 10) ** 2
        r = (2 + 3.5 * a) * SS
        d.ellipse([tx-r, ty-r, tx+r, ty+r], fill=mix(BG, col, a * 0.85))
    px, py = pt(cx, cy, TRACK, t)
    d.ellipse([px-11*SS, py-11*SS, px+11*SS, py+11*SS], outline=mix(BG, col, 0.45), width=2*SS)
    d.ellipse([px-6*SS, py-6*SS, px+6*SS, py+6*SS], fill=col)

    text_c(d, (cx, 342*SS), p["name"], F_LABEL, col)
    text_c(d, (cx, 364*SS), p["sub"], F_SUB, MUTED)

FRAMES = 40
frames = []
for k in range(FRAMES):
    t = k / FRAMES
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    text_c(d, (W//2, 38*SS), "Same agent. Same tool call.", F_TITLE, WHITE)
    d.line([(W//2, 78*SS), (W//2, 318*SS)], fill=LINE, width=1*SS)
    draw_panel(d, LEFT, t)
    draw_panel(d, RIGHT, t)
    img = img.resize((int(900*OUT), int(400*OUT)), Image.LANCZOS)
    frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=64))

out = os.path.join(os.path.dirname(__file__), "agent-loop-vs-runner.gif")
frames[0].save(out, save_all=True, append_images=frames[1:],
               duration=98, loop=0, optimize=True, disposal=2)
print(out, os.path.getsize(out)//1024, "KB")
