# Lab avatar POSKO v2 — chibi full-body 64x64, gaya sheet "POSKO Avatar Builder".
from PIL import Image

W = H = 64

def blank():
    return [["."] * W for _ in range(H)]

def put(g, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = c

def rgb(hexs):
    hexs = hexs.lstrip("#")
    return tuple(int(hexs[i:i+2], 16) for i in (0, 2, 4))

def shade(hexs, f):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * f))) for v in rgb(hexs))

def tint(hexs, f):
    return "#%02x%02x%02x" % tuple(int(v + (255 - v) * f) for v in rgb(hexs))

SKINS = ["#ffd9b8", "#f2bd8f", "#d99a5f", "#a06838"]
HEAD = {
    6: (27, 36), 7: (24, 39), 8: (22, 41), 9: (20, 43), 10: (19, 44),
    11: (18, 45), 12: (17, 46), 13: (17, 46), 14: (16, 47), 15: (16, 47),
    16: (16, 47), 17: (16, 47), 18: (16, 47), 19: (16, 47), 20: (16, 47),
    21: (16, 47), 22: (17, 46), 23: (17, 46), 24: (17, 46), 25: (18, 45),
    26: (18, 45), 27: (19, 44), 28: (20, 43), 29: (21, 42), 30: (22, 41),
    31: (24, 39), 32: (26, 37), 33: (28, 35),
}

def stamp(g, art, ox, oy):
    for dy, row in enumerate(art):
        for dx, ch in enumerate(row):
            if ch != ".":
                put(g, ox + dx, oy + dy, ch)

EYES = {
    "eye1": [".KKKKK.", "KEEEEKK", "KEWWEEK", "KEEEEEK", "KEEEEEK", ".KEEEK.", "..KKK.."],
    "eye2": [".......", ".......", "..KKK..", ".K...K.", "K.....K", ".......", "......."],
    "eye3": [".......", "KKKKKK.", ".KEEEK.", "..KEK..", "..KKK..", ".......", "......."],
    "eye4": [".KKKKK.", "KKKKKKK", "KEEEEK.", ".KKKKK.", ".......", ".......", "......."],
    "eye5": ["KKKKKKK", "KEEEEKK", "KEWWEEK", "KEEEEEK", "KEEEWWK", ".KEEEK.", "..KKK.."],
}
BROWS = {
    "brow1": ["KKKKKK."],
    "brow2": ["..KKKK.", "KK....."],
    "brow3": ["KK.....", ".KKKKK."],
}
MOUTHS = {
    "mouth1": ["K...K", ".KKK."],
    "mouth2": [".KKK.", "KWWWK", ".KKK."],
    "mouth3": ["KKKKK"],
    "mouth4": [".KKK.", "K...K", ".KKK."],
}

TOPS = {
    "top1": {"A": "#2e4b3f", "B": "#26402f", "C": "#8be04e", "style": "hoodie"},
    "top2": {"A": "#f0f0f0", "B": "#dcdcdc", "C": "#778087", "style": "kaos"},
    "top3": {"A": "#3a6fd8", "B": "#2f5cb5", "C": "#f0f0f0", "style": "jaket"},
    "top4": {"A": "#c93a3a", "B": "#a82e2e", "C": "#f0f0f0", "style": "jaket"},
    "top5": {"A": "#e8b83a", "B": "#c99a2e", "C": "#33302e", "style": "hoodie"},
    "top6": {"A": "#33333a", "B": "#26262c", "C": "#c9ced6", "style": "jaket"},
}
BOTTOMS = {
    "bottom1": ("#3a5a8c", "#2f4a75"),
    "bottom2": ("#333338", "#26262c"),
    "bottom3": ("#c9b18a", "#b39a72"),
    "bottom4": ("#3a5a8c", "#2f4a75"),  # pendek: warna sama jeans, kaki kulit di bawah
}
SHOES = {
    "shoe1": ("#f0f0f0", "#c9ced6"),
    "shoe2": ("#33333a", "#1f1f24"),
    "shoe3": ("#8a5a33", "#6f4525"),
    "shoe4": ("#e2703a", "#c25a2a"),
}

