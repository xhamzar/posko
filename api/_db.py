# Helper bersama API POSKO: koneksi Firestore (firebase-admin) + auth mandiri.
# Database memakai project Firebase "tubexin" milik Driyan (sudah aktif untuk RuruHua),
# koleksi POSKO diprefix "posko_" biar tidak tabrakan dengan data RuruHua.
# Kredensial: env FIREBASE_SERVICE_ACCOUNT (JSON utuh) -> file api/_sa.json -> default.
import base64, hashlib, hmac, json, os, secrets, time
from datetime import datetime, timezone

_db = None

def db():
    global _db
    if _db is not None:
        return _db
    import firebase_admin
    from firebase_admin import credentials, firestore
    if not firebase_admin._apps:
        raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if raw:
            cred = credentials.Certificate(json.loads(raw))
        elif os.path.exists(os.path.join(os.path.dirname(__file__), "_sa.json")):
            cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "_sa.json"))
        else:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    _db = firestore.client()
    return _db

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# ---------- password (PBKDF2-HMAC-SHA256) ----------
def hash_password(pw):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000)
    return "pbkdf2$200000$%s$%s" % (salt.hex(), dk.hex())

def verify_password(pw, stored):
    try:
        _, iters, salt_hex, hash_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False

# ---------- token sesi (JWT-like, HMAC-SHA256) ----------
def _secret():
    s = os.environ.get("POSKO_SECRET")
    if s:
        return s.encode()
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")
    if not raw and os.path.exists(os.path.join(os.path.dirname(__file__), "_sa.json")):
        with open(os.path.join(os.path.dirname(__file__), "_sa.json")) as f:
            raw = f.read()
    return hashlib.sha256(raw.encode() or b"posko-dev-secret").digest()

