"""Where a review sends the run, in the learning system's graph (learning/flow.py).

A review sends the run forward, round the same stage again with its reasons, or back
upstream to research when that's where the problem started. The run shown is one path the
flow can take. Each stage gets 3 attempts, then goes forward with its problems recorded.
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

SS = 4
OUT = 1.5
W, H = 900 * SS, 360 * SS
BG = (58, 24, 58); DIM = (140, 100, 136); LINE = (104, 54, 104); WHITE = (250, 238, 248); MUTED = (200, 168, 196)
HOT = (255, 168, 38); BACK = (96, 158, 255)
def font(s): return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", s * SS)
F_T, F_N, F_TAG = font(21), font(12), font(12)
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def text_c(d, xy, s, f, fill):
    x, y = xy; bb = d.textbbox((0, 0), s, font=f)
    d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]), s, font=f, fill=fill)

NODES = ["research", "review", "curriculum", "review", "teaching", "done"]
XS = [W * (i + 1) / (len(NODES) + 1) for i in range(len(NODES))]
Y = 150 * SS
TRACK = Y + 24 * SS          # the dot runs under the pills, so labels stay readable

def arc(i_from, i_to, depth, n=48):
    x0, x1 = XS[i_from], XS[i_to]
    cx, rx = (x0 + x1) / 2, (x0 - x1) / 2
    return [(cx + rx * math.cos(math.pi * k / n), TRACK + depth * math.sin(math.pi * k / n)) for k in range(n + 1)]

def fwd(i_from, i_to):
    return [(XS[i], TRACK) for i in range(i_from, i_to + 1)]

AGAIN = arc(1, 0, 46 * SS)       # research review sends research round again
UPSTREAM = arc(3, 0, 92 * SS)    # curriculum review sends the run back to research

# (path, caption, which back edge is live)
SCENES = [
    (fwd(0, 1), "research, then its review", None),
    ([(XS[1], TRACK)] + AGAIN, "the reviewer has notes: research again, with the reasons", "again"),
    (fwd(0, 2), "no notes: forward to the course plan", None),
    (fwd(2, 3), "the plan, then its review", None),
    ([(XS[3], TRACK)] + UPSTREAM, "the problem started in research: back upstream", "upstream"),
    (fwd(0, 5), "research keeps what it verified, and the run goes forward", None),
]

def walk(path, t):
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]
    tot = sum(seg) or 1; want = max(0.0, min(1.0, t)) * tot; acc = 0
    for i, s in enumerate(seg):
        if acc + s >= want:
            f = (want - acc) / s if s else 0
            return (path[i][0] + (path[i + 1][0] - path[i][0]) * f, path[i][1] + (path[i + 1][1] - path[i][1]) * f)
        acc += s
    return path[-1]

def pill(d, cx, cy, label, hot):
    bb = d.textbbox((0, 0), label, font=F_N); w, h = bb[2] - bb[0], bb[3] - bb[1]
    review = label == "review"
    col = MUTED if review else HOT
    d.rounded_rectangle([cx - w / 2 - 10 * SS, cy - h / 2 - 7 * SS, cx + w / 2 + 10 * SS, cy + h / 2 + 7 * SS],
                        radius=(12 if review else 7) * SS, fill=col if hot else BG, outline=col if hot else DIM, width=2 * SS)
    text_c(d, (cx, cy), label, F_N, BG if hot else WHITE)

def draw_arc(d, pts, live):
    col = BACK if live else mix(BG, BACK, 0.25)
    d.line(pts, fill=col, width=(2 if live else 1) * SS)
    (ex, ey), (qx, qy) = pts[-1], pts[-4]
    ang = math.atan2(ey - qy, ex - qx); L, Wd = 10 * SS, 4.5 * SS
    d.polygon([(ex, ey), (ex - L * math.cos(ang) + Wd * math.sin(ang), ey - L * math.sin(ang) - Wd * math.cos(ang)),
               (ex - L * math.cos(ang) - Wd * math.sin(ang), ey - L * math.sin(ang) + Wd * math.cos(ang))], fill=col)

PER = 18
frames = []
for sc, (path, cap, live) in enumerate(SCENES):
    steps = PER + (6 if sc == len(SCENES) - 1 else 0)
    for k in range(steps):
        t = min(1.0, k / (PER - 4))
        img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
        text_c(d, (W // 2, 30 * SS), "Where a review sends the run", F_T, WHITE)
        for i in range(len(NODES) - 1):
            a, b = XS[i] + 50 * SS, XS[i + 1] - 50 * SS
            d.line([a, Y, b, Y], fill=LINE, width=2 * SS)
            d.polygon([(b, Y), (b - 8 * SS, Y - 4 * SS), (b - 8 * SS, Y + 4 * SS)], fill=LINE)
        draw_arc(d, AGAIN, live == "again")
        draw_arc(d, UPSTREAM, live == "upstream")
        px, py = walk(path, t)
        for i, n in enumerate(NODES):
            pill(d, XS[i], Y, n, abs(px - XS[i]) < 30 * SS and abs(py - TRACK) < 8 * SS)
        for j in range(9, 0, -1):
            tx, ty = walk(path, t - j * 0.02); a = (1 - j / 9) ** 2; r = (2 + 3.2 * a) * SS
            d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=mix(BG, HOT, a * 0.85))
        d.ellipse([px - 6 * SS, py - 6 * SS, px + 6 * SS, py + 6 * SS], fill=HOT)
        text_c(d, (W // 2, 300 * SS), cap, F_TAG, WHITE)
        text_c(d, (W // 2, 330 * SS), "each stage gets 3 attempts, then goes forward with its problems listed in the course", F_TAG, MUTED)
        img = img.resize((int(900 * OUT), int(360 * OUT)), Image.LANCZOS)
        frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=64))
out = os.path.join(os.path.dirname(__file__), "review-routing.gif")
frames[0].save(out, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True, disposal=2)
print(out, os.path.getsize(out) // 1024, "KB")