def draw_body(g, cfg):
    top = TOPS[cfg["top"]]
    # bawahan dulu (di belakang torso bawah)
    main, shd = BOTTOMS[cfg["bottom"]]
    short = cfg["bottom"] == "bottom4"
    for y in range(47, 50):
        for x in range(22, 42):
            g[y][x] = "b"  # pinggang celana
    leg_end = 52 if short else 57
    for y in range(50, leg_end + 1):
        for x in list(range(23, 31)) + list(range(33, 41)):
            g[y][x] = "b"
    if short:
        for y in range(53, 58):
            for x in list(range(23, 31)) + list(range(33, 41)):
                g[y][x] = "S"
    # torso
    for y in range(36, 48):
        x0 = 22 if y == 36 else 21
        x1 = 41 if y == 36 else 42
        for x in range(x0, x1 + 1):
            g[y][x] = "A"
    for y in range(46, 48):
        for x in range(21, 43):
            if g[y][x] == "A":
                g[y][x] = "B"
    # lengan + tangan
    for y in range(37, 48):
        for x in list(range(17, 21)) + list(range(43, 47)):
            g[y][x] = "B"
    for y in range(47, 50):
        for x in list(range(17, 21)) + list(range(43, 47)):
            g[y][x] = "S"
    g[49][17] = "."; g[49][20] = "."; g[49][43] = "."; g[49][46] = "."
    # detail gaya
    st = top["style"]
    if st == "hoodie":
        for y in (38, 39, 40):
            g[y][29] = "C"; g[y][34] = "C"
        for x in range(28, 36):
            g[36][x] = "B"; g[37][x] = "B" if x in (28, 35) else g[37][x]
        for y in range(42, 46):
            for x in range(26, 38):
                if y in (42, 45) or x in (26, 37):
                    g[y][x] = "B"
    elif st == "kaos":
        for x in range(27, 37):
            g[36][x] = "C"
        g[37][29] = "C"; g[37][34] = "C"
    else:  # jaket
        for y in range(37, 48):
            g[y][31] = "C"; g[y][32] = "C"
        g[36][28] = "C"; g[36][35] = "C"; g[37][29] = "C"; g[37][34] = "C"
    # sepatu
    for y in range(58, 61):
        for x in list(range(22, 31)) + list(range(33, 42)):
            g[y][x] = "u"
    for x in list(range(22, 31)) + list(range(33, 42)):
        g[60][x] = "v"
    g[58][22] = "."; g[58][41] = "."

def draw_head_face(g, cfg):
    for y, (x0, x1) in HEAD.items():
        for x in range(x0, x1 + 1):
            g[y][x] = "s" if (x >= x1 - 1 and y > 16) else "S"
    for y in (21, 22, 23):
        for x in (14, 15, 48, 49):
            g[y][x] = "S"
    for y in (34, 35):
        for x in range(28, 36):
            g[y][x] = "s"
    stamp(g, EYES[cfg["eyes"]], 20, 20); stamp(g, EYES[cfg["eyes"]], 36, 20)
    stamp(g, BROWS[cfg["brows"]], 20, 17); stamp(g, BROWS[cfg["brows"]], 36, 17)
    stamp(g, MOUTHS[cfg["mouth"]], 29, 29)
    for y in (26, 27):
        for x in list(range(18, 22)) + list(range(42, 46)):
            if g[y][x] in ("S", "s"):
                g[y][x] = "P"