def _b64e(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def _b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def make_token(user):
    head = _b64e(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64e(json.dumps({
        "u": user["username"], "r": user["role"],
        "exp": int(time.time()) + 30 * 24 * 3600}).encode())
    sig = _b64e(hmac.new(_secret(), (head + "." + payload).encode(), hashlib.sha256).digest())
    return head + "." + payload + "." + sig

def parse_token(tok):
    try:
        head, payload, sig = tok.split(".")
        expect = _b64e(hmac.new(_secret(), (head + "." + payload).encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expect):
            return None
        data = json.loads(_b64d(payload))
        if data.get("exp", 0) < int(time.time()):
            return None
        return data
    except Exception:
        return None

def current_user(handler):
    """Return dict user dari Firestore berdasarkan header Authorization, atau None."""
    auth = handler.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    data = parse_token(auth[7:].strip())
    if not data:
        return None
    snap = db().collection("posko_users").document(data["u"].lower()).get()
    if not snap.exists:
        return None
    u = snap.to_dict()
    return {"username": u["username"], "email": u["email"], "role": u["role"],
            "coins": int(u.get("coins", 0) or 0),
            "bio": u.get("bio", ""), "avatar": effective_avatar(u),
            "owned": u.get("avatar_owned", [])}

# ---------- profil & avatar ----------
AVATAR_IDS = ["kucing", "burunghantu", "rubah", "panda", "kodok", "harimau"]

def user_public(username):
    snap = db().collection("posko_users").document(username.lower()).get()
    if not snap.exists:
        return None
    u = snap.to_dict()
    return {"username": u["username"], "role": u.get("role", "member"),
            "joined": u.get("joined", ""), "bio": u.get("bio", ""),
            "avatar": effective_avatar(u), "coins": int(u.get("coins", 0) or 0),
            "owned": u.get("avatar_owned", []),
            "custom": u.get("avatar_custom", "")}

def avatars_for(names):
    """Peta username -> id avatar preset (buat nempel di topik/balasan)."""
    out = {}
    for n in set(names):
        p = user_public(n)
        out[n] = p["avatar"] if p else ""
    return out

# ---------- node bawaan ----------
NODE_COLORS = ["#2e4b3f", "#3a6fd8", "#c93a3a", "#e2703a",
               "#b8860b", "#8a5fc0", "#3f9e4d", "#546e7a"]
NODE_CREATE_COST = 200  # POSK untuk membuka Pos Jaga baru (admin gratis)
DEFAULT_NODES = [
    {"id": "umum", "name": "Umum", "desc": "Obrolan segala rupa", "order": 1,
     "color": "#2e4b3f", "owner": "admin"},
    {"id": "teknologi", "name": "Teknologi", "desc": "Gadget, software, internet", "order": 2,
     "color": "#3a6fd8", "owner": "admin"},
    {"id": "santai", "name": "Santai", "desc": "Ngobrol ringan penghilang penat", "order": 3,
     "color": "#e2703a", "owner": "admin"},
    {"id": "tanya", "name": "Tanya Jawab", "desc": "Bertanya apa saja, warga menjawab", "order": 4,
     "color": "#8a5fc0", "owner": "admin"},
]

def ensure_nodes():
    col = db().collection("posko_nodes")
    if not list(col.limit(1).stream()):
        for n in DEFAULT_NODES:
            col.document(n["id"]).set(n)
    out = []
    for d in col.order_by("order").stream():
        n = dict(d.to_dict())
        # lengkapi meta node lama (warna/penjaga) dari default bila id cocok
        base = next((x for x in DEFAULT_NODES if x["id"] == n.get("id")), None)
        if base:
            patch = {k: base[k] for k in ("color", "owner") if not n.get(k)}
            if patch:
                d.reference.update(patch)
                n.update(patch)
        out.append(n)
    return out


def make_node_id(name, existing):
    """Slug node dari nama: huruf kecil, strip; unik dgn sufiks angka."""
    import re as _re
    slug = _re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")[:24].strip("-")
    if len(slug) < 3:
        slug = "pos-" + (slug or "baru")
    base = slug
    i = 2
    while slug in existing:
        slug = "%s-%d" % (base, i)
        i += 1
    return slug


def node_owner(node_id):
    """Username Penjaga pos; 'admin' untuk pos bawaan/tim POSKO."""
    if not node_id:
        return "admin"
    snap = db().collection("posko_nodes").document(node_id).get()
    if snap.exists:
        return (snap.to_dict() or {}).get("owner") or "admin"
    return "admin"


def can_moderate_node(user, node_id):
    """Admin global, atau Penjaga pos itu sendiri."""
    if not user:
        return False
    if user.get("role") == "admin":
        return True
    owner = node_owner(node_id)
    return owner not in ("", "admin") and owner == user.get("username")


def node_meta(n):
    """Node + hitungan topik & pengikut untuk API."""
    d = db()
    topics = sum(1 for _ in d.collection("posko_topics")
                 .where("node", "==", n["id"]).stream())
    followers = sum(1 for _ in d.collection("posko_node_favs")
                    .where("node", "==", n["id"]).stream())
    return {"id": n["id"], "name": n.get("name", n["id"]),
            "desc": n.get("desc", ""), "color": n.get("color") or NODE_COLORS[0],
            "owner": n.get("owner", "admin"), "topics": topics,
            "followers": followers}

# ---------- HTTP helpers ----------
def send_json(handler, obj, status=200):
    raw = json.dumps(obj).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)

def read_body(handler):
    try:
        n = int(handler.headers.get("Content-Length") or 0)
        return json.loads(handler.rfile.read(n) or b"{}")
    except Exception:
        return {}

# ---------- POSKOIN (koin internal POSKO) ----------
# Saldo nempel di dokumen user (field "coins"); semua mutasi tercatat di
# koleksi posko_coin_tx {from, to, amount, type, note, created}.
# type: welcome | reward | tip | grant. from/to null = sistem (mint/burn).
COIN_WELCOME = 20
COIN_TOPIC = 5
COIN_REPLY = 2
COIN_DAILY_CAP = 20
COIN_MIN_REPLY_LEN = 10

def coin_balance(username):
    snap = db().collection("posko_users").document(username.lower()).get()
    if not snap.exists:
        return 0
    return int(snap.to_dict().get("coins", 0) or 0)

def _coin_tx(frm, to, amount, typ, note=""):
    db().collection("posko_coin_tx").document().set({
        "from": frm, "to": to, "amount": int(amount), "type": typ,
        "note": note, "created": now_iso()})

def coin_credit(username, amount, typ, note="", frm=None):
    """Tambah saldo user (mint dari sistem / grant admin)."""
    from firebase_admin import firestore as _fs
    amount = int(amount)
    if amount <= 0:
        return coin_balance(username)
    db().collection("posko_users").document(username.lower()).update(
        {"coins": _fs.Increment(amount)})
    _coin_tx(frm, username, amount, typ, note)
    return coin_balance(username)

def coin_tip(frm_user, to_user, amount):
    """Transfer antar user secara transaksional; gagal bila saldo kurang."""
    from firebase_admin import firestore as _fs
    d = db()
    sref = d.collection("posko_users").document(frm_user.lower())
    rref = d.collection("posko_users").document(to_user.lower())
    tx = d.transaction()

    @_fs.transactional
    def _do(tx):
        ss = sref.get(transaction=tx)
        if not ss.exists:
            raise ValueError("Pengirim tidak ditemukan")
        rs = rref.get(transaction=tx)
        if not rs.exists:
            raise ValueError("Penerima tidak ditemukan")
        sbal = int(ss.to_dict().get("coins", 0) or 0)
        if sbal < amount:
            raise ValueError("Saldo POSK tidak cukup")
        rbal = int(rs.to_dict().get("coins", 0) or 0)
        tx.update(sref, {"coins": sbal - amount})
        tx.update(rref, {"coins": rbal + amount})

    _do(tx)
    _coin_tx(frm_user, to_user, amount, "tip")
    return coin_balance(frm_user)

def coin_revoke(username, amount, admin_name):
    """Tarik saldo user (burn) oleh admin; gagal bila saldo kurang."""
    from firebase_admin import firestore as _fs
    d = db()
    ref = d.collection("posko_users").document(username.lower())
    tx = d.transaction()

    @_fs.transactional
    def _do(tx):
        ss = ref.get(transaction=tx)
        if not ss.exists:
            raise ValueError("User tidak ditemukan")
        bal = int(ss.to_dict().get("coins", 0) or 0)
        if bal < amount:
            raise ValueError("Saldo user tidak cukup untuk ditarik segitu")
        tx.update(ref, {"coins": bal - amount})

    _do(tx)
    _coin_tx(username, None, amount, "grant", "Ditarik oleh admin " + admin_name)
    return coin_balance(username)

def coin_award_activity(username, kind):
    """Reward aktivitas (topik/balasan) dengan batas harian anti-farming."""
    amount = COIN_TOPIC if kind == "topic" else COIN_REPLY
    today = now_iso()[:10]
    earned = 0
    q = db().collection("posko_coin_tx").where("to", "==", username).where("type", "==", "reward")
    for s in q.stream():
        d = s.to_dict()
        if str(d.get("created", "")).startswith(today):
            earned += int(d.get("amount", 0) or 0)
    if earned >= COIN_DAILY_CAP:
        return 0
    amount = min(amount, COIN_DAILY_CAP - earned)
    note = "Reward topik baru" if kind == "topic" else "Reward balasan"
    coin_credit(username, amount, "reward", note)
    return amount

# ---------- konten berbayar [jual=HARGA]...[/jual] ----------
import re as _jre
JUAL_RE = _jre.compile(r"\[jual=(\d{1,7})\](.*?)\[/jual\]", _jre.S | _jre.I)
JUAL_MAX_PRICE = 100000
JUAL_FEE_PCT = 10


def _jual_price(raw):
    try:
        p = int(raw)
    except Exception:
        return 0
    return p if 1 <= p <= JUAL_MAX_PRICE else 0


def jual_parse(content):
    """Daftar (harga, isi) blok [jual] sesuai urutan; harga 0 = tidak valid."""
    return [(_jual_price(m.group(1)), m.group(2))
            for m in JUAL_RE.finditer(content or "")]


def jual_strip(content):
    """Buang isi blok berbayar (untuk daftar/pencarian): ganti penanda teks."""
    def repl(m):
        return " [konten berbayar] " if _jual_price(m.group(1)) else m.group(2)
    return JUAL_RE.sub(repl, content or "")


def unlocks_of(username):
    """Set (kind, ref, idx) blok yang sudah dibeli user."""
    out = set()
    if not username:
        return out
    for d in db().collection("posko_unlocks").where("user", "==", username).stream():
        dd = d.to_dict()
        out.add((dd.get("kind"), dd.get("ref"), int(dd.get("idx", 0) or 0)))
    return out


def jual_censor(content, kind, ref_id, viewer_name, viewer_role, author, owned_idx):
    """Ganti blok [jual] dengan token frontend: LOCKED (isi dibuang) atau
    OPEN (isi tetap, dibungkus penanda). Penulis/admin/pembeli melihat OPEN."""
    state = {"i": 0}

    def repl(m):
        idx = state["i"]
        state["i"] += 1
        price = _jual_price(m.group(1))
        inner = m.group(2)
        if not price:
            return inner
        can_see = bool(viewer_name) and (
            viewer_name == author or viewer_role == "admin" or idx in owned_idx)
        if can_see:
            return ("[[JUAL-OPEN:%s:%s:%d:%d]]%s[[/JUAL-OPEN]]"
                    % (kind, ref_id, idx, price, inner))
        return "[[JUAL-LOCKED:%s:%s:%d:%d]]" % (kind, ref_id, idx, price)

    return JUAL_RE.sub(repl, content or "")


def coin_unlock(buyer, kind, ref, idx):
    """Beli satu blok [jual]: buyer bayar harga penuh, penulis menerima
    harga - fee 10% (fee hangus ke POSKO). Return saldo buyer."""
    from firebase_admin import firestore as _fs
    col = {"topic": "posko_topics", "reply": "posko_replies"}.get(kind)
    if not col:
        raise ValueError("Jenis konten tidak dikenal")
    snap = db().collection(col).document(ref).get()
    if not snap.exists:
        raise ValueError("Konten tidak ditemukan")
    d = snap.to_dict()
    blocks = jual_parse(d.get("content", ""))
    if idx < 0 or idx >= len(blocks):
        raise ValueError("Blok berbayar tidak ditemukan")
    price = blocks[idx][0]
    if not price:
        raise ValueError("Harga blok tidak valid")
    author = d.get("author", "")
    if author.lower() == buyer.lower():
        raise ValueError("Ini tulisanmu sendiri")
    fee = price * JUAL_FEE_PCT // 100
    net = price - fee
    dd = db()
    ukey = "%s__%s_%s_%d" % (buyer.lower(), kind, ref, idx)
    uref = dd.collection("posko_unlocks").document(ukey)
    bref = dd.collection("posko_users").document(buyer.lower())
    aref = dd.collection("posko_users").document(author.lower())
    tx = dd.transaction()

    @_fs.transactional
    def _do(tx):
        if uref.get(transaction=tx).exists:
            raise ValueError("Konten ini sudah kamu buka")
        bs = bref.get(transaction=tx)
        if not bs.exists:
            raise ValueError("User tidak ditemukan")
        bal = int(bs.to_dict().get("coins", 0) or 0)
        if bal < price:
            raise ValueError("Saldo POSK tidak cukup")
        asnap = aref.get(transaction=tx)
        abal = int(asnap.to_dict().get("coins", 0) or 0) if asnap.exists else 0
        tx.update(bref, {"coins": bal - price})
        if asnap.exists:
            tx.update(aref, {"coins": abal + net})
        tx.set(uref, {"user": buyer, "kind": kind, "ref": ref, "idx": idx,
                      "price": price, "fee": fee, "author": author,
                      "created": now_iso()})

    _do(tx)
    _coin_tx(buyer, author, net, "unlock",
             "Buka konten berbayar seharga %d POSK" % price)
    if fee:
        _coin_tx(buyer, "POSKO", fee, "fee", "Biaya pos 10% buka konten")
    return coin_balance(buyer)


def topic_out(doc_id, d):
    return {"id": doc_id, "node": d.get("node", ""), "author": d.get("author", ""),
            "title": d.get("title", ""), "content": d.get("content", ""),
            "created": d.get("created", ""), "last": d.get("last", ""),
            "pinned": bool(d.get("pinned")), "locked": bool(d.get("locked")),
            "replies": int(d.get("replyCount", 0)),
            "views": int(d.get("views", 0) or 0),
            "tags": list(d.get("tags") or [])}

import re as _re_tags
_TAG_BAD = _re_tags.compile(r"[^a-z0-9-]+")
_TAG_DASH = _re_tags.compile(r"-{2,}")

def normalize_tags(raw):
    """Normalisasi tag: huruf kecil, spasi->-, maks 5 tag, 2-24 char/tag."""
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = raw.split(",")
    elif isinstance(raw, (list, tuple)):
        parts = [str(x) for x in raw]
    else:
        return []
    out = []
    for p in parts:
        t = _TAG_DASH.sub("-", _TAG_BAD.sub("", p.strip().lower().replace(" ", "-").replace("_", "-"))).strip("-")
        if 2 <= len(t) <= 24 and t not in out:
            out.append(t)
        if len(out) >= 5:
            break
    return out

# ---------- notifikasi mention (@username) ----------
import re as _re
MENTION_RE = _re.compile(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_]{3,24})")

def notify_mentions(author, content, topic_id, topic_title=""):
    """Buat notif untuk tiap user valid yang di-@ dalam content (maks 10).

    Best-effort: pemanggil membungkusnya dengan try/except agar kegagalan
    notif tidak pernah menggagalkan pembuatan topik/balasan.
    """
    names = []
    for m in MENTION_RE.finditer(content or ""):
        n = m.group(1)
        if n.lower() != author.lower() and n.lower() not in [x.lower() for x in names]:
            names.append(n)
    for n in names[:10]:
        snap = db().collection("posko_users").document(n.lower()).get()
        if not snap.exists:
            continue
        db().collection("posko_notifs").document().set({
            "user": snap.to_dict().get("username", n), "from": author,
            "kind": "mention", "topic": topic_id, "title": topic_title,
            "snippet": (content or "")[:90], "created": now_iso(), "read": False})

# ---------- avatar kustom (pixel) + toko POSKOIN ----------
AVATAR_HAIR_COLORS = ["#33302e", "#5a3a26", "#8a5a33", "#b57748", "#e8e3da",
                      "#9aa3ad", "#c93a3a", "#e2703a", "#e8c95a", "#e88bb0",
                      "#58a05c", "#3a6fd8", "#8a5fc0"]
AVATAR_EYE_COLORS = ["#3a3238", "#7a4a21", "#3a6fd8", "#3f9e4d", "#c93a3a", "#8a5fc0"]
AVATAR_PARTS = {
    "hair": ["hair1", "hair2", "hair3", "hair4", "hair5", "hair6", "hair7", "hair8"],
    "eyes": ["eye1", "eye2", "eye3", "eye4", "eye5"],
    "brows": ["brow1", "brow2", "brow3"],
    "mouth": ["mouth1", "mouth2", "mouth3", "mouth4"],
    "top": ["top1", "top2", "top3", "top4", "top5", "top6"],
    "bottom": ["bottom1", "bottom2", "bottom3", "bottom4"],
    "shoes": ["shoe1", "shoe2", "shoe3", "shoe4"],
    "acc": ["none", "acc_topi_posko", "acc_topi_putih", "acc_kacamata",
            "acc_headphone", "acc_kucing", "acc_halo", "acc_tanduk",
            "acc_masker", "acc_syal"],
    "pet": ["none", "pet_kucing", "pet_penguin", "pet_bebek"],
    "frame": ["none", "frame1", "frame2", "frame3", "frame4"],
}
# item berbayar (POSK); yang tidak tercantum = gratis
AVATAR_SHOP = {"hair4": 40, "hair5": 30, "hair7": 50, "hair8": 70,
               "top4": 60, "top5": 50, "top6": 80, "shoe3": 40,
               "acc_topi_posko": 100, "acc_topi_putih": 30, "acc_kacamata": 40,
               "acc_masker": 30, "acc_syal": 50, "acc_kucing": 60,
               "acc_headphone": 80, "acc_tanduk": 90, "acc_halo": 120,
               "pet_kucing": 150, "pet_penguin": 120, "pet_bebek": 100,
               "frame1": 80, "frame2": 60, "frame3": 150, "frame4": 90}
AVATAR_DEFAULT = {"skin": 0, "hair": "hair1", "hairColor": "#33302e",
                  "eyes": "eye1", "eyeColor": "#3a3238", "brows": "brow1",
                  "mouth": "mouth1", "top": "top1", "bottom": "bottom1",
                  "shoes": "shoe1", "acc": "none", "pet": "none",
                  "frame": "none"}

def validate_avatar_config(cfg, owned):
    """Validasi config avatar. Return (json_str, error).
    Field yang hilang diisi default (config v1 tetap sah)."""
    if not isinstance(cfg, dict):
        return None, "Config avatar tidak valid"
    owned = set(owned or [])
    out = dict(AVATAR_DEFAULT)
    out.update(cfg)
    try:
        skin = int(out.get("skin", 0))
    except Exception:
        return None, "Warna kulit tidak valid"
    if skin < 0 or skin > 3:
        return None, "Warna kulit tidak valid"
    out["skin"] = skin
    for field, valid in AVATAR_PARTS.items():
        v = out.get(field)
        if v not in valid:
            return None, "Pilihan %s tidak dikenal" % field
        if v in AVATAR_SHOP and v not in owned:
            return None, "Item %s belum dimiliki — beli dulu pakai POSK" % v
        out[field] = v
    if out.get("hairColor") not in AVATAR_HAIR_COLORS:
        return None, "Warna rambut tidak dikenal"
    if out.get("eyeColor") not in AVATAR_EYE_COLORS:
        return None, "Warna mata tidak dikenal"
    known = set(AVATAR_DEFAULT.keys())
    out = {k: v for k, v in out.items() if k in known}
    return json.dumps(out, separators=(",", ":"), sort_keys=True), None


def effective_avatar(user_dict):
    """String avatar efektif: 'a:<json>' (aset) > 'c:<json>' (pixel lama) > preset."""
    u = user_dict or {}
    asset = u.get("avatar_asset") or ""
    if asset:
        return "a:" + asset
    custom = u.get("avatar_custom") or ""
    if custom:
        return "c:" + custom
    return u.get("avatar", "")


# ---------- avatar aset (potongan gambar CDN) ----------
# Kategori -> awalan id item yang sah. Harga di ASSET_PRICES (POSK);
# kosong = semua gratis (mode tes). Isi harga di sini + di manifest
# avatar GitHub untuk mengaktifkan toko avatar aset.
ASSET_CATS = {"body": "body_", "face": "face_", "mulut": "mulut_",
              "hair": "hair_", "outfit": "outfit_", "celana": "celana_",
              "spatu": "spatu_", "acc": "acc_", "back": "backitem_",
              "hand": "handitem_", "pet": "pet_", "border": "border_",
              "status": "status_", "model": "model_"}
ASSET_PRICES = {}
ASSET_DEFAULT = {"body": "body_1", "face": "face_0", "hair": "hair_2",
                 "outfit": "outfit_0", "celana": "celana_0", "spatu": "spatu_0"}
ASSET_ID_RE = __import__("re").compile(r"^[a-z0-9_]+$")


def validate_asset_config(cfg, owned):
    """Validasi config avatar aset. Return (json_str, error)."""
    if not isinstance(cfg, dict):
        return None, "Config avatar tidak valid"
    owned = set(owned or [])
    out = {}
    for cat, prefix in ASSET_CATS.items():
        v = cfg.get(cat)
        if v is None or v == "":
            if cat in ASSET_DEFAULT:
                out[cat] = ASSET_DEFAULT[cat]
            continue
        if not isinstance(v, str) or not ASSET_ID_RE.match(v) or not v.startswith(prefix):
            return None, "Pilihan %s tidak dikenal" % cat
        price = ASSET_PRICES.get(v)
        if price and v not in owned:
            return None, "Item %s belum dimiliki — beli dulu pakai POSK" % v
        out[cat] = v
    for cat, dv in ASSET_DEFAULT.items():
        out.setdefault(cat, dv)
    return json.dumps(out, separators=(",", ":"), sort_keys=True), None
