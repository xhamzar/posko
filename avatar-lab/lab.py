# Lab desain avatar pixel POSKO: grid 48x48, layer digambar prosedural + stempel.
from PIL import Image

W = H = 48

def blank():
    return [["."] * W for _ in range(H)]

def put(g, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = c

def darken(hexs, f):
    hexs = hexs.lstrip("#")
    r, gg, b = (int(hexs[i:i+2], 16) for i in (0, 2, 4))
    r, gg, b = (max(0, min(255, int(v * f))) for v in (r, gg, b))
    return "#%02x%02x%02x" % (r, gg, b)

def lighten(hexs, f):
    return darken(hexs, f) if f < 1 else "#%02x%02x%02x" % tuple(
        max(0, min(255, int(int(hexs.lstrip('#')[i:i+2], 16) + (255 - int(hexs.lstrip('#')[i:i+2], 16)) * (f - 1)))) for i in (0, 2, 4))

SKINS = ["#ffd9b8", "#f2bd8f", "#d99a5f", "#a06838"]

HEAD_ROWS = {  # y: (x0, x1) inklusif
    4: (20, 27), 5: (17, 30), 6: (15, 32), 7: (13, 34), 8: (12, 35),
    9: (11, 36), 10: (11, 36), 11: (10, 37), 12: (10, 37), 13: (10, 37),
    14: (10, 37), 15: (10, 37), 16: (10, 37), 17: (11, 36), 18: (11, 36),
    19: (11, 36), 20: (12, 35), 21: (12, 35), 22: (13, 34), 23: (14, 33),
    24: (15, 32), 25: (16, 31), 26: (18, 29), 27: (20, 27),
}

def draw_head(g, skin):
    shade = darken(skin, 0.88)
    for y, (x0, x1) in HEAD_ROWS.items():
        for x in range(x0, x1 + 1):
            edge = x in (x0, x1) or y in (4, 27)
            g[y][x] = "s" if (x >= x1 - 1 and y > 12) else "S"
    # telinga
    for y in (15, 16, 17):
        for x in (8, 9, 38, 39):
            g[y][x] = "S"
    # leher
    for y in (28, 29):
        for x in range(21, 27):
            g[y][x] = "s"

def stamp(g, art, ox, oy, pal):
    for dy, row in enumerate(art):
        for dx, ch in enumerate(row):
            if ch != "." and ch in pal:
                put(g, ox + dx, oy + dy, ch)

# ---------- MATA (stempel 5x5 di (15,16) & (28,16)) ----------
EYES = {
    "eye1": [  # bulat besar
        ".KKK.",
        "KEEEK",
        "KEWEK",
        "KEEEK",
        ".KKK.",
    ],
    "eye2": [  # sipit senang (arc)
        ".....",
        ".K.K.",
        "KK.KK",
        ".....",
        ".....",
    ],
    "eye3": [  # tajam
        ".....",
        "KKKKK",
        ".KEK.",
        ".KKK.",
        ".....",
    ],
    "eye4": [  # ngantuk setengah
        ".KKK.",
        "KKKKK",
        "KEEEK",
        ".KKK.",
        ".....",
    ],
}
BROWS = {
    "brow1": ["KKKKK"],
    "brow2": [".KKK.", "K...K"],
    "brow3": ["K....", ".KKKK"],
}
MOUTHS = {
    "mouth1": ["K..K", ".KK."],          # senyum
    "mouth2": [".KK.", "KWWK", ".KK."],   # senyum lebar
    "mouth3": ["KKKK"],                    # datar
    "mouth4": [".KK.", "K..K", ".KK."],    # o kaget
}

def draw_face(g, cfg, pal):
    eye = EYES[cfg["eyes"]]
    stamp(g, eye, 15, 16, pal); stamp(g, eye, 28, 16, pal)
    br = BROWS[cfg["brows"]]
    stamp(g, br, 15, 14, pal); stamp(g, br, 28, 14, pal)
    stamp(g, MOUTHS[cfg["mouth"]], 22, 23, pal)
    # blush
    for y in (21, 22):
        for x in (12, 13, 14, 33, 34, 35):
            if g[y][x] in ("S", "s"):
                g[y][x] = "P"

# ---------- RAMBUT ----------
def draw_hair(g, cfg, pal):
    st = cfg["hair"]
    if st == "hair6":  # cepak: tudung tipis
        for y, (x0, x1) in HEAD_ROWS.items():
            if y > 9: break
            for x in range(x0, x1 + 1):
                g[y][x] = "H"
        return
    # tudung dasar menutupi kepala s/d baris 12 + poni per gaya
    for y, (x0, x1) in HEAD_ROWS.items():
        if y > 12: break
        for x in range(x0, x1 + 1):
            g[y][x] = "H"
    if st == "hair1":  # spiky acak
        spikes = [(18, 3), (19, 2), (20, 3), (23, 2), (24, 1), (25, 2), (27, 3), (29, 3), (15, 4), (31, 4)]
        for x, y in spikes:
            put(g, x, y, "H"); put(g, x, y + 1, "H")
        fringe = {13: (11, 16), 14: (11, 15), 15: (11, 14)}
        for y, (x0, x1) in fringe.items():
            for x in range(x0, x1 + 1): g[y][x] = "H"
        for y, (x0, x1) in {13: (31, 37), 14: (33, 37), 15: (34, 37)}.items():
            for x in range(x0, x1 + 1): g[y][x] = "H"
        # jambul poni tengah acak
        for (x, y) in [(21, 13), (22, 14), (26, 13), (27, 14)]:
            g[y][x] = "H"
        # jambang
        for y in range(13, 20):
            g[y][10] = "H"; g[y][37] = "H"
    elif st == "hair2":  # rapi belah samping
        for y in range(13, 16):
            for x in range(11, 30 - (y - 13) * 3):
                g[y][x] = "H"
        for y in range(13, 19):
            g[y][10] = "H"; g[y][37] = "H"
    elif st == "hair3":  # poni lurus
        for y in range(13, 15):
            x0, x1 = HEAD_ROWS[y]
            for x in range(x0, x1 + 1): g[y][x] = "H"
        for y in range(13, 20):
            g[y][10] = "H"; g[y][37] = "H"
    elif st == "hair4":  # panjang lurus
        for y in range(13, 15):
            x0, x1 = HEAD_ROWS[y]
            for x in range(x0, x1 + 1): g[y][x] = "H"
        for y in range(13, 34):
            for x in (9, 10, 11):
                if g[y][x] in ("S", "s", "."): g[y][x] = "H"
            for x in (36, 37, 38):
                if g[y][x] in ("S", "s", "."): g[y][x] = "H"
    elif st == "hair5":  # bob pendek
        for y in range(13, 16):
            x0, x1 = HEAD_ROWS[y]
            for x in range(x0, x1 + 1): g[y][x] = "H"
        for y in range(13, 24):
            for x in (9, 10):
                g[y][x] = "H"
            for x in (37, 38):
                g[y][x] = "H"
    # highlight simpel: beberapa titik L di tudung atas
    for (x, y) in [(18, 6), (19, 6), (20, 7), (17, 7)]:
        if g[y][x] == "H": g[y][x] = "L"

# ---------- BADAN / PAKAIAN ----------
def draw_body(g, cfg, tops, bottoms):
    # bawahan (strip bawah)
    bc = bottoms[cfg["bottom"]]
    for y in range(43, 48):
        for x in range(14, 34):
            g[y][x] = bc
    # torso + lengan
    top = tops[cfg["top"]]
    for y in range(30, 44):
        w = 13 + (2 if y > 33 else 0)
        for x in range(24 - w, 24 + w):
            g[y][x] = "A"
    for y in range(31, 43):  # lengan
        for x in list(range(8, 12)) + list(range(36, 40)):
            g[y][x] = "B"
    for y in range(43, 46):  # tangan
        for x in list(range(8, 12)) + list(range(36, 40)):
            g[y][x] = "S"
    t = TOPS[cfg["top"]].get("style", "kaos")
    if t == "hoodie":  # hoodie: tali + kantong
        for y in (31, 32):
            g[y][22] = "C"; g[y][25] = "C"
        for x in range(22, 26):
            g[30][x] = "B"
        for y in range(38, 42):
            for x in range(19, 29):
                if y in (38, 41) or x in (19, 28):
                    g[y][x] = "B"
    elif t == "kaos":  # kaos: rib leher
        for x in range(21, 27):
            g[30][x] = "C"
        g[31][22] = "C"; g[31][25] = "C"
    elif t == "jaket":  # jaket: ritsleting tengah + kerah terbuka
        for y in range(31, 44):
            g[y][23] = "C"; g[y][24] = "C"
        g[30][21] = "C"; g[30][26] = "C"; g[31][22] = "C"; g[31][25] = "C"

TOPS = {
    "top1": {"A": "#2e4b3f", "B": "#26402f", "C": "#8be04e", "style": "hoodie"},  # hoodie posko
    "top2": {"A": "#f0f0f0", "B": "#dcdcdc", "C": "#778087", "style": "kaos"},    # kaos putih
    "top3": {"A": "#3a6fd8", "B": "#2f5cb5", "C": "#f0f0f0", "style": "jaket"},   # jaket biru
    "top4": {"A": "#c93a3a", "B": "#a82e2e", "C": "#f0f0f0", "style": "jaket"},   # jaket merah
    "top5": {"A": "#e8b83a", "B": "#c99a2e", "C": "#33302e", "style": "hoodie"},  # hoodie kuning
    "top6": {"A": "#33333a", "B": "#26262c", "C": "#c9ced6", "style": "jaket"},   # jaket hitam
}
BOTTOMS = {"bottom1": "#3a5a8c", "bottom2": "#333338", "bottom3": "#c9b18a"}


ACCS = {
    # id: (warna utama "1", warna aksen "2") — "HAIR" = ikut warna rambut
    "acc_topi_posko": ("#2b2b30", "#8be04e"),
    "acc_topi_putih": ("#f0f0f0", "#c9ced6"),
    "acc_kacamata": ("#3a3238", "#3a3238"),
    "acc_headphone": ("#33333a", "#3a6fd8"),
    "acc_kucing": ("HAIR", "#f0a294"),
    "acc_halo": ("#f2c53d", "#f2c53d"),
    "acc_tanduk": ("#c93a3a", "#a82e2e"),
    "acc_masker": ("#f4f4f4", "#d9dee3"),
}

def draw_acc(g, cfg):
    a = cfg.get("acc", "none")
    if a == "none" or a not in ACCS:
        return
    if a in ("acc_topi_posko", "acc_topi_putih"):
        dome = {3: (18, 29), 4: (16, 31), 5: (14, 33), 6: (13, 34), 7: (12, 35), 8: (12, 35)}
        for y, (x0, x1) in dome.items():
            for x in range(x0, x1 + 1):
                g[y][x] = "1"
        for x in range(11, 37):
            g[9][x] = "1"
        for x in range(10, 38):
            g[10][x] = "1"
        for y in (5, 6, 7):
            for x in range(21, 27):
                g[y][x] = "W"
        g[6][23] = "2"; g[6][24] = "2"
    elif a == "acc_kacamata":
        for (x0, x1) in ((12, 22), (25, 35)):
            for x in range(x0, x1 + 1):
                put(g, x, 15, "1"); put(g, x, 22, "1")
            for y in range(15, 23):
                put(g, x0, y, "1"); put(g, x1, y, "1")
        for x in range(23, 25):
            put(g, x, 17, "1")
    elif a == "acc_headphone":
        for (y, x0, x1) in ((2, 20, 27), (3, 16, 31), (4, 14, 33), (5, 13, 34)):
            for x in range(x0, x1 + 1):
                if g[y][x] in ("H", "L", "."):
                    g[y][x] = "1"
        for cx in (6, 37):
            for y in range(13, 22):
                for x in range(cx, cx + 5):
                    g[y][x] = "1"
            for y in range(16, 19):
                for x in range(cx + 1, cx + 4):
                    g[y][x] = "2"
    elif a == "acc_kucing":
        for bx in (9, 32):
            rows = {0: (3, 3), 1: (2, 4), 2: (2, 5), 3: (1, 5), 4: (1, 6), 5: (0, 6), 6: (0, 6)}
            for y, (dx0, dx1) in rows.items():
                for dx in range(dx0, dx1 + 1):
                    g[y][bx + dx] = "1"
            for (dx, y) in ((3, 3), (3, 4), (4, 4)):
                g[y][bx + dx] = "2"
    elif a == "acc_halo":
        for x in range(19, 29):
            g[1][x] = "1"
        g[2][17] = "1"; g[2][18] = "1"; g[2][29] = "1"; g[2][30] = "1"
    elif a == "acc_tanduk":
        for (x, y) in [(11, 6), (11, 5), (12, 4), (12, 3), (13, 2), (36, 6), (36, 5), (35, 4), (35, 3), (34, 2)]:
            g[y][x] = "1"
    elif a == "acc_masker":
        for y in range(20, 26):
            x0 = 17 if y in (20, 25) else 16
            x1 = 30 if y in (20, 25) else 31
            for x in range(x0, x1 + 1):
                g[y][x] = "1"
        for x in range(18, 30):
            g[22][x] = "2"
        g[21][11] = "2"; g[21][36] = "2"

def compose(cfg):
    g = blank()
    skin = SKINS[cfg["skin"]]
    hairc = cfg["hairColor"]
    pal = {"S": skin, "s": darken(skin, 0.88), "K": "#3a3238", "W": "#ffffff",
           "E": cfg["eyeColor"], "M": "#a85751", "P": "#f0a294",
           "H": hairc, "L": lighten(hairc, 1.35)}
    pal.update({k: v for k, v in TOPS[cfg["top"]].items() if k != "style"})
    acc = cfg.get("acc", "none")
    if acc in ACCS:
        c1, c2 = ACCS[acc]
        pal["1"] = hairc if c1 == "HAIR" else c1
        pal["2"] = hairc if c2 == "HAIR" else c2
    draw_body(g, cfg, TOPS, BOTTOMS)
    draw_head(g, skin)
    draw_face(g, cfg, pal)
    draw_hair(g, cfg, pal)
    draw_acc(g, cfg)
    return g, pal

def render(cfg, path, scale=10):
    g, pal = compose(cfg)
    img = Image.new("RGB", (W, H), (226, 226, 226))
    px = img.load()
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c in pal:
                px[x, y] = tuple(int(pal[c].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    img.resize((W * scale, H * scale), Image.NEAREST).save(path)
    print("render:", path)

if __name__ == "__main__":
    base = {"skin": 0, "hair": "hair1", "hairColor": "#33302e", "eyes": "eye1",
            "eyeColor": "#3a3238", "brows": "brow1", "mouth": "mouth1",
            "top": "top1", "bottom": "bottom1"}
    render(base, "/home/hatch/workspace/posko/avatar-lab/base.png")
    for hst in ("hair2", "hair3", "hair4", "hair5", "hair6"):
        c = dict(base, hair=hst)
        render(c, "/home/hatch/workspace/posko/avatar-lab/%s.png" % hst)