def draw_hair(g, cfg):
    st = cfg["hair"]
    def cap(until, fringe=None):
        for y, (x0, x1) in HEAD.items():
            if y > until:
                break
            for x in range(x0, x1 + 1):
                g[y][x] = "H"
    if st == "hair6":
        cap(11)
    elif st == "hair1":
        cap(15)
        for (x, y) in [(24, 5), (25, 4), (26, 5), (30, 3), (31, 2), (32, 3), (35, 4), (36, 5), (21, 5), (38, 6)]:
            put(g, x, y, "H"); put(g, x, y + 1, "H")
        for (y, x0, x1) in [(16, 17, 22), (17, 17, 21), (18, 17, 20), (16, 41, 46), (17, 42, 46), (18, 43, 46)]:
            for x in range(x0, x1 + 1):
                g[y][x] = "H"
        for (x, y) in [(27, 16), (28, 17), (34, 16), (35, 17)]:
            g[y][x] = "H"
        for y in range(16, 25):
            g[y][16] = "H"; g[y][47] = "H"
    elif st == "hair2":
        cap(16)
        for y in range(17, 20):
            for x in range(17, 40 - (y - 17) * 5):
                g[y][x] = "H"
        for y in range(16, 23):
            g[y][16] = "H"; g[y][47] = "H"
    elif st == "hair3":
        cap(15)
        for y in (16, 17, 18):
            x0, x1 = HEAD[y]
            for x in range(x0, x1 + 1):
                g[y][x] = "H"
        for y in range(16, 25):
            g[y][16] = "H"; g[y][47] = "H"
    elif st == "hair4":
        cap(15)
        for y in (16, 17):
            x0, x1 = HEAD[y]
            for x in range(x0, x1 + 1):
                g[y][x] = "H"
        for y in range(16, 46):
            cols = (14, 15, 16, 17, 18) if y < 35 else (14, 15, 16)
            for x in cols:
                if g[y][x] in ("S", "s", ".", "A", "B"):
                    g[y][x] = "H"
            cols = (45, 46, 47, 48, 49) if y < 35 else (47, 48, 49)
            for x in cols:
                if g[y][x] in ("S", "s", ".", "A", "B"):
                    g[y][x] = "H"
    elif st == "hair5":
        cap(15)
        for y in (16, 17, 18):
            x0, x1 = HEAD[y]
            for x in range(x0, x1 + 1):
                g[y][x] = "H"
        for y in range(16, 30):
            for x in (14, 15, 16, 47, 48, 49):
                g[y][x] = "H"
    elif st == "hair7":  # ikal bergelombang
        cap(15)
        for cx in range(17, 47, 6):
            for (dx, y) in [(0, 16), (1, 17), (2, 18), (3, 18), (4, 17), (5, 16)]:
                if cx + dx <= 46:
                    g[y][cx + dx] = "H"
        for y in range(16, 26):
            g[y][16] = "H"; g[y][47] = "H"
    elif st == "hair8":  # kuncir dua
        cap(15)
        for y in (16, 17, 18):
            x0, x1 = HEAD[y]
            for x in range(x0, x1 + 1):
                g[y][x] = "H"
        for cols in ((10, 15), (48, 53)):
            for y in range(13, 38):
                wob = 1 if (y // 4) % 2 else 0
                shrink = 1 if y > 33 else 0
                for x in range(cols[0] + wob + shrink, cols[1] + 1 + wob - shrink):
                    g[y][x] = "H"
            g[13][cols[0] + 2] = "X"; g[13][cols[0] + 3] = "X"
    # shading: baris bawah tudung + sisi kanan -> h ; highlight kiri atas -> L
    for y in range(H):
        for x in range(W):
            if g[y][x] == "H":
                below = g[y + 1][x] if y + 1 < H else "."
                if below not in ("H",) and y > 13:
                    g[y][x] = "h"
    for (x, y) in [(24, 8), (25, 8), (26, 8), (23, 9), (24, 9), (25, 9), (23, 10), (24, 10)]:
        if g[y][x] == "H":
            g[y][x] = "L"

def outline_pass(g):
    out = [row[:] for row in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] == ".":
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and g[ny][nx] != ".":
                        out[y][x] = "O"
                        break
    return out

def compose(cfg):
    g = blank()
    skin = SKINS[cfg["skin"]]
    hairc = cfg["hairColor"]
    top = TOPS[cfg["top"]]
    bm, bs = BOTTOMS[cfg["bottom"]]
    sm, ss = SHOES[cfg["shoes"]]
    pal = {"S": skin, "s": shade(skin, 0.9), "K": "#38322e", "W": "#ffffff",
           "E": cfg["eyeColor"], "M": "#a85751", "P": "#f0a294",
           "H": hairc, "h": shade(hairc, 0.78), "L": tint(hairc, 0.35),
           "A": top["A"], "B": top["B"], "C": top["C"],
           "b": bm, "u": sm, "v": ss, "X": "#e2703a", "O": "#2e2a26"}
    acc = cfg.get("acc", "none")
    if acc in ACCS2:
        c1, c2 = ACCS2[acc]
        pal["1"] = hairc if c1 == "HAIR" else c1
        pal["2"] = hairc if c2 == "HAIR" else c2
    fr = cfg.get("frame", "none")
    if fr in FRAMES:
        pal["f"], pal["F"] = FRAMES[fr]
    draw_body(g, cfg)
    draw_head_face(g, cfg)
    draw_hair(g, cfg)
    draw_acc2(g, cfg)
    pet_colors = draw_pet(g, cfg)
    if pet_colors:
        for k, v in pet_colors.items():
            pal["PET" + k] = v
    draw_frame(g, cfg)
    g = outline_pass(g)
    if fr in FRAMES:
        # bingkai digambar ulang setelah outline agar tepinya bersih
        for y in range(H):
            for x in range(W):
                if x < 2 or x > 61 or y < 2 or y > 61:
                    g[y][x] = "f"
    return g, pal

def render(cfg, path, scale=8):
    g, pal = compose(cfg)
    img = Image.new("RGB", (W, H), (238, 241, 238))
    px = img.load()
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c in pal:
                px[x, y] = rgb(pal[c])
    img.resize((W * scale, H * scale), Image.NEAREST).save(path)
    print("render:", path)

BASE = {"skin": 0, "hair": "hair1", "hairColor": "#33302e", "eyes": "eye1",
        "eyeColor": "#3a3238", "brows": "brow1", "mouth": "mouth1",
        "top": "top1", "bottom": "bottom1", "shoes": "shoe1"}

if __name__ == "__main__":
    render(BASE, "/home/hatch/workspace/posko/avatar-lab2/base.png")
    render(dict(BASE, hair="hair8", hairColor="#e88bb0", top="top2", mouth="mouth2"),
           "/home/hatch/workspace/posko/avatar-lab2/kuncir.png")
    render(dict(BASE, hair="hair4", hairColor="#5a3a26", eyes="eye5", eyeColor="#3a6fd8", top="top3"),
           "/home/hatch/workspace/posko/avatar-lab2/panjang.png")

# ================= AKSESORIS / PET / FRAME (v2) =================
ACCS2 = {
    "acc_topi_posko": ("#2b2b30", "#8be04e"), "acc_topi_putih": ("#f0f0f0", "#c9ced6"),
    "acc_kacamata": ("#38322e", "#38322e"), "acc_headphone": ("#33333a", "#3a6fd8"),
    "acc_kucing": ("HAIR", "#f0a294"), "acc_halo": ("#f2c53d", "#f2c53d"),
    "acc_tanduk": ("#c93a3a", "#a82e2e"), "acc_masker": ("#f4f4f4", "#d9dee3"),
    "acc_syal": ("#c93a3a", "#a82e2e"),
}

def draw_acc2(g, cfg):
    a = cfg.get("acc", "none")
    if a in ("acc_topi_posko", "acc_topi_putih"):
        for (y, x0, x1) in [(3, 26, 37), (4, 23, 40), (5, 21, 42), (6, 19, 44), (7, 18, 45), (8, 17, 46), (9, 17, 46), (10, 16, 47)]:
            for x in range(x0, x1 + 1):
                g[y][x] = "1"
        for x in range(15, 49):
            g[11][x] = "1"
        for x in range(14, 50):
            g[12][x] = "1"
        for y in (6, 7, 8, 9):
            for x in range(27, 37):
                g[y][x] = "W"
        g[7][30] = "2"; g[7][31] = "2"; g[8][30] = "2"; g[8][31] = "2"
    elif a == "acc_kacamata":
        for (x0, x1) in ((17, 28), (35, 46)):
            for x in range(x0, x1 + 1):
                put(g, x, 19, "1"); put(g, x, 28, "1")
            for y in range(19, 29):
                put(g, x0, y, "1"); put(g, x1, y, "1")
        for x in range(29, 35):
            put(g, x, 22, "1")
    elif a == "acc_headphone":
        for (y, x0, x1) in [(2, 26, 37), (3, 22, 41), (4, 19, 44), (5, 17, 46), (6, 16, 47)]:
            for x in range(x0, x1 + 1):
                if g[y][x] in ("H", "h", "L", "."):
                    g[y][x] = "1"
        for cx in (10, 49):
            for y in range(19, 30):
                for x in range(cx, cx + 6):
                    g[y][x] = "1"
            for y in range(23, 27):
                for x in range(cx + 1, cx + 5):
                    g[y][x] = "2"
    elif a == "acc_kucing":
        for bx in (12, 44):
            rows = {0: (4, 4), 1: (3, 5), 2: (2, 6), 3: (1, 6), 4: (1, 7), 5: (0, 7), 6: (0, 7), 7: (0, 6)}
            for y, (dx0, dx1) in rows.items():
                for dx in range(dx0, dx1 + 1):
                    g[y][bx + dx] = "1"
            g[3][bx + 4] = "2"; g[4][bx + 4] = "2"; g[4][bx + 5] = "2"
    elif a == "acc_halo":
        for x in range(25, 39):
            g[1][x] = "1"; g[2][x] = "1"
        g[3][23] = "1"; g[3][24] = "1"; g[3][39] = "1"; g[3][40] = "1"
    elif a == "acc_tanduk":
        for (x, y) in [(15, 9), (15, 8), (16, 7), (16, 6), (17, 5), (18, 3), (48, 9), (48, 8), (47, 7), (47, 6), (46, 5), (45, 3)]:
            g[y][x] = "1"
    elif a == "acc_masker":
        for y in range(25, 33):
            x0 = 24 if y in (25, 32) else 23
            x1 = 39 if y in (25, 32) else 40
            for x in range(x0, x1 + 1):
                g[y][x] = "1"
        for x in range(25, 39):
            g[28][x] = "2"
        g[27][16] = "2"; g[27][47] = "2"
    elif a == "acc_syal":
        for y in range(34, 38):
            for x in range(20, 44):
                if g[y][x] != ".":
                    g[y][x] = "1"
        for y in range(38, 45):
            for x in range(36, 41):
                g[y][x] = "1" if (y // 2) % 2 == 0 else "2"
        g[44][36] = "1"; g[44][38] = "1"; g[44][40] = "1"

PETS = {
    "pet_kucing": (["..a..........a..",
                    "..aa........aa..",
                    "..aabbaaaabbaa..",
                    ".aaaaaaaaaaaaaa.",
                    ".aKaaaaaaaaaKa..",
                    ".aaaaaMMaaaaaa..",
                    "..aaaaaaaaaa....",
                    "...aaaaaaaaaa...",
                    "...accccccaa....",
                    "...accccccaa....",
                    "...aaaaaaaaaa...",
                    "...aa.....aa....",
                    "..aaa.....aaa..."],
                   {"a": "#e8973f", "b": "#c97a28", "c": "#ffe9d6"}),
    "pet_penguin": ([".....aaaaaa.....",
                     "....aaaaaaaa....",
                     "....aKaaaaKa....",
                     "....aaabbaa.....",
                     "...aaaaaaaaaa...",
                     "...acccccc ca...".replace(" ", ""),
                     "...accccccca....",
                     "...accccccca....",
                     "....aaaaaaaa....",
                     "....aaaaaaaa....",
                     "...bbb....bbb..."],
                   {"a": "#33333a", "b": "#e2703a", "c": "#f4f4f4"}),
    "pet_bebek": ([".....aaaaaa.....",
                   "....aaaaaaaa....",
                   "....aKaaaaKa....",
                   "....aabbbba.....",
                   ".....aaaaaa.....",
                   "....aaaaaaaa....",
                   "..baaaaaaaaab...",
                   "..baaaaaaaaab...",
                   "...aaaaaaaaaa...",
                   "....aaaaaaaa....",
                   "....bbb..bbb...."],
                  {"a": "#f2c53d", "b": "#e2703a", "c": "#f2c53d"}),
}

def draw_pet(g, cfg):
    p = cfg.get("pet", "none")
    if p not in PETS:
        return
    art, colors = PETS[p]
    w = max(len(r) for r in art)
    art = [r.ljust(w, ".") for r in art]
    oy = 62 - len(art)
    for dy, row in enumerate(art):
        for dx, ch in enumerate(row):
            if ch in colors:
                put(g, 47 + dx, oy + dy, "PET" + ch)
    return colors

FRAMES = {
    "frame1": ("#2e4b3f", "#8be04e"),
    "frame2": ("#3a6fd8", "#bcd6ff"),
    "frame3": ("#d9a441", "#f7dc8a"),
    "frame4": ("#8a5fc0", "#d3b8f2"),
}

def draw_frame(g, cfg):
    f = cfg.get("frame", "none")
    if f not in FRAMES:
        return
    for y in range(H):
        for x in range(W):
            if x < 2 or x > 61 or y < 2 or y > 61:
                g[y][x] = "f"
            elif x == 2 or x == 61 or y == 2 or y == 61:
                if (x + y) % 7 < 5:
                    g[y][x] = "F"
