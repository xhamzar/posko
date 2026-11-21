# GET /api/topic?id= -> {topic, replies[]} satu topik + semua balasannya.
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import html as _html, os, re as _re, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import (db, send_json, topic_out, avatars_for, current_user,
                 jual_censor, unlocks_of, jual_strip)

_IMG_RE = _re.compile(r"https?://[^\s)\]]+?\.(?:png|jpe?g|gif|webp)(?:\?[^\s)\]]*)?", _re.I)
_YT_RE = _re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{6,})")

def _send_html(h, body, status=200):
    raw = body.encode("utf-8")
    h.send_response(status)
    h.send_header("Content-Type", "text/html; charset=utf-8")
    h.send_header("Content-Length", str(len(raw)))
    h.send_header("Cache-Control", "public, max-age=300")
    h.end_headers()
    h.wfile.write(raw)

def _share_page(h, tid):
    """Halaman /t/<id>: meta Open Graph buat preview WhatsApp dkk,
    lalu pengunjung manusia langsung diteruskan ke SPA topiknya."""
    host = h.headers.get("Host") or "www.poskoo.my.id"
    base = "https://" + host
    share_url = base + "/t/" + tid
    target = "/#/topic/" + tid
    snap = db().collection("posko_topics").document(tid).get()
    status = 200
    if not snap.exists:
        status = 404
        title = "Topik tidak ditemukan — POSKO"
        desc = "Topik ini tidak ada atau sudah dihapus. Mampir ke POSKO buat lihat obrolan lainnya."
        image = base + "/assets/og-posko.jpg"
        target = "/#/"
    else:
        d = snap.to_dict()
        title = (d.get("title") or "Topik di POSKO") + " — POSKO"
        raw = d.get("content") or ""
        clean = _re.sub(r"\[stiker:[^\]]*\]", "", jual_strip(raw))
        clean = _re.sub(r"https?://\S+", "", clean)
        clean = " ".join(clean.replace("**", "").split())
        excerpt = clean[:180] + ("…" if len(clean) > 180 else "")
        desc = ("oleh %s di POSKO · %s" % (d.get("author", ""), excerpt)) if excerpt \
            else ("Topik oleh %s di POSKO" % d.get("author", ""))
        m = _IMG_RE.search(raw)
        if m:
            image = m.group(0)
        else:
            y = _YT_RE.search(raw)
            image = ("https://i.ytimg.com/vi/%s/hqdefault.jpg" % y.group(1)) if y \
                else base + "/assets/og-posko.jpg"
    e = lambda s: _html.escape(str(s), quote=True)
    body = """<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8">
<title>%s</title>
<meta name="description" content="%s">
<meta property="og:type" content="article">
<meta property="og:site_name" content="POSKO">
<meta property="og:locale" content="id_ID">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="%s">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%s">
<meta name="twitter:description" content="%s">
<meta name="twitter:image" content="%s">
<meta http-equiv="refresh" content="0; url=%s">
<script>location.replace(%r)</script>
</head><body><p>Membuka topik di POSKO… <a href="%s">klik di sini bila tidak otomatis</a>.</p></body></html>""" % (
        e(title), e(desc), e(title), e(desc), e(share_url), e(image),
        e(title), e(desc), e(image), e(target), target, e(target))
    _send_html(h, body, status)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q = parse_qs(urlparse(self.path).query)
            share_id = (q.get("share") or [""])[0]
            if share_id:
                return _share_page(self, share_id)
            tid = (q.get("id") or [""])[0]
            ref = db().collection("posko_topics").document(tid)
            snap = ref.get()
            if not snap.exists:
                return send_json(self, {"error": "Topik tidak ditemukan"}, 404)
            tdoc = snap.to_dict()
            if (q.get("hit") or [""])[0] == "1":
                # hit=1 dikirim frontend sekali per sesi per topik (dedupe
                # di sessionStorage) — refresh/render ulang tidak menggelembungkan.
                from firebase_admin import firestore as _fs
                ref.update({"views": _fs.Increment(1)})
                tdoc["views"] = int(tdoc.get("views", 0) or 0) + 1
            replies = []
            for r in db().collection("posko_replies").where("topic", "==", tid).stream():
                d = r.to_dict()
                replies.append({"id": r.id, "topic": tid, "author": d.get("author", ""),
                                "content": d.get("content", ""), "created": d.get("created", ""),
                                "edited": d.get("edited", "")})
            replies.sort(key=lambda r: r["created"])
            t = topic_out(snap.id, tdoc)
            viewer = current_user(self)
            vname = viewer["username"] if viewer else None
            vrole = viewer.get("role") if viewer else None
            owned = unlocks_of(vname)

            def _idx(kind, ref):
                return {i for (k, r, i) in owned if k == kind and r == ref}

            if vname and (vname == t["author"] or vrole == "admin"):
                t["contentRaw"] = t["content"]
            t["content"] = jual_censor(t["content"], "topic", tid, vname,
                                       vrole, t["author"], _idx("topic", tid))
            for r in replies:
                if vname and (vname == r["author"] or vrole == "admin"):
                    r["contentRaw"] = r["content"]
                r["content"] = jual_censor(r["content"], "reply", r["id"],
                                            vname, vrole, r["author"],
                                            _idx("reply", r["id"]))
            av = avatars_for([t["author"]] + [r["author"] for r in replies])
            t["avatar"] = av.get(t["author"], "")
            for r in replies:
                r["avatar"] = av.get(r["author"], "")
            send_json(self, {"topic": t, "replies": replies})
        except Exception as e:
            send_json(self, {"error": "Gagal memuat topik: %s" % e}, 500)
    def log_message(self, *a):
        pass
